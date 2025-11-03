# AdventureWorksLT Bronze Layer Example

## SQL Server (MSSQL) → PostgreSQL Bronze Data Pipeline with Kerberos Authentication

This example demonstrates extracting data from **SQL Server** using **Kerberos authentication** and loading it into a **PostgreSQL** Bronze warehouse. Perfect for enterprise environments using Windows Active Directory / Samba AD for authentication.

**What this example does:**
- ✓ Connects to SQL Server using Kerberos (no passwords in code!)
- ✓ Extracts tables from AdventureWorksLT sample database
- ✓ Adds Bronze layer metadata (source system, load timestamp, etc.)
- ✓ Loads data into PostgreSQL Bronze warehouse with Kerberos auth
- ✓ Writes data to Parquet and JSON files for backup/analysis

---

## Quick Start (5 Steps!)

### Step 1: Prerequisites

Before you begin, ensure you have:

**System Requirements:**
- Python 3.9+
- `uv` package manager installed ([instructions](https://github.com/astral-sh/uv))
- `sqlcmd` for SQL Server ([install guide](https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-utility))
- Access to:
  - SQL Server instance with AdventureWorksLT database
  - PostgreSQL instance for Bronze warehouse

**Authentication Requirements:**
- **Kerberos ticket** (run `kinit your_username@YOUR.REALM`)
  - Verify with `klist` - you should see your principal
- SQL Server configured for Kerberos authentication
- PostgreSQL configured for GSSAPI authentication (see [pg_hba.conf setup](#postgresql-kerberos-setup))

**Quick verification:**
```bash
# Check Kerberos ticket
klist

# Test SQL Server connection
sqlcmd -S your-mssql-host -G -C -Q "SELECT @@VERSION"

# Test PostgreSQL connection
psql -h your-pg-host -d postgres -c "SELECT version()"
```

### Step 2: Clone and Install

```bash
# Clone the repository
git clone https://github.com/Troubladore/airflow-data-platform-examples.git
cd airflow-data-platform-examples/adventureworks-bronze

# Install dependencies with uv
uv sync
```

This installs:
- pandas (data manipulation)
- sqlalchemy & sqlmodel (database ORM)
- psycopg2 (PostgreSQL driver with Kerberos support)
- pyarrow (Parquet file format)
- pyyaml (configuration files)

### Step 3: Configure Your Environment

Edit `config.yaml` with your server details:

```yaml
# Source Database (SQL Server)
source:
  host: "sql1.eruditis.lab"          # ← Change to your SQL Server
  database: "AdventureWorksLT"       # ← Your source database
  use_kerberos: true

  tables:
    - "SalesLT.ProductCategory"      # ← Add more tables here

# Target Database (PostgreSQL)
target:
  host: "sqlpg.eruditis.lab"         # ← Change to your PostgreSQL server
  port: 5432
  database: "bronze_warehouse"
  schema: "bronze"
  use_kerberos: true

# Storage
storage:
  bronze_path: "/tmp/bronze"         # ← Where to write Parquet/JSON files
  formats:
    - "parquet"
    - "json"
```

**For password authentication instead of Kerberos:**
```yaml
source:
  use_kerberos: false
  # SQL Server uses Windows Auth by default, for SQL auth see docs

target:
  use_kerberos: false
  user: "your_username"
  password: "your_password"  # Or leave empty for prompt
```

### Step 4: Setup Bronze Warehouse

```bash
# This creates the bronze_warehouse database and tables
uv run python setup_bronze_warehouse.py
```

**What this does:**
1. Creates `bronze_warehouse` database on PostgreSQL
2. Creates `bronze` schema
3. Creates Bronze tables (e.g., `bronze_product_category`)
4. Verifies setup

**Expected output:**
```
================================================================================
Bronze Warehouse Setup
================================================================================
Source: AdventureWorksLT on sql1.eruditis.lab
Target: bronze_warehouse on sqlpg.eruditis.lab

Step 1: Creating bronze_warehouse database
✓ Database 'bronze_warehouse' created successfully

Step 2: Creating bronze schema and tables
✓ Schema 'bronze' created
✓ All Bronze tables created successfully

Step 3: Verifying setup
✓ Connected to database: bronze_warehouse
✓ Schema 'bronze' exists
✓ Found 1 table(s) in bronze schema

SUCCESS! Bronze warehouse is ready to use.
```

### Step 5: Run the Extraction

```bash
# Extract data from SQL Server → PostgreSQL
uv run python test_loader.py
```

**Expected output:**
```
================================================================================
AdventureWorksLT Bronze Loader Test
================================================================================
Source: AdventureWorksLT on sql1.eruditis.lab
Target: bronze_warehouse on sqlpg.eruditis.lab
Tables to extract: 1

================================================================================
Extracting: SalesLT.ProductCategory
================================================================================
✓ Successfully loaded 41 rows
  Files written:
    - parquet
    - json

================================================================================
SUMMARY
================================================================================
Tables processed: 1/1
Total rows loaded: 41
```

---

## Verify Your Data

### Check PostgreSQL Database

```bash
# Connect to bronze_warehouse
psql -h sqlpg.eruditis.lab -d bronze_warehouse

# View the data
SELECT productcategoryid, name, bronze_source_system, bronze_load_timestamp
FROM bronze.bronze_product_category
ORDER BY productcategoryid
LIMIT 10;
```

**What you'll see:**
- All source columns (`productcategoryid`, `name`, etc.)
- Bronze metadata columns:
  - `bronze_load_timestamp` - When data was loaded
  - `bronze_source_system` - Identifier (e.g., "adventureworkslt_kerberos")
  - `bronze_source_table` - Original table name
  - `bronze_source_host` - Source server
  - `bronze_extraction_method` - How data was extracted

### Check File Storage

```bash
# View parquet files
ls -lh /tmp/bronze/adventureworkslt_kerberos/SalesLT_ProductCategory/

# Read parquet with pandas
uv run python -c "import pandas as pd; df = pd.read_parquet('/tmp/bronze/adventureworkslt_kerberos/SalesLT_ProductCategory/latest.parquet'); print(df.head())"
```

---

## Adding More Tables

Want to extract more tables from AdventureWorksLT? Follow these 3 steps:

### 1. Identify the Table in SQL Server

```bash
# List all tables in AdventureWorksLT
sqlcmd -S sql1.eruditis.lab -d AdventureWorksLT -G -C -Q "
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME"
```

### 2. Create Bronze Model

Create a new file in `bronze_datakits_adventureworkslt/models/` following the pattern:

**Example: `product_bronze.py`**
```python
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
import uuid
import sys

sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')
from sqlmodel_framework.base.models import BronzeMetadata


class ProductBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for SalesLT.Product table"""
    __tablename__ = "bronze_product"
    __table_args__ = {"schema": "bronze"}

    # Primary key
    productid: int = Field(primary_key=True)

    # Business fields (check SQL Server schema)
    name: str
    productnumber: str
    color: Optional[str] = None
    listprice: float
    # ... add more fields as needed

    modifieddate: datetime
```

### 3. Register the Model

**a) Update `models/__init__.py`:**
```python
from .product_category_bronze import ProductCategoryBronze
from .product_bronze import ProductBronze  # ← Add this

__all__ = ["ProductCategoryBronze", "ProductBronze"]  # ← Add here
```

**b) Update `loader.py` TABLE_MODEL_MAP:**
```python
TABLE_MODEL_MAP = {
    "SalesLT.ProductCategory": ProductCategoryBronze,
    "SalesLT.Product": ProductBronze,  # ← Add this
}
```

**c) Update `config.yaml`:**
```yaml
source:
  tables:
    - "SalesLT.ProductCategory"
    - "SalesLT.Product"  # ← Add this
```

**d) Re-run setup and test:**
```bash
# Create new table in PostgreSQL
uv run python setup_bronze_warehouse.py

# Extract all tables
uv run python test_loader.py
```

