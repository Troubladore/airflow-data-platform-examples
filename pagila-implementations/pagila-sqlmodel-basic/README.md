# Pagila SQLModel Basic Implementation

This is a basic implementation of the Pagila DVD rental database using the SQLModel framework from the Airflow Data Platform.

## Overview

This example demonstrates:
- **Source schema contracts** (`pagila-source`) - Reference schemas matching external Pagila database
- **Bronze warehouse tables** (`pagila-bronze`) - Warehouse ingestion with audit fields
- **Platform dependency** - Uses `sqlmodel-framework` as a pip-installable dependency
- **Business-specific customization** - Shows how to extend platform patterns for your domain

## Architecture

```
pagila-sqlmodel-basic/
├── datakits/
│   ├── pagila-source/          # Source schema contracts (references external DB)
│   └── pagila-bronze/          # Bronze warehouse tables (br__pagila__public schema)
├── orchestration/              # Airflow DAGs (future)
├── config/                     # Environment-specific configs (future)
└── tests/                      # Business-specific tests (future)
```

## Installation

```bash
# Install with platform dependency
uv sync

# Deploy bronze tables to test database
uv run python -m sqlmodel_framework.deployment deploy \
  --datakit ./datakits/pagila-bronze \
  --target-config ./config/test.yml
```

## Usage

This implementation shows the **simplest possible pattern** for using the Airflow Data Platform:

1. **Define source contracts** - Model your external data sources
2. **Create bronze warehouses** - Ingest with audit fields and proper schemas
3. **Deploy via platform** - Use framework utilities for consistent deployment
4. **Extend with business logic** - Add your specific transformations

## Platform Dependency

This example depends on:
```toml
sqlmodel-framework @ git+https://github.com/Troubladore/airflow-data-platform.git@main#subdirectory=data-platform/sqlmodel-workspace/sqlmodel-framework
```

Platform updates are pulled automatically with `uv sync`.

## Next Steps

- See `../pagila-dbt-advanced/` for DBT-based transformations
- See `../pagila-hybrid/` for mixed SQLModel + DBT approach
- Use this as template for your actual business implementation