# Three-Layer Architecture Implementation

This example demonstrates the complete three-layer architecture for SQL Server Bronze ingestion with Kerberos authentication.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│             LAYER 1: PLATFORM (Main Repo)            │
│                                                       │
│  • Kerberos Sidecar (ticket management)              │
│  • Astronomer Airflow (with Kerberos/ODBC)           │
│  • Base images pushed to registry.localhost          │
│                                                       │
└───────────────────┬──────────────────────────────────┘
                    │ Consumed by
┌───────────────────▼──────────────────────────────────┐
│          LAYER 2: DATAKITS (Examples Repo)           │
│                                                       │
│  • SQL Server Source Connector                       │
│  • Bronze ETL Processor                              │
│  • Built on Layer 1 base images                      │
│  • Pushed to registry for Layer 3 consumption        │
│                                                       │
└───────────────────┬──────────────────────────────────┘
                    │ Writes to
┌───────────────────▼──────────────────────────────────┐
│          LAYER 3: WAREHOUSE (Examples Repo)          │
│                                                       │
│  • Bronze Storage (PostgreSQL/S3/ADLS)               │
│  • Silver Storage (Transformed data)                 │
│  • Gold Storage (Analytics-ready)                    │
│  • Consumes Layer 2 containers from registry         │
│                                                       │
└──────────────────────────────────────────────────────┘
```

## 📦 Image Registry Flow

### Layer 1: Platform Images (Built in main repo)
```bash
# Built in airflow-data-platform repo
registry.localhost/platform/kerberos-sidecar:0.1.0
registry.localhost/platform/astronomer-kerberos:0.1.0
```

### Layer 2: Datakit Images (Built here, inherit from Layer 1)
```bash
# Built on top of Layer 1 images
registry.localhost/datakits/sqlserver-source:0.1.0
registry.localhost/datakits/sqlserver-bronze:0.1.0
```

### Layer 3: Warehouse (Consumes from registry)
```bash
# Uses images from registry, no build required
docker-compose pulls from registry.localhost
```

## 🚀 Deployment Workflow

### Step 1: Build & Push Layer 1 (Platform)
```bash
# In airflow-data-platform repo
cd kerberos-astronomer
make build
make push
```

### Step 2: Build & Push Layer 2 (Datakits)
```bash
# In this directory
make layer2-build  # Builds on Layer 1 base
make layer2-push   # Pushes to registry
```

### Step 3: Deploy Layer 3 (Warehouse)
```bash
# Deploy warehouse containers
make layer3-deploy
```

### Step 4: Deploy Full Stack
```bash
# Brings up everything using registry images
make deploy
```

## 🔄 Image Inheritance Chain

```
1. Base OS Image (debian/alpine)
        ↓
2. Platform Base (astronomer-runtime)
        ↓
3. Platform + Kerberos (Layer 1: astronomer-kerberos)
        ↓
4. Datakit Images (Layer 2: sqlserver-source, sqlserver-bronze)
        ↓
5. Runtime Deployment (Layer 3 consumes from registry)
```

## 📋 Configuration Flow

### Environment Variables Cascade:
```yaml
Layer 1 (Platform):
  - KRB_PRINCIPAL
  - KRB_REALM
  - KRB5_CONFIG

Layer 2 (Datakits) inherits + adds:
  - MSSQL_SERVER
  - MSSQL_DATABASE
  - MSSQL_AUTH_TYPE

Layer 3 (Warehouse) adds:
  - BRONZE_HOST
  - BRONZE_DATABASE
  - BRONZE_USER
```

## 🔐 Kerberos Ticket Sharing

```
Kerberos Sidecar (Layer 1)
    ↓ writes ticket to
Shared Volume (/krb5/cache)
    ↓ mounted by
All Layer 2 Datakits
    ↓ authenticate to
SQL Server (External)
    ↓ write to
Layer 3 Warehouse
```

## 🎯 Key Design Principles

1. **Layer Independence**: Each layer can be developed and deployed independently
2. **Registry-Centric**: All images flow through the registry
3. **Configuration Inheritance**: Lower layers inherit from higher layers
4. **Volume Sharing**: Kerberos tickets shared via Docker volumes
5. **Network Isolation**: Each layer has its own network, bridged where needed

## 📊 Data Flow

```
SQL Server (Source)
    ↓ [Kerberos Auth]
Layer 2: Source Datakit (Extract)
    ↓ [Raw Data]
Layer 2: Bronze Datakit (Transform)
    ↓ [Bronze Format]
Layer 3: Bronze Warehouse (Load)
    ↓ [Stored Data]
Layer 3: Silver Processing (Optional)
    ↓ [Cleansed Data]
Layer 3: Gold Analytics (Optional)
```

## 🛠️ Development vs Production

### Development:
- Can build all layers locally
- Use `docker-compose.override.yml` for local paths
- Mock SQL Server for testing

### Production:
- Pull all images from registry
- Use Kubernetes manifests instead of docker-compose
- Real SQL Server with production credentials
- Keytab-based authentication (not passwords)

## 📝 Quick Reference Commands

```bash
# Check what's in the registry
make registry-list

# Verify all layers are available
make status

# Build everything locally
make build

# Push everything to registry
make push

# Deploy from registry
make deploy

# View architecture
make diagram
```

## 🔍 Troubleshooting Layer Issues

### Layer 1 Issues:
```bash
# Check Kerberos sidecar
docker logs kerberos-sidecar

# Verify ticket
docker exec kerberos-sidecar klist
```

### Layer 2 Issues:
```bash
# Test source connectivity
make test-connection

# Check Bronze processing
docker logs datakit-sqlserver-bronze
```

### Layer 3 Issues:
```bash
# Check warehouse
make layer3-status

# View Bronze data
psql -h localhost -U bronze_user -d bronze
```

## 🎉 Success Criteria

You know the architecture is working when:

1. ✅ Layer 1 images are in registry
2. ✅ Layer 2 builds successfully on Layer 1 base
3. ✅ Layer 2 images are pushed to registry
4. ✅ Layer 3 pulls images from registry
5. ✅ Kerberos authentication works end-to-end
6. ✅ Data flows from SQL Server to Bronze warehouse

---

This implementation demonstrates the complete platform vision: modular layers, registry-based distribution, and clean separation of concerns.