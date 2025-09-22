# Mono-Repo Implementation Guide

**Connecting ecosystem theory to actual code organization**

This guide bridges the [Ecosystem Overview](ECOSYSTEM-OVERVIEW.md) concepts with the real directory structure in this repository. Each folder serves a specific purpose in our layered architecture.

## Repository Philosophy

This mono-repo contains **everything needed to build a complete data platform locally**, then deploy the same patterns to production. We prefer self-contained, reproducible environments over external dependencies.

```
🏗️  Build locally → 🧪 Test locally → 🚀 Deploy confidently
```

## Directory Structure Mapped to Ecosystem

### 🎯 **Core Implementation** (Active Development)

#### `layer1-platform/` - Infrastructure Foundation
**Ecosystem Role**: Layer 1 infrastructure runtime
**What it contains**: Docker Compose definitions for local development
```yaml
# Example: PostgreSQL + Airflow containers
services:
  postgres:
    image: postgres:15
  airflow-webserver:
    image: apache/airflow:2.7.0
```
**Teaching Connection**: This is the "Docker Images + Databases + Airflow" box from ecosystem overview

#### `layer2-datakits/` - Data Object Components
**Ecosystem Role**: Layer 2 reusable data contracts
**What it contains**: SQLModel-based datakits for specific systems
```
layer2-datakits/
├── bronze-pagila/      # SystemA datakit (from ecosystem example)
├── postgres-runner/    # Database operations utilities
├── dbt-runner/        # SQL transformation orchestration
└── sqlserver-runner/   # External system integration
```
**Teaching Connection**: These are the "Schema Models + Transform Functions + Typed Contracts" from ecosystem overview

#### `layer2-dbt-projects/` - SQL Transformations
**Ecosystem Role**: Layer 2 SQL-based transforms (complement to Python datakits)
**What it contains**: DBT projects for Bronze→Silver→Gold
```
layer2-dbt-projects/
├── silver-core/        # Data cleaning (Bronze→Silver)
├── gold-dimensions/    # Dimension tables (Silver→Gold)
└── gold-facts/        # Fact tables (Silver→Gold)
```
**Teaching Connection**: These implement the "Silver Layer: Quality-Assured" and "Gold Layer: Business-Optimized" patterns

#### `layer3-warehouses/` - Orchestration Instances
**Ecosystem Role**: Layer 3 specific warehouse configurations
**What it contains**: Airflow DAGs that combine Layer 2 components
```python
# Example: Using bronze-pagila datakit in orchestration
from datakits.bronze_pagila import Customer
dag = DAG('customer_pipeline')
extract_task = PythonOperator(
    python_callable=extract_customers,
    op_kwargs={'datakit_model': Customer}
)
```
**Teaching Connection**: This is the "DAG Configs + Connections + Schedules" from ecosystem overview

#### `data-platform-framework/` - Foundation Library
**Ecosystem Role**: Common utilities for all datakits
**What it contains**: SQLModel mixins, test factories, deployment tools
```python
# Example: Table mixins from ecosystem overview
class TransactionalTableMixin:
    created_at: datetime
    updated_at: datetime
    systime: datetime  # temporal_exclude=True
```
**Teaching Connection**: This provides the "BulkDataLoader", "TransactionalTableMixin", and type-safe transform foundations

### 🚀 **Working Examples** (Learning & Validation)

#### `layer3-warehouses/dags/` - Working Pipeline Examples
**Ecosystem Role**: Complete A→B→Silver→Gold pipeline demonstration
**What it contains**: Working Pagila pipeline using all layers (`pagila_pipeline.py`)
**Teaching Connection**: This is the "customer_transform" example from ecosystem overview, fully implemented
```
Source: pagila.customer → Bronze: bronze.br_customer → Silver: silver.customer → Gold: gold.dim_customer
```

### 🛠️ **Development Tools** (Supporting Infrastructure)

#### `scripts/` - Automation Commands
**Ecosystem Role**: Developer experience automation
**What it contains**: Build, test, and deployment scripts
```bash
./scripts/build-layer2-components.sh    # Build all datakits
./scripts/test-layer2-components.sh     # Test datakit deployment
./scripts/deploy-layer2-runtime.sh      # Runtime deployment
```
**Teaching Connection**: These automate the "Create datakits → Test locally → Deploy Layer 3" workflow

#### `ansible/` - Environment Provisioning
**Ecosystem Role**: Automated setup of Layer 1 infrastructure
**What it contains**: Playbooks for setting up Docker, databases, networking
**Teaching Connection**: Automates the "Layer 1: Build Once" prerequisite setup

### 📚 **Documentation & Reference** (Knowledge Management)

#### `docs/` - Implementation Guides
**What it contains**: This document, ecosystem overview, learning guides
**Teaching Connection**: Bridges theory (ecosystem concepts) to practice (actual code)

#### `ref/` - Historical Reference & Migration Artifacts
**What it contains**: Previous implementations, migration examples
**Purpose**: Shows evolution from older patterns to current approach

## Implementation Journey: Theory to Practice

### From Ecosystem Example to Real Code

**Ecosystem Overview Said:**
> "Create Datakit for System A - reverse-engineer A's schema into SQLModel classes"

**Mono-repo Implementation:**
```bash
# 1. Create new datakit in layer2-datakits/
cd layer2-datakits/
mkdir my-system-a
cd my-system-a/

# 2. Use data-platform-framework patterns
from data_platform_framework.base.models.table_mixins import TransactionalTableMixin
from sqlmodel import SQLModel, Field

class Customer(TransactionalTableMixin, SQLModel, table=True):
    __tablename__ = "customer"
    id: int = Field(primary_key=True)
    name: str
    email: str
```

