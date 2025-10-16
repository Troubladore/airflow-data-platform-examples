# OpenMetadata Ingestion DAGs

**Programmatic metadata ingestion using Astronomer Airflow**

This example demonstrates the "everything as code" approach to metadata cataloging. Instead of manually configuring database connections in a UI, we define metadata ingestion as Airflow DAGs that run on a schedule.

---

## Philosophy: Everything as Code

**Why use DAGs for metadata ingestion?**

✅ **Version controlled** - Configuration in git, code review required
✅ **Repeatable** - Same config every time, no manual drift
✅ **Testable** - Can test ingestion logic before deploying
✅ **Schedulable** - Run weekly/daily to keep catalog fresh
✅ **Observable** - Airflow UI shows success/failure
✅ **Team culture** - Matches how we do everything else

**Not this (manual UI clicking):**
```
1. Open OpenMetadata UI
2. Click "Add Service"
3. Fill out form
4. Click "Test Connection"
5. Click "Add Ingestion"
6. Fill out another form
7. Click "Deploy"
... (repeat for every database)
```

**But this (code):**
```python
# Configuration as Python dict (version controlled!)
config = {
    "source": {...},
    "sink": {...}
}

workflow = Workflow.create(config)
workflow.execute()
```

---

## What This Example Includes

This Astronomer project contains two ingestion DAGs:

### 1. `ingest_pagila_metadata.py`
**Purpose:** Catalog pagila PostgreSQL schema

**What it demonstrates:**
- Basic PostgreSQL ingestion pattern
- Simple authentication (username/password)
- Table and column metadata extraction
- Relationship discovery (foreign keys)

**Run this first!** It's the simplest example with no authentication complexity.

### 2. `ingest_sqlserver_metadata.py`
**Purpose:** Catalog corporate SQL Server databases

**What it demonstrates:**
- SQL Server ingestion with Kerberos authentication
- Leverages platform Kerberos sidecar (no passwords in code!)
- Production-ready security pattern
- Corporate database cataloging

**Run this second!** After pagila works, this proves Kerberos integration.

---

## Prerequisites

### 1. Platform Services Running

The platform must be started first (provides OpenMetadata and Kerberos):

```bash
cd ~/repos/airflow-data-platform/platform-bootstrap
make platform-start
```

