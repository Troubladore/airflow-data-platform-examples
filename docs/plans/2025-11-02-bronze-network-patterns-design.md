# Bronze Layer Network Patterns Design

## Issue #12: Environment Setup & Network Discovery

**Date:** 2025-11-02
**Type:** Research Spike
**Author:** Claude

## Executive Summary

This research spike validates network connectivity patterns for Bronze Layer datakits running in containerized Airflow environments. We create prototype datakits that demonstrate working data extraction from Pagila databases (both local and remote) with various authentication methods, proving our Bronze Layer architecture will function in local development.

## Objectives

1. **Validate Connectivity:** Prove datakits can connect to all required data sources from containers
2. **Test Authentication:** Demonstrate Kerberos/GSSAPI authentication works in containers
3. **Create Prototypes:** Build rudimentary datakits that can evolve into production code
4. **Document Patterns:** Capture working configurations for future development

## Architecture

### Component Structure

Following the monorepo pattern established by `datakits-sqlserver` and other examples:

```
bronze-network-tests/
├── README.md                        # Overview and quick start
├── docker-compose.yml               # Test orchestration
├── docs/
│   ├── setup-guide.md              # Environment setup
│   ├── configuration.md            # Config options
│   └── test-results.md             # Documented findings
├── datakits/
│   ├── postgres_bronze_kerberos/   # Remote Pagila with Kerberos
│   │   ├── Dockerfile
│   │   ├── src/
│   │   │   └── extract.py          # Data extraction logic
│   │   ├── requirements.txt
│   │   └── setup.py
│   ├── postgres_bronze_local/      # Local Pagila connections
│   │   ├── Dockerfile
│   │   ├── src/
│   │   │   └── extract.py
│   │   ├── requirements.txt
│   │   └── setup.py
├── scripts/
│   ├── setup_kerberos.sh          # Ticket mounting
│   └── validate_connections.sh     # Pre-flight checks
├── tests/
│   ├── test_kerberos_conn.py      # Kerberos connectivity tests
│   ├── test_local_conn.py         # Local connectivity tests
│   └── test_extraction.py         # Data extraction tests
└── data/
    └── bronze/                     # Bronze layer output (gitignored)
```

This structure:
- Follows the existing monorepo pattern (like `datakits-sqlserver/`)
- Keeps everything self-contained within `bronze-network-tests/`
- Prevents namespace collisions with other examples
- Can be run independently or as part of the larger platform

### Network Patterns to Validate

#### 1. Remote Kerberos-Authenticated Postgres
- **Target:** sqlpg.eruditis.lab (10.50.50.13)
- **Database:** Pagila
- **Authentication:** Kerberos/GSSAPI
- **Challenges:** Ticket mounting, credential cache in containers
- **Success Criteria:** Extract 100 films from remote Pagila

#### 2. Local Postgres Connections
- **Target:** Host-based Postgres or container Postgres
- **Authentication:** Standard PostgreSQL auth
- **Networking:** Docker host networking or bridge
- **Success Criteria:** Connect from container to local database

#### 3. Container-to-Container Networking
- **Pattern:** Datakit container → Database container
- **Discovery:** Docker Compose service names
- **Success Criteria:** Data flows between containers

#### 4. Bronze Storage Patterns
- **Storage:** Mounted volumes accessible to Airflow
- **Formats:** JSON and Parquet
- **Metadata:** Timestamp, source system, extraction details
- **Success Criteria:** Airflow workers can read written data

## Implementation Approach

### Phase 1: Environment Setup
1. Create Docker Compose configuration
2. Set up Kerberos credential mounting
3. Configure network bridges

### Phase 2: Prototype Datakits
1. Build postgres_bronze_kerberos datakit
2. Build postgres_bronze_local datakit
3. Implement extraction logic with Bronze metadata

### Phase 3: Validation
1. Test each connectivity pattern
2. Verify data extraction and storage
3. Document working configurations

### Example Extraction Logic

```python
def extract_to_bronze(connection_params, table_name):
    """Extract data from source to Bronze layer"""

    # Connect using appropriate method
    if connection_params.get('use_kerberos'):
        conn = create_kerberos_connection(connection_params)
    else:
        conn = create_standard_connection(connection_params)

    # Extract data
    query = f"SELECT * FROM {table_name} LIMIT 100"
    df = pd.read_sql(query, conn)

    # Add Bronze metadata
    df['bronze_load_timestamp'] = datetime.now()
    df['bronze_source_system'] = connection_params['source_system']
    df['bronze_extraction_method'] = 'full_snapshot'

    # Write to Bronze storage
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f"/bronze/{connection_params['source_system']}/{table_name}/{timestamp}.parquet"
    df.to_parquet(output_path)

    return output_path
```

## Success Criteria

1. **Kerberos Authentication:** Successfully connect to sqlpg.eruditis.lab from container
2. **Data Extraction:** Extract at least 3 tables from Pagila
3. **Bronze Storage:** Write data with proper metadata
4. **Documentation:** Clear NETWORK_PATTERNS.md with working examples
5. **Reusable Code:** Prototypes that can evolve into production datakits

## Constraints

- Must work within Docker containers (matching Airflow environment)
- Cannot modify host system configuration
- Must handle credential mounting securely
- Should be runnable on any developer machine with Docker

## Testing Strategy

Each pattern will have:
1. **Connectivity Test:** Verify network path exists
2. **Authentication Test:** Verify credentials work
3. **Data Extraction Test:** Verify data can be retrieved
4. **Storage Test:** Verify Bronze layer write succeeds

## Deliverables

1. **Working Prototype Datakits:** Containerized extractors for each pattern
2. **Docker Compose Configuration:** Orchestration for testing
3. **NETWORK_PATTERNS.md:** Documentation of what works
4. **Test Results:** Evidence of successful extractions
5. **Configuration Templates:** Reusable configs for future datakits

## Future Evolution

These prototypes will evolve into:
- Production Bronze datakits
- Airflow DAG components
- Reusable extraction libraries
- Standard patterns for the data platform

## Notes

- This is a research spike - code quality can be refined later
- Focus on proving patterns work, not production readiness
- Document all failures and workarounds discovered
- Capture specific configuration requirements for each pattern