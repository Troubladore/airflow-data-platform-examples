# Bronze Layer Implementation Plan

## Date: 2025-11-02
## Target Completion: 2 weeks
## Approach: Framework-First with Pre-Built Runners

---

## Phase 1: Environment Setup & Validation (Day 1-2)

### 1.1 Platform Services Verification

**Task**: Verify all platform services are operational

**Steps**:
1. Start platform services from sibling repository
   ```bash
   cd ~/repos/airflow-data-platform
   ./platform start base-platform
   ```
2. Verify Postgres is accessible
3. Verify Kerberos sidecar is running
4. Document service endpoints

**Verification**:
- [ ] Can connect to Postgres at `postgres-platform-service:5432`
- [ ] Kerberos sidecar healthy and maintaining tickets
- [ ] Network connectivity between services confirmed

**Deliverable**: `docs/setup/SERVICES_VERIFICATION.md` with connection details

### 1.2 Pagila Source Setup

**Task**: Configure Pagila database as source system

**Steps**:
1. Deploy Pagila from sibling repo OR use existing instance
2. Document connection parameters
3. Verify all 15 tables are accessible
4. Create read-only user for Bronze ingestion

**Verification**:
- [ ] All Pagila tables readable
- [ ] Connection works from Docker container
- [ ] Sample query returns data

**Deliverable**: Pagila connection configuration documented

### 1.3 Network Connectivity Research Spike

**Task**: Determine exact network patterns for container connectivity

**Steps**:
1. Create test container with network tools
2. Test `host.docker.internal` connectivity to Pagila
3. Test direct hostname resolution
4. Test with and without Kerberos authentication
5. Document working patterns for both local and remote databases

**Verification**:
- [ ] Local Pagila connection pattern confirmed
- [ ] Remote database connection pattern confirmed
- [ ] Kerberos authentication flow validated

**Deliverable**: `docs/setup/NETWORK_PATTERNS.md` with tested configurations

---

## Phase 2: Runner Image Construction (Day 2-3)

### 2.1 Build SQLModel Runner

**Task**: Create pre-built runner with all Bronze layer dependencies

**Location**: `runners/sqlmodel-runner/`

**Steps**:
1. Finalize Dockerfile with Astronomer base image
2. Install sqlmodel-framework dependencies
3. Add PostgreSQL drivers and Kerberos libraries
4. Build and test runner image locally
5. Push to local registry for testing

**Verification**:
- [ ] Runner image builds successfully
- [ ] Python can import all required packages
- [ ] Kerberos libraries functional
- [ ] Can connect to PostgreSQL

**Deliverable**: Working `platform/runners/sqlmodel-runner:local` image

### 2.2 Runner Validation

**Task**: Validate runner can execute mounted code

**Steps**:
1. Create simple test script
2. Mount script into runner container
3. Verify environment variables are accessible
4. Test database connectivity from runner
5. Validate Kerberos ticket mounting

**Verification**:
- [ ] Mounted code executes successfully
- [ ] Environment variables accessible
- [ ] Database connection works
- [ ] Kerberos tickets readable (if mounted)

**Deliverable**: `runners/sqlmodel-runner/test/validation.py` script

---

## Phase 3: Bronze Data Models (Day 3-4)

### 3.1 Create Temporal Base Classes

**Task**: Implement temporal table patterns

**Location**: `bronze-datakits-pagila/datakits/pagila-ingestion/src/models/`

**Steps**:
1. Create `temporal_base.py` with TemporalTable mixin
2. Define audit fields (effective_time, systime, operation_type)
3. Implement field exclusion patterns
4. Add trigger generation logic
5. Create tests for temporal behavior

**Verification**:
- [ ] TemporalTable mixin properly defined
- [ ] Audit fields correctly typed
- [ ] Exclusion patterns work
- [ ] Tests pass

**Deliverable**: Base temporal classes ready for use

### 3.2 Define Pagila Table Models

**Task**: Create SQLModel classes for all 15 Pagila tables

**Tables to Model**:
- actor, address, category, city, country
- customer, film, film_actor, film_category
- inventory, language, payment, rental
- staff, store

**Steps**:
1. Analyze Pagila schema for each table
2. Create SQLModel class with proper types
3. Apply TemporalTable mixin
4. Define relationships where needed
5. Mark fields for exclusion if appropriate

