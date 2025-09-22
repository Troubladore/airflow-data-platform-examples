# Running the Examples - Complete Walkthrough

This guide walks you through installing, testing, and exploring all the Pagila examples to understand how the platform works in practice. You'll run unit/integration tests and navigate the Airflow container to see Bronze→Silver→Gold data flows in action.

## Prerequisites

**Platform setup required first!** Complete the platform environment setup:

👉 **[Platform Setup Guide](https://github.com/Troubladore/airflow-data-platform/blob/main/docs/getting-started.md)**

This installs Docker registry, Traefik proxy, HTTPS certificates, and local development services.

## 🚀 Quick Setup

### Step 1: Clone and Enter Examples Repository

```bash
git clone https://github.com/Troubladore/airflow-data-platform-examples.git
cd airflow-data-platform-examples
```

### Step 2: Validate Integration

Run the integration tests to ensure platform + examples work together:

```bash
./scripts/test-examples-integration.sh
```

**What this validates:**
- Platform framework can deploy business schemas
- PostgreSQL compatibility with all table types
- Complete schema creation including foreign keys
- End-to-end workflow from source models to warehouse

Expected output:
```
✅ Successfully deployed 12 tables
✅ All 12 tables validated
🎉 Datakit deployment completed successfully!
```

## 📋 Pagila SQLModel Basic Example

### Step 3: Install the Basic Example

```bash
cd pagila-implementations/pagila-sqlmodel-basic
uv sync  # Platform installs automatically as Git dependency!
```

**What happens:**
- Downloads platform framework from GitHub
- Installs all Python dependencies
- Creates isolated environment for this example

### Step 4: Explore the Example Structure

```bash
# View the complete example structure
find . -name "*.py" | head -20
```

**Key directories:**
- `datakits/datakit_pagila_source/` - Source database contracts (12 tables)
- `datakits/datakit_pagila_bronze/` - Warehouse ingestion tables (planned)
- `datakits/datakit_pagila_silver/` - Business logic layer (planned)

### Step 5: Examine Source Schema Contracts

```bash
# Look at the customer table definition
cat datakits/datakit_pagila_source/models/customer.py
```

**Key patterns to notice:**
- SQLModel table definitions with proper typing
- Foreign key relationships between tables
- Server defaults and nullable field handling
- Schema specification: `{"schema": "public"}`

### Step 6: Test Schema Deployment

Deploy the Pagila source schema to test database:

```bash
# Test deployment to SQLite (fast)
PYTHONPATH="./src:$PYTHONPATH" uv run python scripts/deploy_datakit.py datakits/datakit_pagila_source --target sqlite_memory --validate

# Test deployment to PostgreSQL (full validation)
PYTHONPATH="./src:$PYTHONPATH" uv run python scripts/deploy_datakit.py datakits/datakit_pagila_source --target postgres_local --validate
```

**What this demonstrates:**
- Platform discovers all 12 SQLModel table classes automatically
- Creates PostgreSQL schemas and tables
- Validates foreign key relationships
- Reports successful deployment

## 🧪 Testing and Validation

### Step 7: Run Unit Tests (if available)

```bash
# Check for unit tests in the example
find . -name "*test*.py" -o -name "test_*" -type d
```

*Note: Unit tests are planned for future implementation. Currently using integration tests.*

### Step 8: Run Integration Tests

```bash
# Return to repository root
cd ../..

# Run full integration test suite
./scripts/test-examples-integration.sh
```

**Integration test workflow:**
1. Bootstraps fresh PostgreSQL container
2. Installs example dependencies
3. Deploys Pagila schema (12 tables)
4. Validates all table creation and relationships
5. Cleans up test environment

### Step 9: Validate Platform Framework Tests

```bash
# Switch to platform repository
cd /path/to/airflow-data-platform  # Adjust path as needed

# Run all framework unit tests
./scripts/test-with-postgres-sandbox.sh
```

Expected results:
- ✅ 11/11 table mixin tests pass
- ✅ 11/11 trigger builder tests pass
- ✅ Framework deployment validation passes

## 🏗️ Understanding the Data Architecture

### Step 10: Analyze the Table Relationships

```bash
cd airflow-data-platform-examples/pagila-implementations/pagila-sqlmodel-basic

# View all model imports to see relationship structure
cat datakits/datakit_pagila_source/models/__init__.py
```

**Pagila Database Relationships:**
```
Country → City → Address → Customer
                        → Store → Staff
                               → Inventory → Rental
Category → Film → Inventory
Language → Film
Actor ↔ Film (many-to-many, not yet implemented)
```

### Step 11: Examine Platform Patterns

Look for these key platform patterns in the source code:

**1. Table Mixins (future enhancement):**
```python
# Will be applied to Bronze/Silver tables
class TransactionalTableMixin(SQLModel):
    systime: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

**2. Platform Dependency:**
```toml
# In pyproject.toml
dependencies = [
    "sqlmodel-framework @ git+https://github.com/Troubladore/airflow-data-platform.git@main#subdirectory=data-platform/sqlmodel-workspace/sqlmodel-framework"
]
```

**3. Multi-Target Deployment:**
```python
# Platform supports multiple database targets
deploy_data_objects(table_classes, target_config)
```

## 🐳 Airflow Container Exploration (Future)

*Note: Full Airflow orchestration is planned for future implementation. Current examples focus on schema deployment and validation.*

### When Available: Navigate Running Airflow

**1. Access Airflow Web UI:**
```bash
# Airflow will be available at:
open https://airflow.local.troubladore.dev
```

**2. Explore Data Pipeline DAGs:**
- `pagila_bronze_ingestion` - Source → Bronze warehouse
- `pagila_silver_transformation` - Bronze → Silver (business rules)
- `pagila_gold_aggregation` - Silver → Gold (analytics)

**3. Monitor Data Flows:**
- View task execution logs
- Inspect data lineage graphs
- Monitor pipeline success/failure rates

## 🎯 What You've Accomplished

After completing this walkthrough, you've:

✅ **Installed and validated** the complete examples repository
✅ **Explored working code** showing platform patterns in practice
✅ **Deployed schemas** to multiple database targets
✅ **Run integration tests** validating platform + examples
✅ **Understood relationships** between 12 Pagila database tables
✅ **Seen deployment utilities** in action with real schemas

## 🚀 Next Steps

### **Ready to Build Your Own?**
1. **[Fork & Customize Guide](implementation-guide.md)** - Adapt Pagila for your business
2. **[Green Field Setup](business-setup-patterns.md)** - Build from scratch
3. **[Migration Guide](migration-guide.md)** - Move existing data workflows

### **Want to Learn More?**
1. **[Learning Path](learning-path.md)** - Structured study progression
2. **[Platform Technical Docs](https://github.com/Troubladore/airflow-data-platform/blob/main/docs/)** - Framework deep dive
3. **[Community Examples](../pagila-implementations/)** - Multiple implementation approaches

---

**Questions or Issues?** Create an issue in the [examples repository](https://github.com/Troubladore/airflow-data-platform-examples/issues) for support!