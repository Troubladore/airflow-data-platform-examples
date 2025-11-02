# Bronze Layer Implementation - GitHub Issues

This document contains the GitHub issues to create for Bronze layer implementation. Each issue is self-contained with clear acceptance criteria and dependencies.

---

## Epic: Bronze Layer Implementation

**Title**: Epic: Implement Bronze Layer for Pagila Data Platform
**Labels**: `epic`, `bronze-layer`, `framework-first`
**Description**:
Implement the Bronze layer ingestion from Pagila source database to Bronze warehouse layer using temporal table patterns and pre-built runners.

### Child Issues:
1. Environment Setup & Validation
2. Build SQLModel Runner Image
3. Create Bronze Data Models
4. Implement Ingestion Logic
5. Build Airflow Orchestration
6. Testing & Validation
7. Documentation & Handoff

---

## Issue #1: Environment Setup & Network Discovery

**Title**: Setup platform services and validate network connectivity patterns
**Labels**: `setup`, `infrastructure`, `spike`
**Assignee**: DevOps/Platform Team
**Priority**: P0 - Blocker
**Estimate**: 2 days

### Description
Set up and validate all platform services required for Bronze layer development. Conduct network connectivity research spike to determine exact patterns for database access.

### Context
Before we can build the Bronze layer, we need:
1. Platform services running (Postgres, Kerberos sidecar)
2. Pagila source database accessible
3. Network patterns validated for both local and remote scenarios

### Acceptance Criteria
- [ ] Platform services started and healthy
- [ ] Central Postgres accessible at documented endpoint
- [ ] Kerberos sidecar running with fresh tickets
- [ ] Pagila database deployed and accessible
- [ ] Network connectivity patterns documented
- [ ] Both local and remote database access tested
- [ ] Connection strings documented in `.env.example`

### Tasks
1. Start platform services from `airflow-data-platform` repo
2. Verify Postgres connectivity at `postgres-platform-service:5432`
3. Deploy Pagila database (or connect to existing)
4. Test connectivity from Docker containers:
   - Using `host.docker.internal`
   - Using direct hostnames
   - Using Docker network names
5. Document working patterns in `docs/setup/NETWORK_PATTERNS.md`
6. Create `.env.example` with all required variables

### Testing
```bash
# Verify platform services
docker ps | grep platform

# Test database connectivity
docker run --rm -it --network platform_default postgres:15 \
  psql -h postgres-platform-service -U airflow -c "SELECT 1"

# Test Pagila access
docker run --rm -it postgres:15 \
  psql -h [PAGILA_HOST] -U pagila_user -c "SELECT COUNT(*) FROM film"
```

### Documentation
- Create `docs/setup/NETWORK_PATTERNS.md`
- Update `bronze-datakits-pagila/README.md` with setup steps

### Dependencies
- Access to `airflow-data-platform` repository
- Docker Desktop running
- Network access to databases

### Blocks
- All subsequent Bronze layer work

---

## Issue #2: Build SQLModel Runner Image

**Title**: Create pre-built runner image for Bronze layer datakits
**Labels**: `infrastructure`, `runner`, `docker`
**Assignee**: Platform Team
**Priority**: P0 - Blocker
**Estimate**: 1 day
**Depends On**: Issue #1

### Description
Build the `sqlmodel-runner` image that contains all dependencies needed for Bronze layer data ingestion. This eliminates the need for developers to build custom images.

### Context
In restricted corporate environments, building custom Docker images is complex due to package repository authentication requirements. Pre-built runners with all dependencies solve this problem.

### Acceptance Criteria
- [ ] Dockerfile created extending Astronomer base image
- [ ] All Python dependencies installed (sqlmodel, psycopg, pandas)
- [ ] Kerberos libraries included
- [ ] Image builds successfully
- [ ] Image size < 500MB
- [ ] Test script validates all imports work
- [ ] Image tagged as `platform/runners/sqlmodel-runner:v1.0.0`

### Tasks
1. Finalize `runners/sqlmodel-runner/Dockerfile`
2. Create comprehensive `requirements.txt`
3. Build image locally:
   ```bash
   cd runners/sqlmodel-runner
   docker build -t platform/runners/sqlmodel-runner:v1.0.0 .
   ```
4. Create validation script to test all imports
5. Test mounting code into runner
6. Document runner usage patterns

