# Astronomer Platform Integration Strategy

How to align our architecture with Astronomer's self-hosted platform model while meeting enterprise requirements.

## 🌟 Astronomer's Self-Hosted Architecture

### What Astronomer Provides Out-of-the-Box

```
┌─────────────────────────────────────────────────────────┐
│                  Platform Namespace                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Astronomer Platform Services                    │    │
│  │  • Houston (API)                                 │    │
│  │  • Orbit (UI)                                    │    │
│  │  • Commander (Provisioning)                      │    │
│  │  • Registry (Images)                             │    │
│  │  • Grafana/Prometheus (Monitoring)               │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                            │
                    ┌───────┴────────┬─────────────┐
                    ▼                ▼             ▼
    ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
    │ Tenant Namespace │ │ Tenant Namespace │ │ Tenant Namespace │
    │   (Finance)      │ │   (Marketing)    │ │   (Analytics)    │
    │                  │ │                  │ │                  │
    │ • Airflow        │ │ • Airflow        │ │ • Airflow        │
    │ • Scheduler      │ │ • Scheduler      │ │ • Scheduler      │
    │ • Workers        │ │ • Workers        │ │ • Workers        │
    └──────────────────┘ └──────────────────┘ └──────────────────┘
```

## 🔄 Our Integration Strategy

### The Right Way: Use Astronomer's Components

