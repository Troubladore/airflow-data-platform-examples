# Bronze Datakits - Pagila Source

## Overview

This repository contains Bronze layer datakits for ingesting data from Pagila source databases into the Bronze layer of our data warehouse. The Bronze layer represents raw, unprocessed data in a 1:1 mapping with source systems, enhanced with temporal tracking.

## Architecture

- **Pattern**: Temporal tables with automatic history tracking
- **Framework**: SQLModel with temporal patterns from `sqlmodel-framework`
- **Execution**: Runs in pre-built `sqlmodel-runner` containers
- **Orchestration**: Apache Airflow via Astronomer

## Repository Structure

```
bronze-datakits-pagila/
├── datakits/
│   └── pagila-ingestion/       # Main Pagila ingestion datakit
├── dags/
│   └── bronze_ingestion_dag.py # Airflow DAG definitions
└── ci/
    └── .gitlab-ci.yml          # CI/CD pipeline
```

## Quick Start

### Local Development

```bash
# Run with local runner
docker run --rm -v $(pwd)/datakits/pagila-ingestion/src:/app/src \
  platform/runners/sqlmodel-runner:latest \
  --table film --mode full

# Run tests
cd datakits/pagila-ingestion
pytest tests/
```

### Deployment

This datakit is deployed via Astronomer and runs using KubernetesPodOperator. The code is mounted into pre-built runner containers at runtime.

## Configuration

Environment variables:
- `PAGILA_CONNECTION_STRING`: Source database connection
- `BRONZE_CONNECTION_STRING`: Target Bronze database
- `USE_KERBEROS`: Enable Kerberos authentication (true/false)
- `BATCH_SIZE`: Records per batch (default: 10000)

## Data Flow

```
Pagila Source → Bronze Datakit → Bronze Tables + History Tables
                                  (with triggers for CDC)
```

## Tables Ingested

- actor, address, category, city, country
- customer, film, film_actor, film_category
- inventory, language, payment, rental
- staff, store

## Temporal Pattern

Each table gets:
1. Primary table: `bronze.{table_name}`
2. History table: `bronze.{table_name}__history`
3. Automatic triggers for INSERT/UPDATE/DELETE tracking

## Team Ownership

- **Team**: Data Ingestion Team
- **Contact**: data-ingestion@company.com
- **SLA**: Data available within 15 minutes of source changes

## Dependencies

All dependencies are pre-installed in the `sqlmodel-runner` image:
- sqlmodel-framework (temporal patterns)
- psycopg3 (PostgreSQL driver)
- pandas (data processing)

No local dependency installation required!

## Testing

```bash
# Unit tests
pytest datakits/pagila-ingestion/tests/unit/

# Integration tests (requires database)
pytest datakits/pagila-ingestion/tests/integration/
```

## Monitoring

- Airflow task logs for execution details
- Database audit tables for ingestion history
- Prometheus metrics exposed by runner

## Related Repositories

In production, these would be separate repos:
- `silver-datakits-pagila`: Silver layer transformations
- `gold-datakits-pagila`: Business aggregations
- `datawarehouse-pagila`: Schema definitions