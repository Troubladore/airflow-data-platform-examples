# Bronze Network Tests

## 📦 What's Inside

**This is now a reference implementation using sqlmodel-framework base classes.**

- **Framework Usage Examples** - Shows how to extend `PostgresConnector` and `BronzeIngestionPipeline`
- **Network Validation** - Proves connectivity patterns work
- **Configuration Examples** - Docker, Kerberos, networking setup
- **Diagnostic Tool** - Validates your environment setup

### Key Files
- `CONFIGURATION_REFERENCE.md` - ⭐ Connection patterns (now framework-based)
- `datakits/postgres_bronze_kerberos/src/extract.py` - Framework extension example with Kerberos
- `datakits/postgres_bronze_local/src/extract.py` - Local connectivity example
- `docker-compose.yml` - Full test orchestration

## 🎯 For Production Use

**Don't copy this code directly.** This is a diagnostic/validation tool.

Instead:
1. Install framework: `pip install git+https://github.com/Troubladore/airflow-data-platform.git@main#subdirectory=sqlmodel-framework`
2. Extend base classes: `from sqlmodel_framework.base.connectors import PostgresConnector`
3. Follow patterns shown here but use framework imports

## 🚀 Quick Start

### Using the Framework

```python
from sqlmodel_framework.base.connectors import PostgresConnector, PostgresConfig
from sqlmodel_framework.base.loaders import BronzeIngestionPipeline

# Configure connection
config = PostgresConfig(
    host='your-postgres-host',
    database='your-database',
    use_kerberos=True  # or False for local
)

# Create connector
connector = PostgresConnector(config)

# Extend the pipeline
class YourExtractor(BronzeIngestionPipeline):
    def extract_data(self):
        with self.connector.connection_context() as conn:
            # Your extraction logic
            pass
```

### Running Tests

```bash
# Install dependencies
uv venv
source .venv/bin/activate
uv pip install -e .[dev]
uv pip install -e ../airflow-data-platform/sqlmodel-framework

# Run unit tests
pytest datakits/*/tests/

# Run integration tests with Docker
docker-compose up test-kerberos test-local
```

## 📂 Project Structure

```
bronze-network-tests/
├── datakits/
│   ├── postgres_bronze_kerberos/    # Kerberos authentication example
│   │   ├── src/
│   │   │   └── extract.py          # Framework-based extractor
│   │   ├── tests/
│   │   │   └── test_framework_extractor.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── postgres_bronze_local/       # Local development example
│       ├── src/
│       │   └── extract.py          # Framework-based extractor
│       ├── tests/
│       │   └── test_framework_extractor.py
│       ├── Dockerfile
│       └── requirements.txt
│
├── docker-compose.yml               # Test orchestration
├── pyproject.toml                   # Project configuration
├── CONFIGURATION_REFERENCE.md       # Detailed configuration guide
└── README.md                        # This file
```

## 🔧 Framework Benefits

### Before (Custom Implementation)
- 180+ lines of connection code per datakit
- Manual Kerberos username extraction
- Custom Bronze metadata handling
- Error-prone subprocess calls
- Inconsistent patterns across datakits

### After (Framework-Based)
- ~50 lines using framework classes
- Automatic Kerberos handling
- Standardized Bronze metadata
- Tested, reliable connection management
- Consistent patterns across all datakits

## 📊 Test Coverage

All extractors have comprehensive test coverage:
- ✅ Framework inheritance verification
- ✅ Connection handling with/without Kerberos
- ✅ Bronze metadata addition
- ✅ Context manager usage
- ✅ Environment-specific configurations

## 🔍 Troubleshooting

### Common Issues

1. **Framework Import Error**
   ```bash
   pip install git+https://github.com/Troubladore/airflow-data-platform.git@main#subdirectory=sqlmodel-framework
   ```

2. **Kerberos Authentication**
   - Ensure KRB5_CONFIG is set
   - Check keytab permissions
   - Verify ticket with `klist`

3. **Docker Build Issues**
   - Ensure Docker daemon is running
   - Check network connectivity for git clone

## 📚 Documentation

- [Configuration Reference](CONFIGURATION_REFERENCE.md) - Detailed setup guide
- [Framework Documentation](https://github.com/Troubladore/airflow-data-platform/tree/main/sqlmodel-framework) - Framework source and docs
- [Issue #141](https://github.com/Troubladore/airflow-data-platform/issues/141) - Framework implementation
- [Issue #12](https://github.com/Troubladore/airflow-data-platform-examples/issues/12) - Refactoring tracker

## 🤝 Contributing

This repo demonstrates framework usage patterns. To contribute:
1. Follow TDD practices (test first, then implement)
2. Use framework base classes
3. Maintain test coverage
4. Update documentation

## 📄 License

MIT

## 🙏 Acknowledgments

Built on top of the sqlmodel-framework from the airflow-data-platform project.