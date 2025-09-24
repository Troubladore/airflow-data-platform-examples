-- Bronze Layer Schema Initialization
-- ====================================
-- Raw data as ingested from SQL Server

-- Create bronze schema
CREATE SCHEMA IF NOT EXISTS bronze;

-- Grant permissions
GRANT ALL ON SCHEMA bronze TO bronze_user;

-- Create audit table for tracking ingestions
CREATE TABLE IF NOT EXISTS bronze.ingestion_audit (
    audit_id SERIAL PRIMARY KEY,
    source_system VARCHAR(50) NOT NULL,
    source_schema VARCHAR(128) NOT NULL,
    source_table VARCHAR(128) NOT NULL,
    target_table VARCHAR(256) NOT NULL,
    ingestion_started_at TIMESTAMP NOT NULL,
    ingestion_completed_at TIMESTAMP,
    rows_processed INTEGER,
    status VARCHAR(20) CHECK (status IN ('running', 'success', 'failed')),
    error_message TEXT,
    batch_id UUID DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for performance
CREATE INDEX idx_bronze_audit_source ON bronze.ingestion_audit(source_system, source_schema, source_table);
CREATE INDEX idx_bronze_audit_batch ON bronze.ingestion_audit(batch_id);
CREATE INDEX idx_bronze_audit_status ON bronze.ingestion_audit(status);

-- Example Bronze table structure (will be created dynamically by datakit)
-- This is just to show the pattern
COMMENT ON SCHEMA bronze IS 'Raw data layer - exact copies from source systems with metadata';

-- Function to add bronze metadata columns to any table
CREATE OR REPLACE FUNCTION bronze.add_bronze_metadata_columns(
    p_table_name TEXT
) RETURNS VOID AS $$
BEGIN
    EXECUTE format('
        ALTER TABLE bronze.%I
        ADD COLUMN IF NOT EXISTS _bronze_loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ADD COLUMN IF NOT EXISTS _bronze_source_system VARCHAR(50),
        ADD COLUMN IF NOT EXISTS _bronze_source_schema VARCHAR(128),
        ADD COLUMN IF NOT EXISTS _bronze_source_table VARCHAR(128),
        ADD COLUMN IF NOT EXISTS _bronze_batch_id UUID,
        ADD COLUMN IF NOT EXISTS _bronze_row_hash VARCHAR(64),
        ADD COLUMN IF NOT EXISTS _bronze_is_deleted BOOLEAN DEFAULT FALSE
    ', p_table_name);
END;
$$ LANGUAGE plpgsql;

-- Create metadata tracking table
CREATE TABLE IF NOT EXISTS bronze.table_metadata (
    table_name VARCHAR(256) PRIMARY KEY,
    source_system VARCHAR(50),
    source_connection_string TEXT,  -- Encrypted/masked
    last_ingestion_at TIMESTAMP,
    row_count BIGINT,
    size_bytes BIGINT,
    columns_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION bronze.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_bronze_metadata_updated_at
    BEFORE UPDATE ON bronze.table_metadata
    FOR EACH ROW
    EXECUTE FUNCTION bronze.update_updated_at_column();