### Testing
```bash
# Test runner with mounted code
docker run --rm -v $(pwd)/test:/app/src \
  platform/runners/sqlmodel-runner:v1.0.0 \
  python /app/src/test_imports.py

# Verify dependencies
docker run --rm platform/runners/sqlmodel-runner:v1.0.0 \
  pip list | grep -E "sqlmodel|psycopg|pandas"
```

### Documentation
- Update `docs/architecture/RUNNER_PATTERN.md`
- Create `runners/sqlmodel-runner/README.md`

### Blocks
- Issue #4 (Ingestion Logic)
- Issue #5 (Orchestration)

---

## Issue #3: Create Bronze Data Models

**Title**: Implement SQLModel table definitions with temporal patterns
**Labels**: `data-modeling`, `sqlmodel`, `bronze-layer`
**Assignee**: Data Engineering Team
**Priority**: P1 - High
**Estimate**: 2 days
**Depends On**: Issue #1

### Description
Create SQLModel classes for all 15 Pagila tables with temporal table patterns for automatic history tracking.

### Context
The Bronze layer uses temporal tables where each table has a companion `__history` table that tracks all changes via triggers.

### Acceptance Criteria
- [ ] Base temporal mixin class created
- [ ] All 15 Pagila tables modeled
- [ ] Field types match source schema exactly
- [ ] Temporal patterns properly applied
- [ ] Field exclusions configured where needed
- [ ] Models can be imported without errors
- [ ] Unit tests for model validation

### Tasks
1. Create `bronze-datakits-pagila/datakits/pagila-ingestion/src/models/temporal_base.py`
   - TemporalTable mixin
   - Audit fields (effective_time, systime, operation_type)
   - Field exclusion patterns
2. Create `bronze-datakits-pagila/datakits/pagila-ingestion/src/models/pagila_tables.py`
   - Model all 15 tables: actor, address, category, city, country, customer, film, film_actor, film_category, inventory, language, payment, rental, staff, store
3. Create SQL schema scripts in `datawarehouse-pagila/schemas/bronze/`
4. Write unit tests for model validation

### Example Model
```python
from sqlmodel import Field, SQLModel
from datetime import datetime
from uuid import UUID
from .temporal_base import TemporalTable

class Film(TemporalTable, table=True):
    __tablename__ = "film"
    __table_args__ = {"schema": "bronze"}

    film_id: int = Field(primary_key=True)
    title: str = Field(max_length=255)
    description: str | None = Field(default=None)
    release_year: int | None = Field(default=None)
    language_id: int = Field(foreign_key="bronze.language.language_id")
    rental_duration: int = Field(default=3)
    rental_rate: float = Field(default=4.99)
    length: int | None = Field(default=None)
    replacement_cost: float = Field(default=19.99)
    rating: str | None = Field(max_length=5)
    last_update: datetime = Field(default_factory=datetime.utcnow)
    special_features: str | None = Field(default=None)
    fulltext: str | None = Field(default=None)
```

### Documentation
- Create `docs/data-model/BRONZE_SCHEMA.md`
- Document temporal patterns in code

### Blocks
- Issue #4 (Ingestion Logic needs models)

---

## Issue #4: Implement Core Ingestion Logic

**Title**: Build data loader, merger, and trigger management for Bronze ingestion
**Labels**: `ingestion`, `core-logic`, `bronze-layer`
**Assignee**: Data Engineering Team
**Priority**: P1 - High
**Estimate**: 3 days
**Depends On**: Issue #2, Issue #3

### Description
Implement the core ingestion logic including data loading, merge operations, and temporal trigger management.

### Context
The ingestion logic handles reading from Pagila, merging into Bronze tables, and ensuring temporal triggers are properly applied.

### Acceptance Criteria
- [ ] Data loader reads from Pagila in configurable batches
- [ ] Merger handles INSERT and UPDATE operations
- [ ] Duplicate prevention logic works
- [ ] Batch ID tracking implemented
- [ ] Triggers automatically created on first run
- [ ] CLI entry point accepts required parameters
- [ ] Error handling and logging implemented
- [ ] Integration tests pass

### Tasks
1. Implement `bronze-datakits-pagila/datakits/pagila-ingestion/src/ingestion/loader.py`
   - Connection management
   - Batch reading with configurable size
   - Progress tracking
