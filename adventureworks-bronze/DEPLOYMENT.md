# Deployment Guide

**Taking the Bronze pipeline from local development to production**

This guide walks you through deploying the AdventureWorksLT Bronze pipeline to a production Airflow environment.

---

## Your Deployment Journey

```
Local Testing  →  Build Images  →  Configure Production  →  Deploy to Airflow
   (You are        (See IMAGES.md)     (This guide)         (Astronomer/K8s)
    here after
   README.md)
```

**Where are you?**
- ✅ Completed README.md and have the pipeline working locally
- ⏭️  Now deploying to Astronomer or production Airflow

---

## Deployment Checklist

Before starting, ensure you have:

- [ ] **Working local setup** - Completed all steps in README.md
- [ ] **Container images built** - See [IMAGES.md](IMAGES.md)
- [ ] **Production databases ready**
  - SQL Server with AdventureWorksLT
  - PostgreSQL for Bronze warehouse
  - Both configured for Kerberos (or password auth)
- [ ] **Airflow environment**
  - Astronomer Cloud/Enterprise, or
  - Self-hosted Airflow on Kubernetes
- [ ] **Secrets management** - Kerberos keytabs or database credentials

---

## Step 1: Understanding Production Requirements

### What Changes from Local to Production?

| Aspect | Local Development | Production |
|--------|------------------|-----------|
| **Code execution** | Run Python directly | Run in containers |
| **Configuration** | `config.yaml` file | Environment variables / Secrets |
| **Kerberos** | Your personal ticket (`kinit`) | Keytab files in containers |
| **Scheduling** | Manual (`python test_loader.py`) | Airflow DAG with schedule |
| **Monitoring** | Terminal output | Airflow UI + logging system |

---

## Step 2: Configuration Management

### Environment Variables Approach

Instead of hardcoding in `config.yaml`, use environment variables for production:

**Update `test_loader.py`** (or create `dag_loader.py`):
```python
import os

# Read from environment
config = {
    'source': {
        'host': os.getenv('BRONZE_SOURCE_HOST', 'sql1.eruditis.lab'),
        'database': os.getenv('BRONZE_SOURCE_DB', 'AdventureWorksLT'),
        'use_kerberos': os.getenv('BRONZE_SOURCE_USE_KERB', 'true') == 'true',
        'tables': os.getenv('BRONZE_TABLES', 'SalesLT.ProductCategory').split(',')
    },
    'target': {
        'host': os.getenv('BRONZE_TARGET_HOST', 'sqlpg.eruditis.lab'),
        'database': os.getenv('BRONZE_TARGET_DB', 'bronze_warehouse'),
        'use_kerberos': os.getenv('BRONZE_TARGET_USE_KERB', 'true') == 'true',
        # ...
    }
}
```

**Set in Astronomer:**
```yaml
# airflow_settings.yaml
environment_variables:
  - variable_name: "BRONZE_SOURCE_HOST"
    value: "sql1.production.company.com"

  - variable_name: "BRONZE_SOURCE_DB"
    value: "AdventureWorksLT"

  - variable_name: "BRONZE_TARGET_HOST"
    value: "postgres.production.company.com"

  - variable_name: "BRONZE_TABLES"
    value: "SalesLT.ProductCategory,SalesLT.Product,SalesLT.Customer"
```

**Or using Astronomer UI:**
1. Go to your Deployment
2. Environment → Environment Variables
3. Add each variable

---

### Secrets Management

**For Kerberos keytabs:**

**Option 1: Astronomer Secrets**
```bash
# Create secret
astro deployment secret create \
  --deployment-id=your-deployment-id \
  --key=KRB5_KEYTAB \
  --value="$(base64 < /path/to/your.keytab)"
```

**Option 2: Kubernetes Secrets**
```bash
# Create secret
kubectl create secret generic bronze-keytab \
  --from-file=krb5.keytab=/path/to/your.keytab \
  --namespace=your-namespace

# Mount in deployment
# (See Kerberos Setup section below)
```

---

## Step 3: Kerberos Setup in Containers

### Understanding Kerberos in Production

**Local:** You run `kinit` manually, ticket stored in `/tmp/krb5cc_*`
**Production:** Container needs keytab file and automatic kinit

### Approach 1: Keytab File (Recommended)

**Create keytab** (run on Kerberos KDC or with admin access):
```bash
# Interactive method
ktutil
addent -password -p airflow@YOUR.REALM -k 1 -e aes256-cts
# Enter password when prompted
wkt /path/to/airflow.keytab
quit

# Verify
klist -k /path/to/airflow.keytab
```

**Mount keytab in container:**

For Astronomer:
```yaml
# In your deployment configuration
volumes:
  - name: krb5-keytab
    secret:
      secretName: bronze-keytab

volumeMounts:
  - name: krb5-keytab
    mountPath: /etc/krb5.keytab
    subPath: krb5.keytab
    readOnly: true
```

For Kubernetes:
```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: airflow-worker
    volumeMounts:
    - name: krb5-keytab
      mountPath: /etc/krb5.keytab
      subPath: krb5.keytab
      readOnly: true
  volumes:
  - name: krb5-keytab
    secret:
      secretName: bronze-keytab
```

