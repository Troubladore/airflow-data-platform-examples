# SQLModel Runner

Pre-built Docker image for running Bronze/Silver/Gold layer datakits with all required dependencies.

## Features

- ✅ SQLModel and all temporal table dependencies
- ✅ PostgreSQL and SQL Server drivers
- ✅ Pandas and data processing libraries
- ✅ Kerberos authentication support
- ✅ Optimized image size (~500MB)
- ✅ Code mounted at runtime (not baked in)

## Image Details

- **Tag**: `platform/runners/sqlmodel-runner:v1.0.0`
- **Base**: Python 3.11 slim
- **Size**: ~503MB
- **Build**: Multi-stage for optimization

## Usage

### Building the Image

```bash
cd runners/sqlmodel-runner
docker build -t platform/runners/sqlmodel-runner:v1.0.0 .
```

### Running with Mounted Code

```bash
# Run with datakit code mounted at /app/src
docker run --rm \
  -v $(pwd)/my-datakit:/app/src \
  platform/runners/sqlmodel-runner:v1.0.0
```

### In Kubernetes/Airflow

```python
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from kubernetes.client import models as k8s

task = KubernetesPodOperator(
    task_id='bronze_ingestion',
    image='platform/runners/sqlmodel-runner:v1.0.0',
    volume_mounts=[
        k8s.V1VolumeMount(
            name='datakit-code',
            mount_path='/app/src',
            sub_path='bronze-pagila/src'
        )
    ],
    env_vars={
        'TABLE_NAME': 'actor',
        'MODE': 'incremental',
        'DATABASE_URL': 'postgresql://...'
    }
)
```

## Pre-installed Packages

### Core Framework
- sqlmodel
- pydantic (>= 2.0.0)
- pydantic-settings

### Database Drivers
- psycopg[binary,pool] (>= 3.1.0)
- pymssql (>= 2.2.0)

### Data Processing
- pandas (>= 2.0.0)
- numpy (>= 1.24.0)
- openpyxl

### Utilities
- python-dotenv
- typer (CLI framework)
- rich (Pretty output)
- tenacity (Retry logic)
- alembic (Migrations)
- structlog (Logging)
- prometheus-client (Metrics)

## Environment Variables

The following environment variables are pre-configured:

- `PYTHONPATH=/app/src:/app/lib` - Code and library paths
- `KRB5_CONFIG=/etc/krb5.conf` - Kerberos config location
- `KRB5CCNAME=/var/krb5/cache/ccache` - Kerberos ticket cache

## Mount Points

The image creates these directories for mounting:

- `/app/src` - Primary code mount point
- `/app/config` - Configuration files
- `/app/lib` - Shared libraries
- `/var/krb5/cache` - Kerberos ticket cache

## Kerberos Support

The image includes Kerberos libraries and a basic `/etc/krb5.conf`. In production, mount your actual krb5.conf:

```bash
docker run --rm \
  -v /etc/krb5.conf:/etc/krb5.conf:ro \
  -v /tmp/krb5cc_1000:/var/krb5/cache/ccache:ro \
  platform/runners/sqlmodel-runner:v1.0.0
```

## Testing

Run the test suite to verify all dependencies:

```bash
# Test imports
docker run --rm \
  --entrypoint /bin/sh \
  -v $(pwd):/app/test \
  platform/runners/sqlmodel-runner:v1.0.0 \
  -c "python /app/test/test_imports.py"

# Test integration
docker run --rm \
  --entrypoint /bin/sh \
  -v $(pwd):/app/test \
  -e DATABASE_URL="postgresql://..." \
  platform/runners/sqlmodel-runner:v1.0.0 \
  -c "python /app/test/test_runner_integration.py"
```

## Development

The Dockerfile uses multi-stage builds to minimize size:

1. **Builder stage**: Installs build dependencies and compiles Python packages
2. **Runtime stage**: Contains only runtime dependencies

This reduces the image from ~985MB to ~503MB.

## Notes

- The image defaults to running `/app/src/main.py`
- Override with custom ENTRYPOINT/CMD as needed
- All packages are installed in a virtual environment at `/opt/venv`
- The image runs as root (production should use non-root user)