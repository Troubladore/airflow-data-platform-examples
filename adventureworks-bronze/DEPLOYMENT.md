# Deployment Guide

Guide for deploying the AdventureWorksLT Bronze pipeline to production environments, including container image specifications for environments requiring pre-layered images.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Container Image Requirements](#container-image-requirements)
3. [Building Container Images](#building-container-images)
4. [Deploying to Astronomer](#deploying-to-astronomer)
5. [Corporate Environment Setup](#corporate-environment-setup)

---

## Architecture Overview

This example uses the **sqlmodel-framework** as a dependency for Bronze layer patterns. The framework can be:
1. **Embedded** - Copy framework source into your image
2. **Sidecar** - Mount framework as a sidecar container (future pattern)
3. **Package** - Install as Python package from internal PyPI

### Framework Dependency

The Bronze datakit depends on:
- `sqlmodel-framework` from `airflow-data-platform` repository
- Location: `/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src`

**Current approach in this example:**
```python
# In loader.py and models
import sys
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel_framework.base.loaders import BronzeIngestionPipeline
from sqlmodel_framework.base.models import BronzeMetadata
```

**For production**, you'll want to package the framework or use a sidecar pattern.

---

## Container Image Requirements

### Base Image

**Recommended:** `quay.io/astronomer/astro-runtime:latest`
- Includes Airflow and common data tools
- Based on Debian/Ubuntu
- Supports apt package installation

### System Dependencies

The following system packages are required:

1. **sqlcmd** (Microsoft SQL Server command-line tool)
   - For Kerberos-authenticated SQL Server connections
   - Installation:
     ```dockerfile
     # Add Microsoft repository
     RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
     RUN curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list

     # Install sqlcmd
     RUN apt-get update && \
         ACCEPT_EULA=Y apt-get install -y mssql-tools18 && \
         echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
     ```

2. **Kerberos Client** (if using Kerberos authentication)
   - Usually included in base image, but verify:
     ```dockerfile
     RUN apt-get update && apt-get install -y \
         krb5-user \
         libkrb5-dev
     ```

3. **PostgreSQL Client Libraries**
   - For GSSAPI support:
     ```dockerfile
     RUN apt-get update && apt-get install -y \
         libpq-dev \
         postgresql-client
     ```

### Python Dependencies

From `pyproject.toml`:
```
pandas>=2.0.0
sqlalchemy>=2.0.0
sqlmodel>=0.0.8
psycopg2-binary>=2.9.0
pyarrow>=10.0.0
pyyaml>=6.0.0
```

Plus the **sqlmodel-framework** (see options below).

---

## Building Container Images

### Option 1: Dockerfile with Embedded Framework (Recommended for Isolated Environments)

**Dockerfile:**
```dockerfile
# Start from Astronomer runtime
FROM quay.io/astronomer/astro-runtime:12.8.0

# Set user to root for package installation
USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    krb5-user \
    libkrb5-dev \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft SQL Server tools (sqlcmd)
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y mssql-tools18 && \
    ln -s /opt/mssql-tools18/bin/sqlcmd /usr/local/bin/sqlcmd && \
    rm -rf /var/lib/apt/lists/*

# Switch back to astro user
USER astro

# Copy sqlmodel-framework into image
COPY --chown=astro:astro airflow-data-platform/sqlmodel-framework /usr/local/airflow/sqlmodel-framework

# Copy Bronze datakit
COPY --chown=astro:astro adventureworks-bronze/bronze_datakits_adventureworkslt /usr/local/airflow/bronze_datakits_adventureworkslt
COPY --chown=astro:astro adventureworks-bronze/config.yaml /usr/local/airflow/config.yaml
COPY --chown=astro:astro adventureworks-bronze/pyproject.toml /usr/local/airflow/bronze-datakit-pyproject.toml

# Install Python dependencies
RUN pip install --no-cache-dir \
    pandas>=2.0.0 \
    sqlalchemy>=2.0.0 \
    sqlmodel>=0.0.8 \
    psycopg2-binary>=2.9.0 \
    pyarrow>=10.0.0 \
    pyyaml>=6.0.0

# Update sys.path to include framework
ENV PYTHONPATH="/usr/local/airflow/sqlmodel-framework/src:${PYTHONPATH}"
```

**Build script:**
```bash
#!/bin/bash
# build-image.sh

# Clone dependencies
git clone https://github.com/Troubladore/airflow-data-platform.git
git clone https://github.com/Troubladore/airflow-data-platform-examples.git

# Build image
docker build \
  --tag your-registry.company.com/adventureworks-bronze:v1.0.0 \
  --file Dockerfile \
  .

# Push to corporate registry
docker push your-registry.company.com/adventureworks-bronze:v1.0.0
```

### Option 2: Multi-Stage Build (Cleaner)

```dockerfile
# Stage 1: Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

# Clone/copy sqlmodel-framework
COPY airflow-data-platform/sqlmodel-framework ./sqlmodel-framework

# Package framework as wheel
WORKDIR /build/sqlmodel-framework
RUN pip install build && \
    python -m build --wheel

# Stage 2: Runtime
FROM quay.io/astronomer/astro-runtime:12.8.0

USER root

# System dependencies (same as Option 1)
RUN apt-get update && apt-get install -y \
    curl gnupg lsb-release \
    krb5-user libkrb5-dev \
    libpq-dev postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install sqlcmd
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y mssql-tools18 && \
    ln -s /opt/mssql-tools18/bin/sqlcmd /usr/local/bin/sqlcmd && \
    rm -rf /var/lib/apt/lists/*

USER astro

# Copy framework wheel from builder
COPY --from=builder /build/sqlmodel-framework/dist/*.whl /tmp/

# Install framework and dependencies
RUN pip install --no-cache-dir /tmp/*.whl && \
    pip install --no-cache-dir \
        pandas>=2.0.0 \
        sqlalchemy>=2.0.0 \
        sqlmodel>=0.0.8 \
        psycopg2-binary>=2.9.0 \
        pyarrow>=10.0.0 \
        pyyaml>=6.0.0 && \
    rm /tmp/*.whl

# Copy Bronze datakit
COPY --chown=astro:astro adventureworks-bronze/bronze_datakits_adventureworkslt /usr/local/airflow/bronze_datakits_adventureworkslt
COPY --chown=astro:astro adventureworks-bronze/config.yaml /usr/local/airflow/config.yaml
```

### Option 3: Using Corporate PyPI Mirror

If your company hosts an internal PyPI repository:

**pyproject.toml (update framework dependency):**
```toml
[project]
dependencies = [
    "pandas>=2.0.0",
    "sqlalchemy>=2.0.0",
    "sqlmodel>=0.0.8",
    "psycopg2-binary>=2.9.0",
    "pyarrow>=10.0.0",
    "pyyaml>=6.0.0",
    "sqlmodel-framework>=1.0.0",  # ← From corporate PyPI
]

[[tool.uv.index]]
url = "https://pypi.company.com/simple"  # ← Corporate mirror
```

**Dockerfile:**
```dockerfile
FROM quay.io/astronomer/astro-runtime:12.8.0

USER root
# System dependencies...
USER astro

# Copy Bronze datakit
COPY --chown=astro:astro adventureworks-bronze /usr/local/airflow/bronze_datakits_adventureworkslt

# Install from corporate PyPI
RUN pip install --index-url https://pypi.company.com/simple \
    -r /usr/local/airflow/bronze_datakits_adventureworkslt/requirements.txt
```

---

## Deploying to Astronomer

### Local Development (Astro CLI)

**Project structure:**
```
my-airflow-project/
├── dags/
│   └── adventureworks_bronze_dag.py
├── include/
│   ├── bronze_datakits_adventureworkslt/  # ← Bronze datakit
│   ├── sqlmodel-framework/                 # ← Framework (if embedded)
│   └── config.yaml
├── Dockerfile
├── packages.txt                            # System packages
├── requirements.txt                        # Python packages
└── airflow_settings.yaml
```

**Dockerfile (Astronomer project):**
```dockerfile
FROM quay.io/astronomer/astro-runtime:12.8.0
```

**packages.txt:**
```
krb5-user
libkrb5-dev
libpq-dev
postgresql-client
# sqlcmd requires manual installation - see Dockerfile
```

**requirements.txt:**
```
pandas>=2.0.0
sqlalchemy>=2.0.0
sqlmodel>=0.0.8
psycopg2-binary>=2.9.0
pyarrow>=10.0.0
pyyaml>=6.0.0
```

**Custom Dockerfile for sqlcmd:**
```dockerfile
FROM quay.io/astronomer/astro-runtime:12.8.0

USER root

# Install sqlcmd
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y mssql-tools18 && \
    ln -s /opt/mssql-tools18/bin/sqlcmd /usr/local/bin/sqlcmd && \
    rm -rf /var/lib/apt/lists/*

USER astro

# Set PYTHONPATH for framework
ENV PYTHONPATH="/usr/local/airflow/include/sqlmodel-framework/src:${PYTHONPATH}"
```

**Deploy:**
```bash
# Start local Airflow
astro dev start

# Test locally
astro dev bash
python /usr/local/airflow/include/bronze_datakits_adventureworkslt/test_loader.py

# Deploy to Astronomer cloud
astro deploy
```

### Astronomer Deployment Variables

Set these in Astronomer UI or `airflow_settings.yaml`:

```yaml
# Environment variables
environment_variables:
  - variable_name: "BRONZE_SOURCE_HOST"
    value: "sql1.eruditis.lab"

  - variable_name: "BRONZE_SOURCE_DB"
    value: "AdventureWorksLT"

  - variable_name: "BRONZE_TARGET_HOST"
    value: "sqlpg.eruditis.lab"

  - variable_name: "BRONZE_TARGET_DB"
    value: "bronze_warehouse"

# Secrets (use Astronomer secrets management)
# - Kerberos keytab file
# - Database passwords (if not using Kerberos)
```

---

## Corporate Environment Setup

### Pre-Layering Images (No PAT Required)

Many corporate environments restrict image building and require pre-layered images. Here's the process:

#### Image Build Specification

**Base Images Required:**
1. `quay.io/astronomer/astro-runtime:12.8.0` (or your corporate approved version)

**Custom Layers to Add:**

**Layer 1: System Dependencies**
```dockerfile
FROM quay.io/astronomer/astro-runtime:12.8.0 AS system-deps

USER root

RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    krb5-user=1.20.1-* \
    libkrb5-dev=1.20.1-* \
    libpq-dev=15.* \
    postgresql-client=15+* \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft SQL Server tools
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y mssql-tools18=18.3.* && \
    ln -s /opt/mssql-tools18/bin/sqlcmd /usr/local/bin/sqlcmd && \
    ln -s /opt/mssql-tools18/bin/bcp /usr/local/bin/bcp && \
    rm -rf /var/lib/apt/lists/*

USER astro

# Tag: your-registry.company.com/astro-runtime-bronze:system-deps-v1
```

**Layer 2: Python Dependencies**
```dockerfile
FROM your-registry.company.com/astro-runtime-bronze:system-deps-v1 AS python-deps

USER astro

# Install Python packages from requirements file or inline
RUN pip install --no-cache-dir \
    pandas==2.3.3 \
    sqlalchemy==2.0.44 \
    sqlmodel==0.0.27 \
    psycopg2-binary==2.9.11 \
    pyarrow==22.0.0 \
    pyyaml==6.0.3

# Tag: your-registry.company.com/astro-runtime-bronze:python-deps-v1
```

**Layer 3: Application Code**
```dockerfile
FROM your-registry.company.com/astro-runtime-bronze:python-deps-v1

USER astro

# Copy framework
COPY --chown=astro:astro sqlmodel-framework /usr/local/airflow/sqlmodel-framework

# Copy Bronze datakit
COPY --chown=astro:astro bronze_datakits_adventureworkslt /usr/local/airflow/include/bronze_datakits_adventureworkslt

# Copy configuration (use ConfigMap/Secret in K8s instead)
COPY --chown=astro:astro config.yaml /usr/local/airflow/include/config.yaml

# Update PYTHONPATH
ENV PYTHONPATH="/usr/local/airflow/sqlmodel-framework/src:${PYTHONPATH}"

# Tag: your-registry.company.com/adventureworks-bronze:v1.0.0
```

#### Build and Push Script

```bash
#!/bin/bash
# build-and-push.sh

REGISTRY="your-registry.company.com"
PROJECT="adventureworks-bronze"

# Build base layers (do once, reuse across projects)
docker build --target system-deps \
  -t ${REGISTRY}/astro-runtime-bronze:system-deps-v1 \
  -f Dockerfile.layers .

docker push ${REGISTRY}/astro-runtime-bronze:system-deps-v1

docker build --target python-deps \
  -t ${REGISTRY}/astro-runtime-bronze:python-deps-v1 \
  -f Dockerfile.layers .

docker push ${REGISTRY}/astro-runtime-bronze:python-deps-v1

# Build application layer (rebuild when code changes)
docker build \
  -t ${REGISTRY}/${PROJECT}:v1.0.0 \
  -f Dockerfile.app .

docker push ${REGISTRY}/${PROJECT}:v1.0.0
```

### Kerberos Setup in Containers

**Option 1: Keytab File (Recommended)**
```yaml
# In Astronomer deployment or K8s
volumes:
  - name: krb5-keytab
    secret:
      secretName: bronze-keytab

volumeMounts:
  - name: krb5-keytab
    mountPath: /etc/krb5.keytab
    readOnly: true

env:
  - name: KRB5_KTNAME
    value: /etc/krb5.keytab
```

**Option 2: Init Container with kinit**
```yaml
initContainers:
  - name: kerberos-init
    image: your-registry.company.com/krb5-client:latest
    command:
      - sh
      - -c
      - |
        echo "${KRB5_PASSWORD}" | kinit ${KRB5_PRINCIPAL}
        cp /tmp/krb5cc_* /shared/krb5cc
    env:
      - name: KRB5_PRINCIPAL
        value: airflow@YOUR.REALM
      - name: KRB5_PASSWORD
        valueFrom:
          secretKeyRef:
            name: kerberos-secret
            key: password
    volumeMounts:
      - name: shared
        mountPath: /shared
```

### Configuration Management

**Use ConfigMaps for config.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: bronze-config
data:
  config.yaml: |
    source:
      host: "sql1.eruditis.lab"
      database: "AdventureWorksLT"
      use_kerberos: true
      tables:
        - "SalesLT.ProductCategory"

    target:
      host: "sqlpg.eruditis.lab"
      port: 5432
      database: "bronze_warehouse"
      schema: "bronze"
      use_kerberos: true

    storage:
      bronze_path: "/tmp/bronze"
      formats:
        - "parquet"
```

Mount in deployment:
```yaml
volumeMounts:
  - name: bronze-config
    mountPath: /usr/local/airflow/include/config.yaml
    subPath: config.yaml
```

---

## Image Registry Requirements

### Images to Host in Corporate Registry

1. **Base Astronomer Runtime**
   - `quay.io/astronomer/astro-runtime:12.8.0`
   - Pull from Quay, push to corporate registry

2. **Custom Bronze Runtime** (system deps + Python deps)
   - `${REGISTRY}/astro-runtime-bronze:system-deps-v1`
   - `${REGISTRY}/astro-runtime-bronze:python-deps-v1`

3. **Application Image** (with Bronze datakit)
   - `${REGISTRY}/adventureworks-bronze:v1.0.0`

### Example Pull and Push

```bash
# Pull from public registries
docker pull quay.io/astronomer/astro-runtime:12.8.0

# Re-tag for corporate registry
docker tag quay.io/astronomer/astro-runtime:12.8.0 \
  your-registry.company.com/astronomer/astro-runtime:12.8.0

# Push to corporate registry
docker push your-registry.company.com/astronomer/astro-runtime:12.8.0
```

---

## Verification Checklist

After deployment:

- [ ] Container starts successfully
- [ ] `sqlcmd` is available (`which sqlcmd`)
- [ ] Kerberos ticket is valid (`klist`)
- [ ] Can connect to SQL Server (`sqlcmd -S ... -G -C -Q "SELECT 1"`)
- [ ] Can connect to PostgreSQL (`psql -h ... -d bronze_warehouse -c "SELECT 1"`)
- [ ] Framework is importable (`python -c "from sqlmodel_framework.base.models import BronzeMetadata"`)
- [ ] Bronze datakit is importable (`python -c "from bronze_datakits_adventureworkslt.loader import AdventureWorksLTBronzeLoader"`)
- [ ] Test extraction works (`python test_loader.py`)

---

**Questions about deployment?** Create an issue with your specific environment details.