**Use keytab in code:**

Add to beginning of your DAG or loader:
```python
import subprocess
import os

def init_kerberos():
    """Initialize Kerberos ticket from keytab"""
    keytab_path = os.getenv('KRB5_KTNAME', '/etc/krb5.keytab')
    principal = os.getenv('KRB5_PRINCIPAL', 'airflow@YOUR.REALM')

    # Get ticket from keytab
    result = subprocess.run(
        ['kinit', '-kt', keytab_path, principal],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"kinit failed: {result.stderr}")

    # Verify
    klist_result = subprocess.run(['klist'], capture_output=True, text=True)
    print(f"Kerberos ticket: {klist_result.stdout}")

# Call at start of DAG run
init_kerberos()
```

---

### Approach 2: Init Container

Run kinit before main container starts:

```yaml
initContainers:
- name: kerberos-init
  image: your-registry.com/krb5-client:latest
  command:
    - sh
    - -c
    - |
      kinit -kt /etc/krb5.keytab airflow@YOUR.REALM
      cp /tmp/krb5cc_* /shared/krb5cc
  volumeMounts:
    - name: krb5-keytab
      mountPath: /etc/krb5.keytab
      subPath: krb5.keytab
    - name: shared
      mountPath: /shared

containers:
- name: airflow-worker
  env:
    - name: KRB5CCNAME
      value: /shared/krb5cc
  volumeMounts:
    - name: shared
      mountPath: /shared
```

---

### Approach 3: Ticket Renewal Sidecar

For long-running deployments, renew tickets automatically:

```python
# ticket_renewer.py
import subprocess
import time
import logging

def renew_ticket():
    """Renew Kerberos ticket using keytab"""
    subprocess.run(['kinit', '-R'], check=True)
    logging.info("Kerberos ticket renewed")

def main():
    while True:
        try:
            renew_ticket()
            time.sleep(3600)  # Renew every hour
        except Exception as e:
            logging.error(f"Renewal failed: {e}")
            time.sleep(60)  # Retry after 1 minute

if __name__ == "__main__":
    main()
```

Run as sidecar:
```yaml
containers:
- name: airflow-worker
  # ... main container

- name: ticket-renewer
  image: your-image:tag
  command: ["python", "/scripts/ticket_renewer.py"]
  volumeMounts:
    - name: krb5-keytab
      mountPath: /etc/krb5.keytab
```

---

## Step 4: Creating an Airflow DAG

### Basic DAG Structure

```python
# dags/adventureworks_bronze_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

# Add datakit to path
sys.path.insert(0, '/usr/local/airflow/include')

from bronze_datakits_adventureworkslt.loader import AdventureWorksLTBronzeLoader

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def extract_table(table_name: str, **context):
    """Extract single table"""
    import os

    # Initialize Kerberos
    init_kerberos()  # From earlier example

    # Create loader
    loader = AdventureWorksLTBronzeLoader(
        source_host=os.getenv('BRONZE_SOURCE_HOST'),
        source_database=os.getenv('BRONZE_SOURCE_DB'),
        use_kerberos=True,
        target_db_url=os.getenv('BRONZE_TARGET_URL')
    )

    # Load table
    result = loader.load_table(table_name)

    # Return for XCom
    return result

with DAG(
    'adventureworks_bronze_ingestion',
    default_args=default_args,
    description='Extract AdventureWorksLT tables to Bronze',
    schedule_interval='0 2 * * *',  # 2 AM daily
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['bronze', 'adventureworks', 'mssql'],
) as dag:

    # Create task for each table
    tables = ['SalesLT.ProductCategory', 'SalesLT.Product', 'SalesLT.Customer']

    for table in tables:
        task = PythonOperator(
            task_id=f'extract_{table.replace(".", "_")}',
            python_callable=extract_table,
            op_args=[table],
            pool='bronze_pool',  # Limit concurrent extractions
        )
```

---

### Advanced DAG: Dynamic Task Creation

```python
# dags/adventureworks_bronze_dynamic_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from datetime import datetime, timedelta
import os

# Table groups by size (for parallel processing)
TABLE_GROUPS = {
    'small': ['SalesLT.ProductCategory', 'SalesLT.ProductModel'],
    'medium': ['SalesLT.Product', 'SalesLT.Customer'],
    'large': ['SalesLT.SalesOrderHeader', 'SalesLT.SalesOrderDetail'],
}

def extract_table_group(group_name: str, **context):
    """Extract all tables in a group"""
    tables = TABLE_GROUPS[group_name]

    for table in tables:
        result = extract_table(table)
        context['task_instance'].xcom_push(
            key=f'{table}_result',
            value=result
        )

with DAG(
    'adventureworks_bronze_dynamic',
    default_args=default_args,
    schedule_interval='0 2 * * *',
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:

    # Create task group for each table group
    for group_name in TABLE_GROUPS.keys():
        with TaskGroup(group_id=f'{group_name}_tables') as tg:
            task = PythonOperator(
                task_id=f'extract_{group_name}',
                python_callable=extract_table_group,
                op_args=[group_name],
            )

    # Task groups run in parallel automatically
```