**Ecosystem Overview Said:**
> "Layer 3: Use A+D+E datakits in your transfer DAG"

**Mono-repo Implementation:**
```bash
# 1. Create DAG in layer3-warehouses/
cd layer3-warehouses/dags/
# 2. Import your Layer 2 datakits
from datakits.system_a import Customer as SystemACustomer
from datakits.bronze import Customer as BronzeCustomer

# 3. Use data-platform-framework factories
from data_platform_framework.base.loaders.data_factory import BulkDataLoader
```

### Development Workflow

**Step 1: Build Foundation (Layer 1)**
```bash
cd layer1-platform/
docker-compose up -d  # Start PostgreSQL, Airflow locally
```

**Step 2: Create Data Objects (Layer 2)**
```bash
cd layer2-datakits/bronze-pagila/
# Develop your SQLModel classes
# Test with data-platform-framework factories
```

**Step 3: Orchestrate (Layer 3)**
```bash
cd layer3-warehouses/
# Create DAG using your datakits
# Test end-to-end pipeline locally
```

**Step 4: Validate with Examples**
```bash
cd layer3-warehouses/
# Review pagila_pipeline.py for complete Bronze→Silver→Gold example
```

## Consistency Across Documentation

### Language Standards
- **Datakit** = SQLModel-based data contract (Layer 2)
- **Transform function** = Type-safe source→target conversion
- **Factory** = BulkDataLoader + transform logic
- **Mixin** = Reusable table patterns (TransactionalTableMixin, etc.)

### Concept Mapping
| Ecosystem Concept | Implementation Location | Key Files |
|-------------------|------------------------|-----------|
| "Layer 1: Infrastructure" | `layer1-platform/` | `docker-compose.yml` |
| "Layer 2: Data Objects" | `layer2-datakits/`, `data-platform-framework/` | `*.py` SQLModel classes |
| "Layer 3: Warehouse Instances" | `layer3-warehouses/` | `dags/*.py` |
| "A→B Transform" | `data-platform-framework/base/loaders/` | `data_factory.py` |
| "Bronze: Speed-Optimized" | `layer2-datakits/bronze-*/` | No FK constraints |
| "Silver: Quality-Assured" | `layer2-dbt-projects/silver-*/` | With constraints |

## Complete Build & Test Pipeline

### **Step 1: Environment Setup**
```bash
# Start Layer 1 infrastructure (requires Docker)
cd layer1-platform/docker
./start-pagila-db.sh  # Pagila source database on port 15432

# Setup Layer 2 development environment
cd ../../data-workspace
uv sync  # Install all workspace dependencies
```

### **Step 2: Validate Framework Core**
```bash
# Test data-platform-framework with all table mixins
PYTHONPATH="./data-platform-framework/src:$PYTHONPATH" \
uv run -m pytest data-platform-framework/tests/unit/test_table_mixins.py -v

# Expected: All 11 tests pass ✅
```

### **Step 3: Deploy & Test Layer 2 Datakits**
```bash
# Automated testing with PostgreSQL sandbox (recommended)
./scripts/test-with-postgres-sandbox.sh

# Manual testing with specific targets
uv run python data-platform-framework/scripts/deploy_datakit.py \
    ../layer2-datakits/pagila-bronze \
    --target-type postgres --host localhost --port 15444 \
    --database datakit_tests --user test_user --password test_password_123 \
    --validate

# Expected: SQLModel tables deployed to br__pagila__public.* schema ✅
```

### **Step 4: End-to-End Data Pipeline** *(Future)*
```bash
# Transform Pagila source → Bronze warehouse
pagila-bronze transform \
    --source-host localhost --source-port 15432 \
    --target sqlite_memory \
    --batch-id $(date +%Y%m%d_%H%M%S)

# Layer 3 orchestration
cd ../layer3-warehouses
./scripts/run-integration-tests.sh  # Full pipeline validation
```

## Getting Started Journey

**New Developer Path:**
1. **Read**: [Ecosystem Overview](ECOSYSTEM-OVERVIEW.md) for concepts
2. **Build**: Follow complete build pipeline above
3. **Explore**: This guide for where concepts live in code
4. **Extend**: Create your first datakit in `layer2-datakits/`

**System Architect Path:**
1. **Understand**: `ref/docs/philosophy/` for design decisions
2. **Validate**: Run complete build pipeline to see working system
3. **Design**: Plan your datakits using `data-platform-framework/` patterns

## Common Implementation Questions

**Q: Where do I put my SystemA→Bronze transform?**
A: Create `layer2-datakits/system-a/` with SQLModel classes, then use `data-platform-framework.base.loaders.BulkDataLoader` in your Layer 3 DAG.

**Q: How do I test my datakit before using it in Airflow?**
A: Use `data-platform-framework` test factories and run `./scripts/test-layer2-components.sh your-datakit-name`

**Q: Where's the parallel batching from ecosystem overview?**
A: Not implemented yet - tracked in [Issue #7](https://github.com/Troubladore/workstation-setup/issues/7)

**Q: How do I handle the "~15% performance penalty" tradeoff?**
A: Most transforms use SQLModel for safety. For performance-critical paths, drop to raw SQL in your transform functions while keeping the datakit structure.

---

**Next Steps:**
- **New to ecosystem**: Start with [Ecosystem Overview](ECOSYSTEM-OVERVIEW.md)
- **Ready to code**: Follow [Layer 2 Data Processing](../README-LAYER2-DATA-PROCESSING.md)
- **Need full pipeline**: Review [Pagila Pipeline Example](../layer3-warehouses/README.md)
- **Advanced features**: Check [Issue #7](https://github.com/Troubladore/workstation-setup/issues/7) roadmap
