# Configuration Guide

Detailed configuration options for the SQL Server Bronze datakit.

## 🎛️ Configuration Methods

Configure the datakit using (in order of precedence):

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **.env file**
4. **Config file** (JSON/YAML)
5. **Defaults** (lowest priority)

## 🔑 Core Settings

### Connection Settings

| Setting | Environment Variable | CLI Flag | Default | Description |
|---------|---------------------|----------|---------|-------------|
| Server | `MSSQL_SERVER` | `--server` | localhost | SQL Server hostname/IP |
| Port | `MSSQL_PORT` | `--port` | 1433 | SQL Server port |
| Database | `MSSQL_DATABASE` | `--database` | master | Target database |
| Driver | `MSSQL_DRIVER` | `--driver` | ODBC Driver 18 | ODBC driver name |

### Authentication Settings

| Setting | Environment Variable | CLI Flag | Default | Description |
|---------|---------------------|----------|---------|-------------|
| Auth Type | `MSSQL_AUTH_TYPE` | `--auth` | kerberos | Authentication method |
| Username | `MSSQL_USERNAME` | `--username` | - | For SQL auth only |
| Password | `MSSQL_PASSWORD` | `--password` | - | For SQL auth only |

**Auth Types**:
- `kerberos` - Windows/NT Authentication via Kerberos
- `sql` - SQL Server authentication (user/pass)
- `azure_ad` - Azure Active Directory

### Kerberos Settings

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| Ticket Cache | `KRB5CCNAME` | /krb5/cache/krb5cc | Kerberos ticket location |
| Config File | `KRB5_CONFIG` | /etc/krb5.conf | krb5.conf location |
| Realm | `KRB_REALM` | - | Kerberos realm (auto-detected) |

### Performance Settings

| Setting | Environment Variable | CLI Flag | Default | Description |
|---------|---------------------|----------|---------|-------------|
| Batch Size | `BRONZE_BATCH_SIZE` | `--batch-size` | 10000 | Rows per batch |
| Max Workers | `BRONZE_MAX_WORKERS` | `--workers` | 4 | Parallel workers |
| Timeout | `MSSQL_CONNECT_TIMEOUT` | `--timeout` | 30 | Connection timeout (sec) |

## 📁 Configuration Files

### Using .env File

Create `.env` in your project root:

```bash
# Connection
MSSQL_SERVER=sql.company.com
MSSQL_PORT=1433
MSSQL_DATABASE=DataWarehouse

# Authentication
MSSQL_AUTH_TYPE=kerberos
# For SQL auth:
# MSSQL_AUTH_TYPE=sql
# MSSQL_USERNAME=datakit_user
# MSSQL_PASSWORD=secret

# Performance
BRONZE_BATCH_SIZE=50000
BRONZE_MAX_WORKERS=8

# Security
MSSQL_TRUST_CERT=false
MSSQL_ENCRYPT=true
```

### Using JSON Config

Create `config.json`:

```json
{
  "connection": {
    "server": "sql.company.com",
    "port": 1433,
    "database": "DataWarehouse",
    "driver": "ODBC Driver 18 for SQL Server"
  },
  "auth": {
    "type": "kerberos"
  },
  "performance": {
    "batch_size": 50000,
    "max_workers": 8
  }
}
```

Load with: `datakit-sqlserver --config config.json ingest-all`

## 🎯 Common Configurations

### High-Volume Production

```bash
# Optimize for large tables
export BRONZE_BATCH_SIZE=100000
export BRONZE_MAX_WORKERS=16
export MSSQL_CONNECT_TIMEOUT=60

datakit-sqlserver ingest-all \
  --batch-size 100000 \
  --workers 16
```

### Development/Testing

```bash
# Small batches, verbose logging
export BRONZE_BATCH_SIZE=100
export LOG_LEVEL=DEBUG
export MSSQL_TRUST_CERT=true  # For self-signed certs

datakit-sqlserver ingest-table TestTable \
  --batch-size 100 \
  --dry-run
```

### Filtered Ingestion

```bash
# Only specific tables
datakit-sqlserver ingest-all \
  --include "^(Customer|Order|Product).*" \
  --exclude ".*_Archive$"
```

## 🔐 Security Configuration

### Certificate Trust

For self-signed certificates:

```bash
export MSSQL_TRUST_CERT=true
export MSSQL_ENCRYPT=true
```

For production with CA certificates:

```bash
export MSSQL_TRUST_CERT=false
export MSSQL_ENCRYPT=true
export SSL_CERT_DIR=/path/to/certs
```

### Credential Management

**Never hardcode credentials!** Use one of:

1. **Environment variables** (from secure vault)
2. **Kubernetes secrets** (mounted as files)
3. **Azure Key Vault** (with managed identity)
4. **AWS Secrets Manager**

Example with Azure Key Vault:

```python
from azure.keyvault.secrets import SecretClient

def get_config():
    client = SecretClient(vault_url, credential)
    return SQLServerConfig(
        server=client.get_secret("mssql-server").value,
        password=client.get_secret("mssql-password").value
    )
```

## 📊 Bronze Layer Settings

### Metadata Columns

The datakit automatically adds:

| Column | Type | Description |
|--------|------|-------------|
| `_bronze_loaded_at` | timestamp | When data was loaded |
| `_bronze_source_system` | string | Always "sqlserver" |
| `_bronze_source_schema` | string | Original schema name |
| `_bronze_source_table` | string | Original table name |
| `_bronze_batch_id` | string | Unique batch identifier |

### Target Schema Patterns

Configure naming patterns:

```bash
# Default: bronze.{schema}_{table}
export BRONZE_NAMING_PATTERN=bronze.{schema}_{table}

# Date partitioned: bronze.{schema}_{table}_{date}
export BRONZE_NAMING_PATTERN=bronze.{schema}_{table}_{date}

# Environment tagged: bronze_{env}.{schema}_{table}
export BRONZE_NAMING_PATTERN=bronze_${ENV}.{schema}_{table}
```

## 🔄 Advanced Options

### Connection Pooling

```python
# In Python code
config = SQLServerConfig(
    pool_size=10,        # Connection pool size
    max_overflow=20,     # Max overflow connections
    pool_timeout=30,     # Pool timeout in seconds
    pool_recycle=3600    # Recycle connections after 1 hour
)
```

### Retry Configuration

```bash
# Retry failed operations
export BRONZE_RETRY_COUNT=3
export BRONZE_RETRY_DELAY=5  # seconds
export BRONZE_RETRY_BACKOFF=2  # exponential backoff multiplier
```

### Logging Configuration

```bash
# Log levels: DEBUG, INFO, WARNING, ERROR
export LOG_LEVEL=INFO
export LOG_FORMAT=json  # or 'text'
export LOG_FILE=/var/log/datakit/bronze.log
```

## 📋 Configuration Validation

Validate your configuration:

```bash
# Check all settings
datakit-sqlserver validate-env

# Test specific configuration
datakit-sqlserver test-connection --config my-config.json

# Dry run to see what would happen
datakit-sqlserver ingest-all --dry-run
```

## 🚦 Next Steps

- **Troubleshoot issues** → [Troubleshooting](./troubleshooting.md)
- **Understand internals** → [Architecture](./architecture.md)
- **See examples** → [DAG Examples](../examples/)