# Architecture Guide

**How the AdventureWorksLT Bronze datakit works**

This guide explains the code architecture so you can understand, modify, and extend it.

---

## The Big Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Data Flow                                │
└─────────────────────────────────────────────────────────────────┘

   SQL Server                                    PostgreSQL
   (Source)                                      (Bronze Warehouse)

   ┌──────────────┐                             ┌──────────────────┐
   │AdventureWorks│                              │bronze_warehouse  │
   │      LT      │                              │                  │
   │              │                              │                  │
   │  SalesLT.    │   1. sqlcmd + Kerberos      │  bronze.         │
   │  Product     │   ───────────────────>       │  product_        │
   │  Category    │                              │  category        │
   │              │   2. Add Bronze metadata    │                  │
   │  (41 rows)   │   ───────────────────>       │  + metadata      │
   │              │                              │  (41 rows)       │
   └──────────────┘   3. Load to PostgreSQL     └──────────────────┘
                      ───────────────────>               │
                                                         │
                      4. Write to files                  │
                      ───────────────────>        ┌──────v───────┐
                                                  │ /tmp/bronze/ │
                                                  │  - parquet   │
                                                  │  - json      │
                                                  └──────────────┘
```

---

## Component Overview

### 1. Configuration (config.yaml)

**Purpose:** Single source of truth for database connections and settings.

**Structure:**
```yaml
source:              # Where data comes from
  host: ...
  database: ...
  use_kerberos: ...
  tables: [...]      # What to extract

target:              # Where data goes
  host: ...
  database: ...
  schema: "bronze"

storage:             # File storage options
  bronze_path: ...
  formats: [...]
```

**Why separate config?**
- Change databases without modifying code
- Different configs for dev/test/prod
- Easy to see what's being extracted

---

### 2. Bronze Models (bronze_datakits_adventureworkslt/models/)

**Purpose:** Define the structure of Bronze tables in PostgreSQL.

**Example: product_category_bronze.py**
```python
class ProductCategoryBronze(BronzeMetadata, SQLModel, table=True):
    __tablename__ = "bronze_product_category"
    __table_args__ = {"schema": "bronze"}

    # Source fields
    productcategoryid: int = Field(primary_key=True)
    parentproductcategoryid: Optional[int] = None
    name: str
    rowguid: uuid.UUID
    modifieddate: datetime

    # Inherits from BronzeMetadata:
    # - bronze_load_timestamp
    # - bronze_source_system
    # - bronze_source_table
    # - bronze_source_host
    # - bronze_extraction_method
```

**Key concepts:**

1. **Inheritance from BronzeMetadata**
   - Automatically adds standard Bronze columns
   - Tracks data lineage
   - Implemented in sqlmodel-framework

2. **SQLModel table=True**
   - Creates actual PostgreSQL table
   - Uses SQLAlchemy under the hood
   - Type-safe Python models

3. **Field definitions**
   - `Field(primary_key=True)` - Primary key
   - `Optional[type]` - Nullable columns
   - `max_length` - String length limits

**Why models?**
- Schema as code (version controlled)
- Type safety (catch errors early)
- Auto-generate tables
- Clear documentation

---

### 3. Loader (bronze_datakits_adventureworkslt/loader.py)

**Purpose:** Orchestrates the extraction and loading process.

**Key class:**
```python
class AdventureWorksLTBronzeLoader(BronzeIngestionPipeline):
    TABLE_MODEL_MAP = {
        "SalesLT.ProductCategory": ProductCategoryBronze,
        # Maps SQL Server tables to Python models
    }
```

**Main methods:**

#### extract_table(table_name)
**What it does:**
1. Uses `sqlcmd` to query SQL Server
2. Parses CSV output into pandas DataFrame
3. Converts column names to lowercase
4. Handles NULLs properly

```python
def extract_table(self, table_name: str) -> pd.DataFrame:
    # Build sqlcmd command with Kerberos (-G flag)
    cmd = ["sqlcmd", "-S", self.source_host, "-d", self.source_database,
           "-G", "-C", "-Q", f"SELECT * FROM {table_name}"]

    # Execute and parse CSV output
    result = subprocess.run(cmd, capture_output=True, text=True)
    df = pd.read_csv(io.StringIO(result.stdout), names=columns)

    # Normalize column names (PascalCase → lowercase)
    df.columns = [col.lower() for col in df.columns]

    return df
