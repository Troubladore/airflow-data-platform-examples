# Airflow Data Platform - Examples

Business implementations and learning examples for the Airflow Data Platform.

This repository contains **examples** showing how to use the platform. For the platform framework itself, see [airflow-data-platform](https://github.com/Troubladore/airflow-data-platform).

## 🚀 Start Here - Hello World Examples

### **New to the Platform?**
Start with these simple examples in order:

1. **[hello-world/](hello-world/)** - Basic Astronomer project with platform patterns
   - Minimal setup
   - Shows platform integration
   - 5 minutes to running

2. **[hello-kerberos/](hello-kerberos/)** - SQL Server with Windows Authentication
   - Kerberos ticket sharing
   - Secure database connections
   - No passwords in code

## 📚 Learning Path

### **Step 1: Platform Setup**
First, set up the platform services:
```bash
# Clone and start platform services
git clone https://github.com/Troubladore/airflow-data-platform.git
cd airflow-data-platform/platform-bootstrap
make start
```
See [Platform Setup Guide](https://github.com/Troubladore/airflow-data-platform/blob/main/docs/getting-started-simple.md)

### **Step 2: Try Hello World**
```bash
# Clone examples
git clone https://github.com/Troubladore/airflow-data-platform-examples.git
cd airflow-data-platform-examples/hello-world

# Follow the README there
```

### **Step 3: Explore Real Examples**
- **[pagila-implementations/](pagila-implementations/)** - Complete data pipeline examples
- **[datakits-sqlserver/](datakits-sqlserver/)** - Production SQL Server patterns

## 🏗️ Repository Structure

```
airflow-data-platform-examples/
├── hello-world/                # Simplest possible example
├── hello-kerberos/            # Kerberos authentication example
├── pagila-implementations/     # Complete pipeline examples
│   └── pagila-sqlmodel-basic/ # SQLModel implementation
├── datakits-sqlserver/        # SQL Server production patterns
│   ├── datakit_sqlserver_bronze_kerberos/
│   └── datakit_sqlserver_silver/
└── docs/                      # Detailed documentation
```

## 📖 Documentation

### **Getting Started**
- [Platform Setup](https://github.com/Troubladore/airflow-data-platform/blob/main/docs/getting-started-simple.md) - Set up platform services
- [Hello World](hello-world/) - Your first project
- [Hello Kerberos](hello-kerberos/) - SQL Server authentication

### **Deep Dives**
- [Running the Examples](docs/running-examples.md) - Complete walkthrough
- [Learning Path](docs/learning-path.md) - Structured learning progression
- [Implementation Guide](docs/implementation-guide.md) - Build your own

### **Patterns & Architecture**
- [SQLModel Patterns](https://github.com/Troubladore/airflow-data-platform/blob/main/docs/patterns/sqlmodel-patterns.md)
- [Runtime Patterns](https://github.com/Troubladore/airflow-data-platform/blob/main/docs/patterns/runtime-patterns.md)
- [Business Setup Patterns](docs/business-setup-patterns.md)

## 🎯 Which Example Should I Use?

| If you want to... | Start with... |
|-------------------|---------------|
| See if it works | [hello-world/](hello-world/) |
| Connect to SQL Server | [hello-kerberos/](hello-kerberos/) |
| Build a data pipeline | [pagila-sqlmodel-basic/](pagila-implementations/pagila-sqlmodel-basic/) |
| Production SQL Server | [datakits-sqlserver/](datakits-sqlserver/) |

## 🤝 Contributing

We welcome contributions! Especially:
- **New examples** - Different databases, cloud providers, etc.
- **Pattern documentation** - When/why to use specific approaches
- **Tutorial improvements** - Make it easier for newcomers

## 🔧 Prerequisites

All examples assume you have:
1. Docker Desktop installed
2. Python 3.8+ available
3. Platform services running (see setup guide)

For SQL Server examples, you'll also need:
- WSL2 (Windows users)
- Kerberos configuration
- Access to a SQL Server instance

---

**Questions?** Start with [hello-world/](hello-world/) or create an issue for help.