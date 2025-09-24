# Hello World - Your First Astronomer + Platform Project

A minimal example showing how to create an Astronomer project with our platform enhancements.

## 📋 Prerequisites

1. **Platform services running** (see [platform setup](https://github.com/Troubladore/airflow-data-platform/blob/main/docs/getting-started-simple.md))
2. **Astronomer CLI installed**:
   ```bash
   curl -sSL install.astronomer.io | sudo bash
   ```

## 🚀 Quick Start

```bash
# 1. Initialize Astronomer project
astro dev init

# 2. Add platform framework (optional but recommended)
echo "sqlmodel-framework @ git+https://github.com/Troubladore/airflow-data-platform.git@main#subdirectory=sqlmodel-framework" >> requirements.txt

# 3. Copy our example DAG
cp dags/hello_world_dag.py dags/

# 4. Start Airflow
astro dev start

# 5. Open http://localhost:8080
# Username: admin, Password: admin
```

## 📁 What's Included

### `dags/hello_world_dag.py`
A simple DAG that demonstrates:
- Basic Astronomer project structure
- How to check if SQLModel framework is available
- Simple task creation

### `.astro/` (created by astro dev init)
Astronomer configuration - you don't need to modify this

### `requirements.txt`
Python dependencies including our SQLModel framework

## 🎯 Try It Out

1. Open Airflow UI at http://localhost:8080
2. Find `hello_world_platform` DAG
3. Toggle it on and trigger a run
4. Check the logs to see the output

## 🔧 Next Steps

### Add SQLModel Tables
Create `dags/models.py`:
```python
from sqlmodel_framework import ReferenceTable
from sqlmodel import Field

class Customer(ReferenceTable, table=True):
    __tablename__ = "customers"

    customer_id: int = Field(primary_key=True)
    name: str
    email: str
    # Auto-includes: created_at, updated_at, audit columns
```

### Use in Your DAG
```python
from models import Customer
from sqlmodel_framework import deploy_data_objects

def setup_tables():
    deploy_data_objects([Customer], target="sqlite_memory")
```

## 🚀 What's Next?

- Try [hello-kerberos](../hello-kerberos/) for SQL Server authentication
- Explore [datakits-sqlserver](../datakits-sqlserver/) for real data processing
- Read about [SQLModel patterns](https://github.com/Troubladore/airflow-data-platform/blob/main/docs/patterns/sqlmodel-patterns.md)

## 🛑 Cleanup

```bash
# Stop Airflow
astro dev stop

# Remove project (optional)
cd ..
rm -rf hello-world
```