# Bronze Layer Implementation Design

## Date: 2025-11-02
## Status: Approved
## Approach: Framework-First Integration

## Executive Summary

This design document outlines the implementation of the Bronze layer for the Airflow Data Platform, which ingests data from Pagila source databases into a Bronze warehouse layer using temporal table patterns. The implementation leverages the existing `sqlmodel-framework` with full temporal table support, automatic history tracking, and merge capabilities.

## Architecture Overview

### High-Level Data Flow
```
Pagila Source DB → Bronze Datakit Container → Bronze Target DB
                   (sqlmodel-framework)       (temporal tables)
```

### Key Architectural Decisions

1. **Framework-First Approach**: Full integration with `sqlmodel-framework` temporal patterns
2. **Container-Based Execution**: Datakits run as isolated containers via KubernetesPodOperator
3. **Temporal Table Pattern**: Primary tables with `__history` tables and trigger-based tracking
4. **Platform Services Integration**: Shared Kerberos sidecar for authentication
5. **Astronomer Orchestration**: Using Astronomer CLI locally, Astronomer platform in production

## Platform Services Integration

### Always-On Services Architecture

The platform maintains always-running services that datakits can leverage:

```yaml
# Platform Services (always running)
- Kerberos Sidecar: Maintains fresh tickets in shared volume
- Registry Proxy: Routes to corporate Artifactory
- Network Bridge: Handles corporate network access
```

### Integration Points

1. **Kerberos Authentication**
   - Sidecar maintains tickets in `/var/krb5/cache`
   - Datakits mount cache as read-only
   - Automatic ticket renewal without datakit involvement

2. **Network Connectivity**
   - Local: Docker network communication
   - Remote: Corporate network via Kerberos auth
   - Configurable via environment variables

## Bronze Datakit Implementation

### Component Structure (Monorepo with Sub-Repositories)

```
airflow-data-platform-examples/          # Monorepo root
├── bronze-datakits-pagila/              # Sub-repo for Bronze layer
│   ├── datakits/
│   │   └── pagila-ingestion/
│   │       ├── src/
│   │       │   ├── models/             # SQLModel table definitions
│   │       │   ├── ingestion/          # Loader and merger logic
│   │       │   └── main.py             # Entry point
│   │       └── tests/
│   └── dags/
│       └── bronze_ingestion_dag.py     # Bronze-specific DAGs
│
├── silver-datakits-pagila/              # Separate sub-repo (different team)
├── gold-datakits-pagila/                # Separate sub-repo (BI team)
├── datawarehouse-pagila/                # Separate sub-repo (platform team)
│
└── runners/                             # Shared runner images
    └── sqlmodel-runner/
        ├── Dockerfile                   # Pre-built with all dependencies
        └── requirements.txt
```

**Key Design Decision**: Each layer (Bronze, Silver, Gold) is a separate sub-repository within the monorepo, reflecting real-world team boundaries and deployment patterns. In production, these would be independent repositories with different ownership and deployment cycles.

### Key Implementation Details

1. **Runner Pattern**
   - Pre-built `sqlmodel-runner` image with all dependencies
   - Datakit code mounted at runtime via ConfigMap or volume
   - No build step required for code changes

2. **Table Models**
   - SQLModel classes for each Pagila table
   - TemporalTable mixin for automatic history
   - Field-level exclusion annotations where needed

3. **Data Loading**
   - DataFactory for bulk operations
   - Batch ID tracking for audit trail
   - Configurable batch sizes

4. **Merge Operations**
   - UPSERT logic for incremental updates
   - Conflict resolution based on primary keys
   - Preservation of historical records

5. **Trigger Management**
   - Automatic trigger creation on first run
   - INSERT, UPDATE, DELETE tracking
   - Temporal metadata (effective_time, systime, operation_type)

## DAG Orchestration Pattern

### Parallel Table Ingestion with Runner Pattern

The Bronze ingestion DAG uses pre-built runners with mounted code:

