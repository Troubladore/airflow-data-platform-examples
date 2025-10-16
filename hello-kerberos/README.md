# Hello Kerberos - SQL Server with Windows Authentication

Example showing how to connect to SQL Server using Kerberos authentication in Astronomer.

## 📋 Prerequisites

1. **Platform services running** with ticket sharing enabled
2. **Valid Kerberos tickets** in WSL2:
   ```bash
   kinit YOUR_USERNAME@COMPANY.COM
   klist  # Should show your tickets
   ```
3. **SQL Server** that accepts Windows Authentication

## 🎯 What This Demonstrates

- Using shared Kerberos tickets from WSL2 in Airflow containers
- Connecting to SQL Server with Windows Authentication
- No passwords in code or configuration!

## 🚀 Quick Start

```bash
# 1. Ensure you have Kerberos tickets
kinit YOUR_USERNAME@COMPANY.COM

# 2. Start platform services (if not running)
cd ~/airflow-data-platform/platform-bootstrap
make start

# 3. Initialize this project
astro dev init

# 4. Add dependencies
cat >> requirements.txt << EOF
sqlmodel-framework @ git+https://github.com/Troubladore/airflow-data-platform.git@main#subdirectory=sqlmodel-framework
pyodbc==5.0.1
EOF

# 5. Copy our example DAG
cp dags/hello_kerberos_dag.py dags/

# 6. Configure your SQL Server connection
export SQLSERVER_HOST="your-server.company.com"
export SQLSERVER_DATABASE="YourDatabase"

# 7. Start Airflow
astro dev start
```

## 🔧 Configuration

### Environment Variables
Create `.env` file:
```bash
# SQL Server connection
SQLSERVER_HOST=your-server.company.com
SQLSERVER_DATABASE=YourDatabase

# Kerberos realm (optional, usually auto-detected)
KRB5_REALM=COMPANY.COM
```

### Docker Compose Override
The platform automatically mounts Kerberos tickets. If you need custom configuration, create `docker-compose.override.yml`:
```yaml
version: '3'
services:
  webserver:
    volumes:
      - ~/.krb5_cache:/tmp/krb5_cache:ro
    environment:
      - KRB5CCNAME=/tmp/krb5_cache/krb5cc_1000
```

## 📁 What's Included

### `dags/hello_kerberos_dag.py`
Demonstrates:
- Checking for Kerberos tickets
- Connecting to SQL Server with Windows Auth
- Running a simple query
- Error handling for auth issues

## 🧪 Test Your Connection

1. Open Airflow UI at http://localhost:8080
2. Find `hello_kerberos_sqlserver` DAG
3. Trigger it manually
4. Check logs for connection status

Expected output:
```
✅ Kerberos tickets found
✅ Connected to SQL Server
   Server: your-server.company.com
   Database: YourDatabase
   User: DOMAIN\username
```

## 🚨 Troubleshooting

### "No Kerberos tickets found"
```bash
# Get new tickets
kinit YOUR_USERNAME@COMPANY.COM

# Verify tickets exist
klist
ls ~/.krb5_cache/
```

### "Cannot connect to SQL Server"
1. Check SQL Server allows Kerberos auth
2. Verify server name and database
3. Check network connectivity from container:
   ```bash
   docker exec -it <container> ping your-server.company.com
   ```

### "Ticket expired"
Kerberos tickets expire (usually after 10 hours). Renew them:
```bash
kinit -R  # Renew if possible
# or
kinit YOUR_USERNAME@COMPANY.COM  # Get new tickets
```

## 🔐 Security Notes

- Tickets are mounted **read-only** to containers
- No passwords stored anywhere
- Tickets expire automatically (corporate policy)
- Each developer uses their own credentials

## 🎯 Next Steps

- See [datakits-sqlserver](../datakits-sqlserver/) for production patterns
- Learn about [Bronze/Silver/Gold architecture](../datakits-sqlserver/datakit_sqlserver_bronze_kerberos/)
- Read [Kerberos Setup Guide](https://github.com/Troubladore/airflow-data-platform/blob/main/docs/kerberos-setup-wsl2.md)

## 🛑 Cleanup

```bash
# Stop Airflow
astro dev stop

# Destroy tickets (optional)
kdestroy
```