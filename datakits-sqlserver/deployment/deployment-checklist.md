# Deployment Checklist

Step-by-step checklist for deploying the full SQL Server Bronze ingestion stack.

## 📋 Pre-Deployment Checklist

### Environment Setup
- [ ] Docker installed and running
- [ ] Docker Compose v2+ installed
- [ ] Local registry running (`registry.localhost`)
- [ ] Kerberos configured in WSL2/Linux
- [ ] Valid keytab or credentials available

### Repository Access
- [ ] `airflow-data-platform` repo cloned
- [ ] `airflow-data-platform-examples` repo cloned
- [ ] Both repos on correct branches

## 🏗️ Layer 1: Platform Deployment

### Build Platform Images
```bash
cd ~/repos/airflow-data-platform/kerberos-astronomer
```

- [ ] Build Kerberos sidecar:
  ```bash
  docker build -f Dockerfile.kerberos-sidecar -t kerberos-sidecar:0.1.0 .
  ```

- [ ] Build Astronomer with Kerberos:
  ```bash
  docker build -f Dockerfile.astronomer-kerberos -t astronomer-kerberos:0.1.0 .
  ```

### Push to Registry
- [ ] Tag for registry:
  ```bash
  docker tag kerberos-sidecar:0.1.0 registry.localhost/platform/kerberos-sidecar:0.1.0
  docker tag astronomer-kerberos:0.1.0 registry.localhost/platform/astronomer-kerberos:0.1.0
  ```

- [ ] Push to registry:
  ```bash
  docker push registry.localhost/platform/kerberos-sidecar:0.1.0
  docker push registry.localhost/platform/astronomer-kerberos:0.1.0
  ```

### Verify Layer 1
- [ ] Check images in registry:
  ```bash
  curl http://registry.localhost/v2/platform/kerberos-sidecar/tags/list
  curl http://registry.localhost/v2/platform/astronomer-kerberos/tags/list
  ```

## 🔧 Layer 2: Datakit Deployment

### Navigate to Datakits
```bash
cd ~/repos/airflow-data-platform-examples/datakits-sqlserver
```

### Configure Environment
- [ ] Copy environment template:
  ```bash
  cp .env.template .env
  ```

- [ ] Edit `.env` with your values:
  ```bash
  MSSQL_SERVER=your.sqlserver.com
  MSSQL_DATABASE=YourDatabase
  KRB_PRINCIPAL=svc_airflow@COMPANY.COM
  ```

### Build Datakit Images
- [ ] Build source connector:
  ```bash
  make layer2-build
  ```

- [ ] Verify builds:
  ```bash
  docker images | grep sqlserver
  ```

### Push Datakits to Registry
- [ ] Push to registry:
  ```bash
  make layer2-push
  ```

- [ ] Verify in registry:
  ```bash
  make layer2-status
  ```

## 📦 Layer 3: Warehouse Deployment

### Deploy Warehouse Infrastructure
- [ ] Start warehouse containers:
  ```bash
  make layer3-deploy
  ```

- [ ] Wait for initialization (30 seconds)

- [ ] Verify warehouse is running:
  ```bash
  make layer3-status
  ```

### Test Warehouse Connectivity
- [ ] Test Bronze database:
  ```bash
  psql -h localhost -p 5432 -U bronze_user -d bronze -c "\dt"
  ```

## 🚀 Full Stack Deployment

### Deploy Complete Stack
- [ ] Deploy all services:
  ```bash
  make deploy
  ```

- [ ] Wait for services to start (60 seconds)

### Verify All Services
- [ ] Check all containers running:
  ```bash
  make status
  ```

- [ ] Verify Kerberos ticket:
  ```bash
  docker exec kerberos-sidecar klist
  ```

- [ ] Test SQL Server connection:
  ```bash
  make test-connection
  ```

### Access Web Interfaces
- [ ] Open Airflow UI: http://localhost:8080
  - Username: admin
  - Password: admin

- [ ] Check DAGs are visible

## ✅ Post-Deployment Validation

### Test Data Flow
- [ ] Discover available tables:
  ```bash
  make test-discover
  ```

- [ ] Run test ingestion:
  ```bash
  make test-ingest
  ```

- [ ] Verify data in Bronze:
  ```bash
  psql -h localhost -p 5432 -U bronze_user -d bronze \
    -c "SELECT COUNT(*) FROM bronze.dbo_customer;"
  ```

### Monitor Services
- [ ] View logs:
  ```bash
  make logs
  ```

- [ ] Check for errors:
  ```bash
  docker-compose -f docker-compose.full-stack.yml logs | grep ERROR
  ```

## 🔧 Troubleshooting

### If Layer 1 fails:
```bash
# Check registry is running
docker ps | grep registry

# Rebuild and push
cd ~/repos/airflow-data-platform/kerberos-astronomer
make build && make push
```

### If Layer 2 fails:
```bash
# Verify Layer 1 images exist
docker pull registry.localhost/platform/astronomer-kerberos:0.1.0

# Check build arguments
make layer2-build REGISTRY_URL=registry.localhost
```

### If Layer 3 fails:
```bash
# Check PostgreSQL logs
docker logs sqlserver-bronze-warehouse

# Recreate warehouse
make clean
make layer3-deploy
```

### If Kerberos fails:
```bash
# Check ticket
docker exec kerberos-sidecar klist

# Verify keytab
ls -la ./config/airflow.keytab

# Test with password mode
export USE_PASSWORD=true
export KRB_PASSWORD=yourpassword
make deploy
```

## 📊 Success Metrics

### All Green Checklist:
- [ ] ✅ All containers running
- [ ] ✅ Kerberos ticket valid
- [ ] ✅ SQL Server connection successful
- [ ] ✅ Tables discovered
- [ ] ✅ Test ingestion completed
- [ ] ✅ Data visible in Bronze warehouse
- [ ] ✅ Airflow UI accessible
- [ ] ✅ No errors in logs

## 🎉 Deployment Complete!

When all items are checked, your three-layer SQL Server Bronze ingestion platform is fully deployed and operational.

### Next Steps:
1. Configure production credentials
2. Schedule DAGs in Airflow
3. Set up monitoring/alerting
4. Plan Silver/Gold transformations