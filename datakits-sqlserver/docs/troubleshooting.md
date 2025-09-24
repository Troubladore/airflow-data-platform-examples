# Troubleshooting Guide

Quick solutions to common issues with SQL Server Bronze ingestion.

## 🔴 Connection Issues

### "Cannot contact KDC"

**Symptom**:
```
Error: Cannot contact any KDC for realm 'COMPANY.COM'
```

**Solutions**:

1. **Check network connectivity**:
   ```bash
   ping kdc.company.com
   nslookup kdc.company.com
   ```

2. **Verify krb5.conf**:
   ```bash
   cat /etc/krb5.conf | grep -A 5 "COMPANY.COM"
   # Should show KDC servers
   ```

3. **Use correct realm**:
   ```bash
   export KRB_REALM=COMPANY.COM  # Case sensitive!
   ```

### "No valid Kerberos ticket found"

**Symptom**:
```
Error: No credentials cache found (ticket cache FILE:/krb5/cache/krb5cc)
```

**Solutions**:

1. **Check ticket status**:
   ```bash
   klist -s || echo "No ticket"
   ```

2. **Get new ticket**:
   ```bash
   kinit username@COMPANY.COM
   ```

3. **Check sidecar is running**:
   ```bash
   docker ps | grep kerberos-sidecar
   docker logs kerberos-sidecar
   ```

4. **Verify volume mount**:
   ```bash
   docker exec airflow-scheduler ls -la /krb5/cache/
   ```

### "Login failed for user"

**Symptom**:
```
Error: Login failed for user 'NT AUTHORITY\ANONYMOUS LOGON'
```

**Solutions**:

1. **Ensure Kerberos auth is enabled**:
   ```bash
   export MSSQL_AUTH_TYPE=kerberos
   ```

2. **Check SPN registration**:
   ```bash
   # On Windows domain controller
   setspn -L sql-server-hostname
   ```

3. **Verify delegation settings**:
   - SQL Server service account must have delegation rights
   - Check "Trust this computer for delegation" in AD

## 🟡 Performance Issues

### "Ingestion is very slow"

**Solutions**:

1. **Increase batch size**:
   ```bash
   datakit-sqlserver ingest-all --batch-size 50000
   ```

2. **Use parallel processing**:
   ```bash
   export BRONZE_MAX_WORKERS=8
   ```

3. **Check network latency**:
   ```bash
   ping -c 10 sql.company.com
   # Look for high latency or packet loss
   ```

4. **Profile the query**:
   ```sql
   -- In SQL Server
   SET STATISTICS TIME ON
   SET STATISTICS IO ON
   SELECT TOP 1000 * FROM your_table
   ```

### "Out of memory errors"

**Solutions**:

1. **Reduce batch size**:
   ```bash
   datakit-sqlserver ingest-table BigTable --batch-size 1000
   ```

2. **Process tables sequentially**:
   ```python
   # In your DAG
   for table in tables:
       ingest_task = ingest_table(table)
       # Don't parallelize
   ```

3. **Increase container memory**:
   ```yaml
   # docker-compose.yml
   services:
     scheduler:
       mem_limit: 4g
   ```

## 🟠 Data Issues

### "Data type conversion errors"

**Symptom**:
```
Error: ODBC SQL type -155 is not yet supported
```

**Solutions**:

1. **Cast problematic columns**:
   ```python
   # In configuration
   column_overrides = {
       'problematic_column': 'CAST(problematic_column AS VARCHAR(MAX))'
   }
   ```

2. **Skip unsupported columns**:
   ```bash
   datakit-sqlserver ingest-table MyTable \
     --exclude-columns "xml_column,geography_column"
   ```

### "Character encoding issues"

**Solutions**:

1. **Set correct encoding**:
   ```bash
   export PYTHONIOENCODING=utf-8
   export LANG=en_US.UTF-8
   ```

2. **Use Unicode driver**:
   ```python
   config = SQLServerConfig(
       driver="ODBC Driver 18 for SQL Server",
       extra_params="CharacterSet=UTF-8"
   )
   ```

