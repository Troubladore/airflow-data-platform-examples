# Pre-Built Runner Pattern

## Problem Statement

In restricted corporate environments:
- Package repositories require authentication
- Building custom images is complex and slow
- Network policies block public registries
- Security scanning required for all images

## Solution: Pre-Built Runners

### Core Concept

Instead of building custom datakit images, we use **pre-built runner images** with all dependencies installed, and mount our code at runtime.

```
Traditional Approach:          Runner Pattern:
┌─────────────────┐           ┌─────────────────┐
│ Custom Datakit  │           │ Standard Runner │
│ - Base Image    │           │ - All Deps      │
│ - Install Deps  │           │ - Frameworks    │
│ - Copy Code     │     →     │ - Tools         │
│ - Run           │           └─────────────────┘
└─────────────────┘                    +
                              ┌─────────────────┐
                              │ Mount Code      │
                              │ - /app/src      │
                              │ - /app/config   │
                              └─────────────────┘
```

## Runner Types for Bronze Layer

### 1. SQLModel Runner
**Purpose**: Bronze/Silver/Gold layer transformations using temporal patterns
```dockerfile
# runners/sqlmodel-runner/Dockerfile
FROM ${ASTRONOMER_BASE_IMAGE}

# Pre-installed dependencies
- sqlmodel-framework (from platform)
- psycopg3
- pandas
- SQLAlchemy
- Temporal pattern libraries

# Entry point expects mounted code
ENTRYPOINT ["python", "/app/src/main.py"]
```

### 2. Spark Runner
**Purpose**: Large-scale data processing
```dockerfile
# runners/spark-runner/Dockerfile
FROM ${ASTRONOMER_BASE_IMAGE}

# Pre-installed dependencies
- PySpark
- Delta Lake
- Hadoop libraries
- JDBC drivers

ENTRYPOINT ["spark-submit", "/app/src/main.py"]
```

### 3. DBT Runner
**Purpose**: SQL-based transformations
```dockerfile
# runners/dbt-runner/Dockerfile
FROM ${ASTRONOMER_BASE_IMAGE}

# Pre-installed dependencies
- dbt-core
- dbt-postgres
- dbt-sqlserver
- dbt-snowflake

ENTRYPOINT ["dbt", "run", "--project-dir", "/app/dbt"]
```

## Implementation Strategy

### Phase 1: Local Development (Current)
**Location**: `airflow-data-platform-examples/runners/`
- Define runner specifications here
- Build and test locally
- Iterate quickly without dependencies

### Phase 2: Platform Integration (Future)
**Location**: `airflow-data-platform/runtime-images/`
- Move proven runner definitions to platform
- Central build pipeline
- Security scanning and approval

### Phase 3: Production Usage (Final)
**Registry**: `artifactory.company.com/platform/runners/`
- Pre-built, vetted runners
- Version controlled
- No build required by developers

## Usage Pattern

### In Airflow DAG

```python
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

# Using pre-built runner with mounted code
bronze_task = KubernetesPodOperator(
    task_id='bronze_ingestion',
    name='bronze-pagila',
    # Pre-built runner image
    image='artifactory.company.com/platform/runners/sqlmodel-runner:v1.2.0',
    # Mount the datakit code
    volume_mounts=[
        V1VolumeMount(
            name='datakit-code',
            mount_path='/app/src',
            sub_path='bronze-pagila/src'
        ),
        V1VolumeMount(
            name='krb5-cache',
            mount_path='/var/krb5/cache',
            read_only=True
        )
    ],
    volumes=[
        V1Volume(
            name='datakit-code',
            config_map=V1ConfigMapVolumeSource(
                name='bronze-pagila-code'
            )
        )
    ],
    # Pass configuration
    env_vars={
        'TABLE_NAME': 'film',
        'INGESTION_MODE': 'incremental',
        'BATCH_ID': '{{ ds }}'
    }
)
```

### Local Development

```yaml
# docker-compose.override.yml for local dev
services:
  sqlmodel-runner:
    image: platform/runners/sqlmodel-runner:local
    volumes:
      # Mount local code for hot reload
      - ./datakits/bronze-pagila/src:/app/src:ro
      - ./config:/app/config:ro
    environment:
      - DEV_MODE=true
```

## Benefits

1. **No Build Required**: Developers just write code, no Dockerfile management
2. **Faster Deployment**: Pull pre-built image, mount code, run
3. **Centralized Updates**: Platform team manages dependencies
4. **Security Compliance**: Images pre-scanned and approved
5. **Network Friendly**: Built in environment with proper access

## Migration Path

### Current State (Examples Repo)
```
examples/
├── runners/                    # Temporary location
│   ├── sqlmodel-runner/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── spark-runner/
│       ├── Dockerfile
│       └── requirements.txt
├── datakits/
│   └── bronze-pagila/
│       └── src/                # Just code, no Dockerfile
│           ├── main.py
│           └── models/
```

### Future State (Platform Repo)
```
platform/
├── runtime-images/             # Permanent location
│   ├── sqlmodel-runner/
│   ├── spark-runner/
│   └── dbt-runner/

examples/
├── datakits/                   # Just application code
│   └── bronze-pagila/
│       └── src/
```

## Runner Specifications

### SQLModel Runner (for Bronze Layer)

**Base Requirements**:
- Python 3.11+
- Astronomer base image
- Kerberos client libraries

**Python Packages**:
- sqlmodel-framework (from platform)
- psycopg[binary,pool]
- pandas>=2.0.0
- openpyxl (for Excel support)
- python-dotenv
- pydantic>=2.0.0

**System Packages**:
- postgresql-client
- krb5-user
- libpq-dev

**Environment Variables**:
- `PYTHONPATH=/app/src:/app/lib`
- `KRB5_CONFIG=/etc/krb5.conf`
- `KRB5CCNAME=/var/krb5/cache/ccache`

## Security Considerations

1. **Image Scanning**: All runners scanned for CVEs before deployment
2. **Minimal Surface**: Only required packages installed
3. **Read-Only Mounts**: Code mounted as read-only
4. **Non-Root User**: Runners execute as non-privileged user
5. **Network Policies**: Restricted egress in production

## Developer Experience

### Writing a Datakit

1. **No Dockerfile needed** - Just write Python code
2. **Standard structure** - Follow conventions for mount points
3. **Local testing** - Use docker-compose with mounted code
4. **CI/CD friendly** - No build step, just deploy code

### Example Datakit Structure

```
bronze-pagila/
├── src/
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration
│   └── models/              # Business logic
├── tests/
│   └── test_ingestion.py
└── README.md                # Documentation only
```

No Dockerfile, no requirements.txt, no build complexity!