---

## Step 5: Deploying to Astronomer

### Astronomer Cloud / Enterprise

**Project structure:**
```
my-airflow-project/
├── dags/
│   └── adventureworks_bronze_dag.py
├── include/
│   ├── bronze_datakits_adventureworkslt/
│   └── config.yaml
├── Dockerfile                          # Points to your image
├── airflow_settings.yaml               # Environment variables
└── .astro/                            # Astronomer config
```

**Dockerfile:**
```dockerfile
# Use your custom image from IMAGES.md
FROM your-registry.company.com/adventureworks-bronze:v1.0.0

# That's it! Image already has everything
```

**Deploy:**
```bash
# Login to Astronomer
astro login

# Initialize project (if needed)
astro dev init

# Test locally
astro dev start

# Deploy to production
astro deploy --deployment-id=your-deployment-id
```

---

### Self-Hosted Airflow on Kubernetes

**Helm values:**
```yaml
# values.yaml
images:
  airflow:
    repository: your-registry.company.com/adventureworks-bronze
    tag: v1.0.0

env:
  - name: BRONZE_SOURCE_HOST
    value: "sql1.production.company.com"
  - name: BRONZE_TARGET_URL
    valueFrom:
      secretKeyRef:
        name: bronze-db-credentials
        key: target_url

extraVolumes:
  - name: krb5-keytab
    secret:
      secretName: bronze-keytab

extraVolumeMounts:
  - name: krb5-keytab
    mountPath: /etc/krb5.keytab
    subPath: krb5.keytab
    readOnly: true

dags:
  gitSync:
    enabled: true
    repo: https://github.com/your-org/airflow-dags.git
    branch: main
    subPath: "dags/"
```

**Deploy:**
```bash
helm upgrade --install airflow apache-airflow/airflow \
  --namespace airflow \
  --values values.yaml
```

---

## Step 6: Monitoring & Operations

### Logging

**Access logs in Astronomer:**
```bash
# View DAG logs
astro deployment logs --deployment-id=your-deployment-id

# Stream logs
astro deployment logs --follow
```

**Access logs in Kubernetes:**
```bash
# View worker logs
kubectl logs -n airflow -l component=worker --tail=100

# Stream logs
kubectl logs -n airflow -l component=worker -f
```

---

### Alerting

**Airflow email alerts** (configured in DAG):
```python
default_args = {
    'email': ['data-team@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
}
```

**Custom alerts on data quality:**
```python
def check_data_quality(**context):
    """Verify Bronze data looks correct"""
    import psycopg2

    conn = psycopg2.connect(os.getenv('BRONZE_TARGET_URL'))
    cursor = conn.execute("""
        SELECT COUNT(*) FROM bronze.bronze_product_category
        WHERE bronze_load_timestamp > NOW() - INTERVAL '1 hour'
    """)

    count = cursor.fetchone()[0]

    if count == 0:
        raise Exception("No data loaded in last hour!")

    return count
```

---

### Scaling

**Adjust Airflow pools** for parallel extraction:
```bash
# Astronomer UI: Admin → Pools
# or via Airflow CLI
airflow pools set bronze_pool 3 "Bronze extraction pool"
```

**Assign tasks to pool:**
```python
task = PythonOperator(
    task_id='extract_table',
    python_callable=extract_table,
    pool='bronze_pool',  # Max 3 concurrent
)
```

---

## Troubleshooting Production Issues

### Container can't connect to databases

**Check:**
1. Network policies allow traffic
2. Kerberos ticket is valid (`klist`)
3. Database hostnames resolve (`nslookup`)

```bash
# Debug from container
kubectl exec -it airflow-worker-xxx -- bash
klist
nslookup sql1.production.company.com
sqlcmd -S sql1.production.company.com -G -C -Q "SELECT 1"
```

---

### Kerberos tickets expire

**Solution:** Use ticket renewal sidecar (see Step 3, Approach 3)

---

### DAG imports fail

**Check:**
1. Image has datakit code
2. PYTHONPATH is set correctly

```bash
# Test import
kubectl exec -it airflow-worker-xxx -- \
  python -c "from bronze_datakits_adventureworkslt.loader import AdventureWorksLTBronzeLoader; print('OK')"
```

---

## Production Checklist

Before going live:

- [ ] **Images built and pushed** to corporate registry
- [ ] **Secrets created** (keytabs, credentials)
- [ ] **Environment variables** configured
- [ ] **DAG tested** locally (`astro dev start`)
- [ ] **Kerberos working** in container
- [ ] **Database connections** verified
- [ ] **Monitoring** set up (logs, alerts)
- [ ] **Backup strategy** for Bronze data
- [ ] **Runbook created** for on-call team

---

## Next Steps

- **Monitor your pipeline** - Check Airflow UI for task success
- **Add data quality checks** - Validate Bronze data
- **Build Silver layer** - Transform Bronze for analytics
- **Document runbook** - For operations team

---

**Questions?** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or create an issue.
