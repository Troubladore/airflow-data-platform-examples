# Monorepo Structure - Examples Repository

## Overview

The `airflow-data-platform-examples` repository is structured as a **monorepo** containing multiple sub-repositories that would typically be separate in a real organization. This demonstrates proper separation of concerns and ownership boundaries.

## Repository Structure

```
airflow-data-platform-examples/           # Monorepo root
├── bronze-datakits-pagila/              # Sub-repo 1: Source team owns
│   ├── README.md
│   ├── .gitignore
│   ├── datakits/
│   │   ├── pagila-ingestion/
│   │   │   ├── src/
│   │   │   └── tests/
│   │   └── other-sources/
│   ├── dags/
│   │   └── bronze_ingestion_dag.py
│   └── ci/
│       └── .gitlab-ci.yml
│
├── silver-datakits-pagila/              # Sub-repo 2: Analytics team owns
│   ├── README.md
│   ├── .gitignore
│   ├── datakits/
│   │   ├── customer-360/
│   │   ├── inventory-analytics/
│   │   └── revenue-metrics/
│   ├── dags/
│   │   └── silver_transformation_dag.py
│   └── dbt/                            # Might use dbt for Silver
│       └── models/
│
├── gold-datakits-pagila/                # Sub-repo 3: Business team owns
│   ├── README.md
│   ├── .gitignore
│   ├── datakits/
│   │   ├── executive-dashboard/
│   │   ├── ml-features/
│   │   └── reporting-marts/
│   ├── dags/
│   │   └── gold_aggregation_dag.py
│   └── notebooks/                      # Analysis notebooks
│
├── datawarehouse-pagila/                # Sub-repo 4: Platform team owns
│   ├── README.md
│   ├── .gitignore
│   ├── schemas/
│   │   ├── bronze/
│   │   │   ├── tables.sql
│   │   │   └── migrations/
│   │   ├── silver/
│   │   └── gold/
│   ├── terraform/                      # IaC for warehouse
│   ├── alembic/                       # Database migrations
│   └── monitoring/
│       └── queries.sql
│
├── runners/                            # Shared runners (or in platform)
│   ├── sqlmodel-runner/
│   ├── spark-runner/
│   └── dbt-runner/
│
├── docs/                               # Monorepo-level documentation
│   ├── architecture/
│   └── plans/
│
└── scripts/                            # Monorepo management scripts
    ├── setup-all.sh
    └── test-all.sh
```

## Ownership Model

### Bronze Datakits (Source Data Team)
- **Responsibility**: Raw data ingestion from source systems
- **Ownership**: Team closest to source systems
- **Technologies**: SQLModel, pandas, direct SQL
- **Deployment**: Triggered on source system changes
- **SLA**: Data freshness guarantees

### Silver Datakits (Analytics Engineering Team)
- **Responsibility**: Cleaned, conformed, business-ready data
- **Ownership**: Central analytics team
- **Technologies**: dbt, SQLModel, Spark
- **Deployment**: Triggered after Bronze completes
- **SLA**: Data quality and consistency

### Gold Datakits (Business Intelligence Team)
- **Responsibility**: Aggregated marts and features
- **Ownership**: Business/BI teams
- **Technologies**: dbt, notebooks, ML frameworks
- **Deployment**: Scheduled or triggered
- **SLA**: Business metrics accuracy

### Data Warehouse (Platform Team)
- **Responsibility**: Schema definitions, migrations, infrastructure
- **Ownership**: Data platform team
- **Technologies**: Terraform, Alembic, SQL
- **Deployment**: GitOps with approval gates
- **SLA**: Uptime and performance

## Why This Structure?

### 1. Realistic Separation
In practice, these would be separate repos because:
- Different teams own them
- Different deployment cycles
- Different testing requirements
- Different access controls

### 2. Clear Boundaries
Each sub-repo has:
- Its own README and documentation
- Independent test suites
- Separate CI/CD pipelines
- Distinct dependencies

### 3. Monorepo Benefits for Examples
While separate in production, the monorepo structure helps for examples:
- See the complete picture in one place
- Easy to run end-to-end demos
- Simplified dependency management for learning
- Common runner definitions

## Development Workflow

### Local Development
```bash
# Work on Bronze layer
cd bronze-datakits-pagila/
make test
make run-local

# Work on Silver layer
cd ../silver-datakits-pagila/
make test
```

### CI/CD Pipelines
Each sub-repo has its own pipeline:
- Bronze: Triggered by source changes
- Silver: Triggered by Bronze completion
- Gold: Scheduled or triggered by Silver
- Warehouse: Manual approval required

## Migration to Production

In a real organization, you would:

1. **Fork each sub-repo** into separate repositories
2. **Set up team ownership** in GitHub/GitLab
3. **Configure separate CI/CD** per repository
4. **Establish inter-repo contracts** (schemas, SLAs)
5. **Implement proper secrets management** per team

## Example: Bronze Sub-Repository Structure

```
bronze-datakits-pagila/
├── README.md                     # "Bronze Datakits for Pagila Source"
├── Makefile                      # Local development commands
├── .gitignore                    # Bronze-specific ignores
├── requirements-dev.txt          # Testing dependencies only
│
├── datakits/
│   └── pagila-ingestion/
│       ├── src/
│       │   ├── main.py          # Entry point
│       │   ├── config.py        # Configuration
│       │   ├── models/          # SQLModel definitions
│       │   │   ├── __init__.py
│       │   │   ├── actor.py
│       │   │   ├── film.py
│       │   │   └── temporal_base.py
│       │   └── ingestion/       # Ingestion logic
│       │       ├── __init__.py
│       │       ├── loader.py
│       │       └── merger.py
│       └── tests/
│           ├── test_models.py
│           └── test_ingestion.py
│
├── dags/
│   ├── bronze_daily_ingestion.py
│   └── bronze_backfill.py
│
└── ci/
    └── .gitlab-ci.yml           # Bronze-specific CI/CD
```

## Key Design Principles

1. **Each sub-repo is self-contained** - Can be developed and tested independently
2. **Clear contracts between layers** - Schema definitions, data quality rules
3. **No cross-repo imports** - Communication through database schemas only
4. **Independent deployment** - Each layer can be deployed separately
5. **Shared infrastructure** - Runners and platform services are centralized

This structure demonstrates best practices for organizing data platform code while maintaining clear separation of concerns and team boundaries.