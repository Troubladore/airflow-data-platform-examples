# First-Time User Guide

**For**: Someone who has never used this framework before and needs to ingest SQL Server data with NT Authentication.

## 📍 Where You Are

You have:
- A SQL Server database that requires Windows Authentication
- A table you need to ingest
- WSL2 or Linux environment

You need:
- To get that data into your Bronze layer
- Using Kerberos/NT Authentication
- In an automated, repeatable way

## 🎯 What We'll Accomplish

By the end of this guide, you'll have:
1. ✅ Connected to SQL Server using NT Authentication
2. ✅ Ingested your first table
3. ✅ Understood where everything goes
4. ✅ Ready to customize for your tables

## 📝 Step-by-Step Instructions

### Step 1: Get Your Information Ready

Before starting, gather this information:

```text
SQL Server hostname: _________________ (e.g., sql.company.com)
Database name:       _________________ (e.g., AdventureWorks)
Table to ingest:     _________________ (e.g., dbo.Customer)
Your domain:         _________________ (e.g., COMPANY.COM)
Your username:       _________________ (e.g., jsmith)
```

### Step 2: Check Your Kerberos Setup

In your terminal, run:

```bash
# See if you have a Kerberos ticket
klist
```

**If you see tickets**: Skip to Step 3

**If you see "No credentials cache found"**:

```bash
# Get a ticket (replace with YOUR username and domain)
kinit jsmith@COMPANY.COM
# Enter your Windows password when prompted

# Verify it worked
klist
```

### Step 3: Install the Datakit

```bash
# Navigate to the datakit directory
cd datakits-sqlserver/datakit_sqlserver_bronze_kerberos

# Install it
pip install -e .

# Verify installation
datakit-sqlserver --help
```

### Step 4: Configure Your Environment

Create a file called `.env` in the datakit directory:

```bash
# Create the file
nano .env
```

Add these lines (replace with YOUR values):

```bash
# Your SQL Server connection info
MSSQL_SERVER=sql.company.com
MSSQL_DATABASE=AdventureWorks
MSSQL_AUTH_TYPE=kerberos

# Optional: if self-signed certificates
MSSQL_TRUST_CERT=true
```

Save and exit (Ctrl+X, Y, Enter).

### Step 5: Test Your Connection

Run this command:

```bash
datakit-sqlserver test-connection
```

**What you should see**:
```
✅ Connected successfully!
   Login: DOMAIN\your_username
   Database: AdventureWorks
```

**If it fails**, check:
- Is your Kerberos ticket valid? (`klist`)
- Is the SQL Server hostname correct?
- Can you ping the server? (`ping sql.company.com`)

### Step 6: Discover Available Tables

See what tables you can access:

```bash
datakit-sqlserver discover --limit 10
```

This shows the first 10 tables you have access to.

### Step 7: Run Your First Ingestion

Let's ingest the Customer table:

```bash
# Basic ingestion
datakit-sqlserver ingest-table Customer

# Or if your table is in a different schema
datakit-sqlserver ingest-table Customer --source-schema Sales
```

**What happens**:
1. Connects to SQL Server using your Kerberos ticket
2. Reads all data from the Customer table
3. Adds Bronze metadata (when loaded, source info)
4. Saves to bronze.dbo_Customer

### Step 8: Use the Simple Example

For a complete working example:

```bash
# Go to examples directory
cd ../../examples

# Edit the simple example
nano simple_customer_ingestion.py
```

**Change ONLY these lines**:

```python
# Line 35-37: Your SQL Server
SQL_SERVER_HOST = "your-sql-server.company.com"
SQL_SERVER_DATABASE = "YourDatabase"

# Line 41-42: Your table
SOURCE_TABLE = "YourTableName"
```

Run it:

```bash
python simple_customer_ingestion.py
```

## 🗂️ Where Everything Goes

```
Your Project/
│
├── .env                          <- Your configuration (server, database)
│
├── config/
│   ├── krb5.conf                <- Kerberos config (from IT)
│   └── airflow.keytab           <- Service account keytab (production)
│
├── dags/
│   └── simple_bronze_dag.py     <- Your Airflow DAG
│
└── datakits-sqlserver/
    └── datakit_sqlserver_bronze_kerberos/  <- The datakit code
```

## 🔧 Customizing for Your Table

To ingest YOUR specific table, you need to change:

### In Python Script:
```python
# Change these 4 lines:
SQL_SERVER_HOST = "your.server.com"      # Your server
SQL_SERVER_DATABASE = "YourDB"           # Your database
SOURCE_TABLE = "YourTable"               # Your table
BRONZE_TABLE = "your_table_bronze"       # Name in Bronze
```

### In Command Line:
```bash
datakit-sqlserver ingest-table YourTable \
  --source-schema YourSchema \
  --target-table your_table_bronze
```

### In Airflow DAG:
```python
CONFIG = {
    "server": "your.server.com",
    "database": "YourDB",
    "source_table": "YourTable",
    # ... rest of config
}
```

## ❓ Common Questions

### "Where does the data actually go?"

The Bronze data is written to:
- Schema: `bronze`
- Table: `{source_schema}_{source_table}`
- With added columns: `_bronze_loaded_at`, `_bronze_source_system`, etc.

### "How do I schedule this to run daily?"

Use the Airflow DAG:
1. Copy `simple_bronze_dag.py` to your Airflow dags folder
2. Update the CONFIG section
3. It will run daily at 2 AM (configurable)

### "What if I don't have Kerberos configured?"

For testing, you can use SQL authentication:
```python
AUTH_TYPE = "sql"
SQL_USERNAME = "your_username"
SQL_PASSWORD = "your_password"
```

### "How do I ingest multiple tables?"

```bash
# Multiple specific tables
datakit-sqlserver ingest-tables Customer Order Product

# All tables matching pattern
datakit-sqlserver ingest-all --include "Sales.*"
```

## ✅ Success Checklist

You know you're successful when:

- [ ] `klist` shows a valid ticket
- [ ] `datakit-sqlserver test-connection` works
- [ ] `datakit-sqlserver discover` shows your tables
- [ ] `datakit-sqlserver ingest-table YourTable` completes
- [ ] You see "✅ Ingestion complete!" with row count

## 🆘 Getting Help

If stuck:

1. **Check your Kerberos ticket**: `klist`
2. **Validate environment**: `datakit-sqlserver validate-env`
3. **Check logs**: Add `--log-level DEBUG` to any command
4. **See troubleshooting**: [Troubleshooting Guide](./troubleshooting.md)

## 🎉 Next Steps

Now that you've successfully ingested your first table:

1. **Ingest more tables**: Update the table names and run again
2. **Automate with Airflow**: Use the DAG example
3. **Add to production**: Use keytab instead of password
4. **Monitor and alert**: Add email notifications

---

**Remember**: The hardest part is getting the first table working. Once that works, everything else is just changing table names!