**STOP Building**:
- ❌ Our own registry (use Astronomer's)
- ❌ Our own base images (extend Astronomer's)
- ❌ Our own deployment pipeline (use Astronomer's)

**START Using**:
- ✅ Astronomer's Houston API for deployments
- ✅ Astronomer's image inheritance model
- ✅ Astronomer's namespace-per-tenant pattern

## 🏗️ Revised Architecture for Astronomer Platform

### Layer 1: Platform Extensions (Not Replacements)

```dockerfile
# Instead of building our own base image...
# We EXTEND Astronomer's certified image from Artifactory

ARG ARTIFACTORY_URL=artifactory.company.com
ARG ASTRONOMER_VERSION=11.10.0

# Pull Astronomer's certified image from YOUR Artifactory
FROM ${ARTIFACTORY_URL}/astronomer-certified/ap-airflow:${ASTRONOMER_VERSION}

# Add only what's missing (Kerberos support)
USER root
RUN apt-get update && apt-get install -y krb5-user
USER astro

# That's it! Don't rebuild their platform
```

### Layer 2: Tenant-Specific Images

```yaml
# Each tenant (line of business) gets their own namespace
# with their own Airflow deployment

tenants:
  finance:
    namespace: airflow-finance
    image: ${ARTIFACTORY_URL}/airflow-images/finance:v1.2.3
    datakits:
      - sqlserver-bronze
      - oracle-bronze

  marketing:
    namespace: airflow-marketing
    image: ${ARTIFACTORY_URL}/airflow-images/marketing:v2.0.1
    datakits:
      - salesforce-bronze
      - mailchimp-bronze
```

## 📦 Artifactory Integration Pattern

### Configure Astronomer to Use Artifactory

```yaml
# astronomer-values.yaml
global:
  registry:
    # Point to your Artifactory instead of Docker Hub
    baseUrl: artifactory.company.com
    repository: astronomer-certified

  # Image pull secrets for Artifactory
  imagePullSecrets:
    - name: artifactory-credentials

astronomer:
  houston:
    config:
      deployments:
        # Force all deployments to use Artifactory
        registry:
          url: artifactory.company.com
          repository: airflow-deployments

  commander:
    env:
      # Ensure all pulled images are from Artifactory
      COMMANDER_REGISTRY_URL: artifactory.company.com
```

### Image Vetting Pipeline

```mermaid
Astronomer Releases v11.10.0
            ↓
    Security Team Vets
            ↓
    Push to Artifactory
            ↓
    Available for Tenants
```

## 🚀 Deployment Workflow with Astronomer Platform

### Step 1: Base Image Certification

```bash
# Security team vets and pushes Astronomer images to Artifactory
docker pull astronomer/ap-airflow:11.10.0-python-3.10

# Scan and verify
trivy image astronomer/ap-airflow:11.10.0-python-3.10

# Push to Artifactory
docker tag astronomer/ap-airflow:11.10.0-python-3.10 \
  artifactory.company.com/astronomer-certified/ap-airflow:11.10.0-python-3.10

docker push artifactory.company.com/astronomer-certified/ap-airflow:11.10.0-python-3.10
```

### Step 2: Tenant Deployment

```bash
# Each line of business deploys via Astronomer CLI
astro deployment create \
  --name finance-prod \
  --executor KubernetesExecutor \
  --registry artifactory.company.com/airflow-deployments

# Deploy their DAGs
astro deploy --deployment-id finance-prod-uuid
```

### Step 3: Datakit Integration

```python
# In tenant's DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

# Datakit images also from Artifactory
bronze_ingestion = KubernetesPodOperator(
    task_id='ingest_bronze',
    image='artifactory.company.com/datakits/sqlserver-bronze:v1.2.3',
    # Runs in tenant's namespace automatically
    namespace='{{ var.value.astronomer_namespace }}',
)
```

## 🔐 Kerberos Integration with Astronomer

### Platform-Level Kerberos Sidecar

```yaml
# Added to Astronomer platform namespace
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kerberos-sidecar
  namespace: astronomer-platform
spec:
  template:
    spec:
      containers:
      - name: kerberos-manager
        image: artifactory.company.com/platform/kerberos-sidecar:v1.0.0
        env:
        - name: DELINEA_VAULT_URL
          valueFrom:
            secretKeyRef:
              name: delinea-config
              key: vault-url
```

### Tenant Access to Kerberos Tickets

```yaml
# Each tenant namespace gets access to tickets
apiVersion: v1
kind: ConfigMap
metadata:
  name: kerberos-mount-config
  namespace: airflow-finance
data:
  mount_path: /krb5/cache
  ticket_cache: krb5cc_finance
```

## 📋 Configuration Management

### Global Platform Configuration

```yaml
# platform-config.yaml
artifactory:
  url: artifactory.company.com
  credentials_secret: artifactory-creds

kerberos:
  sidecar_image: artifactory.company.com/platform/kerberos-sidecar:v1.0.0
  realm: COMPANY.COM

tenants:
  - name: finance
    namespace: airflow-finance
    max_workers: 10
    datakits:
      - sqlserver-bronze
      - oracle-bronze

  - name: marketing
    namespace: airflow-marketing
    max_workers: 5
    datakits:
      - salesforce-bronze
```

### Per-Tenant Configuration

```python
# finance/airflow_settings.yaml
airflow:
  connections:
    - conn_id: sql_server_prod
      conn_type: mssql
      host: sql-prod.company.com
      extra:
        auth_type: kerberos

  variables:
    artifactory_url: artifactory.company.com
    datakit_registry: artifactory.company.com/datakits
    environment: production
```

## 🔄 Migration Path

### From Our Current Architecture → Astronomer Platform

1. **Keep**: Kerberos sidecar pattern (becomes platform service)
2. **Keep**: Datakit concept (but deploy via Astronomer)
3. **Change**: Use Astronomer's registry instead of our own
4. **Change**: Use Houston API instead of direct Docker commands
5. **Change**: Tenant namespaces instead of warehouse separation

### Local Development Changes

```bash
# Before: Complex docker-compose
docker-compose -f docker-compose.full-stack.yml up

# After: Astronomer CLI
astro dev start
```

### The `.astro/config.yaml` for Local Dev

```yaml
project:
  name: finance-datakits

# Point to Artifactory for base image
airflow:
  image:
    repository: artifactory.company.com/astronomer-certified/ap-airflow
    tag: 11.10.0-python-3.10

# Mount local datakits for development
docker:
  volumes:
    - ./datakits:/usr/local/airflow/datakits

# Local Artifactory credentials
registry:
  url: artifactory.company.com
  username: ${ARTIFACTORY_USERNAME}
  password: ${ARTIFACTORY_PASSWORD}
```

## 🎯 Benefits of Aligning with Astronomer

1. **Platform Services**: Get monitoring, logging, and alerting for free
2. **Multi-Tenancy**: Built-in namespace isolation per line of business
3. **Upgrade Path**: Easier Astronomer version upgrades
4. **Support**: Can get help from Astronomer support
5. **Community**: Follows patterns other Astronomer users expect

## 📊 Final Architecture

```
Artifactory (Company Registry)
    ├── astronomer-certified/
    │   └── ap-airflow:11.10.0  (Vetted Astronomer images)
    ├── platform/
    │   └── kerberos-sidecar:v1.0.0  (Our platform additions)
    └── datakits/
        ├── sqlserver-bronze:v1.2.3
        └── oracle-bronze:v2.0.1

Astronomer Platform (Kubernetes)
    ├── Platform Namespace
    │   ├── Houston API
    │   ├── Astronomer Registry (proxies to Artifactory)
    │   └── Kerberos Sidecar (our addition)
    └── Tenant Namespaces
        ├── airflow-finance/
        ├── airflow-marketing/
        └── airflow-analytics/
```

## 🚦 Next Steps

1. **Install Astronomer Platform** with Artifactory configuration
2. **Migrate base images** to extend Astronomer's certified images
3. **Create tenant namespaces** per line of business
4. **Deploy datakits** using Houston API
5. **Retire custom registry** in favor of Astronomer's

---

This approach gives you the best of both worlds: Astronomer's battle-tested platform with your enterprise requirements (Artifactory, Kerberos, multi-tenancy) properly integrated.