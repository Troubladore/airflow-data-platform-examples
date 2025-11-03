# Container Images Guide

**Building Docker images for the AdventureWorksLT Bronze pipeline**

This guide explains what container images you need and how to build them for production deployment.

---

## Do I Need This?

**Skip this if:**
- You're just testing locally with Python
- You're running `test_loader.py` from your workstation

**Read this if:**
- Deploying to Astronomer or Airflow in production
- Your company requires pre-built images (no building images on-the-fly)
- You need to push images to a corporate registry

---

## Understanding the Image Layers

Think of container images like a layer cake. You build from the bottom up:

```
┌─────────────────────────────────────┐
│  Your Bronze Datakit Code           │ ← Layer 3: Your code
├─────────────────────────────────────┤
│  Python Dependencies                 │ ← Layer 2: pandas, sqlalchemy, etc.
├─────────────────────────────────────┤
│  System Tools (sqlcmd, Kerberos)    │ ← Layer 1: Operating system packages
├─────────────────────────────────────┤
│  Astronomer Runtime (Base)          │ ← Layer 0: Airflow + Python
└─────────────────────────────────────┘
```

**Why layers?**
- Layers can be cached and reused
- Only rebuild what changed
- Corporate environments can pre-approve base layers

---

## Image Requirements

### Base Image

**Start with:** `quay.io/astronomer/astro-runtime:12.8.0`

This includes:
- Apache Airflow
- Python 3.11
- Common data tools
- Debian/Ubuntu base

### System Dependencies (Layer 1)

You need to install these system packages:

1. **sqlcmd** - Microsoft SQL Server command-line tool
   - Required for connecting to SQL Server with Kerberos
   - Binary location: `/opt/mssql-tools18/bin/sqlcmd`

2. **Kerberos client** - For GSSAPI authentication
   - Packages: `krb5-user`, `libkrb5-dev`
   - Usually included in base image, but verify

3. **PostgreSQL client libraries** - For GSSAPI support
   - Packages: `libpq-dev`, `postgresql-client`
   - Required for psycopg2 Kerberos support

### Python Dependencies (Layer 2)

From `pyproject.toml`:
```
pandas>=2.0.0
sqlalchemy>=2.0.0
sqlmodel>=0.0.8
psycopg2-binary>=2.9.0
pyarrow>=10.0.0
pyyaml>=6.0.0
```

### Application Code (Layer 3)

- sqlmodel-framework (from airflow-data-platform repo)
- bronze_datakits_adventureworkslt (this datakit)
- config.yaml (your configuration)

---

## Building Images: Three Approaches

### Option 1: Simple Single-Stage Build (Easiest)

**Best for:** Development, testing, simple deployments

**Dockerfile:**
```dockerfile
FROM quay.io/astronomer/astro-runtime:12.8.0

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

USER astro

# Copy sqlmodel-framework
COPY --chown=astro:astro airflow-data-platform/sqlmodel-framework /usr/local/airflow/sqlmodel-framework

# Copy Bronze datakit
COPY --chown=astro:astro adventureworks-bronze/bronze_datakits_adventureworkslt /usr/local/airflow/include/bronze_datakits_adventureworkslt
COPY --chown=astro:astro adventureworks-bronze/config.yaml /usr/local/airflow/include/config.yaml

# Install Python dependencies
RUN pip install --no-cache-dir \
    pandas>=2.0.0 \
    sqlalchemy>=2.0.0 \
    sqlmodel>=0.0.8 \
    psycopg2-binary>=2.9.0 \
    pyarrow>=10.0.0 \
    pyyaml>=6.0.0

# Add framework to Python path
ENV PYTHONPATH="/usr/local/airflow/sqlmodel-framework/src:${PYTHONPATH}"
```

**Build and test:**
```bash
# Clone dependencies first
git clone https://github.com/Troubladore/airflow-data-platform.git
git clone https://github.com/Troubladore/airflow-data-platform-examples.git

# Build
docker build \
  -t adventureworks-bronze:dev \
  -f Dockerfile \
  .

# Test
docker run -it adventureworks-bronze:dev \
  python -c "from bronze_datakits_adventureworkslt.loader import AdventureWorksLTBronzeLoader; print('OK')"
```

---

### Option 2: Multi-Layer Build (Corporate Environments)

**Best for:** Environments that require pre-approved base images

This approach builds three separate images that can be approved independently:

#### Step 1: System Dependencies Layer

```dockerfile
# Dockerfile.system-deps
FROM quay.io/astronomer/astro-runtime:12.8.0

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

# Install sqlcmd with specific version
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y mssql-tools18=18.3.* && \
    ln -s /opt/mssql-tools18/bin/sqlcmd /usr/local/bin/sqlcmd && \
    rm -rf /var/lib/apt/lists/*

USER astro
```

**Build:**
```bash
docker build \
  -f Dockerfile.system-deps \
  -t your-registry.company.com/astro-runtime:system-deps-v1 \
  .
docker push your-registry.company.com/astro-runtime:system-deps-v1
```

#### Step 2: Python Dependencies Layer

