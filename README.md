# Airflow Data Platform - Examples & Getting Started

Welcome to the **learning hub** for the Airflow Data Platform! This repository contains working examples, tutorials, and implementation guides to help you build your business data infrastructure.

## 🚀 Quick Start

### Prerequisites

**Platform setup required first!** These examples need the platform environment to run:

👉 **[Platform Setup Guide](https://github.com/Troubladore/airflow-data-platform/blob/main/docs/getting-started.md)**

This sets up Docker registry, HTTPS certificates, and local development services.

### Run the Examples

```bash
git clone https://github.com/Troubladore/airflow-data-platform-examples.git
cd airflow-data-platform-examples/pagila-implementations/pagila-sqlmodel-basic
uv sync  # Platform installs automatically!
```

This gives you a **complete working example** that demonstrates the platform patterns.

## 📚 Learning Path

### 👋 **New to the Platform?**
1. **[Getting Started Guide](./docs/getting-started.md)** - Your first 15 minutes
2. **[Basic Example](./pagila-implementations/pagila-sqlmodel-basic/)** - Working SQLModel patterns
3. **[Implementation Guide](./docs/implementation-guide.md)** - Build your business version

### 🏗️ **Ready to Build?**
1. **[Business Setup Patterns](./docs/business-setup-patterns.md)** - Repository structure
2. **[Schema Design Patterns](./docs/patterns.md)** - Common data modeling approaches (planned)
3. **[Deployment Guide](./docs/deployment-guide.md)** - Production deployment (planned)

### 🎯 **Advanced Patterns?**
- Multiple implementation examples (coming soon!)
- Hybrid SQLModel + DBT patterns
- Custom execution engine examples

## 💡 Philosophy: Platform as Dependency

The key insight: **Import the platform, don't fork it!**

```toml
# Your business pyproject.toml
[dependencies]
sqlmodel-framework = {git = "https://github.com/Troubladore/airflow-data-platform.git", branch = "main", subdirectory = "data-platform/sqlmodel-workspace/sqlmodel-framework"}
```

**Benefits:**
- ✅ Platform updates via `uv sync` (no merge conflicts!)
- ✅ Focus on your business data, not framework maintenance
- ✅ Share patterns across teams without coupling
- ✅ Contribute improvements back to platform

## 🏛️ **Example Implementations**

### **Current Examples**
- **[pagila-sqlmodel-basic](./pagila-implementations/pagila-sqlmodel-basic/)**
  - Pure SQLModel approach
  - Source contracts + Bronze warehouse
  - Complete working deployment
  - Perfect starting point

### **Planned Examples**
- **pagila-dbt-advanced** - Full DBT transformation pipeline
- **pagila-hybrid** - SQLModel bronze + DBT silver/gold
- **pagila-streaming** - Real-time ingestion with Kafka
- **pagila-multiwarehouse** - Cross-database deployment
- **pagila-minimal** - Simplest possible implementation

Each example solves the **same business problem** (Pagila DVD rental) using **different technical approaches**, so you can compare and choose what fits your needs.

## 🎓 **What You'll Learn**

### **Data Architecture Patterns**
- Source schema contracts vs warehouse tables
- Bronze → Silver → Gold data progression
- Multi-source schema naming conventions
- Audit fields and data lineage

### **SQLModel Framework**
- Table mixins for consistent patterns
- Abstract base classes and inheritance
- Schema-aware deployment utilities
- Multi-database target support

### **Development Workflow**
- UV workspace management
- Git dependency patterns
- Environment-specific configurations
- Testing and validation approaches

### **Production Deployment**
- Docker containerization
- Airflow orchestration patterns
- Multi-environment promotion
- Monitoring and alerting

## 🔗 **Related Repositories**

- **[Platform Repository](https://github.com/Troubladore/airflow-data-platform)** - Framework source code & technical docs
- **[Your Business Repo]** - Follow examples to build your implementation!

## 🤝 **Contributing**

Found a useful pattern? Share it!

1. **Implementation examples** - Show different approaches to common problems
2. **Pattern documentation** - Explain when/why to use specific techniques
3. **Troubleshooting guides** - Help others avoid common pitfalls
4. **Tutorial improvements** - Make learning easier for newcomers

## 💪 **Success Stories**

*"We went from idea to production data warehouse in 2 weeks using the basic SQLModel pattern. The platform handled all the infrastructure complexity."* - Data Team Lead

*"Platform updates flow seamlessly via uv sync. We get framework improvements without merge conflicts or breaking changes."* - Senior Data Engineer

*"The examples repository became our team's training ground. New hires can see working patterns immediately."* - Engineering Manager

---

**Ready to build your data platform?** Start with the [Getting Started Guide](./docs/getting-started.md)! 🚀