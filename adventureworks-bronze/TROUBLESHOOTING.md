# Troubleshooting Guide

**Common issues and how to fix them**

---

## Connection Issues

### "No Kerberos ticket found"

**Symptom:**
```
ERROR: No Kerberos ticket found. Run 'kinit' first.
```

**Cause:** You don't have a valid Kerberos ticket.

**Fix:**
```bash
# Get a Kerberos ticket
kinit your_username@YOUR.REALM

# Enter your password when prompted

# Verify ticket
klist
# Should show: Default principal: your_username@YOUR.REALM
```

**In production containers:**
Use a keytab file instead:
```bash
# Create keytab (run on KDC or with admin privileges)
ktutil
addent -password -p your_username@YOUR.REALM -k 1 -e aes256-cts
wkt /path/to/your.keytab
quit

# Use keytab in container
kinit -kt /etc/krb5.keytab your_username@YOUR.REALM
```

---

### "pg_hba.conf rejects connection"

**Symptom:**
```
FATAL: pg_hba.conf rejects connection for host "...", user "...", database "...", GSS encryption
```

**Cause:** PostgreSQL isn't configured to accept Kerberos connections.

**Fix:**
Edit PostgreSQL's `pg_hba.conf` file:
```conf
# Add this line (adjust for your network)
hostgssenc  all  all  0.0.0.0/0  gss include_realm=0 krb_realm=YOUR.REALM
```

Reload PostgreSQL:
```bash
sudo systemctl reload postgresql
# or
sudo pg_ctl reload
```

**Verify:**
```bash
psql -h your-pg-host -d postgres -c "SELECT version()"
# Should connect without password
```

---

### "sqlcmd: command not found"

**Symptom:**
```bash
sqlcmd -S host -Q "SELECT 1"
bash: sqlcmd: command not found
```

**Cause:** Microsoft SQL Server tools aren't installed.

**Fix for Ubuntu/Debian:**
```bash
# Add Microsoft repository
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

# Install
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y mssql-tools18

# Add to PATH
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
source ~/.bashrc

# Verify
sqlcmd -?
```

