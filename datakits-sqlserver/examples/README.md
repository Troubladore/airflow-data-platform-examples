# SQL Server Bronze Ingestion Examples

Ready-to-run examples for ingesting SQL Server data with NT Authentication.

## 🚀 Quick Start - Try It in 2 Minutes!

### Step 1: Start the Mock Environment

```bash
# Start mock SQL Server with test data
docker-compose -f docker-compose.mock.yml up -d

# Wait for it to initialize (about 30 seconds)
docker-compose -f docker-compose.mock.yml logs mock-data-loader
```

### Step 2: Run the Fill-in-the-Blanks Example

```bash
# Install the datakit first (one time only)
cd ../datakit_sqlserver_bronze_kerberos
pip install -e .
cd ../examples

# Run with mock data (no changes needed!)
python FILL_IN_THE_BLANKS_ingestion.py
```

You should see:
```
🎭 RUNNING IN MOCK MODE - Using test data
✅ Connected successfully!
✅ INGESTION COMPLETE!
   Rows ingested: 10
```

### Step 3: Switch to Your Real SQL Server

Edit `FILL_IN_THE_BLANKS_ingestion.py`:

1. Change line 29: `USE_MOCK_DATA = False`
2. Fill in your values in Section 3 (lines 69-89)
3. Run again: `python FILL_IN_THE_BLANKS_ingestion.py`

## 📁 What's Included

| File | Purpose | When to Use |
|------|---------|-------------|
| **FILL_IN_THE_BLANKS_ingestion.py** | Main example - works immediately | Start here! |
| **simple_customer_ingestion.py** | Detailed standalone script | Learning the details |
| **simple_bronze_dag.py** | Airflow DAG example | Scheduling ingestion |
| **docker-compose.mock.yml** | Mock SQL Server setup | Testing without real server |
| **mock_warehouse_setup.sql** | Sample database/table | Reference for structure |

## 🎯 Usage Patterns

### Pattern 1: Test First, Then Switch to Production

```python
# In FILL_IN_THE_BLANKS_ingestion.py

# Step 1: Run as-is with mock data
USE_MOCK_DATA = True  # Default

# Step 2: Verify it works
# python FILL_IN_THE_BLANKS_ingestion.py

# Step 3: Switch to real data
USE_MOCK_DATA = False

# Step 4: Fill in your SQL Server details
SQL_CONFIG = {
    "server": "sql.company.com",    # <- Your server
    "database": "DataWarehouse",    # <- Your database
    "source_table": "Customer",     # <- Your table
    # ...
}
```

### Pattern 2: Direct to Production

If you already have Kerberos configured:

```bash
# Just edit and run
nano FILL_IN_THE_BLANKS_ingestion.py
# Change USE_MOCK_DATA to False
# Fill in your server details
python FILL_IN_THE_BLANKS_ingestion.py
```

### Pattern 3: Scheduled with Airflow

```python
# Copy DAG to your Airflow dags folder
cp simple_bronze_dag.py ~/airflow/dags/

# Edit the CONFIG section
# It will run daily automatically
```

## 🔧 Customization Guide

### Change the Table Being Ingested

In `FILL_IN_THE_BLANKS_ingestion.py`, modify:

```python
SQL_CONFIG = {
    "source_schema": "Sales",        # Your schema
    "source_table": "Orders",        # Your table
}

BRONZE_CONFIG = {
    "target_table": "sales_orders_daily",  # Name in Bronze
}
```

### Add Multiple Tables

Copy the file for each table:

```bash
cp FILL_IN_THE_BLANKS_ingestion.py customer_ingestion.py
cp FILL_IN_THE_BLANKS_ingestion.py orders_ingestion.py
cp FILL_IN_THE_BLANKS_ingestion.py products_ingestion.py

# Edit each file with different table names
```

### Change the Schedule

In `simple_bronze_dag.py`:

```python
SCHEDULE = "@hourly"  # Every hour
# or
SCHEDULE = "0 6 * * *"  # Daily at 6 AM
# or
SCHEDULE = "@weekly"  # Weekly
```

## 🐛 Troubleshooting

### "Connection Failed" with Mock Data

```bash
# Make sure mock SQL Server is running
docker-compose -f docker-compose.mock.yml ps

# Check logs
docker-compose -f docker-compose.mock.yml logs mock-sqlserver

# Restart if needed
docker-compose -f docker-compose.mock.yml restart
```

### "No module named datakit_sqlserver_bronze"

```bash
# Install the datakit
cd ../datakit_sqlserver_bronze_kerberos
pip install -e .
```

### "No Kerberos ticket found" (Production)

```bash
# Get a ticket
kinit your_username@COMPANY.COM

# Verify
klist
```

## 📊 Mock Data Structure

The mock environment creates this table:

```sql
TestWarehouse.dbo.Customer
├── customer_id (INT)
├── first_name (NVARCHAR)
├── last_name (NVARCHAR)
├── email (NVARCHAR)
├── phone (NVARCHAR)
├── address (NVARCHAR)
├── city (NVARCHAR)
├── state (NVARCHAR)
├── zip_code (NVARCHAR)
├── country (NVARCHAR)
├── created_date (DATETIME)
├── last_modified (DATETIME)
└── is_active (BIT)
```

With 10 sample rows for testing.

## ✅ Success Checklist

- [ ] Mock example runs successfully
- [ ] You understand where to put your SQL Server details
- [ ] You can see the 10 rows being ingested
- [ ] You know how to switch to production mode
- [ ] Your real table ingests successfully

## 🎉 You're Ready!

Once the mock example works, you have everything needed to ingest your production data. Just:

1. Set `USE_MOCK_DATA = False`
2. Fill in your server/database/table
3. Ensure you have a Kerberos ticket
4. Run the script

The hardest part is done - now it's just configuration!