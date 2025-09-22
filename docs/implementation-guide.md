# Business Implementation Guide

This guide walks you through implementing the Airflow Data Platform for your actual business data.

## 🎯 From Example to Business Implementation

### Phase 1: Setup Your Repository

1. **Create your business data repository**:
   ```bash
   mkdir your-company-data-platform
   cd your-company-data-platform
   git init
   ```

2. **Copy the basic structure**:
   ```bash
   # Copy from pagila-sqlmodel-basic as template
   cp -r ../airflow-data-platform-examples/pagila-implementations/pagila-sqlmodel-basic/* .

   # Update pyproject.toml with your project name
   sed -i 's/pagila-sqlmodel-basic/your-company-data-platform/' pyproject.toml
   ```

3. **Initialize UV workspace**:
   ```bash
   uv sync  # This installs the platform framework automatically
   ```

### Phase 2: Replace Example Schemas

#### Replace Source Schemas
```bash
# Remove Pagila examples
rm -rf datakits/datakit_pagila_source

# Create your business source schemas
mkdir -p datakits/your_company_source/models
```

Example business source datakit:
```python
# datakits/your_company_source/models/customer.py
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class CustomerSource(SQLModel, table=True):
    """Customer data from CRM system."""
    __tablename__ = "customer"
    # No __table_args__ - this is a source reference, not warehouse table

    customer_id: int = Field(primary_key=True)
    email: str = Field(nullable=False)
    first_name: str
    last_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
```

#### Replace Bronze Schemas
```python
# datakits/your_company_bronze/models/customer.py
from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import TransactionalTableMixin
from datetime import datetime

class BronzeCustomer(TransactionalTableMixin, SQLModel, table=True):
    """Customer data ingested to bronze layer."""
    __tablename__ = "customer"
    __table_args__ = {"schema": "br__yourcompany__crm"}  # Your schema pattern

    # Source fields
    customer_id: int = Field(primary_key=True)
    email: str = Field(nullable=False)
    first_name: str
    last_name: str
    source_created_at: datetime
    source_updated_at: Optional[datetime] = None

    # Bronze audit fields come from TransactionalTableMixin:
    # br_load_time, br_batch_id, br_is_current, etc.
```

### Phase 3: Configure Your Databases

#### Update Connection Configs
```yaml
# config/production.yml
target:
  type: postgres
  host: your-production-db.company.com
  port: 5432
  database: your_data_warehouse
  user: data_platform_user
  # No password in config - use environment variables

schemas:
  bronze: "br__yourcompany__crm"
  silver: "sl__yourcompany__crm"
  gold: "gl__yourcompany__metrics"
```

#### Environment Variables
```bash
# .env.production
DATABASE_PASSWORD=your_secure_password
AIRFLOW_CONN_WAREHOUSE=postgresql://user:${DATABASE_PASSWORD}@host:5432/db
```

### Phase 4: Deploy Your Datakits

```bash
# Deploy bronze layer to production
uv run python -c "
from sqlmodel_framework.utils.deployment import deploy_datakit
from pathlib import Path

result = deploy_datakit(
    datakit_path=Path('./datakits/your_company_bronze'),
    target_config={
        'type': 'postgres',
        'host': 'your-warehouse.company.com',
        'database': 'your_warehouse',
        'user': 'data_platform'
    },
    validate=True
)
print(f'Deployed {result[\"tables_deployed\"]} tables')
"
```

### Phase 5: Build Orchestration

#### Simple Airflow DAG
```python
# orchestration/dags/daily_customer_sync.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess

def sync_customer_data():
    \"\"\"Sync customer data from CRM to bronze layer.\"\"\"
    result = subprocess.run([
        "uv", "run", "python", "-m", "your_company_bronze.sync",
        "--source", "crm_production",
        "--target", "warehouse_bronze"
    ], check=True)
    return f"Synced customer data: {result}"

dag = DAG(
    'daily_customer_sync',
    default_args={
        'owner': 'data-platform',
        'retries': 1,
        'retry_delay': timedelta(minutes=5)
    },
    description='Daily customer data synchronization',
    schedule_interval='0 2 * * *',  # 2 AM daily
    start_date=datetime(2024, 1, 1),
    catchup=False
)

sync_task = PythonOperator(
    task_id='sync_customer_data',
    python_callable=sync_customer_data,
    dag=dag
)
```

## 🔧 Common Patterns

### Multi-Source Bronze Pattern
```python
# Different sources = different schemas
__table_args__ = {"schema": "br__salesforce__contacts"}  # Salesforce
__table_args__ = {"schema": "br__hubspot__deals"}        # HubSpot
__table_args__ = {"schema": "br__mysql__orders"}         # Internal DB
```

### Incremental Loading Pattern
```python
class BronzeOrder(TransactionalTableMixin, SQLModel, table=True):
    # Add watermark fields for incremental loading
    source_modified_date: datetime = Field(nullable=False)
    br_extraction_time: datetime = Field(default_factory=datetime.utcnow)

    # Use br_is_current for SCD Type 2
    br_is_current: bool = Field(default=True)
```

### Reference Data Pattern
```python
from sqlmodel_framework.base.models import ReferenceTableMixin

class ProductCategory(ReferenceTableMixin, SQLModel, table=True):
    """Product categories - reference/lookup table."""
    category_id: int = Field(primary_key=True)
    category_name: str
    # inactivated_date, inactivated_by come from ReferenceTableMixin
```

## 🚀 Advanced Topics

### Custom Execution Engines
- Extend platform execution engines for your specific needs
- Build custom data quality checks
- Implement business-specific transformations

### Multi-Environment Deployment
- Use different configs for dev/staging/production
- Implement environment-specific schema naming
- Build promotion pipelines

### Monitoring and Alerting
- Integrate with your monitoring stack
- Build data quality dashboards
- Set up automated failure notifications

## 🆘 Getting Help

- **Platform Issues**: [airflow-data-platform/issues](https://github.com/Troubladore/airflow-data-platform/issues)
- **Implementation Questions**: [airflow-data-platform-examples/discussions](https://github.com/Troubladore/airflow-data-platform-examples/discussions)
- **Pattern Sharing**: Contribute examples back to the community!

Remember: Start simple, then expand. The platform grows with your business needs! 📈