**Verification**:
- [ ] All 15 tables have models
- [ ] Models match source schema
- [ ] Temporal mixin applied correctly
- [ ] Type hints complete

**Deliverable**: `models/pagila_tables.py` with all table definitions

### 3.3 Create Database Schema Scripts

**Task**: SQL scripts to create Bronze schema structure

**Location**: `datawarehouse-pagila/schemas/bronze/`

**Steps**:
1. Create `create_schemas.sql` for bronze and bronze_history schemas
2. Generate CREATE TABLE statements for all tables
3. Include history table definitions
4. Add indexes for performance
5. Create migration scripts

**Verification**:
- [ ] Schemas created successfully
- [ ] All tables created with correct structure
- [ ] History tables include temporal fields
- [ ] Indexes applied

**Deliverable**: Complete Bronze schema DDL scripts

---

## Phase 4: Ingestion Logic Implementation (Day 5-6)

### 4.1 Implement Data Loader

**Task**: Create loader using DataFactory patterns

**Location**: `bronze-datakits-pagila/datakits/pagila-ingestion/src/ingestion/loader.py`

**Steps**:
1. Implement connection management
2. Create batch reading logic
3. Add progress tracking
4. Implement error handling
5. Add metrics collection

**Verification**:
- [ ] Can read from Pagila in batches
- [ ] Progress tracking works
- [ ] Errors handled gracefully
- [ ] Metrics collected

**Deliverable**: Working data loader class

### 4.2 Implement Merge Logic

**Task**: UPSERT operations for incremental updates

**Location**: `bronze-datakits-pagila/datakits/pagila-ingestion/src/ingestion/merger.py`

**Steps**:
1. Implement MERGE/UPSERT logic
2. Handle primary key conflicts
3. Preserve historical records
4. Add batch_id tracking
5. Implement rollback on failure

**Verification**:
- [ ] Inserts new records
- [ ] Updates existing records
- [ ] No duplicates created
- [ ] Batch tracking works

**Deliverable**: Merge logic for incremental loads

### 4.3 Create Trigger Management

**Task**: Apply temporal triggers to Bronze tables

**Location**: `bronze-datakits-pagila/datakits/pagila-ingestion/src/ingestion/triggers.py`

**Steps**:
1. Import trigger builder from framework
2. Create trigger generation logic
3. Implement idempotent trigger creation
4. Add trigger validation
5. Handle trigger updates

**Verification**:
- [ ] Triggers created on first run
- [ ] Triggers are idempotent
- [ ] INSERT/UPDATE/DELETE tracked
- [ ] History records created

**Deliverable**: Automatic trigger management system

### 4.4 Build Main Entry Point

**Task**: CLI interface for the datakit

**Location**: `bronze-datakits-pagila/datakits/pagila-ingestion/src/main.py`

**Steps**:
1. Create CLI using typer/argparse
2. Add table selection parameter
3. Implement mode selection (full/incremental)
4. Add configuration loading
5. Wire together loader, merger, and triggers

**Verification**:
- [ ] CLI accepts required parameters
- [ ] Configuration loads from environment
- [ ] Full pipeline executes
- [ ] Proper exit codes

**Deliverable**: Complete executable datakit

---

## Phase 5: Orchestration Development (Day 7-8)

### 5.1 Create Airflow DAG

**Task**: Build DAG for Bronze ingestion

**Location**: `bronze-datakits-pagila/dags/bronze_ingestion_dag.py`

**Steps**:
1. Define DAG with proper schedule
2. Create KubernetesPodOperator for each table
3. Configure parallel execution
4. Add error handling and retries
5. Implement monitoring and alerts

**Verification**:
- [ ] DAG parses without errors
- [ ] All tables have tasks
- [ ] Parallel execution configured
- [ ] Error handling works

**Deliverable**: Complete Bronze ingestion DAG

### 5.2 Configure Astronomer Deployment

**Task**: Set up Astronomer project structure

**Location**: Root of examples repo

**Steps**:
1. Initialize Astronomer project if needed
2. Configure `airflow_settings.yaml`
3. Add Bronze DAG to include path
4. Configure connections and variables
5. Test with `astro dev start`

**Verification**:
- [ ] Astronomer starts successfully
- [ ] DAG visible in UI
- [ ] Connections configured
- [ ] Can trigger DAG manually

**Deliverable**: Working Astronomer configuration

---

## Phase 6: Testing & Validation (Day 9-10)