**This starts:**
- Kerberos sidecar (shares tickets)
- Platform PostgreSQL (metadata storage)
- OpenMetadata Server (http://localhost:8585)
- Elasticsearch (search)

### 2. Pagila Database (For Example 1)

**Option A: Use existing pagila**
If you already have pagila running from other examples.

**Option B: Start pagila for this example**
```bash
docker run -d \
  --name pagila-postgres \
  --network platform_network \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=pagila \
  -p 5432:5432 \
  postgres:15

# Load pagila schema
wget https://github.com/devrimgunduz/pagila/raw/master/pagila-schema.sql
wget https://github.com/devrimgunduz/pagila/raw/master/pagila-data.sql
docker exec -i pagila-postgres psql -U postgres -d pagila < pagila-schema.sql
docker exec -i pagila-postgres psql -U postgres -d pagila < pagila-data.sql
```

### 3. SQL Server Access (For Example 2)

For SQL Server ingestion, you need:
- Corporate SQL Server accessible
- Valid Kerberos ticket (`kinit`)
- Kerberos sidecar sharing tickets

**Test first:**
```bash
cd ~/repos/airflow-data-platform/platform-bootstrap
./diagnostics/test-sql-direct.sh sqlserver01.company.com TestDB
```

Should show: ✅ SUCCESS!

---

## Quick Start

### Step 1: Start This Astronomer Project

```bash
cd openmetadata-ingestion
astro dev start
```

**Astronomer will:**
- Build Docker image with OpenMetadata SDK
- Start Airflow webserver (http://localhost:8080)
- Connect to `platform_network` (access to OpenMetadata!)
- Mount Kerberos volume (for SQL Server ingestion)

### Step 2: Access Airflow UI

Open: **http://localhost:8080**

**You'll see two DAGs:**
- `openmetadata_ingest_pagila` (ready to run)
- `openmetadata_ingest_sqlserver` (ready to run)

### Step 3: Run Pagila Ingestion DAG

1. Click on `openmetadata_ingest_pagila`
2. Click "Trigger DAG" ▶️
3. Watch the logs in real-time
4. Should complete in ~10 seconds

**Expected output:**
```
[INFO] Connecting to PostgreSQL...
[INFO] ✓ Connection successful
[INFO] Extracting schema: public
[INFO] Found 15 tables
[INFO] Sending metadata to OpenMetadata API...
[SUCCESS] ✓ Metadata ingestion completed!
```

### Step 4: Verify in OpenMetadata UI

Open: **http://localhost:8585**

**Login:**
- Email: `admin@open-metadata.org`
- Password: `admin`

**Navigate:**
- Click "Explore" → "Tables"
- You should see pagila tables!

**Try searching:**
- Type "film" in search box
- See: `film`, `film_actor`, `film_category`

**Click on `film` table:**
- See schema (13 columns)
- See relationships (foreign keys)
- See sample data

### Step 5: Run SQL Server Ingestion (Optional)

**Prerequisites:**
- Kerberos ticket valid
- SQL Server accessible
- Tested with `test-sql-direct.sh`

**In Airflow:**
1. Click on `openmetadata_ingest_sqlserver`
2. Click "Trigger DAG" ▶️
3. Watch logs - should show Kerberos authentication!

**In OpenMetadata:**
- Search now shows both PostgreSQL AND SQL Server tables
- Cross-database discovery!

---

## Project Structure

```
openmetadata-ingestion/
├── README.md (this file)
├── Dockerfile
├── requirements.txt
├── docker-compose.override.yml
├── .dockerignore
├── .gitignore
├── dags/
│   ├── ingest_pagila_metadata.py
│   └── ingest_sqlserver_metadata.py
└── packages.txt (if needed for SQL Server)
```

---

## How It Works

### Ingestion Architecture

```
┌──────────────────────────────────────────────────────────┐
│ Astronomer Airflow (This Project)                       │
│                                                          │
│ DAG: ingest_pagila_metadata                             │
│   ↓                                                      │
│ Python Function (OpenMetadata SDK)                      │
│   ↓                                                      │
│ Connects to pagila-postgres:5432                        │
│   ↓                                                      │
│ Extracts schema metadata                                │
│   ↓                                                      │
│ Sends to OpenMetadata API                               │
│   (http://openmetadata-server:8585/api)                 │
└──────────────────────────────────────────────────────────┘
          ↓
┌──────────────────────────────────────────────────────────┐
│ OpenMetadata Server                                      │
│   ↓                                                      │
│ Stores metadata in platform-postgres:5432/openmetadata_db│
│   ↓                                                      │
│ Indexes in Elasticsearch for search                     │
│   ↓                                                      │
│ Available in UI at http://localhost:8585                │
└──────────────────────────────────────────────────────────┘
```

### Key Insight: Network Connectivity

All containers are on `platform_network`:
- ✅ Astronomer can reach pagila-postgres
- ✅ Astronomer can reach openmetadata-server API
- ✅ Astronomer can reach SQL Server (via network)
- ✅ Astronomer has Kerberos ticket (via volume mount)

---

## Customizing for Your Databases

### Adding a New PostgreSQL Database

**Copy:** `dags/ingest_pagila_metadata.py` → `dags/ingest_my_database.py`

**Edit the config:**
```python
config = {
    "source": {
        "type": "postgres",
        "serviceName": "my-database",  # Change this
        "serviceConnection": {
            "config": {
                "type": "Postgres",
                "hostPort": "my-postgres:5432",  # Change this
                "username": "my_user",           # Change this
                "password": "my_password",       # Or use env var
                "database": "my_database"        # Change this
            }
        },
        # ... rest stays the same
    }
}
```

**Commit and run!**

### Adding a New SQL Server Database

**Copy:** `dags/ingest_sqlserver_metadata.py` → `dags/ingest_my_sqlserver.py`

**Edit the config:**
```python
config = {
    "source": {
        "type": "mssql",
        "serviceName": "my-sql-server",              # Change this
        "serviceConnection": {
            "config": {
                "hostPort": "sqlserver02.company.com:1433",  # Change this
                "database": "MyDatabase",            # Change this
                # Kerberos settings stay the same!
            }
        }
    }
}
```

**No password needed!** Kerberos handles authentication.

---

## Scheduling Ingestion

By default, DAGs are set to `schedule_interval=None` (manual trigger only).

**To schedule weekly ingestion:**

Edit the DAG definition:
```python
with DAG(
    dag_id='openmetadata_ingest_pagila',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@weekly',  # Changed from None!
    catchup=False,
) as dag:
    # ...
```

**Cron schedules:**
- `@daily` - Every day at midnight
- `@weekly` - Every Sunday at midnight
- `@monthly` - First day of month
- `0 2 * * 0` - Every Sunday at 2 AM (custom cron)

---

## Troubleshooting

### Issue: DAG import errors

**Symptom:** DAG doesn't appear in Airflow UI

**Check:**
```bash
astro dev bash
# Inside container:
python dags/ingest_pagila_metadata.py
```

If it errors, check Python syntax or missing imports.

### Issue: Cannot connect to pagila

**Symptom:** "Connection refused" or "Could not resolve host"

**Solutions:**
1. Verify pagila is running: `docker ps | grep pagila`
2. Check network: `docker network inspect platform_network`
3. Test connection:
   ```bash
   docker exec -it <webserver-container> bash
   psql -h pagila-postgres -U postgres -d pagila
   ```

### Issue: Kerberos authentication fails (SQL Server)

**Symptom:** "Cannot authenticate using Kerberos"

**Solutions:**
1. Verify ticket in Airflow container:
   ```bash
   docker exec <webserver-container> klist -s
   ```
2. Run diagnostic:
   ```bash
   cd platform-bootstrap
   ./diagnostics/test-sql-direct.sh sqlserver01.company.com TestDB
   ```
3. Check Kerberos volume mount in `docker-compose.override.yml`

### Issue: OpenMetadata API not reachable

**Symptom:** "Connection refused to openmetadata-server:8585"

**Solutions:**
1. Check OpenMetadata is running:
   ```bash
   cd platform-bootstrap
   make platform-status
   ```
2. Verify network connectivity:
   ```bash
   docker exec <webserver-container> curl http://openmetadata-server:8585/api/v1/health
   ```

---

## Learning Resources

### OpenMetadata Documentation
- [Python SDK Guide](https://docs.open-metadata.org/latest/sdk/python)
- [Ingestion Framework](https://docs.open-metadata.org/latest/connectors/ingestion)
- [Database Connectors](https://docs.open-metadata.org/latest/connectors/database)

### Platform Documentation
- `docs/openmetadata-developer-journey.md` - The user experience vision
- `docs/openmetadata-integration-design.md` - Architecture details
- `docs/openmetadata-implementation-spec.md` - Implementation guide

### Example DAG Code
- `dags/ingest_pagila_metadata.py` - Start here (simple)
- `dags/ingest_sqlserver_metadata.py` - Advanced (Kerberos)

---

## Next Steps

After running these examples:

1. **Explore the metadata:** Browse tables, search schemas, understand relationships
2. **Add your databases:** Copy DAG patterns for your data sources
3. **Schedule ingestion:** Set appropriate schedules (weekly/monthly)
4. **Add descriptions:** Document tables in OpenMetadata UI
5. **Enable lineage:** (Phase 3) Track data flow through DAGs

---

## Questions?

**"Should I use programmatic ingestion or the OpenMetadata UI?"**
→ Use DAGs (everything as code). UI is for browsing metadata, not configuring it.

**"How often should I run ingestion?"**
→ Weekly for most databases. Daily if schema changes frequently. Monthly for stable schemas.

**"Can I ingest from multiple schemas/databases in one DAG?"**
→ Yes! Configure multiple sources or use filter patterns in the config.

**"Does this replace our data documentation?"**
→ Complements it! OpenMetadata provides searchable schema. Add descriptions in UI for business context.

**"What if I need to catalog cloud sources (S3, BigQuery)?"**
→ OpenMetadata supports 50+ connectors. Copy pattern, change source type. See OpenMetadata docs for specific config.

---

**Ready to start cataloging your data!** 🚀

Run `astro dev start` and trigger your first ingestion DAG.