```

**Why sqlcmd?**
- Native Kerberos support (``-G` flag)
- No need for pyodbc or ODBC drivers
- Simple text output (easy to parse)
- Works in containers

#### load_table(table_name)
**What it does:**
1. Extract data from source
2. Handle NULLs (convert NaN → None)
3. Add Bronze metadata
4. Write to PostgreSQL
5. Write to Parquet/JSON files

```python
def load_table(self, table_name: str) -> Dict:
    # 1. Extract
    df = self.extract_table(table_name)

    # 2. Handle NULLs
    df = df.replace({pd.NA: None, pd.NaT: None, np.nan: None})

    # 3. Add Bronze metadata
    df = self.add_bronze_metadata(
        df,
        source_system="adventureworkslt_kerberos",
        source_table=table_name,
        source_host=self.source_host,
        extraction_method="full_snapshot"
    )

    # 4. Write to PostgreSQL
    if self.target_db_url:
        # ... write to database

    # 5. Write to files
    paths = self.write_bronze(df, ...)

    return {"rows_loaded": len(df), "table": table_name, "paths": paths}
```

**Why this workflow?**
- Separation of concerns (extract ≠ transform ≠ load)
- Data lineage tracking
- Dual storage (database + files)
- Easy to test each step

---

### 4. Setup Script (setup_bronze_warehouse.py)

**Purpose:** Creates the Bronze warehouse infrastructure.

**What it does:**
```python
def main():
    # 1. Load configuration
    config = load_config()

    # 2. Create bronze_warehouse database
    create_database(config)

    # 3. Create bronze schema and tables
    create_schema_and_tables(config)

    # 4. Verify setup
    verify_setup(config)
```

**Key operations:**

1. **Database creation:**
   ```python
   engine = create_engine(..., isolation_level="AUTOCOMMIT")
   conn.execute(text("CREATE DATABASE bronze_warehouse"))
   ```
   - Uses AUTOCOMMIT (required for CREATE DATABASE)
   - Handles "already exists" gracefully

2. **Schema & table creation:**
   ```python
   conn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze"))
   SQLModel.metadata.create_all(engine)
   ```
   - Creates schema first
   - SQLModel auto-generates CREATE TABLE statements

**Why separate setup script?**
- Run once (not every extraction)
- Can be run by DBA for initial setup
- Verifies infrastructure before data loads

---

### 5. Test Runner (test_loader.py)

**Purpose:** Demonstrates the complete pipeline.

**What it does:**
```python
def main():
    # 1. Load config
    config = load_config()

    # 2. Build database URLs
    target_url = build_target_url(config)

    # 3. Create loader
    loader = AdventureWorksLTBronzeLoader(
        source_host=config['source']['host'],
        source_database=config['source']['database'],
        target_db_url=target_url
    )

    # 4. Extract each table
    for table_name in config['source']['tables']:
        result = loader.load_table(table_name)
        # ... show results
```

**Why this pattern?**
- Configuration-driven (no hardcoded values)
- Easy to adapt for Airflow DAG
- Clear success/failure reporting

---

## Data Flow in Detail

### Step 1: Extract from SQL Server

```
SQL Server (SalesLT.ProductCategory)
  ProductCategoryID | ParentProductCategoryID | Name   | rowguid | ModifiedDate
  ──────────────────┼─────────────────────────┼────────┼─────────┼──────────────
  1                 | NULL                    | Bikes  | ...     | 2002-06-01
  2                 | NULL                    | Components | ... | 2002-06-01

         │
         │ sqlcmd -G (Kerberos)
         │ Parse CSV output
         ▼

Pandas DataFrame (lowercase columns)
  productcategoryid | parentproductcategoryid | name   | rowguid | modifieddate
  ──────────────────┼─────────────────────────┼────────┼─────────┼──────────────
  1                 | None                    | Bikes  | ...     | 2002-06-01
  2                 | None                    | Components | ... | 2002-06-01
```

**Key transformations:**
- Column names: PascalCase → lowercase
- NULLs: SQL Server NULL → pandas None

---

### Step 2: Add Bronze Metadata