```dockerfile
# Dockerfile.python-deps
FROM your-registry.company.com/astro-runtime:system-deps-v1

USER astro

RUN pip install --no-cache-dir \
    pandas==2.3.3 \
    sqlalchemy==2.0.44 \
    sqlmodel==0.0.27 \
    psycopg2-binary==2.9.11 \
    pyarrow==22.0.0 \
    pyyaml==6.0.3
```

**Build:**
```bash
docker build \
  -f Dockerfile.python-deps \
  -t your-registry.company.com/astro-runtime:python-deps-v1 \
  .
docker push your-registry.company.com/astro-runtime:python-deps-v1
```

#### Step 3: Application Code Layer

```dockerfile
# Dockerfile.app
FROM your-registry.company.com/astro-runtime:python-deps-v1

USER astro

# Copy framework
COPY --chown=astro:astro sqlmodel-framework /usr/local/airflow/sqlmodel-framework

# Copy Bronze datakit
COPY --chown=astro:astro bronze_datakits_adventureworkslt /usr/local/airflow/include/bronze_datakits_adventureworkslt
COPY --chown=astro:astro config.yaml /usr/local/airflow/include/config.yaml

# Set Python path
ENV PYTHONPATH="/usr/local/airflow/sqlmodel-framework/src:${PYTHONPATH}"
```

**Build:**
```bash
docker build \
  -f Dockerfile.app \
  -t your-registry.company.com/adventureworks-bronze:v1.0.0 \
  .
docker push your-registry.company.com/adventureworks-bronze:v1.0.0
```

**Why this approach?**
- IT can approve system-deps layer once (rarely changes)
- IT can approve python-deps layer when dependencies change
- You rebuild app layer frequently (your code changes)
- Faster builds (layer caching)

---

### Option 3: Using Corporate PyPI Mirror

**Best for:** Companies with internal package repositories

If your company hosts packages internally, simplify by installing framework as a package:

**Add to pyproject.toml:**
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
url = "https://pypi.company.com/simple"
```

**Dockerfile:**
```dockerfile
FROM quay.io/astronomer/astro-runtime:12.8.0

USER root
# Install system dependencies (same as Option 1)
USER astro

COPY --chown=astro:astro adventureworks-bronze /usr/local/airflow/bronze_datakits_adventureworkslt

RUN pip install \
    --index-url https://pypi.company.com/simple \
    -e /usr/local/airflow/bronze_datakits_adventureworkslt
```

---

## Production Checklist

Before pushing to production, verify:

- [ ] **sqlcmd is installed and in PATH**
  ```bash
  docker run -it your-image:tag which sqlcmd
  # Should output: /usr/local/bin/sqlcmd
  ```

- [ ] **Kerberos libraries are available**
  ```bash
  docker run -it your-image:tag klist --version
  # Should show Kerberos version
  ```

- [ ] **Python packages are installed**
  ```bash
  docker run -it your-image:tag python -c "import pandas, sqlalchemy, psycopg2; print('OK')"
  ```

- [ ] **Framework is importable**
  ```bash
  docker run -it your-image:tag python -c "from sqlmodel_framework.base.models import BronzeMetadata; print('OK')"
  ```

- [ ] **Datakit is importable**
  ```bash
  docker run -it your-image:tag python -c "from bronze_datakits_adventureworkslt.loader import AdventureWorksLTBronzeLoader; print('OK')"
  ```

---

## Deploying to Astronomer

Once you have your image built:

### Local Astronomer Development

```bash
# In your Astronomer project directory
astro dev start --image your-registry.company.com/adventureworks-bronze:v1.0.0
```

### Astronomer Cloud/Enterprise

Update `Dockerfile` in your Astronomer project:
```dockerfile
FROM your-registry.company.com/adventureworks-bronze:v1.0.0
```

Deploy:
```bash
astro deploy
```

---

## Troubleshooting Images

### "sqlcmd: command not found"

The sqlcmd binary isn't in PATH. Check:
```bash
docker run -it your-image:tag find /opt -name sqlcmd
```

Fix by adding symlink:
```dockerfile
RUN ln -s /opt/mssql-tools18/bin/sqlcmd /usr/local/bin/sqlcmd
```

### "Cannot import BronzeMetadata"

Framework isn't in PYTHONPATH. Check:
```bash
docker run -it your-image:tag python -c "import sys; print('\n'.join(sys.path))"
```

Fix:
```dockerfile
ENV PYTHONPATH="/usr/local/airflow/sqlmodel-framework/src:${PYTHONPATH}"
```

### Large Image Size

Optimize by:
1. Cleaning apt cache: `rm -rf /var/lib/apt/lists/*`
2. Using `--no-cache-dir` with pip
3. Multi-stage builds (copy only runtime artifacts)

---

## Next Steps

- **Configure Kerberos in containers** → [DEPLOYMENT.md](DEPLOYMENT.md#kerberos-setup)
- **Set up environment variables** → [DEPLOYMENT.md](DEPLOYMENT.md#configuration-management)
- **Create Airflow DAGs** → [DEPLOYMENT.md](DEPLOYMENT.md#airflow-integration)
