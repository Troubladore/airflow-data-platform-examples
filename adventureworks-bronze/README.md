# AdventureWorksLT Bronze Layer Example

**Extract data from SQL Server → Load to PostgreSQL Bronze warehouse**

This example shows you how to build a Bronze layer data pipeline that:
- Pulls data from **SQL Server** (Microsoft SQL Server)
- Stores it in a **PostgreSQL** data warehouse
- Uses **Kerberos** for authentication (no passwords!)
- Tracks data lineage with Bronze metadata

Perfect for enterprise environments using Active Directory or Samba AD.

---

## What You'll Build

A complete data pipeline that extracts one table from SQL Server's AdventureWorksLT sample database and loads it into PostgreSQL:

**Source:** SQL Server → `AdventureWorksLT.SalesLT.ProductCategory` (41 rows)
**Target:** PostgreSQL → `bronze_warehouse.bronze.bronze_product_category`
**Authentication:** Kerberos (both source and target)
**Output:** Database table + Parquet/JSON files

Once you understand this example, you can easily add more tables by following the patterns.

---

## Prerequisites: What You Need

Before starting, you'll need these ingredients ready:

### 1. The Platform (Infrastructure)
You need the Airflow Data Platform running with Kerberos services.

**→ See:** [Platform Setup Guide](https://github.com/Troubladore/airflow-data-platform/blob/main/docs/getting-started.md)

**Quick version:**
```bash
git clone https://github.com/Troubladore/airflow-data-platform.git
cd airflow-data-platform/platform-bootstrap
make setup
```

This sets up PostgreSQL, Kerberos KDC, and other platform services.

### 2. Custom Images (Optional for Development)
For local development, you can use Python directly. For production/Airflow deployment, you'll need container images.

**→ See:** [IMAGES.md](IMAGES.md) - Details on building custom images with sqlcmd and Kerberos

### 3. Source & Target Databases
- **SQL Server** with AdventureWorksLT database
- **PostgreSQL** server for Bronze warehouse
- Both configured for Kerberos authentication

**→ See:** Platform setup guide for Kerberos-enabled PostgreSQL configuration

### 4. Your Workstation
- Python 3.9+
- `uv` package manager ([install guide](https://github.com/astral-sh/uv))
- `sqlcmd` tool for SQL Server ([install guide](https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-utility))
- Valid Kerberos ticket (`kinit your_username@YOUR.REALM`)

---

## Getting Started: Your Journey

### Step 1: Get the Code

```bash
# Clone this examples repository
git clone https://github.com/Troubladore/airflow-data-platform-examples.git
cd airflow-data-platform-examples/adventureworks-bronze

# Install Python dependencies
uv sync
```

**What this does:** Downloads the Bronze datakit code and installs required Python packages (pandas, sqlalchemy, psycopg2, etc.)

### Step 2: Configure Your Environment

Edit `config.yaml` to point to your databases:

```yaml
source:
  host: "your-sqlserver.company.com"    # ← Your SQL Server
  database: "AdventureWorksLT"

target:
  host: "your-postgres.company.com"     # ← Your PostgreSQL
  database: "bronze_warehouse"
```

**→ See:** [CONFIGURATION.md](CONFIGURATION.md) for complete configuration options (Kerberos vs passwords, adding tables, etc.)

### Step 3: Create the Bronze Warehouse

```bash
# This creates the database and tables on PostgreSQL
uv run python setup_bronze_warehouse.py
```

**What this does:**
1. Creates `bronze_warehouse` database
2. Creates `bronze` schema
3. Creates table: `bronze_product_category`

### Step 4: Run the Extraction

```bash
# Extract from SQL Server → Load to PostgreSQL
uv run python test_loader.py
```

**Expected output:**
```
Extracting: SalesLT.ProductCategory
✓ Successfully loaded 41 rows

Tables processed: 1/1
Total rows loaded: 41
```

### Step 5: Verify Your Data

```bash
# Check PostgreSQL
psql -h your-postgres.company.com -d bronze_warehouse -c "
  SELECT COUNT(*) FROM bronze.bronze_product_category
"
```

**You should see:** 41 rows with Bronze metadata (load timestamp, source system, etc.)

---

## What's Next?

Now that you have the basic pipeline working:

1. **Add more tables** → [CONFIGURATION.md](CONFIGURATION.md) - Step-by-step guide
2. **Deploy to production** → [DEPLOYMENT.md](DEPLOYMENT.md) - Container images and Airflow setup
3. **Understand the code** → [ARCHITECTURE.md](ARCHITECTURE.md) - How the Bronze datakit works
4. **Troubleshooting** → [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions

---

## Quick Reference

### Files in This Example

```
adventureworks-bronze/
├── README.md                          # ← You are here (start here!)
├── CONFIGURATION.md                   # How to add tables and customize
├── DEPLOYMENT.md                      # Production deployment guide
├── IMAGES.md                          # Container image build guide
├── ARCHITECTURE.md                    # How the code works
├── TROUBLESHOOTING.md                 # Common issues and fixes
├── config.yaml                        # Your database configuration
├── setup_bronze_warehouse.py          # Creates PostgreSQL database/tables
├── test_loader.py                     # Runs the extraction pipeline
└── bronze_datakits_adventureworkslt/  # The Bronze datakit code
```

### Common Commands

```bash
# Setup
uv sync                                          # Install dependencies
uv run python setup_bronze_warehouse.py          # Create database/tables

# Run extraction
uv run python test_loader.py                     # Extract and load data

# Verify
psql -h HOST -d bronze_warehouse -c "SELECT COUNT(*) FROM bronze.bronze_product_category"
```

---

## Getting Help

- **Can't connect to databases?** → [TROUBLESHOOTING.md](TROUBLESHOOTING.md#connection-issues)
- **Want to add more tables?** → [CONFIGURATION.md](CONFIGURATION.md#adding-new-tables)
- **Need container images?** → [IMAGES.md](IMAGES.md)
- **Questions about the code?** → [ARCHITECTURE.md](ARCHITECTURE.md)

---

**Ready to get started?** Follow [Step 1](#step-1-get-the-code) above!
