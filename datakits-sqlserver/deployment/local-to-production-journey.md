# The Journey: From Local Development to Production

How code moves from a developer's laptop to production, showcasing the environment abstraction.

## 🏃 Developer's Morning: Local Development

### 8:00 AM - Start Local Environment

```bash
# Developer's laptop (Windows with Docker Desktop)
cd ~/repos/airflow-data-platform-examples/datakits-sqlserver

# Start mock SQL Server (no real credentials needed)
make dev-mock

# Start local Airflow with Docker
make deploy
```

**What's Running**:
- Mock SQL Server (Docker container)
- Airflow (DockerOperator mode)
- Mock Kerberos (password auth for simplicity)
- Local registry at `registry.localhost`

### 8:30 AM - Develop New Feature

```python
# Developer edits the DAG
vim dags/sqlserver_bronze_dag.py

# Add a new table to ingest
TABLES_TO_INGEST = [
    "dbo.Customer",
    "dbo.Orders",
    "dbo.Products",  # ← New table added
]
```

### 9:00 AM - Test Locally

```bash
# Trigger DAG in Airflow UI (localhost:8080)
# DAG automatically uses DockerOperator because it detects local environment

# Watch it run
docker logs datakit-sqlserver-bronze

# Verify data landed in local Bronze
psql -h localhost -U bronze_user -d bronze \
  -c "SELECT COUNT(*) FROM bronze.dbo_products;"
```

**Key Point**: Developer never configured Docker vs Kubernetes - the code detected the environment and adapted.

## 🚀 Afternoon: Push to Integration

### 2:00 PM - Commit Changes

```bash
# Create feature branch
git checkout -b feature/add-products-table

# Commit
git add .
git commit -m "feat: add Products table to Bronze ingestion"

# Push to trigger CI/CD
git push origin feature/add-products-table
```

### 2:15 PM - CI/CD Pipeline (Automated)

```yaml
# .github/workflows/ci.yml runs automatically

steps:
  - name: Build Datakit
    run: |
      docker build -t sqlserver-bronze:${GITHUB_SHA} .

  - name: Run Tests
    run: |
      make test

  - name: Push to INT Registry
    run: |
      docker tag sqlserver-bronze:${GITHUB_SHA} \
        registry.int.company.com/datakits/sqlserver-bronze:development
      docker push registry.int.company.com/datakits/sqlserver-bronze:development
```

### 2:30 PM - Deploy to Integration (Kubernetes)

```yaml
# ArgoCD detects new image and deploys

# What happens in INT Kubernetes:
apiVersion: batch/v1
kind: Job
metadata:
  name: bronze-ingestion-${TIMESTAMP}
spec:
  template:
    spec:
      containers:
      - name: sqlserver-bronze
        image: registry.int.company.com/datakits/sqlserver-bronze:development
        env:
        - name: ENVIRONMENT
          value: "int"
```

**The Same DAG Now**:
- Detects it's in Kubernetes
- Uses KubernetesPodOperator automatically
- Pulls from INT registry
- Connects to INT SQL Server
- Uses Kerberos from K8s secret

### 3:00 PM - Verify in Integration

```bash
# Developer checks INT environment
kubectl -n airflow-int logs -f bronze-ingestion-pod

# Verify Products table was ingested
kubectl -n airflow-int exec -it bronze-warehouse -- \
  psql -U bronze_user -d bronze_int -c "SELECT COUNT(*) FROM bronze.dbo_products;"
```

## 📋 Next Day: QA Testing

### Day 2, 10:00 AM - Promote to QA

```bash
# After INT validation, promote version
git tag datakit-sqlserver-bronze-v1.3.3
git push --tags

# Update QA environment
cd ~/repos/gitops-config
vim environments/qa/kustomization.yaml
```

```yaml
# Change version for QA
images:
  - name: registry.qa.company.com/datakits/sqlserver-bronze
    newTag: v1.3.3  # ← Specific version for QA
```

```bash
git commit -m "chore: promote sqlserver-bronze v1.3.3 to QA"
git push
```

### Day 2, 11:00 AM - QA Validation

**In QA Kubernetes**:
- Same DAG code
- Now uses QA registry
- Connects to QA SQL Server
- Real Kerberos tickets from Delinea
- KubernetesPodOperator (detected automatically)

## 🏭 Week Later: Production Deployment

### Day 7, 2:00 PM - Production Approval

```bash
# After QA sign-off
cd ~/repos/gitops-config
vim environments/prod/kustomization.yaml
```

```yaml
# Update PROD to tested version
images:
  - name: registry.prod.company.com/datakits/sqlserver-bronze
    newTag: v1.3.3  # ← Same version QA tested
```

### Day 7, 8:00 PM - Production Deployment (Automated)

```bash
# Merge to main triggers production deployment
git checkout main
git merge feature/promote-v1.3.3
git push

# ArgoCD deploys to production Kubernetes
```

**In Production**:
- Same DAG code that developer wrote
- KubernetesPodOperator (auto-detected)
- Production registry
- Production SQL Server
- Kerberos from production Delinea
- Full monitoring and alerting

## 🔍 The Magic: Same Code Everywhere

### What the Developer Wrote Once:

```python
# This SAME code works in all environments
ingest_task = DatakitOperator.create(
    task_id='ingest_products',
    datakit_name='sqlserver-bronze',
    datakit_version=datakit_version,  # Changes per environment
    command='datakit-sqlserver ingest-table dbo.Products',
)
```

### What Actually Runs:

**Local (Docker Desktop)**:
```python
DockerOperator(
    image='registry.localhost/datakits/sqlserver-bronze:latest',
    docker_url='unix://var/run/docker.sock',
    # ... Docker-specific settings
)
```

**INT/QA/PROD (Kubernetes)**:
```python
KubernetesPodOperator(
    image='registry.{env}.company.com/datakits/sqlserver-bronze:v1.3.3',
    namespace='airflow-{env}',
    # ... Kubernetes-specific settings
)
```

## 📊 Environment Differences Summary

| Aspect | Local | INT | QA | PROD |
|--------|-------|-----|-----|------|
| **Execution** | Docker | K8s | K8s | K8s |
| **Registry** | localhost | int.company | qa.company | prod.company |
| **SQL Server** | Mock | INT DB | QA DB | PROD DB |
| **Kerberos** | Password | Test Keytab | QA Keytab | Prod Keytab |
| **Version** | latest | development | v1.3.3 | v1.3.3 |
| **Secrets** | .env file | K8s Secrets | Delinea | Delinea |

## 🎯 Key Achievements

1. **Developer writes once** - No environment-specific code
2. **Automatic adaptation** - Code detects and adjusts
3. **Same business logic** - Only infrastructure changes
4. **Progressive validation** - Test → INT → QA → PROD
5. **GitOps deployment** - Version controlled, auditable

## 💡 Why This Matters

**Without This Abstraction**:
- Developer has local DAG
- DevOps rewrites for Kubernetes
- Different code in each environment
- "Works on my machine" problems
- Deployment delays

**With This Abstraction**:
- One DAG for all environments
- Automatic environment detection
- Consistent behavior
- Fast deployment
- Developer autonomy

---

This journey shows how the same Bronze ingestion code seamlessly moves from a developer's Docker Desktop to production Kubernetes, automatically adapting to each environment while maintaining identical business logic.