**Fix for containers:**
See [IMAGES.md](IMAGES.md#system-dependencies-layer-1) for Dockerfile instructions.

---

## Data Issues

### "integer out of range" or NaN errors

**Symptom:**
```
psycopg2.errors.NumericValueOutOfRange: integer out of range
```

**Cause:** SQL Server NULL values converted to pandas `NaN`, which PostgreSQL can't store in INTEGER columns.

**Fix:** This is already fixed in the latest code. If you still see this:

1. **Update to latest code:**
   ```bash
   cd adventureworks-bronze
   git pull origin main
   ```

2. **Verify NULL handling in loader.py:**
   ```python
   # Should see this in loader.py around line 152:
   df = df.replace({pd.NA: None, pd.NaT: None})
   import numpy as np
   df = df.replace({np.nan: None})
   ```

---

### Column name not found

**Symptom:**
```
KeyError: 'ProductCategoryID'
# or
sqlalchemy.exc.NoSuchColumnError
```

**Cause:** SQL Server uses PascalCase (`ProductCategoryID`), but our model expects lowercase (`productcategoryid`).

**Fix:** The loader automatically converts to lowercase. If you're seeing this:

1. **Check your model definition** matches lowercase:
   ```python
   class ProductCategoryBronze(BronzeMetadata, SQLModel, table=True):
       productcategoryid: int = Field(primary_key=True)  # ← lowercase
       # NOT: ProductCategoryID
   ```

2. **Verify column name conversion** in loader.py:
   ```python
   # Should see this in extract_table():
   df.columns = [col.lower() for col in df.columns]
   ```

---

## Permission Issues

### "Permission denied to create database"

**Symptom:**
```
psycopg2.errors.InsufficientPrivilege: permission denied to create database
```

**Cause:** Your PostgreSQL user doesn't have CREATEDB privilege.

**Fix:**
```sql
-- Run as PostgreSQL superuser (e.g., postgres)
ALTER USER your_username CREATEDB;
```

**Or:** Manually create the database first:
```bash
# As superuser
psql -U postgres -c "CREATE DATABASE bronze_warehouse"
psql -U postgres -c "GRANT ALL ON DATABASE bronze_warehouse TO your_username"

# Then run setup script (skip database creation)
# It will just create tables
uv run python setup_bronze_warehouse.py
```

---

### "Cannot remove worktree" (permission denied)

**Symptom:**
```
fatal: refusing to remove worktree: permission denied
```

**Cause:** Worktree directory owned by different user (e.g., root).

**Fix:**
```bash
# Use sudo to remove
sudo rm -rf .worktrees/problematic-worktree
git worktree prune

# Prevent future issues: don't run git commands with sudo
```

---

## Configuration Issues

### "No model found for table"

**Symptom:**
```
ValueError: No model found for table: SalesLT.Customer
```

**Cause:** You added a table to `config.yaml` but didn't create the model or register it.

**Fix:** Follow the complete workflow:

1. **Create model** in `models/customer_bronze.py`
2. **Import in** `models/__init__.py`
3. **Register in** `loader.py` TABLE_MODEL_MAP
4. **Add to** `config.yaml` tables list

See [CONFIGURATION.md](CONFIGURATION.md#adding-new-tables) for complete guide.

---

### Config file not found

**Symptom:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'config.yaml'
```

**Cause:** Running script from wrong directory.

**Fix:**
```bash
# Always run from the adventureworks-bronze directory
cd /path/to/airflow-data-platform-examples/adventureworks-bronze
uv run python test_loader.py
```

**In containers:**
Ensure config.yaml is copied to the right location:
```dockerfile
COPY --chown=astro:astro config.yaml /usr/local/airflow/include/config.yaml
```

---

## Import Errors

### "Cannot import BronzeMetadata"

**Symptom:**
```python
ImportError: cannot import name 'BronzeMetadata' from 'sqlmodel_framework.base.models'
```

**Cause:** sqlmodel-framework not in Python path.

**Fix for local development:**
```python
# In your model files, check this path is correct:
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')
```

**Fix for containers:**
```dockerfile
ENV PYTHONPATH="/usr/local/airflow/sqlmodel-framework/src:${PYTHONPATH}"
```

**Verify:**
```bash
python -c "from sqlmodel_framework.base.models import BronzeMetadata; print('OK')"
```

---

### "No module named 'pandas'" (or other package)

**Symptom:**
```
ModuleNotFoundError: No module named 'pandas'
```

**Cause:** Dependencies not installed.

**Fix:**
```bash
# Reinstall dependencies
cd adventureworks-bronze
uv sync

# Or if using pip
pip install pandas sqlalchemy sqlmodel psycopg2-binary pyarrow pyyaml
```

---

## Kerberos Issues

### Ticket expired

**Symptom:**
```
kinit: Ticket expired while renewing credentials
```

**Fix:**
```bash
# Destroy old ticket
kdestroy

# Get new ticket
kinit your_username@YOUR.REALM

# Verify
klist
```

**Prevent expiration:**
```bash
# Set ticket lifetime in krb5.conf
[libdefaults]
    ticket_lifetime = 24h
    renew_lifetime = 7d
```

---

### Wrong realm

**Symptom:**
```
kinit: Cannot find KDC for realm "WRONG.REALM" while getting initial credentials
```

**Cause:** You're using the wrong Kerberos realm.

**Fix:**
Check `/etc/krb5.conf` for correct realm:
```conf
[libdefaults]
    default_realm = YOUR.CORRECT.REALM

[realms]
    YOUR.CORRECT.REALM = {
        kdc = kdc.your.domain
    }
```

Use correct realm:
```bash
kinit your_username@YOUR.CORRECT.REALM
```

---

## Getting More Help

Still stuck? Try these:

1. **Check platform setup** - [Platform docs](https://github.com/Troubladore/airflow-data-platform/blob/main/docs/getting-started.md)

2. **Review logs:**
   ```bash
   # PostgreSQL logs
   sudo tail -f /var/log/postgresql/postgresql-*.log

   # Test extraction with verbose output
   uv run python test_loader.py --verbose  # (if implemented)
   ```

3. **Test components individually:**
   ```bash
   # Test SQL Server connection
   sqlcmd -S sql1.eruditis.lab -G -C -Q "SELECT @@VERSION"

   # Test PostgreSQL connection
   psql -h sqlpg.eruditis.lab -d postgres -c "SELECT version()"

   # Test Python imports
   python -c "from bronze_datakits_adventureworkslt.loader import AdventureWorksLTBronzeLoader; print('OK')"
   ```

4. **Create an issue** with:
   - Error message (full traceback)
   - Steps to reproduce
   - Environment (OS, Python version, etc.)
   - Relevant configuration (sanitize passwords!)
