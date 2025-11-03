# Configuration Guide

Complete guide for customizing the AdventureWorksLT Bronze extraction pipeline for your tables and environment.

---

## Table of Contents

1. [Configuration File Structure](#configuration-file-structure)
2. [Adding New Tables (Step-by-Step)](#adding-new-tables-step-by-step)
3. [Authentication Modes](#authentication-modes)
4. [Data Type Mapping](#data-type-mapping)
5. [Handling Special Cases](#handling-special-cases)
6. [Performance Tuning](#performance-tuning)

---

## Configuration File Structure

### config.yaml Overview

```yaml
source:                    # SQL Server source database
  host: "..."             # SQL Server hostname
  database: "..."          # Database name
  use_kerberos: true       # Authentication method
  tables: []               # List of tables to extract

target:                    # PostgreSQL target database
  host: "..."             # PostgreSQL hostname
  port: 5432              # PostgreSQL port
  database: "..."          # Database name
  schema: "bronze"        # Schema for Bronze tables
  use_kerberos: true       # Authentication method
  # Optional password auth:
  # user: "username"
  # password: "password"

storage:                   # File storage settings
  bronze_path: "/tmp/bronze"
  formats:
    - "parquet"
    - "json"
```

---

## Adding New Tables (Step-by-Step)

### Example: Adding SalesLT.Customer Table

#### Step 1: Inspect Source Table Schema

```bash
# Get column information from SQL Server
sqlcmd -S sql1.eruditis.lab -d AdventureWorksLT -G -C -Q "
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'SalesLT'
  AND TABLE_NAME = 'Customer'
ORDER BY ORDINAL_POSITION"
```

**Example output:**
```
COLUMN_NAME          DATA_TYPE    IS_NULLABLE  CHARACTER_MAXIMUM_LENGTH
CustomerID           int          NO           NULL
NameStyle            bit          NO           NULL
Title                nvarchar     YES          8
FirstName            nvarchar     NO           50
MiddleName           nvarchar     YES          50
LastName             nvarchar     NO           50
EmailAddress         nvarchar     YES          50
Phone                nvarchar     YES          25
ModifiedDate         datetime     NO           NULL
rowguid              uniqueidentifier  NO      NULL
```

#### Step 2: Create Bronze Model

Create `bronze_datakits_adventureworkslt/models/customer_bronze.py`:

```python
"""Bronze model for AdventureWorksLT Customer table"""

from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
import uuid
import sys

# Add framework to path
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel_framework.base.models import BronzeMetadata


class CustomerBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer model for SalesLT.Customer table"""
    __tablename__ = "bronze_customer"
    __table_args__ = {"schema": "bronze"}

    # Primary key
    customerid: int = Field(primary_key=True, description="Customer ID from source")

    # Business fields (match SQL Server schema)
    namestyle: bool = Field(description="Name style flag")
    title: Optional[str] = Field(default=None, max_length=8, description="Customer title")
    firstname: str = Field(max_length=50, description="First name")
    middlename: Optional[str] = Field(default=None, max_length=50, description="Middle name")
    lastname: str = Field(max_length=50, description="Last name")
    emailaddress: Optional[str] = Field(default=None, max_length=50, description="Email address")
    phone: Optional[str] = Field(default=None, max_length=25, description="Phone number")
    modifieddate: datetime = Field(description="Last modified timestamp")
    rowguid: uuid.UUID = Field(description="GUID from source system")

    # Bronze metadata fields are inherited from BronzeMetadata:
    # - bronze_load_timestamp
    # - bronze_source_system
    # - bronze_source_table
    # - bronze_source_host
    # - bronze_extraction_method
```

**Key points:**
- Column names in lowercase (SQL Server uses PascalCase, we convert to lowercase)
- Use `Optional[type]` for nullable columns
- Set `max_length` for string fields to match source
- Primary key uses `Field(primary_key=True)`

#### Step 3: Register Model in Package

**a) Update `models/__init__.py`:**
```python
"""Bronze models for AdventureWorksLT database"""

from .product_category_bronze import ProductCategoryBronze
from .customer_bronze import CustomerBronze  # ← Add this import

__all__ = [
    "ProductCategoryBronze",
    "CustomerBronze",  # ← Add to exports
]
```

**b) Update `loader.py` TABLE_MODEL_MAP:**
```python
# In the AdventureWorksLTBronzeLoader class:
TABLE_MODEL_MAP = {
    "SalesLT.ProductCategory": ProductCategoryBronze,
    "SalesLT.Customer": CustomerBronze,  # ← Add this mapping
}
```

#### Step 4: Update Configuration

Edit `config.yaml`:
```yaml
source:
  tables:
    - "SalesLT.ProductCategory"
    - "SalesLT.Customer"  # ← Add new table
```

#### Step 5: Create Table and Test

```bash
# Recreate Bronze tables (creates new CustomerBronze table)
uv run python setup_bronze_warehouse.py

# Run extraction
uv run python test_loader.py
```

**Expected output:**
```
Tables to extract: 2

Extracting: SalesLT.ProductCategory
✓ Successfully loaded 41 rows

Extracting: SalesLT.Customer
✓ Successfully loaded 847 rows

SUMMARY
Tables processed: 2/2
Total rows loaded: 888
```

---

## Authentication Modes

### Kerberos Authentication (Recommended for AD environments)

**Configuration:**
```yaml
source:
  host: "sql1.eruditis.lab"
  database: "AdventureWorksLT"
  use_kerberos: true  # ← Kerberos mode

target:
  host: "sqlpg.eruditis.lab"
  database: "bronze_warehouse"
  use_kerberos: true  # ← Kerberos mode
```

**Requirements:**
- Valid Kerberos ticket (`kinit username@REALM`)
- SQL Server configured for Kerberos/Windows Authentication
- PostgreSQL configured with GSSAPI (`pg_hba.conf`)

**Advantages:**
- No passwords in configuration files
- Centralized authentication via Active Directory
- Automatic ticket renewal
- Audit trail via Kerberos logs

### Password Authentication

**Configuration:**
```yaml
source:
  host: "sql1.example.com"
  database: "AdventureWorksLT"
  use_kerberos: false
  # For SQL Server SQL Authentication (not Windows Auth):
  # See SQL Server connection string docs

target:
  host: "pg.example.com"
  database: "bronze_warehouse"
  use_kerberos: false
  user: "bronze_user"
  password: "your_password"  # Or use environment variable
```

**Using environment variables for passwords:**
```yaml
target:
  user: "bronze_user"
  # Leave password empty - will prompt or read from PGPASSWORD env var
```

```bash
# Set password via environment variable
export PGPASSWORD="your_password"
uv run python test_loader.py
```

---

## Data Type Mapping

### SQL Server → Python → PostgreSQL

| SQL Server Type       | Python Type          | PostgreSQL Type | Notes |
|----------------------|----------------------|-----------------|-------|
| `int`, `INT`         | `int`                | `INTEGER`       | Use `Optional[int]` if nullable |
| `bigint`             | `int`                | `BIGINT`        | |
| `smallint`, `tinyint`| `int`                | `SMALLINT`      | |
| `bit`                | `bool`               | `BOOLEAN`       | `True`/`False` |
| `decimal`, `numeric` | `Decimal`            | `NUMERIC`       | Import from `decimal` |
| `money`, `smallmoney`| `Decimal`            | `NUMERIC(19,4)` | |
| `float`, `real`      | `float`              | `FLOAT`         | |
| `varchar`, `nvarchar`| `str`                | `VARCHAR`       | Use `max_length` parameter |
| `char`, `nchar`      | `str`                | `CHAR`          | Fixed-length strings |
| `text`, `ntext`      | `str`                | `TEXT`          | Large text |
| `datetime`, `datetime2` | `datetime`        | `TIMESTAMP`     | From `datetime` module |
| `date`               | `date`               | `DATE`          | From `datetime` module |
| `time`               | `time`               | `TIME`          | From `datetime` module |
| `uniqueidentifier`   | `uuid.UUID`          | `UUID`          | Import `uuid` module |
| `binary`, `varbinary`| `bytes`              | `BYTEA`         | Binary data |

### Examples

```python
from sqlmodel import Field
from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional
import uuid

class ExampleBronze(BronzeMetadata, SQLModel, table=True):
    # Integer types
    id: int = Field(primary_key=True)
    quantity: Optional[int] = None
    big_number: int  # bigint

    # Decimal/Money
    price: Decimal = Field(max_digits=19, decimal_places=4)
    total: Optional[Decimal] = Field(default=None, max_digits=19, decimal_places=2)

    # Boolean
    is_active: bool = False

    # Strings
    code: str = Field(max_length=10)  # varchar(10)
    name: str = Field(max_length=100)
    description: Optional[str] = None  # text or nvarchar(max)

    # Dates/Times
    created_date: datetime
    birth_date: Optional[date] = None
    start_time: Optional[time] = None

    # UUID/GUID
    rowguid: uuid.UUID

    # Defaults
    status: str = Field(default="pending", max_length=20)
```

---

## Handling Special Cases

### NULL Values

SQL Server NULLs are automatically converted to Python `None`. Always use `Optional[type]` for nullable columns:

```python
# WRONG - will fail if column has NULLs
parent_id: int

# CORRECT - handles NULLs properly
parent_id: Optional[int] = None
```

### Large Text Fields (NVARCHAR(MAX), TEXT)

```python
# Don't specify max_length for unlimited text
notes: Optional[str] = None  # Maps to TEXT in PostgreSQL
```

### Computed Columns

SQL Server computed columns can't be set directly. Exclude them or include in SELECT if stored:

```python
# Option 1: Omit computed column from model (won't be extracted)

# Option 2: Include if stored computed column
total_price: Optional[Decimal] = None  # Computed but stored
```

### Identity Columns (IDENTITY)

Mark as primary key, PostgreSQL will use SERIAL:

```python
id: int = Field(primary_key=True)  # SQL Server IDENTITY → PostgreSQL SERIAL
```

### Hierarchical Data (Parent-Child)

```python
# Self-referencing foreign key
class CategoryBronze(BronzeMetadata, SQLModel, table=True):
    categoryid: int = Field(primary_key=True)
    parentcategoryid: Optional[int] = None  # Can be NULL for top-level
    name: str
```

### Multi-Column Primary Keys

```python
class OrderDetailBronze(BronzeMetadata, SQLModel, table=True):
    orderid: int = Field(primary_key=True)
    productid: int = Field(primary_key=True)  # Composite key
    quantity: int
```

### Binary/BLOB Data

```python
# For small binary data
photo_thumbnail: Optional[bytes] = None

# For large BLOBs, consider excluding and storing reference
# FIELD_EXCLUSIONS pattern (see below)
```

---

## Performance Tuning

### Excluding Large/Sensitive Fields

Edit `loader.py` to exclude fields:

```python
class AdventureWorksLTBronzeLoader(BronzeIngestionPipeline):
    # Fields to exclude per table
    FIELD_EXCLUSIONS = {
        "SalesLT.Product": ["thumbnail_photo", "large_photo"],  # Exclude BLOBs
        "SalesLT.Customer": ["password_hash", "password_salt"],  # Exclude sensitive
        # Add more exclusions as needed
    }
```

### Batch Size for Large Tables

For tables with millions of rows, consider pagination (future enhancement):

```python
# Future feature - not yet implemented
def extract_table(self, table_name: str, batch_size: int = 10000):
    # Extract in batches using OFFSET/FETCH
    pass
```

### Parallel Extraction

Extract multiple tables concurrently (future enhancement):

```python
# Future feature
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(loader.load_table, table) for table in tables]
```

### File Storage Optimization

```yaml
# In config.yaml
storage:
  formats:
    - "parquet"  # Compressed, efficient for analytics
    # - "json"   # Comment out if not needed
```

---

## Advanced Topics

### Custom Source System Identifier

Edit `loader.py` to customize the source system name:

```python
def load_table(self, table_name: str) -> Dict[str, any]:
    df = self.add_bronze_metadata(
        df,
        source_system="prod_adventureworks_v2",  # ← Customize this
        source_table=table_name,
        source_host=self.source_host,
        extraction_method="full_snapshot"
    )
```

### Incremental Loads (Future)

For change data capture (CDC) or incremental loads:

```python
# Future pattern
def extract_table(self, table_name: str, since_timestamp: Optional[datetime] = None):
    if since_timestamp:
        query = f"SELECT * FROM {table_name} WHERE ModifiedDate > '{since_timestamp}'"
    else:
        query = f"SELECT * FROM {table_name}"  # Full load
```

### Custom Transformations

Add transformations before loading:

```python
def load_table(self, table_name: str) -> Dict[str, any]:
    df = self.extract_table(table_name)

    # Custom transformations
    if table_name == "SalesLT.Customer":
        # Example: Mask email addresses
        df['emailaddress'] = df['emailaddress'].str.replace(r'@.*', '@xxxxx.com', regex=True)

        # Example: Clean phone numbers
        df['phone'] = df['phone'].str.replace(r'[^0-9]', '', regex=True)

    # Continue with standard processing...
    df = self.add_bronze_metadata(...)
```

---

## Troubleshooting

### "No model found for table"

Ensure table is in `TABLE_MODEL_MAP`:
```python
TABLE_MODEL_MAP = {
    "SalesLT.YourTable": YourTableBronze,  # ← Add this
}
```

### Data Type Mismatch Errors

Check PostgreSQL logs for specific column causing issues:
```bash
tail -f /var/log/postgresql/postgresql-*.log
```

Common fixes:
- NULL handling: Use `Optional[type]`
- Integer overflow: Use `bigint` instead of `int`
- String too long: Increase `max_length`

### Column Name Conflicts

If SQL Server column name conflicts with Python/SQLModel reserved words:

```python
# Use different field name with alias
class_: str = Field(alias="class", max_length=50)  # 'class' is Python keyword
```

---

## Summary Checklist

When adding a new table:

- [ ] Inspect source schema (`sqlcmd` query)
- [ ] Create Bronze model file (`*_bronze.py`)
- [ ] Import model in `models/__init__.py`
- [ ] Add to `TABLE_MODEL_MAP` in `loader.py`
- [ ] Add to `config.yaml` tables list
- [ ] Run `setup_bronze_warehouse.py`
- [ ] Run `test_loader.py`
- [ ] Verify data in PostgreSQL
- [ ] Check file storage `/tmp/bronze/`

---

**Need help?** Open an issue on GitHub or refer to [SQLModel documentation](https://sqlmodel.tiangolo.com/).
