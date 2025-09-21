# Airflow Data Platform - Examples

This repository contains example implementations using the [Airflow Data Platform](https://github.com/Troubladore/airflow-data-platform).

## 🎯 Purpose

These examples show **real-world implementation patterns** for businesses using the platform. Each example demonstrates different approaches to the same underlying data (Pagila DVD rental database), so you can compare techniques and choose what fits your needs.

## 🏗️ Implementation Varieties

### **Current Examples**

- **[pagila-sqlmodel-basic](./pagila-implementations/pagila-sqlmodel-basic/)** - Simplest SQLModel approach
  - Pure SQLModel framework usage
  - Source contracts + Bronze warehouse
  - Platform dependency via git+https
  - Perfect starting point for new implementations

### **Planned Examples**

- **pagila-dbt-advanced** - Full DBT transformation pipeline
- **pagila-hybrid** - SQLModel bronze + DBT silver/gold
- **pagila-streaming** - Real-time ingestion patterns
- **pagila-multiwarehouse** - Cross-database deployments

## 🚀 Getting Started

1. **Clone this repo**:
   ```bash
   git clone https://github.com/Troubladore/airflow-data-platform-examples.git
   cd airflow-data-platform-examples
   ```

2. **Try the basic example**:
   ```bash
   cd pagila-implementations/pagila-sqlmodel-basic
   uv sync  # Installs platform + dependencies
   ```

3. **Use as template for your business**:
   - Copy the structure that matches your needs
   - Replace Pagila schemas with your business schemas
   - Customize orchestration and deployment configs

## 🎓 Learning Path

1. **Start with `pagila-sqlmodel-basic`** - Understand core patterns
2. **Explore other implementations** - See different approaches
3. **Build your business version** - Use examples as templates
4. **Contribute back** - Share interesting patterns!

## 🔗 Platform Documentation

- **Platform Repository**: [airflow-data-platform](https://github.com/Troubladore/airflow-data-platform)
- **Framework Documentation**: See platform repo docs/
- **Installation Guide**: Each example includes setup instructions

## 💡 Philosophy

These examples mirror **exactly how a business should structure** their data platform implementation:

- **Platform as dependency** - No forking, just import and extend
- **Business-specific customization** - Your schemas, your orchestration
- **Template-driven development** - Start from patterns, not scratch
- **Continuous platform updates** - `uv sync` pulls latest improvements

Each example is a **complete, runnable implementation** that demonstrates real-world usage patterns.