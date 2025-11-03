# Configuration Reference

## 🎯 Using the Framework (RECOMMENDED)

**These examples now use the sqlmodel-framework base classes.**

### Installation
```bash
pip install git+https://github.com/Troubladore/airflow-data-platform.git@main#subdirectory=sqlmodel-framework
```

Or once published to PyPI (after issue #143):
```bash
pip install sqlmodel-framework>=1.0.0
```

### Framework-Based Connection

```python
from sqlmodel_framework.base.connectors import PostgresConnector, PostgresConfig
from sqlmodel_framework.base.loaders import BronzeIngestionPipeline

# Framework handles Kerberos username extraction automatically!
config = PostgresConfig(
    host='sqlpg.eruditis.lab',
    database='pagila',
    use_kerberos=True
)

connector = PostgresConnector(config)  # Done! Framework handles everything

# Extend the framework pipeline
class MyExtractor(BronzeIngestionPipeline):
    def extract_table(self, table_name: str) -> pd.DataFrame:
        with self.connector.connection_context() as conn:
            return pd.read_sql(f"SELECT * FROM {table_name}", conn)
```

### Why Use the Framework?
- ✅ Kerberos username extraction built-in (no manual subprocess calls)
- ✅ Bronze metadata standardized across all datakits
- ✅ Connection context managers prevent leaks
- ✅ Tested and maintained centrally
- ✅ Less code to write and maintain

---

## Framework Components

### PostgresConnector
Handles PostgreSQL connections with optional Kerberos authentication:

```python
from sqlmodel_framework.base.connectors import PostgresConnector, PostgresConfig

# With Kerberos
kerberos_config = PostgresConfig(
    host='sqlpg.eruditis.lab',
    port=5432,
    database='pagila',
    use_kerberos=True,
    gssencmode='require'
)

# Without Kerberos (local development)
local_config = PostgresConfig(
    host='localhost',
    port=5432,
    database='pagila',
    username='postgres',
    password='postgres',
    use_kerberos=False
)

connector = PostgresConnector(config)
```

### BronzeIngestionPipeline
Base class for Bronze layer data ingestion:

```python
from sqlmodel_framework.base.loaders import BronzeIngestionPipeline

class MyDataExtractor(BronzeIngestionPipeline):
    def __init__(self, connector, bronze_path):
        super().__init__(connector, bronze_path)
        self.source_system = 'my_system'

    def extract_table(self, table_name: str):
        with self.connector.connection_context() as conn:
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)

        # Add Bronze metadata automatically
        df = self.add_bronze_metadata(
            df,
            source_system=self.source_system,
            source_table=table_name,
            source_host=self.connector.config.host,
            extraction_method='full_snapshot'
        )

        # Write to Bronze storage
        paths = self.write_bronze(
            df,
            source_system=self.source_system,
            table_name=table_name,
            formats=['parquet', 'json']
        )

        return paths
```

### Bronze Metadata
The framework automatically adds Bronze layer metadata columns:
- `bronze_ingestion_timestamp`: When data was ingested
- `bronze_source_system`: Source system identifier
- `bronze_source_table`: Original table name
- `bronze_source_host`: Source host/server
- `bronze_extraction_method`: How data was extracted (full/incremental)
- `bronze_record_hash`: Hash for deduplication
- `bronze_batch_id`: Batch identifier for this extraction

---

## Docker Configuration

### Using Framework in Docker

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    krb5-user \
    libkrb5-dev \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install framework
RUN pip install git+https://github.com/Troubladore/airflow-data-platform.git@main#subdirectory=sqlmodel-framework

# Your application dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "your_extractor.py"]
```

### Docker Compose Example

```yaml
version: '3.8'

services:
  extractor:
    build: .
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_DB: pagila
      KRB5_CONFIG: /etc/krb5.conf
    volumes:
      - ./krb5.conf:/etc/krb5.conf:ro
      - bronze-data:/data/bronze
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: pagila
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres

volumes:
  bronze-data:
```

---

## Environment Variables

The framework respects these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL host | Required |
| `POSTGRES_PORT` | PostgreSQL port | 5432 |
| `POSTGRES_DB` | Database name | Required |
| `POSTGRES_USER` | Username (non-Kerberos) | None |
| `POSTGRES_PASSWORD` | Password (non-Kerberos) | None |
| `KRB5_CONFIG` | Kerberos config path | /etc/krb5.conf |
| `KRB5_CLIENT_KTNAME` | Keytab file path | None |

---

## Migration from Custom Code

### Before (Custom Implementation)
```python
# 180+ lines of custom connection handling
class PostgresBronzeExtractor:
    def __init__(self):
        # Manual Kerberos handling
        # Custom connection logic
        # Error-prone subprocess calls
        ...

    def get_connection(self):
        # Complex connection management
        ...
```

### After (Framework-Based)
```python
# ~50 lines using framework
from sqlmodel_framework.base.connectors import PostgresConnector
from sqlmodel_framework.base.loaders import BronzeIngestionPipeline

class MyExtractor(BronzeIngestionPipeline):
    # Just implement your business logic!
    pass
```

---

## Testing

### Unit Testing with Framework

```python
import pytest
from unittest.mock import Mock
from sqlmodel_framework.base.connectors import PostgresConnector
from your_module import YourExtractor

def test_extraction():
    # Mock the connector
    mock_connector = Mock(spec=PostgresConnector)

    # Create extractor
    extractor = YourExtractor(
        connector=mock_connector,
        bronze_path=Path('/tmp/bronze')
    )

    # Test your logic
    result = extractor.extract_table('test_table')
    assert result['success'] is True
```

### Integration Testing

```bash
# Run tests with Docker Compose
docker-compose run test-extractor pytest tests/
```

---

## Troubleshooting

### Common Issues

1. **Import Error**: `ModuleNotFoundError: No module named 'sqlmodel_framework'`
   - Solution: Install framework: `pip install git+https://github.com/Troubladore/airflow-data-platform.git@main#subdirectory=sqlmodel-framework`

2. **Kerberos Authentication Failed**
   - Check KRB5_CONFIG environment variable
   - Verify keytab file permissions
   - Run `klist` to check ticket status

3. **Connection Timeout**
   - Verify network connectivity
   - Check firewall rules
   - Ensure PostgreSQL is accepting connections

---

## Additional Resources

- [Framework Source Code](https://github.com/Troubladore/airflow-data-platform/tree/main/sqlmodel-framework)
- [Issue #141: Framework Base Classes](https://github.com/Troubladore/airflow-data-platform/issues/141)
- [Issue #142: Framework Documentation](https://github.com/Troubladore/airflow-data-platform/issues/142)
- [Issue #143: PyPI Publishing](https://github.com/Troubladore/airflow-data-platform/issues/143)