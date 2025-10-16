# Setup Guide

A step-by-step guide to get SQL Server Bronze ingestion working with Kerberos authentication.

## 📋 Prerequisites Checklist

Before starting, verify you have:

- [ ] WSL2 or Linux environment
- [ ] Docker installed and running
- [ ] Access to a SQL Server database
- [ ] Kerberos configuration (or use our test environment)

## 🔧 Setup Paths

Choose your path based on your environment:

### Path A: Production Setup (You have Kerberos)

**When to use**: You have corporate Kerberos/AD already configured.

1. **Verify Kerberos is working**:
   ```bash
   kinit your_username@COMPANY.COM
   klist  # Should show your ticket
   ```

2. **Install the datakit**:
   ```bash
   cd datakit_sqlserver_bronze_kerberos
   pip install -e .
   ```

3. **Configure environment**:
   ```bash
   export MSSQL_SERVER=sql.company.com
   export MSSQL_DATABASE=DataWarehouse
   export MSSQL_AUTH_TYPE=kerberos
   ```

4. **Test connection**:
   ```bash
   datakit-sqlserver test-connection
   ```

**Next**: Jump to [Using the CLI](#using-the-cli)

### Path B: Development Setup (No Domain Access)

**When to use**: Local development without corporate network.

1. **Start the test environment**:
   ```bash
   cd ../../kerberos-astronomer
   docker-compose -f docker-compose.kdc-test.yml up -d
   ```

2. **Get a test ticket**:
   ```bash
   docker exec krb-client kinit airflow@TEST.LOCAL
   # Password: airflow123
   ```

3. **Install and configure**:
   ```bash
   cd ../datakits-sqlserver/datakit_sqlserver_bronze_kerberos
   pip install -e .

   export MSSQL_SERVER=sql.test.local
   export MSSQL_DATABASE=TestDB
   export MSSQL_AUTH_TYPE=kerberos
   ```

**Next**: Continue to [Using the CLI](#using-the-cli)

### Path C: Docker/Astronomer Setup

**When to use**: Running in containerized Airflow.

1. **Build the Kerberos sidecar**:
   ```bash
   cd ../../kerberos-astronomer
   make build
   ```

2. **Configure Astronomer project**:
   ```yaml
   # In your docker-compose.override.yml
   services:
     kerberos-sidecar:
       extends:
         file: ../kerberos-astronomer/docker-compose.override.yml
         service: kerberos-sidecar
   ```

3. **Mount the datakit**:
   ```yaml
   scheduler:
     volumes:
       - ./datakits-sqlserver:/opt/datakits
   ```

**Next**: See [Airflow Integration](#airflow-integration)

## 🎮 Using the CLI

Basic commands to get you started:

### 1. Discover What's Available

```bash
# List all tables
datakit-sqlserver discover

# Filter by pattern
datakit-sqlserver discover --pattern "Customer.*"

# Save metadata
datakit-sqlserver discover --output tables.json
```

### 2. Ingest Data

```bash
# Single table
datakit-sqlserver ingest-table Customer

# Multiple tables
datakit-sqlserver ingest-tables Customer Order Product

# All matching tables
datakit-sqlserver ingest-all --include "^Sales.*"
```

### 3. Monitor Progress

The CLI shows real-time progress with:
- ✓ Success indicators
- Row counts
- Processing time
- Error messages

## 🔄 Airflow Integration

For automated ingestion in Airflow:

1. **Create a connection**:
   - Type: `mssql`
   - Host: Your SQL Server
   - Extra: `{"auth_type": "kerberos"}`

2. **Use in a DAG**:
   ```python
   from datakit_sqlserver_bronze import BronzeIngestionPipeline

   @task
   def ingest_bronze():
       pipeline = BronzeIngestionPipeline(config)
       return pipeline.ingest_all_tables()
   ```

See [DAG Examples](../examples/) for complete patterns.

## ✅ Verification Steps

After setup, verify everything works:

1. **Check Kerberos ticket**:
   ```bash
   klist -s && echo "✓ Ticket valid" || echo "✗ No ticket"
   ```

2. **Test database connection**:
   ```bash
   datakit-sqlserver test-connection
   ```

3. **List available tables**:
   ```bash
   datakit-sqlserver discover --limit 5
   ```

4. **Try a small ingestion**:
   ```bash
   datakit-sqlserver ingest-table SmallTable --batch-size 100
   ```

## 🚦 Next Steps

- **Configure for your needs** → [Configuration Guide](./configuration.md)
- **Understand the design** → [Architecture](./architecture.md)
- **Fix common issues** → [Troubleshooting](./troubleshooting.md)

## 💡 Tips

- Start with a small table to test your setup
- Use `--dry-run` flag to preview what would be ingested
- Check logs in `/tmp/datakit-sqlserver.log` for details
- Set `MSSQL_TRUST_CERT=true` for self-signed certificates