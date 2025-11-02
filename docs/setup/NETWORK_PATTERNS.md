# Bronze Layer Network Patterns

**Date:** 2025-11-02
**Issue:** #12 - Environment Setup & Network Discovery
**Status:** Research Spike Complete

## Executive Summary

This document captures validated network connectivity patterns for Bronze Layer datakits running in containerized Airflow environments. We successfully tested multiple patterns and created working prototype datakits that demonstrate data extraction to Bronze storage.

## Test Environment

- **Platform:** WSL2 on Windows 11
- **Container Runtime:** Docker Desktop
- **Test Database:** PostgreSQL 15 with minimal Pagila schema
- **Bronze Storage:** Local filesystem (mounted volumes)

## Network Patterns Tested

### ✅ Pattern 1: Container-to-Container Networking

**Status:** WORKING

**Configuration:**
- Docker Compose service networking
- Service discovery via container names
- Bridge network mode

**Test Results:**
```
postgres-pagila container → test-local container
- Resolved to: 172.19.0.2
- Port 5432: OPEN
- Connection: SUCCESSFUL
- Data extraction: 10 rows from film table
- Bronze storage: Written successfully
```

**Key Findings:**
- Container names resolve automatically in Docker Compose
- No authentication issues with standard PostgreSQL auth
- Data successfully written to mounted volumes
- Bronze metadata correctly appended

**Usage in Airflow:**
```yaml
services:
  postgres-source:
    image: postgres:15
    networks:
      - airflow-network

  airflow-worker:
    environment:
      POSTGRES_HOST: postgres-source
```

### ⚠️ Pattern 2: Host Network Access

**Status:** CONDITIONAL - Requires host Postgres

**Configuration:**
- `host.docker.internal` hostname (Docker Desktop)
- `host-gateway` for Linux compatibility
- Requires Postgres running on host machine

**Test Results:**
```
host.docker.internal → Host machine
- Resolved to: 192.168.65.254
- Port 5432: CLOSED (no host Postgres running)
- Connection: NOT TESTED
```

**Key Findings:**
- Resolution works on Docker Desktop
- Requires `extra_hosts` configuration on Linux
- No host Postgres available for testing
- Pattern is viable when host database exists

**Usage in Airflow:**
```yaml
services:
  airflow-worker:
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      POSTGRES_HOST: host.docker.internal
```

### 🔄 Pattern 3: Remote Kerberos Authentication

**Status:** PENDING - Kerberos ticket issue

**Configuration:**
- Target: sqlpg.eruditis.lab (10.50.50.13)
- Authentication: Kerberos/GSSAPI
- Credential cache mounting required

**Test Results:**
```
Kerberos connectivity test
- Network path to KDC (10.50.50.11:88): OPEN
- kinit command: FAILED - "Cannot contact any KDC"
- Status: Awaiting network admin investigation
```

**Key Findings:**
- Network connectivity to KDC confirmed
- Issue appears to be DNS/hostname resolution
- Prototype datakit created and ready for testing
- Will integrate with SQLModel runner from PR #20

**Required Configuration:**
```yaml
services:
  airflow-worker:
    volumes:
      - /etc/krb5.conf:/etc/krb5.conf:ro
      - ~/.krb5-cache/dev:/tmp/krb5cc:ro
    environment:
      KRB5CCNAME: DIR:/tmp/krb5cc
    extra_hosts:
      - "sqlpg.eruditis.lab:10.50.50.13"
```

## Bronze Layer Implementation

### Successful Data Extraction

**What Works:**
1. **Extraction:** SQLAlchemy/psycopg2 connections from containers
2. **Transformation:** Adding Bronze metadata (timestamps, source info)
3. **Loading:** Writing to mounted volumes in multiple formats
4. **Formats:** Both Parquet and JSON successfully tested

**Bronze Metadata Added:**
```json
{
  "bronze_load_timestamp": "2025-11-02T21:49:44.849300",
  "bronze_source_system": "pagila_local",
  "bronze_source_table": "film",
  "bronze_source_host": "postgres-pagila",
  "bronze_extraction_method": "full_snapshot"
}
```

### File Structure
```
data/bronze/
└── pagila_local/
    └── film/
        ├── 20251102_214944.json      # JSON format
        └── 20251102_214944.parquet   # Parquet format
```

## Prototype Datakits Created

### 1. postgres_bronze_local
- **Purpose:** Local and container-to-container connections
- **Status:** Fully functional
- **Features:** Network discovery, multiple host testing
- **Output:** Successfully extracts and stores data

### 2. postgres_bronze_kerberos
- **Purpose:** Remote database with Kerberos auth
- **Status:** Code complete, awaiting Kerberos fix
- **Features:** Ticket validation, GSSAPI connection
- **Integration:** Ready for SQLModel runner (PR #20)

## Recommendations

### For Development Environment

1. **Use Container-to-Container** for local development
   - Simplest setup
   - No authentication complexity
   - Reliable service discovery

2. **Prepare for Kerberos** in production
   - Mount credential caches
   - Configure host entries
   - Use specialized runner images

3. **Standardize Bronze Metadata**
   - Always include: timestamp, source system, table, method
   - Consider adding: row count, schema version, extraction duration

### For Production Deployment

1. **Network Configuration**
   ```yaml
   # Recommended docker-compose pattern
   networks:
     bronze-network:
       driver: bridge
   ```

2. **Volume Mounting**
   ```yaml
   volumes:
     - ./bronze:/opt/airflow/bronze  # Bronze storage
     - /etc/krb5.conf:/etc/krb5.conf:ro  # Kerberos config
   ```

3. **Environment Variables**
   ```bash
   BRONZE_PATH=/opt/airflow/bronze
   KRB5CCNAME=DIR:/tmp/krb5cc
   POSTGRES_GSSENCMODE=require
   ```

## Next Steps

### Immediate Actions
1. ✅ Container-to-container networking validated
2. ✅ Bronze extraction patterns proven
3. ⏳ Await Kerberos ticket resolution for remote testing
4. 🔄 Integrate with SQLModel runner image from PR #20

### Future Enhancements
1. Add retry logic for transient failures
2. Implement incremental extraction (CDC)
3. Add data quality checks
4. Create reusable extraction library
5. Build Airflow operators for Bronze ingestion

## Test Commands

### Run Individual Tests
```bash
# Container-to-container test
docker-compose run test-local

# Host network test (requires host Postgres)
docker-compose run test-host-network

# Kerberos test (requires valid ticket)
docker-compose run test-kerberos
```

### Validate Connectivity
```bash
# Check prerequisites
./scripts/validate_connections.sh

# Setup Kerberos
./scripts/setup_kerberos.sh
```

## Conclusion

The research spike successfully validated core network patterns for Bronze Layer implementation. Container-to-container networking works reliably and can be used immediately for development. The Kerberos pattern is architecturally sound but awaits environment fixes. The prototype datakits created here can evolve into production Bronze Layer components with minimal changes.

**Key Achievement:** We have working code that extracts data from Postgres databases in containers and writes to Bronze storage with proper metadata - proving the Bronze Layer architecture is viable.