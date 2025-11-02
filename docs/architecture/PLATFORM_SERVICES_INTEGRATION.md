# Platform Services Integration Strategy

## Available Platform Services

Based on the sibling repository (`airflow-data-platform`), we have these platform services available:

### 1. Central PostgreSQL Database
- **Purpose**: Shared database for multiple uses
- **Current Uses**:
  - Airflow metadata store
  - Can host Bronze/Silver/Gold schemas
  - Test data storage
- **Connection**: Available at `postgres-platform-service:5432`

### 2. Kerberos Sidecar
- **Purpose**: Maintains fresh Kerberos tickets
- **Status**: Always-on service
- **Mount Point**: `/var/krb5/cache`

### 3. Pagila Database
- **Purpose**: Source data for demos
- **Location**: Can run as platform service or standalone

## Integration Options for Bronze Layer

### Option A: Use Central Postgres (Recommended for Simplicity)

```yaml
# All schemas in one database
Central Postgres Platform Service:
  ├── airflow schema (Airflow metadata)
  ├── bronze schema (Bronze layer tables)
  ├── bronze_history schema (Temporal history)
  ├── silver schema (Silver layer)
  └── gold schema (Gold layer)
```

**Pros**:
- Single database to manage
- Simplified networking
- Easy cross-schema queries
- Already running as platform service

**Cons**:
- Less production-like (typically separate databases)
- All eggs in one basket
- Schema naming must be careful

### Option B: Separate Bronze Database

```yaml
# Dedicated Bronze database
services:
  postgres-platform:     # Existing - Airflow metadata
  postgres-bronze:       # New - Bronze/Silver/Gold warehouse
  postgres-pagila:       # Source data
```

**Pros**:
- More production-like
- Clear separation of concerns
- Independent scaling/backup

**Cons**:
- More services to manage
- Additional network complexity

## Recommended Approach for Examples

For the Examples repository, we'll use **Option A** (Central Postgres) because:

1. **Faster Development**: One less service to manage
2. **Simpler Configuration**: Single connection string
3. **Platform Service Reuse**: Leverages existing infrastructure
4. **Easy Migration**: Can split later if needed

## Implementation Details

### Database Schema Structure

```sql
-- In the central Postgres platform service

-- Bronze layer schemas
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS bronze_history;

-- Silver layer schemas
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS silver_history;

-- Gold layer schemas
CREATE SCHEMA IF NOT EXISTS gold;

-- Grant permissions
GRANT ALL ON SCHEMA bronze TO airflow_user;
GRANT ALL ON SCHEMA bronze_history TO airflow_user;
```

### Connection Configuration

```python
# Environment variables for datakits
BRONZE_DB_HOST=postgres-platform-service
BRONZE_DB_PORT=5432
BRONZE_DB_NAME=airflow  # Same DB, different schemas
BRONZE_SCHEMA=bronze
HISTORY_SCHEMA=bronze_history

# Connection string
BRONZE_CONNECTION="postgresql://airflow_user:${DB_PASSWORD}@${BRONZE_DB_HOST}:${BRONZE_DB_PORT}/${BRONZE_DB_NAME}"
```

### Docker Compose Integration

```yaml
# docker-compose.yml extension for examples
services:
  # Reuse platform postgres
  postgres:
    external: true
    external_name: platform_postgres-platform-service

  # Our runners can connect to it
  bronze-runner:
    image: runners/sqlmodel-runner:local
    environment:
      - DATABASE_URL=postgresql://airflow:airflow@postgres:5432/airflow
      - TARGET_SCHEMA=bronze
    networks:
      - platform_default
```

## Migration Path

### Development Phase
1. Use central Postgres with schemas
2. Test temporal patterns
3. Validate performance

### Production Readiness
1. Document schema separation needs
2. Create terraform/IaC for separate databases if needed
3. Update connection configurations

## Network Connectivity Testing

To validate the platform service connectivity:

```bash
# Test from a runner container
docker run --rm -it \
  --network platform_default \
  runners/sqlmodel-runner:local \
  python -c "
import psycopg
conn = psycopg.connect('host=postgres-platform-service dbname=airflow user=airflow')
print('Connected to platform Postgres!')
"
```

## Decision Record

**Decision**: Use central Postgres platform service with schema separation

**Date**: 2025-11-02

**Rationale**:
- Simplifies initial development
- Leverages existing platform services
- Can evolve to separate databases later
- Reduces operational complexity for examples

**Review Date**: After first successful Bronze layer implementation