## 🔵 Docker/Container Issues

### "Kerberos sidecar keeps restarting"

**Solutions**:

1. **Check logs**:
   ```bash
   docker logs kerberos-sidecar --tail 50
   ```

2. **Verify keytab permissions**:
   ```bash
   ls -la ./config/airflow.keytab
   # Should be readable by container user
   ```

3. **Test keytab manually**:
   ```bash
   docker exec kerberos-sidecar kinit -kt /krb5/keytabs/airflow.keytab airflow@COMPANY.COM
   ```

### "Permission denied errors"

**Solutions**:

1. **Fix volume permissions**:
   ```bash
   chmod 755 ./datakits
   chmod 644 ./config/*
   ```

2. **Check user mapping**:
   ```yaml
   # docker-compose.yml
   services:
     scheduler:
       user: "${AIRFLOW_UID:-50000}:${AIRFLOW_GID:-0}"
   ```

## 🟣 Configuration Issues

### "Environment variables not working"

**Solutions**:

1. **Check .env file location**:
   ```bash
   ls -la .env
   # Should be in project root
   ```

2. **Verify variable export**:
   ```bash
   env | grep MSSQL
   ```

3. **Use explicit config file**:
   ```bash
   datakit-sqlserver --config config.json test-connection
   ```

### "SSL/TLS certificate errors"

**Symptom**:
```
Error: SSL Provider: The certificate chain was issued by an authority that is not trusted
```

**Solutions**:

1. **For self-signed certificates**:
   ```bash
   export MSSQL_TRUST_CERT=true
   ```

2. **Install CA certificates**:
   ```bash
   # Copy CA cert to system store
   sudo cp company-ca.crt /usr/local/share/ca-certificates/
   sudo update-ca-certificates
   ```

3. **Disable encryption (dev only)**:
   ```bash
   export MSSQL_ENCRYPT=false
   ```

## 🛠️ Debug Commands

### Information Gathering

```bash
# Check all configurations
datakit-sqlserver validate-env

# Test specific server
datakit-sqlserver test-connection --server sql.test.com -vv

# List ODBC drivers
odbcinst -q -d

# Check Kerberos config
klist -kte /path/to/keytab

# Network diagnostics
nc -zv sql.company.com 1433
```

### Enable Debug Logging

```bash
# Maximum verbosity
export LOG_LEVEL=DEBUG
export KRB5_TRACE=/dev/stdout
export PYTHONASYNCIODEBUG=1

# ODBC trace
export ODBCTRACE=1
export ODBCTRACEFILE=/tmp/odbc.log
```

### Container Debugging

```bash
# Interactive shell in container
docker exec -it airflow-scheduler /bin/bash

# Check mounted volumes
docker inspect airflow-scheduler | jq '.[0].Mounts'

# View all environment variables
docker exec airflow-scheduler env | sort
```

## 💡 Prevention Tips

1. **Always validate configuration before production**:
   ```bash
   datakit-sqlserver validate-env
   datakit-sqlserver test-connection
   ```

2. **Start small**:
   - Test with one small table first
   - Use --dry-run flag
   - Gradually increase batch size

3. **Monitor resources**:
   ```bash
   docker stats
   htop
   ```

4. **Keep logs**:
   ```bash
   export LOG_FILE=/var/log/datakit/bronze-$(date +%Y%m%d).log
   ```

## 🆘 Still Stuck?

1. **Collect diagnostic information**:
   ```bash
   datakit-sqlserver validate-env > diagnostics.txt 2>&1
   docker logs kerberos-sidecar >> diagnostics.txt 2>&1
   env | grep -E "(KRB|MSSQL)" >> diagnostics.txt
   ```

2. **Check existing issues**: [GitHub Issues](https://github.com/...)

3. **Create detailed bug report** with:
   - Error message
   - Configuration (sanitized)
   - Diagnostic output
   - Steps to reproduce

## 🚦 Related Documentation

- [Setup Guide](./setup-guide.md) - Initial configuration
- [Configuration](./configuration.md) - All settings
- [Architecture](./architecture.md) - How it works internally