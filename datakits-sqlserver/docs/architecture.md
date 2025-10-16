# Architecture

Technical design and implementation details of the SQL Server Bronze datakit.

## 🏗️ System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────┐
│                   Airflow/Orchestrator               │
│                         ↓                            │
│                 BronzeIngestionPipeline              │
│                         ↓                            │
│              SQLServerKerberosConnector              │
│                    ↓         ↓                       │
│              pyodbc     SQLAlchemy                   │
│                    ↓         ↓                       │
│            ODBC Driver   Connection Pool             │
│                    ↓         ↓                       │
│              [Kerberos Ticket Cache]                 │
│                         ↓                            │
│                   SQL Server                         │
└─────────────────────────────────────────────────────┘
```

### Data Flow

```
Source Tables → Batch Reader → Transformer → Bronze Writer
                     ↓             ↓              ↓
                  Chunking    Add Metadata   Bulk Insert
```

## 🔐 Authentication Flow

### Kerberos Authentication

1. **Ticket Acquisition**:
   ```
   KDC → Kerberos Sidecar → Ticket Cache
                               ↓
                         Shared Volume
                               ↓
                         Datakit Container
   ```

2. **Connection Establishment**:
   ```python
   # Simplified flow
   def connect():
       os.environ['KRB5CCNAME'] = '/krb5/cache/krb5cc'
       conn_string = build_kerberos_connection_string()
       return pyodbc.connect(conn_string)
   ```

3. **Token Refresh**:
   - Sidecar refreshes ticket every hour (configurable)
   - Connection pool validates tickets before use
   - Automatic reconnection on ticket expiration

## 📦 Core Components

### SQLServerKerberosConnector

**Purpose**: Manages SQL Server connections with Kerberos authentication.

**Key Methods**:
- `get_connection()` - Raw ODBC connection
- `get_engine()` - SQLAlchemy engine with pooling
- `test_connection()` - Validates connectivity
- `read_table()` - Efficient batch reading

**Design Decisions**:
- Uses connection pooling for performance
- Implements retry logic with exponential backoff
- Validates Kerberos tickets before operations

### BronzeIngestionPipeline

**Purpose**: Orchestrates the ETL process from SQL Server to Bronze.

**Key Methods**:
- `discover_tables()` - Schema introspection
- `ingest_table()` - Single table ingestion
- `ingest_all_tables()` - Bulk ingestion

**Design Patterns**:
- **Strategy Pattern**: Different ingestion strategies
- **Builder Pattern**: Configuration construction
- **Observer Pattern**: Progress tracking and logging

### Metadata Management

**Bronze Metadata Schema**:

```sql
-- Automatically added columns
_bronze_loaded_at TIMESTAMP NOT NULL,
_bronze_source_system VARCHAR(50) NOT NULL,
_bronze_source_schema VARCHAR(128) NOT NULL,
_bronze_source_table VARCHAR(128) NOT NULL,
_bronze_batch_id UUID NOT NULL,
_bronze_row_hash VARCHAR(64),  -- Optional: for deduplication
```

**Lineage Tracking**:

```python
class IngestionMetadata:
    start_time: datetime
    end_time: datetime
    source_connection: str
    target_location: str
    rows_processed: int
    errors: List[Error]
```

## 🚀 Performance Optimizations

### Batch Processing

```python
# Chunked reading for memory efficiency
for chunk in pd.read_sql_query(
    query,
    engine,
    chunksize=batch_size
):
    process_chunk(chunk)
```

**Optimization Strategies**:
- Configurable batch sizes (default: 10,000 rows)
- Parallel processing for independent tables
- Connection pooling to reduce overhead
- Bulk insert operations

### Memory Management

- **Streaming**: Process data in chunks, never load full table
- **Garbage Collection**: Explicit cleanup after processing
- **Resource Limits**: Configurable memory thresholds

### Query Optimization

```sql
-- Use NOLOCK for read-only operations (configurable)
SELECT * FROM [table] WITH (NOLOCK)

-- Parallel hints for large tables
OPTION (MAXDOP 4)
```

## 🔄 Error Handling

### Retry Strategy

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    retry=retry_if_exception_type(ConnectionError)
)
def resilient_operation():
    # Operation that might fail
```

### Error Categories

1. **Transient Errors** (retry):
   - Connection timeout
   - Kerberos ticket expired
   - Network issues

2. **Permanent Errors** (fail fast):
   - Table doesn't exist
   - Permission denied
   - Invalid configuration

3. **Data Errors** (log and continue):
   - Data type mismatch
   - Constraint violations
   - Truncation warnings

## 🐳 Container Architecture

### Docker Image Layers

```dockerfile
Base: astronomer-runtime
  ↓
Kerberos Libraries
  ↓
ODBC Drivers
  ↓
Python Dependencies
  ↓
Datakit Code
```

### Volume Mounts

```yaml
volumes:
  - /krb5/cache:/krb5/cache:ro      # Kerberos tickets
  - /etc/krb5.conf:/etc/krb5.conf:ro # Kerberos config
  - ./datakits:/opt/datakits:ro      # Datakit code
  - ./config:/opt/config:ro          # Configuration
```

## 🔍 Monitoring & Observability

### Metrics Collected

- **Performance Metrics**:
  - Rows per second
  - Batch processing time
  - Connection pool utilization

- **Business Metrics**:
  - Tables processed
  - Total rows ingested
  - Data freshness

### Logging Strategy

```python
# Structured logging
logger.info("ingestion_complete", extra={
    "table": table_name,
    "rows": row_count,
    "duration_seconds": duration,
    "batch_id": batch_id
})
```

### Health Checks

```python
def health_check():
    return {
        "kerberos_ticket_valid": check_ticket(),
        "database_accessible": check_connection(),
        "bronze_writable": check_write_access(),
    }
```

## 🔗 Integration Points

### Airflow Integration

```python
# Custom operator
class SQLServerBronzeOperator(BaseOperator):
    def execute(self, context):
        pipeline = BronzeIngestionPipeline(self.config)
        return pipeline.ingest_all_tables()
```

### Event Streaming

```python
# Kafka producer for CDC events
def publish_change_event(table, operation, data):
    producer.send('bronze-changes', {
        'table': table,
        'operation': operation,
        'data': data,
        'timestamp': datetime.now()
    })
```

## 📊 Data Quality

### Validation Rules

```python
class DataQualityCheck:
    def validate_completeness(self, df):
        # Check for required columns
        pass

    def validate_uniqueness(self, df, keys):
        # Check primary key uniqueness
        pass

    def validate_freshness(self, df):
        # Check data recency
        pass
```

## 🚦 Next Steps

- **Fix issues** → [Troubleshooting](./troubleshooting.md)
- **Configure** → [Configuration](./configuration.md)
- **Get started** → [Setup Guide](./setup-guide.md)