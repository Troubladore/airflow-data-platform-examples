# Learning Path - Airflow Data Platform

Detailed study progression for mastering the Airflow Data Platform, from basic concepts to advanced implementation patterns.

## 🎓 What You'll Learn

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

## 📚 Structured Learning Path

### **Beginner (Week 1-2)**
1. **[Getting Started Guide](getting-started.md)** - Core platform concepts
2. **[Running the Examples](running-examples.md)** - Hands-on exploration
3. **[pagila-sqlmodel-basic](../pagila-implementations/pagila-sqlmodel-basic/README.md)** - Study the complete implementation

**Learning Objectives:**
- Understand platform-as-dependency pattern
- Run and validate working examples
- Identify source vs warehouse table patterns
- Execute basic deployment workflows

### **Intermediate (Week 3-4)**
1. **[Implementation Guide](implementation-guide.md)** - Build your first custom datakit
2. **[Business Setup Patterns](business-setup-patterns.md)** - Repository structure best practices
3. **Schema Design Patterns** - Advanced modeling techniques (planned)

**Learning Objectives:**
- Create custom business schemas
- Implement table mixins and audit patterns
- Deploy to multiple database targets
- Understand testing and validation strategies

### **Advanced (Month 2+)**
1. **Production Deployment** - Multi-environment patterns (planned)
2. **Hybrid Architectures** - SQLModel + DBT integration (planned)
3. **Custom Execution Engines** - Advanced orchestration (planned)

**Learning Objectives:**
- Design production-ready data architectures
- Integrate multiple tools and frameworks
- Contribute patterns back to the community
- Mentor other teams in platform adoption

## 🛠️ Hands-On Projects

### **Project 1: Basic Implementation**
- Clone and customize the Pagila example
- Replace DVD rental domain with your business domain
- Deploy to local PostgreSQL environment

### **Project 2: Multi-Source Integration**
- Design schemas for 2-3 different source systems
- Implement Bronze warehouse with audit fields
- Create Silver layer with business rules

### **Project 3: Production Deployment**
- Containerize your implementation
- Set up multi-environment deployment
- Implement monitoring and alerting

## 📖 Additional Resources

### **Platform Deep Dive**
- **[Platform Repository](https://github.com/Troubladore/airflow-data-platform)** - Technical documentation
- **[CLAUDE.md](https://github.com/Troubladore/airflow-data-platform/blob/main/CLAUDE.md)** - Development patterns and workflows

### **Community Learning**
- **GitHub Issues** - Real-world problem solving
- **Example Implementations** - Multiple approaches to common challenges
- **Pattern Library** - Reusable solutions and best practices

---

**Ready to start learning?** Begin with the **[Getting Started Guide](getting-started.md)**!