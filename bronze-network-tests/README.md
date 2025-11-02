# Bronze Network Tests

**Quick Start**: Research spike to validate network connectivity patterns for Bronze Layer datakits in containerized environments.

## 🎯 What & Why

**What**: Prototype Bronze datakits that test connectivity to Pagila databases (local and remote) with various authentication methods including Kerberos.

**Why**: Before building production Bronze Layer DAGs, we need to prove that containerized Airflow can connect to all required data sources with proper authentication.

## 📚 Test Coverage

| Pattern | Target | Authentication | Status |
|---------|--------|---------------|--------|
| Remote Postgres | sqlpg.eruditis.lab | Kerberos/GSSAPI | 🔄 Testing |
| Local Postgres | host.docker.internal | Standard auth | 🔄 Testing |
| Container-to-Container | postgres:5432 | Standard auth | 🔄 Testing |
| Kerberos Mounting | N/A | Ticket cache | 🔄 Testing |

## 🚀 Quick Test

```bash
# Run all network pattern tests
docker-compose up --build

# Test specific pattern
docker-compose run kerberos-test
docker-compose run local-test
```

## 📦 Structure

- `datakits/postgres_bronze_kerberos/` - Remote Pagila with Kerberos auth
- `datakits/postgres_bronze_local/` - Local Pagila connections
- `scripts/` - Helper scripts for setup and validation
- `tests/` - Automated connectivity tests
- `data/bronze/` - Output directory for extracted data

## 🔍 Test Results

See [docs/test-results.md](docs/test-results.md) for detailed findings from each connectivity pattern test.

## ⚡ Key Findings

- **Kerberos in Containers**: [Status pending]
- **Host Networking**: [Status pending]
- **Volume Mounting**: [Status pending]
- **Credential Caching**: [Status pending]

## 🤝 Next Steps

Once patterns are validated:
1. Refine prototypes into production datakits
2. Create Airflow DAG templates
3. Document standard patterns in platform docs
4. Build reusable extraction libraries