```python
# Conceptual DAG structure using runners
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from kubernetes.client import models as k8s

PAGILA_TABLES = [
    'actor', 'address', 'category', 'city', 'country',
    'customer', 'film', 'film_actor', 'film_category',
    'inventory', 'language', 'payment', 'rental',
    'staff', 'store'
]

# Using pre-built runner image - no custom image build needed!
for table in PAGILA_TABLES:
    task = KubernetesPodOperator(
        task_id=f'bronze_{table}',
        # Pre-built runner with all dependencies
        image='platform/runners/sqlmodel-runner:v1.0.0',
        # Mount the datakit code at runtime
        volume_mounts=[
            k8s.V1VolumeMount(
                name='datakit-code',
                mount_path='/app/src',
                sub_path='bronze-pagila/src'
            )
        ],
        # Pass table-specific configuration
        env_vars={'TABLE_NAME': table, 'MODE': 'incremental'}
    )
```

### Orchestration Features

- **Parallel Execution**: All tables ingest simultaneously
- **Mode Selection**: Full load vs incremental updates
- **Batch Tracking**: Using Airflow execution date as batch_id
- **Error Isolation**: Table-level error handling
- **Retry Logic**: Configurable retries per table

## Connectivity Requirements

### Design Intent

The Bronze layer must flexibly support multiple deployment scenarios without code changes.

### Connectivity Scenarios

1. **Local Development**
   - Pagila in same Docker network
   - Direct container-to-container communication
   - No Kerberos required

2. **Remote/Production**
   - Pagila on corporate network
   - Kerberos authentication required
   - Network policies enforced

### Configuration Strategy

All connectivity configured via environment variables:
- `PAGILA_CONNECTION_STRING`: Source database connection
- `BRONZE_CONNECTION_STRING`: Target database connection
- `USE_KERBEROS`: Enable/disable Kerberos auth
- `INGESTION_MODE`: Full or incremental
- `BATCH_SIZE`: Records per batch

## Temporal Table Pattern Details

### Table Structure

For each Pagila table, the Bronze layer creates:
1. **Primary Table**: `bronze.{table_name}` - Current state
2. **History Table**: `bronze.{table_name}__history` - All changes

### History Tracking

History tables include:
- All columns from primary table (except excluded fields)
- `history_id`: UUID for history record
- `effective_time`: Business effective timestamp
- `systime`: System timestamp of change
- `operation_type`: INSERT, UPDATE, or DELETE

### Trigger Behavior

PostgreSQL triggers automatically:
1. Create history record on INSERT
2. Create history record on UPDATE
3. Create history record on DELETE
4. Handle temporal metadata population

## Success Criteria

### Functional Requirements
- ✓ All Pagila tables replicated to Bronze layer
- ✓ Temporal history maintained automatically
- ✓ Incremental updates merge without duplicates
- ✓ Batch tracking for audit and reprocessing

### Non-Functional Requirements
- ✓ Parallel ingestion for performance
- ✓ Configurable for different environments
- ✓ Kerberos authentication when required
- ✓ Error isolation per table

## Implementation Phases

### Phase 1: Foundation
1. Set up development environment with Astronomer CLI
2. Configure platform services (Kerberos sidecar)
3. Verify network connectivity patterns

### Phase 2: Datakit Development
1. Create SQLModel table definitions
2. Implement DataFactory loader
3. Add merge/UPSERT logic
4. Test trigger creation

### Phase 3: Orchestration
1. Create Airflow DAG
2. Configure KubernetesPodOperator tasks
3. Add monitoring and alerting
4. Test parallel execution

### Phase 4: Integration Testing
1. Full load testing
2. Incremental update testing
3. Error handling validation
4. Performance benchmarking

## Risk Mitigation

### Identified Risks

1. **Network Connectivity**
   - Risk: Container-to-database connectivity issues
   - Mitigation: Research spike to validate patterns

2. **Kerberos Authentication**
   - Risk: Ticket mounting complexity
   - Mitigation: Platform sidecar pattern proven in sibling repo

3. **Performance at Scale**
   - Risk: Large table ingestion timeouts
   - Mitigation: Configurable batch sizes and parallel processing

## Next Steps

1. Complete network connectivity research spike
2. Begin datakit implementation with single table prototype
3. Extend to all Pagila tables
4. Deploy to Astronomer dev environment
5. Performance testing and optimization

## References

- Architecture Diagram: `/docs/architecture/airflow-data-platform-concept.pdf`
- Temporal Patterns: `airflow-data-platform/sqlmodel-framework/`
- Astronomer Integration: `/datakits-sqlserver/deployment/astronomer-platform-integration.md`
- Platform Services: `airflow-data-platform/kerberos/kerberos-sidecar/`