2. Implement `bronze-datakits-pagila/datakits/pagila-ingestion/src/ingestion/merger.py`
   - UPSERT logic
   - Conflict resolution
   - Batch ID tracking
3. Implement `bronze-datakits-pagila/datakits/pagila-ingestion/src/ingestion/triggers.py`
   - Trigger generation from framework
   - Idempotent trigger creation
4. Create `bronze-datakits-pagila/datakits/pagila-ingestion/src/main.py`
   - CLI interface using typer
   - Configuration loading from environment
   - Wire together all components

### CLI Interface
```bash
# Full load
python main.py --table film --mode full --batch-size 10000

# Incremental load
python main.py --table film --mode incremental --batch-id 2024-01-15

# All tables
python main.py --table all --mode full
```

### Testing
```bash
# Run with test database
export PAGILA_CONNECTION_STRING=postgresql://test@localhost/pagila
export BRONZE_CONNECTION_STRING=postgresql://test@localhost/bronze
python main.py --table language --mode full

# Verify data and history
psql -d bronze -c "SELECT COUNT(*) FROM bronze.language"
psql -d bronze -c "SELECT COUNT(*) FROM bronze.language__history"
```

### Documentation
- Create `docs/ingestion/INGESTION_PATTERNS.md`
- Add docstrings to all classes and methods

### Blocks
- Issue #5 (Orchestration needs working ingestion)

---

## Issue #5: Implement Airflow Orchestration

**Title**: Create DAG for Bronze layer orchestration with Astronomer
**Labels**: `airflow`, `orchestration`, `astronomer`
**Assignee**: Data Engineering Team
**Priority**: P1 - High
**Estimate**: 2 days
**Depends On**: Issue #4

### Description
Build Airflow DAG to orchestrate Bronze layer ingestion using KubernetesPodOperator with pre-built runners.

### Context
The DAG orchestrates parallel ingestion of all Pagila tables using the sqlmodel-runner image with mounted datakit code.

### Acceptance Criteria
- [ ] DAG created with proper configuration
- [ ] All 15 tables have tasks
- [ ] Parallel execution configured
- [ ] KubernetesPodOperator properly configured
- [ ] Error handling and retries implemented
- [ ] Astronomer project configured
- [ ] DAG visible in Airflow UI
- [ ] Manual trigger works successfully

### Tasks
1. Create `bronze-datakits-pagila/dags/bronze_ingestion_dag.py`
2. Configure parallel task execution for all tables
3. Set up Astronomer project structure
4. Configure connections and variables
5. Test with `astro dev start`

### DAG Structure
```python
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-platform',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'bronze_pagila_ingestion',
    default_args=default_args,
    description='Bronze layer ingestion from Pagila',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['bronze', 'pagila'],
) as dag:

    tables = ['actor', 'address', 'category', ...]

    for table in tables:
        KubernetesPodOperator(
            task_id=f'ingest_{table}',
            name=f'bronze-{table}',
            image='platform/runners/sqlmodel-runner:v1.0.0',
            cmds=['python', '/app/src/main.py'],
            arguments=['--table', table, '--mode', 'incremental'],
            # Volume mounts for code and Kerberos tickets
        )
```

### Testing
```bash
# Start Astronomer locally
astro dev start

# Verify DAG is loaded
astro dev dags list

# Trigger DAG
astro dev dags trigger bronze_pagila_ingestion
```

### Documentation
- Create `docs/orchestration/BRONZE_DAG.md`
- Update `bronze-datakits-pagila/README.md`

### Blocks
- Issue #6 (Testing needs working orchestration)

---

## Issue #6: Comprehensive Testing Suite

**Title**: Implement unit, integration, and performance tests for Bronze layer
**Labels**: `testing`, `quality`, `bronze-layer`
**Assignee**: QA/Data Engineering Team
**Priority**: P2 - Medium
**Estimate**: 3 days
**Depends On**: Issue #5

### Description
Create comprehensive test suites to validate Bronze layer functionality, performance, and reliability.

### Context
Testing ensures the Bronze layer works correctly, handles errors gracefully, and performs within acceptable limits.

### Acceptance Criteria
- [ ] Unit tests achieve 80%+ code coverage
- [ ] Integration tests validate end-to-end flow
- [ ] Performance tests confirm scalability
- [ ] All tests automated in CI/CD
- [ ] Test data fixtures created
- [ ] Error scenarios covered
- [ ] Temporal patterns validated