```python
df = self.add_bronze_metadata(
    df,
    source_system="adventureworkslt_kerberos",
    source_table="SalesLT.ProductCategory",
    source_host="sql1.eruditis.lab",
    extraction_method="full_snapshot"
)
```

**Adds columns:**
```
productcategoryid | name  | bronze_load_timestamp    | bronze_source_system       | ...
──────────────────┼───────┼──────────────────────────┼────────────────────────────┼─────
1                 | Bikes | 2025-11-03 10:42:03.341  | adventureworkslt_kerberos  | ...
```

---

### Step 3: Write to PostgreSQL

```python
with Session(engine) as session:
    for _, row in df.iterrows():
        instance = ProductCategoryBronze(**row.to_dict())
        session.add(instance)
    session.commit()
```

**Creates:**
```sql
INSERT INTO bronze.bronze_product_category (
    productcategoryid,
    parentproductcategoryid,
    name,
    rowguid,
    modifieddate,
    bronze_load_timestamp,
    bronze_source_system,
    bronze_source_table,
    bronze_source_host,
    bronze_extraction_method
) VALUES (...);
```

---

### Step 4: Write to Files

```python
paths = self.write_bronze(
    df,
    source_system="adventureworkslt_kerberos",
    table_name="SalesLT_ProductCategory",
    formats=['parquet', 'json']
)
```

**Creates files:**
```
/tmp/bronze/
  └── adventureworkslt_kerberos/
      └── SalesLT_ProductCategory/
          ├── latest.parquet
          ├── latest.json
          └── 2025-11-03_104203.parquet
```

**Why both database and files?**
- **Database:** Fast queries, SQL access
- **Files:** Backup, data lake integration, Spark processing

---

## Extension Points

### Adding a New Table

**What you need to change:**

1. **Model** (`models/your_table_bronze.py`)
   - Define table structure
   - Map SQL Server columns to Python types

2. **Model registry** (`models/__init__.py`)
   - Import new model
   - Add to `__all__`

3. **Loader mapping** (`loader.py`)
   - Add to `TABLE_MODEL_MAP`

4. **Configuration** (`config.yaml`)
   - Add to `tables` list

**Nothing else needs to change!** The framework handles:
- Table creation
- Data extraction
- Metadata addition
- File writing

---

### Custom Transformations

Add logic in `load_table()`:

```python
def load_table(self, table_name: str) -> Dict:
    df = self.extract_table(table_name)

    # Custom transformations here
    if table_name == "SalesLT.Customer":
        # Mask email addresses
        df['emailaddress'] = df['emailaddress'].str.replace(
            r'@.*', '@example.com', regex=True
        )

    # Continue with standard processing
    df = self.add_bronze_metadata(...)
```

---

### Incremental Loads

Modify `extract_table()` to support watermarks:

```python
def extract_table(self, table_name: str,
                  since_timestamp: Optional[datetime] = None) -> pd.DataFrame:
    if since_timestamp:
        query = f"""
            SELECT * FROM {table_name}
            WHERE ModifiedDate > '{since_timestamp}'
        """
    else:
        query = f"SELECT * FROM {table_name}"

    # Execute query with sqlcmd...
```

---

## Design Decisions

### Why sqlcmd instead of pyodbc?

**Pros:**
- ✅ Native Kerberos support
- ✅ No ODBC driver installation
- ✅ Works in containers easily
- ✅ Simple text output

**Cons:**
- ❌ Less efficient for large datasets
- ❌ Text parsing overhead
- ❌ Limited data type inference

**Verdict:** Good for Bronze layer (full snapshots, moderate sizes). For very large tables, consider pyodbc with pagination.

---

### Why separate models from loader?

**Separation allows:**
- Reuse models in different loaders
- Version control schema independently
- Auto-generate documentation from models
- Type-safe data access

---

### Why BronzeMetadata mixin?

**Standardizes:**
- Common Bronze columns across all tables
- Data lineage tracking
- Audit trail for compliance
- Framework consistency

---

## Next Steps

- **Add tables** → [CONFIGURATION.md](CONFIGURATION.md)
- **Deploy** → [DEPLOYMENT.md](DEPLOYMENT.md)
- **Build images** → [IMAGES.md](IMAGES.md)
