# Key Architecture Documents Index

## Primary References (Current/Authoritative)

### 1. Airflow Data Platform Concept Diagram
- **File**: `airflow-data-platform-concept.pdf`
- **Location**: `/docs/architecture/`
- **Purpose**: Visual overview of the complete data platform architecture including Bronze, Silver, and Gold layers
- **Use for**: Understanding data flow, layer responsibilities, and integration points
- **Status**: CURRENT - This is the most up-to-date architectural view

### 2. Bronze Layer Implementation Guide
- **File**: `03_bronze.md`
- **Location**: `airflow-data-platform/deprecated/ref/docs/dev-local-experience/`
- **Purpose**: Detailed implementation steps for Bronze layer datakits
- **Use for**: Understanding datakit pattern, ingestion process, and container-based ETL
- **Status**: Reference implementation (marked deprecated but contains valid patterns)

## Secondary References (Context/Patterns)

### 3. Runtime Patterns Documentation
- **Location**: `airflow-data-platform/docs/patterns/`
- **Files**:
  - `runtime-patterns.md` - Core runtime execution patterns
  - `runtime-creating.md` - How to create runtime containers
  - `runtime-base-images.md` - Base image specifications
- **Use for**: Understanding container-based task execution patterns

### 4. SQLModel Patterns
- **File**: `sqlmodel-patterns.md`
- **Location**: `airflow-data-platform/docs/patterns/`
- **Use for**: Database schema management and ORM patterns for Bronze/Silver/Gold layers

## Implementation Context

### 5. Technical Architecture (Historical)
- **Location**: `airflow-data-platform/docs/archive/`
- **Status**: ARCHIVED - Contains older concepts, reference with caution
- **Use for**: Understanding historical decisions and evolution

## Notes on Documentation Status

- The sibling repository (`airflow-data-platform`) contains many files marked "deprecated" but they still contain valid architectural patterns
- Focus on the PDF diagram as the source of truth for current architecture
- Implementation patterns from deprecated folders are still valid for container-based ETL approaches

## Key Architectural Decisions from Primary Docs

1. **Astronomer-based deployment** - Using Astronomer for Airflow orchestration
2. **Container-based datakits** - Each ETL job runs in its own container (datakit pattern)
3. **Bronze layer responsibility** - 1:1 raw data ingestion with audit metadata
4. **Pagila as source** - Sample PostgreSQL database for demonstration
5. **PostgreSQL warehouse** - Target database for Bronze/Silver/Gold layers