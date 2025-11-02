#!/bin/bash
# Script to create GitHub issues for Bronze layer implementation
# Requires: gh CLI tool installed and authenticated

set -e

echo "Creating Bronze Layer Implementation Issues..."
echo "==========================================="

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    echo "Install from: https://cli.github.com/"
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Creating Epic issue...${NC}"

# Create Epic
EPIC_NUMBER=$(gh issue create \
  --title "Epic: Implement Bronze Layer for Pagila Data Platform" \
  --body "## Overview
Implement the Bronze layer ingestion from Pagila source database to Bronze warehouse layer using temporal table patterns and pre-built runners.

## Architecture
- Framework-First approach using sqlmodel-framework
- Pre-built runners for restricted environments
- Temporal table patterns with automatic history tracking
- Orchestration via Astronomer/Airflow

## Success Criteria
- [ ] All 15 Pagila tables ingested to Bronze layer
- [ ] Temporal history maintained automatically
- [ ] Incremental updates working without duplicates
- [ ] Performance meets SLAs
- [ ] Full documentation and handoff complete

## Child Issues
Will be linked after creation

## Reference
See detailed design: docs/plans/2025-11-02-bronze-layer-design.md" \
  --label "epic" \
  --label "bronze-layer" \
  --label "framework-first" \
  | grep -o '[0-9]*')

echo -e "${GREEN}✓ Created Epic #$EPIC_NUMBER${NC}"

# Create Issue #1: Environment Setup
echo -e "${BLUE}Creating Issue #1: Environment Setup...${NC}"
ISSUE_1=$(gh issue create \
  --title "Setup platform services and validate network connectivity patterns" \
  --body "## Context
Before we can build the Bronze layer, we need platform services running and network patterns validated.

## Acceptance Criteria
- [ ] Platform services started and healthy
- [ ] Central Postgres accessible at documented endpoint
- [ ] Kerberos sidecar running with fresh tickets
- [ ] Pagila database deployed and accessible
- [ ] Network connectivity patterns documented
- [ ] Both local and remote database access tested
- [ ] Connection strings documented in \`.env.example\`

## Tasks
1. Start platform services from \`airflow-data-platform\` repo
2. Verify Postgres connectivity
3. Deploy/connect to Pagila database
4. Test connectivity patterns (host.docker.internal, direct hostnames, etc.)
5. Document working patterns in \`docs/setup/NETWORK_PATTERNS.md\`
6. Create \`.env.example\` with all required variables

## Testing
\`\`\`bash
# Verify platform services
docker ps | grep platform

# Test database connectivity
docker run --rm -it --network platform_default postgres:15 \\
  psql -h postgres-platform-service -U airflow -c \"SELECT 1\"
\`\`\`

## Dependencies
- Access to airflow-data-platform repository
- Docker Desktop running

## Blocks
- All subsequent Bronze layer work

## Parent Epic
- #$EPIC_NUMBER" \
  --label "setup" \
  --label "infrastructure" \
  --label "spike" \
  --label "P0-blocker" \
  | grep -o '[0-9]*')

echo -e "${GREEN}✓ Created Issue #$ISSUE_1${NC}"

# Create Issue #2: Build Runner
echo -e "${BLUE}Creating Issue #2: Build SQLModel Runner...${NC}"
ISSUE_2=$(gh issue create \
  --title "Create pre-built runner image for Bronze layer datakits" \
  --body "## Context
Pre-built runners solve the problem of complex Docker image building in restricted environments.

## Acceptance Criteria
- [ ] Dockerfile created extending Astronomer base image
- [ ] All Python dependencies installed
- [ ] Kerberos libraries included
- [ ] Image builds successfully
- [ ] Image size < 500MB
- [ ] Test script validates all imports work
- [ ] Image tagged as \`platform/runners/sqlmodel-runner:v1.0.0\`

## Tasks
1. Finalize \`runners/sqlmodel-runner/Dockerfile\`
2. Create comprehensive \`requirements.txt\`
3. Build image locally
4. Create validation script
5. Test mounting code into runner
6. Document runner usage

## Testing
\`\`\`bash
# Build runner
cd runners/sqlmodel-runner
docker build -t platform/runners/sqlmodel-runner:v1.0.0 .

# Test with mounted code
docker run --rm -v \$(pwd)/test:/app/src \\
  platform/runners/sqlmodel-runner:v1.0.0 \\
  python /app/src/test_imports.py
\`\`\`

## Dependencies
- Depends on: #$ISSUE_1

## Blocks
- Ingestion Logic implementation
- Orchestration implementation

## Parent Epic
- #$EPIC_NUMBER" \
  --label "infrastructure" \
  --label "runner" \
  --label "docker" \
  --label "P0-blocker" \
  | grep -o '[0-9]*')

echo -e "${GREEN}✓ Created Issue #$ISSUE_2${NC}"

# Create Issue #3: Data Models
echo -e "${BLUE}Creating Issue #3: Data Models...${NC}"
ISSUE_3=$(gh issue create \
  --title "Implement SQLModel table definitions with temporal patterns" \
  --body "## Context
The Bronze layer uses temporal tables where each table has a companion \`__history\` table that tracks all changes.

## Acceptance Criteria
- [ ] Base temporal mixin class created
- [ ] All 15 Pagila tables modeled
- [ ] Field types match source schema exactly
- [ ] Temporal patterns properly applied
- [ ] Models can be imported without errors
- [ ] Unit tests for model validation

## Tables to Model
actor, address, category, city, country, customer, film, film_actor, film_category, inventory, language, payment, rental, staff, store

## Tasks
1. Create \`temporal_base.py\` with TemporalTable mixin
2. Model all 15 Pagila tables in \`pagila_tables.py\`
3. Create SQL schema scripts
4. Write unit tests

## Files
- \`bronze-datakits-pagila/datakits/pagila-ingestion/src/models/temporal_base.py\`
- \`bronze-datakits-pagila/datakits/pagila-ingestion/src/models/pagila_tables.py\`
- \`datawarehouse-pagila/schemas/bronze/\`

## Dependencies
- Depends on: #$ISSUE_1

## Blocks
- Ingestion Logic implementation

## Parent Epic
- #$EPIC_NUMBER" \
  --label "data-modeling" \
  --label "sqlmodel" \
  --label "bronze-layer" \
  --label "P1-high" \
  | grep -o '[0-9]*')

echo -e "${GREEN}✓ Created Issue #$ISSUE_3${NC}"

# Create Issue #4: Ingestion Logic
echo -e "${BLUE}Creating Issue #4: Ingestion Logic...${NC}"
ISSUE_4=$(gh issue create \
  --title "Build data loader, merger, and trigger management for Bronze ingestion" \
  --body "## Context
Core ingestion logic handles reading from Pagila, merging into Bronze tables, and managing temporal triggers.

## Acceptance Criteria
- [ ] Data loader reads from Pagila in configurable batches
- [ ] Merger handles INSERT and UPDATE operations
- [ ] Duplicate prevention logic works
- [ ] Batch ID tracking implemented
- [ ] Triggers automatically created on first run
- [ ] CLI entry point accepts required parameters
- [ ] Error handling and logging implemented
- [ ] Integration tests pass

## Components
1. \`loader.py\` - Data loading from source
2. \`merger.py\` - UPSERT operations
3. \`triggers.py\` - Temporal trigger management
4. \`main.py\` - CLI entry point

## CLI Interface
\`\`\`bash
# Full load
python main.py --table film --mode full

# Incremental load
python main.py --table film --mode incremental --batch-id 2024-01-15
\`\`\`

## Dependencies
- Depends on: #$ISSUE_2 (Runner)
- Depends on: #$ISSUE_3 (Models)

## Blocks
- Orchestration implementation

## Parent Epic
- #$EPIC_NUMBER" \
  --label "ingestion" \
  --label "core-logic" \
  --label "bronze-layer" \
  --label "P1-high" \
  | grep -o '[0-9]*')

echo -e "${GREEN}✓ Created Issue #$ISSUE_4${NC}"

# Create Issue #5: Orchestration
echo -e "${BLUE}Creating Issue #5: Orchestration...${NC}"
ISSUE_5=$(gh issue create \
  --title "Create DAG for Bronze layer orchestration with Astronomer" \
  --body "## Context
DAG orchestrates parallel ingestion of all Pagila tables using pre-built runners.

## Acceptance Criteria
- [ ] DAG created with proper configuration
- [ ] All 15 tables have tasks
- [ ] Parallel execution configured
- [ ] KubernetesPodOperator properly configured
- [ ] Error handling and retries implemented
- [ ] Astronomer project configured
- [ ] DAG visible in Airflow UI
- [ ] Manual trigger works successfully

## Files
- \`bronze-datakits-pagila/dags/bronze_ingestion_dag.py\`
- Astronomer project configuration

## Testing
\`\`\`bash
# Start Astronomer
astro dev start

# Trigger DAG
astro dev dags trigger bronze_pagila_ingestion
\`\`\`

## Dependencies
- Depends on: #$ISSUE_4

## Blocks
- Testing and validation

## Parent Epic
- #$EPIC_NUMBER" \
  --label "airflow" \
  --label "orchestration" \
  --label "astronomer" \
  --label "P1-high" \
  | grep -o '[0-9]*')

echo -e "${GREEN}✓ Created Issue #$ISSUE_5${NC}"

# Create Issue #6: Testing
echo -e "${BLUE}Creating Issue #6: Testing...${NC}"
ISSUE_6=$(gh issue create \
  --title "Implement unit, integration, and performance tests for Bronze layer" \
  --body "## Context
Comprehensive testing ensures Bronze layer reliability and performance.

## Acceptance Criteria
- [ ] Unit tests achieve 80%+ code coverage
- [ ] Integration tests validate end-to-end flow
- [ ] Performance tests confirm scalability
- [ ] All tests automated in CI/CD
- [ ] Test data fixtures created
- [ ] Error scenarios covered
- [ ] Temporal patterns validated

## Test Suites
1. **Unit Tests** - Model validation, loader logic, configuration
2. **Integration Tests** - Full pipeline, history tables, triggers
3. **Performance Tests** - Large tables, memory usage, concurrency

## Success Metrics
- Unit test coverage > 80%
- Integration tests < 5 min runtime
- Performance: 1M records < 60 seconds

## Dependencies
- Depends on: #$ISSUE_5

## Blocks
- Documentation and handoff

## Parent Epic
- #$EPIC_NUMBER" \
  --label "testing" \
  --label "quality" \
  --label "bronze-layer" \
  --label "P2-medium" \
  | grep -o '[0-9]*')

echo -e "${GREEN}✓ Created Issue #$ISSUE_6${NC}"

# Create Issue #7: Documentation
echo -e "${BLUE}Creating Issue #7: Documentation...${NC}"
ISSUE_7=$(gh issue create \
  --title "Complete documentation and operational handoff for Bronze layer" \
  --body "## Context
Proper documentation ensures the Bronze layer can be operated and maintained by other teams.

## Acceptance Criteria
- [ ] Architecture documentation complete
- [ ] Setup guide tested by another developer
- [ ] Operational runbook created
- [ ] Troubleshooting guide with common issues
- [ ] Configuration reference documented
- [ ] Code fully documented with docstrings
- [ ] Knowledge transfer session conducted

## Documentation Components
1. **Technical Documentation** - Architecture, setup, configuration
2. **Operational Runbook** - Monitoring, alerts, troubleshooting
3. **Developer Guide** - Extending, testing, deployment

## Validation
- Have another developer follow setup guide
- Test all procedures in runbook
- Review with operations team

## Dependencies
- Depends on: #$ISSUE_6

## Parent Epic
- #$EPIC_NUMBER" \
  --label "documentation" \
  --label "handoff" \
  --label "bronze-layer" \
  --label "P2-medium" \
  | grep -o '[0-9]*')

echo -e "${GREEN}✓ Created Issue #$ISSUE_7${NC}"

echo ""
echo -e "${GREEN}Successfully created all Bronze Layer issues!${NC}"
echo ""
echo "Epic: #$EPIC_NUMBER"
echo "Issues created: #$ISSUE_1, #$ISSUE_2, #$ISSUE_3, #$ISSUE_4, #$ISSUE_5, #$ISSUE_6, #$ISSUE_7"
echo ""
echo "Next steps:"
echo "1. Review issues in GitHub: gh issue list"
echo "2. Add to project board: gh project item-add [PROJECT_NUMBER] --issue [ISSUE_NUMBER]"
echo "3. Assign team members: gh issue edit [ISSUE_NUMBER] --add-assignee [USERNAME]"
echo "4. Start with Issue #$ISSUE_1 (Environment Setup)"