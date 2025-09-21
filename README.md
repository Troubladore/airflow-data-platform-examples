# Airflow Data Platform - Examples

Working examples and implementation guides for the Airflow Data Platform. Contains business implementations using the platform framework as a dependency, demonstrating real-world data engineering patterns.

This repository contains **examples and business implementations**. For the platform framework, see [airflow-data-platform](https://github.com/Troubladore/airflow-data-platform).

## 🏗️ Learning Journeys

### **How to Use the Platform**
1. **[Getting Started Guide](docs/getting-started.md)** - Core concepts and patterns
2. **[Learning Path](docs/learning-path.md)** - Detailed study progression

### **Running the Examples**
1. **[Running the Examples](docs/running-examples.md)** - Complete walkthrough of Pagila examples
   - Install and validate examples
   - Run unit/integration tests
   - Navigate Airflow to see Bronze→Silver→Gold data flows

### **Ready to Build** (3 approaches)
1. **[Fork & Customize](docs/implementation-guide.md)** - Start with examples, adapt for your business
2. **[Green Field Setup](docs/business-setup-patterns.md)** - Build from scratch using platform patterns
3. **[Migration Guide](docs/migration-guide.md)** - Move existing data workflows to platform

## 📖 Documentation

- **[docs/](docs/)** - Complete examples documentation and guides
- **[Getting Started](docs/getting-started.md)** - Platform concepts and first steps
- **[Running the Examples](docs/running-examples.md)** - Install, test, and explore Pagila examples
- **[Learning Path](docs/learning-path.md)** - Detailed study progression
- **[Business Implementation](docs/implementation-guide.md)** - Build your own data platform

## 🏛️ Example Implementations

### **Current Examples**
- **[pagila-sqlmodel-basic](pagila-implementations/pagila-sqlmodel-basic/)** - Complete SQLModel implementation with source contracts and Bronze warehouse

### **Planned Examples**
- **pagila-dbt-advanced** - Full DBT transformation pipeline
- **pagila-hybrid** - SQLModel bronze + DBT silver/gold
- **pagila-streaming** - Real-time ingestion patterns

## 🤝 Contributing

- **Implementation examples** - Share different approaches to common data problems
- **Pattern documentation** - Explain when/why to use specific techniques
- **Tutorial improvements** - Make learning easier for newcomers

See the platform repository [CLAUDE.md](https://github.com/Troubladore/airflow-data-platform/blob/main/CLAUDE.md) for development patterns.

---

**Questions?** Check the [documentation](docs/) or create an issue for support.