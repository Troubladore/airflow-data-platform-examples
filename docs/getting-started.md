# Getting Started with Airflow Data Platform

Welcome! This guide will walk you through using the Airflow Data Platform to build your business data infrastructure.

## Prerequisites

**Complete platform setup first!** Examples require the platform environment:

👉 **[Platform Setup Guide](https://github.com/Troubladore/airflow-data-platform/blob/main/docs/getting-started.md)**

This installs Docker registry, Traefik proxy, HTTPS certificates, and local development services.

## 🎯 Quick Start

The fastest way to understand the platform is to explore our working examples and then build your own implementation.

### Step 1: Install the Basic Example

```bash
git clone https://github.com/Troubladore/airflow-data-platform-examples.git
cd airflow-data-platform-examples

# Install the basic example (downloads platform framework from GitHub)
cd pagila-implementations/pagila-sqlmodel-basic
uv sync  # Installs platform + dependencies automatically
```

This example shows:
- **Source schema contracts** - How to model external data sources
- **Bronze warehouse tables** - How to ingest with audit fields
- **Platform dependency** - How to import framework utilities
- **Business customization** - How to extend for your domain

### Step 2: Validate the Integration

Test that the platform + examples work together:

```bash
# Run integration tests to verify everything works
# (Return to repository root from the pagila-sqlmodel-basic directory)
cd ../..
./scripts/test-examples-integration.sh
```

This validates:
- **Platform framework** can deploy business schemas
- **PostgreSQL compatibility** with all table types
- **Complete schema creation** including foreign keys
- **End-to-end workflow** from source models to warehouse

### Step 3: Understand the Pattern

The platform follows a **dependency pattern**:
- **Your business repo** imports the platform as a UV dependency
- **Platform updates** flow via `uv sync` (no merge conflicts!)
- **You customize** schemas, orchestration, and configs for your business

```toml
# Your business pyproject.toml
[dependencies]
sqlmodel-framework = {git = "https://github.com/Troubladore/airflow-data-platform.git", branch = "main", subdirectory = "data-platform/sqlmodel-workspace/sqlmodel-framework"}
```

### Step 4: Build Your Implementation

1. **Copy example structure** as your starting point
2. **Replace Pagila schemas** with your business schemas
3. **Customize orchestration** for your data flows
4. **Deploy using platform utilities**

## 📚 Learning Path

### Beginners
- Start with [pagila-sqlmodel-basic](./pagila-implementations/pagila-sqlmodel-basic/)
- Understand table mixins and deployment utilities
- Learn the SQLModel → Bronze → Silver → Gold pattern

### Intermediate
- Explore multiple implementation approaches
- Learn schema design patterns and audit fields
- Understand multi-database deployments

### Advanced
- Build custom execution engines
- Create hybrid SQLModel + DBT pipelines
- Contribute patterns back to examples

## 🏗️ Implementation Structure

Your business data platform should follow this pattern:

```
your-company-data-platform/
├── pyproject.toml                # Platform dependency + your deps
├── company_datakits/            # Your business schemas
│   ├── sales_source/            # External source contracts
│   ├── sales_bronze/            # Warehouse ingestion tables
│   └── sales_silver/            # Quality/business rules
├── company_orchestration/       # Your Airflow DAGs
├── company_config/             # Environment configs
└── deployment/                 # Your infrastructure
```

## 🎓 Core Concepts

### **Schema Contracts**
- **Source datakits** define external system schemas
- **Bronze datakits** define warehouse ingestion with audit
- **Silver datakits** add quality rules and business logic

### **Table Mixins**
- **ReferenceTableMixin** - Lookup tables with inactivation
- **TransactionalTableMixin** - Audit fields and timestamps
- **TemporalTableMixin** - Time-based versioning

### **Deployment Utilities**
- **Schema auto-creation** - Platform creates PostgreSQL schemas
- **Multi-database support** - Deploy to different targets
- **Validation testing** - Automated deployment verification

## 🚀 Next Steps

1. **Try the basic example** - Get familiar with platform patterns
2. **Read implementation guides** - Learn business customization
3. **Build your version** - Apply patterns to your business data
4. **Join the community** - Share patterns and get help

## 📖 Additional Resources

- **[Platform Repository](https://github.com/Troubladore/airflow-data-platform)** - Technical documentation
- **[Implementation Guide](./implementation-guide.md)** - Step-by-step business setup
- **[Pattern Library](./business-setup-patterns.md)** - Common data platform patterns
- **[Troubleshooting](./troubleshooting.md)** - Common issues and solutions

Remember: The platform provides the foundation, you provide the business value! 🎯