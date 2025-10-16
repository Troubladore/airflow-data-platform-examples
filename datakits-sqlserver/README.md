# SQL Server Bronze Datakits

**Quick Start**: Production-ready data ingestion from SQL Server to Bronze layer using Kerberos authentication.

## 🎯 What & Why

**What**: Containerized datakit that extracts data from SQL Server databases using Windows Authentication (Kerberos/NT Auth) and loads it into your Bronze layer.

**Why**: Your enterprise SQL Server databases require NT Authentication. This datakit bridges that gap, enabling secure, automated ingestion into your data platform.

## 📚 Documentation Layers

Start at the top and drill down as needed:

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **This Page** | Overview & quick start | First visit |
| [Setup Guide](./docs/setup-guide.md) | Environment setup | Getting started |
| [Configuration](./docs/configuration.md) | All config options | Customizing behavior |
| [Architecture](./docs/architecture.md) | Technical design | Understanding internals |
| [Troubleshooting](./docs/troubleshooting.md) | Common issues | When stuck |

## 🚀 30-Second Quick Start

If you already have Kerberos configured in WSL2:

```bash
# 1. Install the datakit
cd datakit_sqlserver_bronze_kerberos
pip install -e .

# 2. Test your connection
datakit-sqlserver test-connection \
  --server sql.company.com \
  --database DataWarehouse

# 3. Discover available tables
datakit-sqlserver discover --schema dbo

# 4. Ingest a table
datakit-sqlserver ingest-table Customer
```

## 🔄 How It Works

```
Your SQL Server ──Kerberos──> Datakit ──> Bronze Layer
                    Auth       Extract     Load
```

The datakit:
1. Uses your Kerberos ticket for authentication
2. Connects to SQL Server securely
3. Extracts data in configurable batches
4. Adds Bronze metadata (load time, source info)
5. Writes to your Bronze storage

## 📦 What's Included

- **CLI Tool**: Command-line interface for manual runs
- **Python Package**: Import into your DAGs or scripts
- **Airflow Examples**: Ready-to-use DAG templates
- **Docker Support**: Runs in containers with Kerberos sidecar

## ⚡ Next Steps

1. **New to Kerberos?** → [Setup Guide](./docs/setup-guide.md)
2. **Ready to configure?** → [Configuration](./docs/configuration.md)
3. **Using with Airflow?** → [DAG Examples](./examples/)
4. **Having issues?** → [Troubleshooting](./docs/troubleshooting.md)

## 🤝 Support

- **Issues**: Create an issue in this repository
- **Questions**: Check [Troubleshooting](./docs/troubleshooting.md) first
- **Contributing**: See [Architecture](./docs/architecture.md) for design details