### 6.1 Unit Testing

**Task**: Comprehensive unit tests

**Location**: `bronze-datakits-pagila/datakits/pagila-ingestion/tests/unit/`

**Test Coverage**:
- Model definitions
- Loader logic
- Merger operations
- Trigger generation
- Configuration handling

**Verification**:
- [ ] 80%+ code coverage
- [ ] All critical paths tested
- [ ] Edge cases handled
- [ ] Tests run in CI

**Deliverable**: Complete unit test suite

### 6.2 Integration Testing

**Task**: End-to-end testing with real database

**Location**: `bronze-datakits-pagila/datakits/pagila-ingestion/tests/integration/`

**Test Scenarios**:
1. Full table load
2. Incremental update
3. Error recovery
4. Trigger functionality
5. History table population

**Verification**:
- [ ] Full pipeline works end-to-end
- [ ] History correctly maintained
- [ ] Incremental updates work
- [ ] Error scenarios handled

**Deliverable**: Integration test suite

### 6.3 Performance Testing

**Task**: Validate performance at scale

**Test Cases**:
1. Large table ingestion (payment table)
2. Parallel table processing
3. Memory usage monitoring
4. Network throughput
5. Database load testing

**Verification**:
- [ ] Meets performance targets
- [ ] No memory leaks
- [ ] Scales appropriately
- [ ] Database handles load

**Deliverable**: Performance test report

---

## Phase 7: Documentation & Handoff (Day 11-12)

### 7.1 Technical Documentation

**Task**: Complete technical docs

**Documents to Create**:
1. Architecture overview
2. Setup instructions
3. Configuration guide
4. Troubleshooting guide
5. API documentation

**Verification**:
- [ ] Docs are clear and complete
- [ ] Examples provided
- [ ] Diagrams included
- [ ] Reviewed by peer

**Deliverable**: Complete documentation set

### 7.2 Operational Runbook

**Task**: Create operational procedures

**Sections**:
1. Monitoring and alerts
2. Common issues and fixes
3. Performance tuning
4. Backup and recovery
5. Upgrade procedures

**Verification**:
- [ ] Procedures tested
- [ ] Contact information current
- [ ] Escalation paths defined
- [ ] Recovery tested

**Deliverable**: Operational runbook

---

## Dependencies

### External Dependencies
- Astronomer CLI installed and configured
- Access to Astronomer base image
- PostgreSQL platform service running
- Pagila database accessible
- Kerberos sidecar operational (if using auth)

### Framework Dependencies
- sqlmodel-framework from sibling repo
- Temporal patterns library
- Trigger builder components

### Team Dependencies
- Platform team: Runner image approval
- Security team: Kerberos configuration
- Database team: Schema creation permissions
- Network team: Connectivity validation

---

## Risk Mitigation

### Risk 1: Network Connectivity Issues
**Mitigation**: Early spike in Phase 1.3 to validate all patterns

### Risk 2: Runner Image Build Failures
**Mitigation**: Have fallback to local development without runners

### Risk 3: Temporal Pattern Complexity
**Mitigation**: Start with single table prototype before scaling

### Risk 4: Performance Issues
**Mitigation**: Implement batching and parallel processing from start

---

## Success Criteria

### Functional Success
- [ ] All 15 Pagila tables ingested to Bronze layer
- [ ] Temporal history maintained automatically
- [ ] Incremental updates working without duplicates
- [ ] Triggers managing CDC correctly

### Operational Success
- [ ] DAG running on schedule
- [ ] Monitoring and alerting configured
- [ ] Documentation complete
- [ ] Handoff to operations team complete

### Performance Success
- [ ] Full load completes in < 30 minutes
- [ ] Incremental updates in < 5 minutes
- [ ] No memory issues with large tables
- [ ] Database performs within SLA

---

## Next Steps After Implementation

1. **Silver Layer Planning**: Design Silver transformation patterns
2. **Gold Layer Architecture**: Plan aggregation strategies
3. **Production Readiness**: Security review and hardening
4. **Scale Testing**: Validate with production data volumes
5. **Automation**: CI/CD pipeline setup

---

## Notes for Implementers

- Start with a single small table (e.g., `language`) for prototype
- Use `film` table for medium complexity testing
- Use `payment` table for scale testing (largest table)
- Keep Bronze layer simple - just ingestion and history
- Save complex transformations for Silver layer
- Document all decisions and deviations from plan