### Tasks
1. **Unit Tests** (`bronze-datakits-pagila/datakits/pagila-ingestion/tests/unit/`)
   - Model validation
   - Loader logic
   - Merger operations
   - Configuration handling

2. **Integration Tests** (`bronze-datakits-pagila/datakits/pagila-ingestion/tests/integration/`)
   - Full pipeline execution
   - History table population
   - Trigger functionality
   - Error recovery

3. **Performance Tests** (`bronze-datakits-pagila/datakits/pagila-ingestion/tests/performance/`)
   - Large table handling (payment table)
   - Memory usage monitoring
   - Concurrent execution
   - Database load testing

### Test Execution
```bash
# Unit tests
pytest tests/unit/ -v --cov=src --cov-report=html

# Integration tests (requires databases)
pytest tests/integration/ -v

# Performance tests
pytest tests/performance/ -v --benchmark-only
```

### Documentation
- Create `docs/testing/TEST_STRATEGY.md`
- Add test examples to README

### Success Metrics
- Unit test coverage > 80%
- Integration tests < 5 min runtime
- Performance: 1M records < 60 seconds

---

## Issue #7: Documentation and Handoff

**Title**: Complete documentation and operational handoff for Bronze layer
**Labels**: `documentation`, `handoff`, `bronze-layer`
**Assignee**: Tech Lead/Documentation Team
**Priority**: P2 - Medium
**Estimate**: 2 days
**Depends On**: Issue #6

### Description
Create comprehensive documentation and operational procedures for Bronze layer maintenance and support.

### Context
Proper documentation ensures the Bronze layer can be operated, maintained, and extended by other teams.

### Acceptance Criteria
- [ ] Architecture documentation complete
- [ ] Setup guide tested by another developer
- [ ] Operational runbook created
- [ ] Troubleshooting guide with common issues
- [ ] Configuration reference documented
- [ ] Code fully documented with docstrings
- [ ] Knowledge transfer session conducted

### Tasks
1. **Technical Documentation**
   - Architecture overview with diagrams
   - Setup instructions
   - Configuration guide
   - API documentation

2. **Operational Runbook**
   - Monitoring procedures
   - Alert definitions
   - Common issues and fixes
   - Performance tuning guide
   - Backup/recovery procedures

3. **Developer Guide**
   - How to add new tables
   - How to modify models
   - Testing procedures
   - Deployment process

### Documentation Structure
```
docs/
├── architecture/
│   ├── BRONZE_LAYER_DESIGN.md
│   └── DATA_FLOW.md
├── setup/
│   ├── QUICKSTART.md
│   └── CONFIGURATION.md
├── operations/
│   ├── RUNBOOK.md
│   └── TROUBLESHOOTING.md
└── development/
    ├── CONTRIBUTING.md
    └── EXTENDING.md
```

### Validation
- Have another developer follow setup guide
- Test all procedures in runbook
- Review with operations team

---

## GitHub Project Board Structure

### Columns:
1. **Backlog** - Future enhancements
2. **Ready** - Issues with all dependencies met
3. **In Progress** - Active development
4. **Review** - Code review/testing
5. **Done** - Completed and merged

### Issue Dependencies:
```
#1 Environment Setup
  └─> #2 Runner Image
      └─> #4 Ingestion Logic
          └─> #5 Orchestration
              └─> #6 Testing
                  └─> #7 Documentation
  └─> #3 Data Models
      └─> #4 Ingestion Logic
```

### Milestones:
- **Milestone 1**: Environment Ready (Issues #1, #2)
- **Milestone 2**: Core Implementation (Issues #3, #4)
- **Milestone 3**: Orchestration (Issue #5)
- **Milestone 4**: Production Ready (Issues #6, #7)

---

## Issue Templates

For consistency, use these templates when creating the actual GitHub issues:

```markdown
## Context
[Why this work is needed]

## Acceptance Criteria
- [ ] Specific measurable outcome
- [ ] Another measurable outcome

## Technical Details
[Link to design doc if applicable]

## Dependencies
- Depends on: #[issue number]
- Blocks: #[issue number]

## Testing
[How to verify this work]

## Documentation
[What needs to be documented]
```