# Bronze Network Tests

**Quick Start**: Diagnostic and validation tool for Bronze Layer network connectivity patterns.

## 🎯 What & Why

**What**: Working prototype Bronze datakits that test and validate connectivity to Postgres databases (local and remote) with various authentication methods including Kerberos/GSSAPI.

**Why**: Use this to:
- **Diagnose** connectivity issues in your environment
- **Validate** your Kerberos/Docker/network configuration
- **Check assumptions** about Bronze Layer architecture
- **Reference** working connection patterns for your own datakits

This is a proven, tested implementation you can use as a reference or diagnostic tool.

## 📚 Validated Patterns

| Pattern | Target | Authentication | Status |
|---------|--------|---------------|--------|
| Remote Postgres | sqlpg.eruditis.lab:5432 | Kerberos/GSSAPI | ✅ Working |
| Container-to-Container | postgres-pagila:5432 | Standard auth | ✅ Working |
| Host Networking | host.docker.internal:5432 | Standard auth | ✅ Pattern Validated |
| Kerberos Ticket Mounting | DIR:/tmp/krb5cc | Credential cache | ✅ Working |

## 🚀 Quick Start

### Run Tests
```bash
cd bronze-network-tests

# Test container-to-container networking
docker-compose run test-local

# Test Kerberos authentication (requires valid ticket)
docker-compose run test-kerberos

# Test host networking (requires host Postgres)
docker-compose run test-host-network
```

### Validate Your Environment
```bash
# Check prerequisites
./scripts/validate_connections.sh

# Setup Kerberos
./scripts/setup_kerberos.sh
```

## 📦 What's Inside

- **`CONFIGURATION_REFERENCE.md`** - ⭐ **START HERE** - All connection strings, configurations, and examples
- **`datakits/postgres_bronze_kerberos/`** - Working Kerberos/GSSAPI implementation
- **`datakits/postgres_bronze_local/`** - Container and host networking examples
- **`docker-compose.yml`** - Full orchestration with all test patterns
- **`scripts/`** - Validation and setup helpers
- **`../docs/setup/NETWORK_PATTERNS.md`** - Detailed test results and findings

## 🔍 Key Findings

All patterns successfully validated:

- ✅ **Kerberos in Containers**: Working with proper credential cache mounting
- ✅ **Username Extraction**: Must extract user from ticket (containers run as root)
- ✅ **Host Networking**: `host.docker.internal` pattern validated
- ✅ **Bronze Metadata**: Automatic addition of load timestamps and source tracking
- ✅ **Multi-format Output**: Parquet and JSON both working

See `CONFIGURATION_REFERENCE.md` for specific connection strings and Python code examples.

## 🎯 Using This for Your Own Datakits

1. Review `CONFIGURATION_REFERENCE.md` for connection patterns
2. Check `datakits/postgres_bronze_kerberos/src/extract.py` for Kerberos implementation
3. Check `datakits/postgres_bronze_local/src/extract.py` for standard auth patterns
4. Copy the Bronze metadata schema for consistency
5. Use `docker-compose.yml` as a template for your own services

## 📖 Full Documentation

- **Design**: `../docs/plans/2025-11-02-bronze-network-patterns-design.md`
- **Results**: `../docs/setup/NETWORK_PATTERNS.md`
- **Configuration**: `CONFIGURATION_REFERENCE.md`