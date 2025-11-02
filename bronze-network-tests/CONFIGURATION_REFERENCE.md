# Bronze Network Tests - Configuration Reference

## Quick Reference for Future Developers

This document contains all the specific configurations and connection strings used for Bronze Layer network testing. Keep this handy when implementing Bronze datakits.

## Remote Postgres with Kerberos (ERUDITIS.LAB)

### Connection Details
```
Host: sqlpg.eruditis.lab
IP: 10.50.50.13
Port: 5432
Database: pagila
Authentication: Kerberos/GSSAPI
```

### Connection String (from host with ticket)
```bash
# Get Kerberos ticket first
kinit emaynard@ERUDITIS.LAB
# Password: Quicksand123!

# Connect with psql
psql "host=sqlpg.eruditis.lab port=5432 dbname=pagila gssencmode=require"
```

### Docker Configuration for Kerberos
```yaml
services:
  bronze-datakit:
    volumes:
      # Mount Kerberos config
      - /etc/krb5.conf:/etc/krb5.conf:ro
      # Mount credential cache
      - ~/.krb5-cache/dev:/tmp/krb5cc:ro
    environment:
      # Set credential cache location
      KRB5CCNAME: DIR:/tmp/krb5cc
      # Postgres settings
      POSTGRES_HOST: sqlpg.eruditis.lab
      POSTGRES_PORT: 5432
      POSTGRES_DB: pagila
      POSTGRES_GSSENCMODE: require
    extra_hosts:
      # Required host entries
      - "dc1.eruditis.lab:10.50.50.11"
      - "sqlpg.eruditis.lab:10.50.50.13"
```

### Python Connection (psycopg2)
```python
import psycopg2
import subprocess

# Extract username from Kerberos ticket
result = subprocess.run(['klist'], capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if 'Default principal:' in line:
        principal = line.split(':')[1].strip()  # e.g., emaynard@ERUDITIS.LAB
        username = principal.split('@')[0]      # e.g., emaynard
        break

# Connect with Kerberos
conn = psycopg2.connect(
    host='sqlpg.eruditis.lab',
    port='5432',
    database='pagila',
    user=username,  # IMPORTANT: Must specify user from ticket
    gssencmode='require'
)
```

## Container-to-Container Networking

### Docker Compose Service Names
```yaml
services:
  # Database service
  postgres-source:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: pagila
    networks:
      - bronze-network

  # Bronze datakit
  bronze-extractor:
    environment:
      POSTGRES_HOST: postgres-source  # Use service name
      POSTGRES_PORT: 5432
      POSTGRES_DB: pagila
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    networks:
      - bronze-network
```

### Python Connection
```python
conn = psycopg2.connect(
    host='postgres-source',  # Docker service name
    port='5432',
    database='pagila',
    user='postgres',
    password='postgres'
)
```

## Host Network Access (Docker Desktop)

### Configuration
```yaml
services:
  bronze-datakit:
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      POSTGRES_HOST: host.docker.internal
      POSTGRES_PORT: 5432
      POSTGRES_DB: pagila
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
```

### Connection String
```python
# From container to host machine
conn = psycopg2.connect(
    host='host.docker.internal',
    port='5432',
    database='pagila',
    user='postgres',
    password='postgres'
)
```

## Bronze Metadata Schema

Every extraction should add these metadata fields:

```python
df['bronze_load_timestamp'] = datetime.now().isoformat()
df['bronze_source_system'] = 'pagila_kerberos'  # or appropriate source
df['bronze_source_table'] = 'film'              # source table name
df['bronze_source_host'] = 'sqlpg.eruditis.lab' # actual host used
df['bronze_extraction_method'] = 'full_snapshot' # or 'incremental'
```

## File Storage Pattern

```
data/bronze/
├── {source_system}/
│   └── {table_name}/
│       ├── {YYYYMMDD_HHMMSS}.parquet
│       └── {YYYYMMDD_HHMMSS}.json
```

Example:
```
data/bronze/
├── pagila_kerberos/
│   └── film/
│       ├── 20251102_225515.parquet
│       └── 20251102_225515.json
```

## Testing Commands

### Quick Test All Patterns
```bash
cd bronze-network-tests

# Container-to-container
docker-compose run test-local

# Kerberos (ensure ticket is valid first)
docker-compose run test-kerberos

# Host networking
docker-compose run test-host-network
```

### Validate Prerequisites
```bash
# Check Kerberos ticket
klist

# Validate connections
./scripts/validate_connections.sh
```

## Troubleshooting

### Kerberos Issues
- **"Cannot contact any KDC"**: Check /etc/hosts has `10.50.50.11 dc1.eruditis.lab`
- **"GSSAPI authentication failed for user 'root'"**: Must extract username from ticket
- **"Server not found in Kerberos database"**: Must use hostname, not IP

### Docker Issues
- **"host.docker.internal not found"**: Add extra_hosts configuration
- **Container can't resolve service names**: Ensure both containers on same network

## Environment Details

Tested and validated on:
- Platform: WSL2 on Windows 11
- Docker: Docker Desktop
- Kerberos: MIT Kerberos with ERUDITIS.LAB domain
- PostgreSQL: 15.x (container) and 17.6 (remote)
- Python: 3.11 with psycopg2-binary 2.9.9

## Contact

For questions about the ERUDITIS.LAB test environment:
- Domain: ERUDITIS.LAB
- KDC: dc1.eruditis.lab (10.50.50.11)
- Test credentials documented in /home/emaynard/repos/networking/