**See [CONFIGURATION.md](CONFIGURATION.md) for detailed customization guide.**

---

## PostgreSQL Kerberos Setup

If you're setting up PostgreSQL for Kerberos authentication, add this to `pg_hba.conf`:

```conf
# Allow Kerberos (GSSAPI) connections
hostgssenc  all  all  0.0.0.0/0  gss include_realm=0 krb_realm=YOUR.REALM
```

Then restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

---

## Troubleshooting

### "No Kerberos ticket found"

```bash
# Get a Kerberos ticket
kinit your_username@YOUR.REALM

# Verify
klist
```

### "sqlcmd: command not found"

Install the latest sqlcmd ([Microsoft docs](https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-utility)):
```bash
# Example for Ubuntu/Debian
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo add-apt-repository "$(curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list)"
sudo apt-get update
sudo apt-get install sqlcmd
```

### "pg_hba.conf rejects connection"

PostgreSQL needs to allow Kerberos connections. See [PostgreSQL Kerberos Setup](#postgresql-kerberos-setup) above.

### "integer out of range" or "NaN errors"

This is fixed in the latest code (NULL handling). If you still see this, ensure you have the latest version.

### "Permission denied to create database"

Your PostgreSQL user needs `CREATEDB` privilege:
```sql
-- Run as PostgreSQL superuser
ALTER USER your_username CREATEDB;
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Data Flow                                │
└─────────────────────────────────────────────────────────────────┘

   SQL Server                                    PostgreSQL
   (Source)                                      (Bronze Warehouse)
   ┌──────────────┐                             ┌──────────────────┐
   │AdventureWorksLT│                           │bronze_warehouse  │
   │              │                              │                  │
   │  SalesLT.    │   ──sqlcmd + Kerberos──>   │  bronze.         │
   │  Product     │                              │  product_        │
   │  Category    │   ──Extract & Transform──>  │  category        │
   │              │                              │                  │
   │  (41 rows)   │                              │  + metadata      │
   └──────────────┘                             │  (41 rows)       │
                                                  └──────────────────┘
                                                         │
                                                         │
                                                         v
                                                  ┌──────────────────┐
                                                  │ File Storage     │
                                                  │ /tmp/bronze/     │
                                                  │  - parquet       │
                                                  │  - json          │
                                                  └──────────────────┘
```

**Bronze Layer Metadata:**
- `bronze_load_timestamp` - UTC timestamp when loaded
- `bronze_source_system` - "adventureworkslt_kerberos"
- `bronze_source_table` - e.g., "SalesLT.ProductCategory"
- `bronze_source_host` - SQL Server hostname
- `bronze_extraction_method` - "full_snapshot"

---

## Corporate Environment Considerations

### Using Custom Package Repositories

If your corporate environment blocks PyPI:

```bash
# Use corporate PyPI mirror
uv sync --index-url https://your-pypi-mirror.company.com/simple

# Or install from pre-built wheels
uv sync --find-links /path/to/wheels/
```

### Pre-building Container Images

For Airflow/Astronomer deployments:

```dockerfile
FROM quay.io/astronomer/astro-runtime:latest

# Copy the bronze datakit
COPY bronze_datakits_adventureworkslt /usr/local/airflow/bronze_datakits_adventureworkslt

# Install dependencies
COPY pyproject.toml /tmp/
RUN pip install -e /tmp/

# Copy config (use secrets for production!)
COPY config.yaml /usr/local/airflow/
```

### Using Custom Framework Paths

If your company hosts the sqlmodel-framework internally:

**Option 1: Modify sys.path in code**
```python
# In your models/loader files
sys.path.insert(0, '/path/to/your/custom/sqlmodel-framework/src')
```

**Option 2: Install framework from corporate repository**
```bash
uv add sqlmodel-framework --index-url https://your-repo.company.com/simple
```

---

## Next Steps

- **Production Deployment**: See [Astronomer deployment guide](../docs/deploying-to-astronomer.md)
- **Silver Layer**: Transform Bronze data for analytics
- **Scheduling**: Run extractions on a schedule with Airflow
- **Monitoring**: Add data quality checks and alerting

---

## Files in This Example

```
adventureworks-bronze/
├── config.yaml                          # ← Configuration (source/target databases)
├── setup_bronze_warehouse.py            # ← Creates PostgreSQL database/tables
├── test_loader.py                       # ← Runs the extraction pipeline
├── bronze_datakits_adventureworkslt/    # ← Main package
│   ├── __init__.py
│   ├── loader.py                        # ← Extraction logic
│   └── models/                          # ← Bronze table definitions
│       ├── __init__.py
│       └── product_category_bronze.py
├── pyproject.toml                       # ← Dependencies
├── README.md                            # ← This file
└── CONFIGURATION.md                     # ← Detailed customization guide
```

---

## Learn More

- [AdventureWorksLT Sample Database](https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure)
- [Kerberos Authentication Concepts](https://web.mit.edu/kerberos/)
- [PostgreSQL GSSAPI Authentication](https://www.postgresql.org/docs/current/gssapi-auth.html)
- [Bronze/Silver/Gold Architecture (Medallion)](https://www.databricks.com/glossary/medallion-architecture)

---

**Questions or issues?** Open an issue on GitHub or check [CONFIGURATION.md](CONFIGURATION.md) for advanced topics.
