#!/bin/bash

set -euo pipefail

echo "🚀 PAGILA MEDALLION ARCHITECTURE - COMPLETE DEMONSTRATION"
echo "=========================================================="
echo ""

# Check if we're in the right directory
if [[ ! -f "docker-compose.yml" ]] || [[ ! -d "orchestration" ]]; then
    echo "❌ Please run this script from the pagila-sqlmodel-basic directory"
    echo "   cd pagila-implementations/pagila-sqlmodel-basic"
    exit 1
fi

# Set up environment variables for Airflow
export AIRFLOW_UID=$(id -u)
echo "🔧 Setting AIRFLOW_UID=$AIRFLOW_UID"

# Stop any running containers first
echo "🛑 Stopping any existing containers..."
docker-compose down -v > /dev/null 2>&1 || true

# Start the infrastructure
echo ""
echo "🏗️ STEP 1: Starting infrastructure (Airflow + Pagila database)..."
docker-compose up -d airflow-postgres pagila-source-db

# Wait for databases to be healthy
echo "⏳ Waiting for databases to be healthy..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose ps | grep -q "healthy.*healthy"; then
        echo "✅ Databases are healthy!"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts - waiting..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Databases failed to become healthy"
    docker-compose logs
    exit 1
fi

# Load Pagila data
echo ""
echo "📊 STEP 2: Loading Pagila source data..."

# Check if pagila repository exists
if [[ ! -d "/home/troubladore/repos/pagila" ]]; then
    echo "❌ Pagila repository not found at /home/troubladore/repos/pagila"
    echo "   Please ensure the Pagila repository is available"
    exit 1
fi

echo "   Loading Pagila schema..."
docker exec pagila-source-db psql -U postgres -d pagila < /home/troubladore/repos/pagila/pagila-schema.sql > /dev/null

echo "   Loading Pagila data (this may take a moment)..."
docker exec pagila-source-db psql -U postgres -d pagila < /home/troubladore/repos/pagila/pagila-insert-data.sql > /dev/null

# Verify data loaded
customer_count=$(docker exec pagila-source-db psql -U postgres -d pagila -t -c "SELECT COUNT(*) FROM public.customer" | tr -d ' ')
echo "   ✅ Loaded $customer_count customers"

# Initialize Airflow
echo ""
echo "⚙️ STEP 3: Initializing Airflow..."
docker-compose up airflow-init

# Start Airflow services
echo ""
echo "🎯 STEP 4: Starting Airflow services..."
docker-compose up -d airflow-webserver airflow-scheduler

# Wait for Airflow to be ready
echo "⏳ Waiting for Airflow to be ready..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:18080/health > /dev/null 2>&1; then
        echo "✅ Airflow is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts - waiting for Airflow webserver..."
    sleep 3
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Airflow failed to start"
    docker-compose logs airflow-webserver
    exit 1
fi

# Create medallion schemas
echo ""
echo "🏗️ STEP 5: Creating medallion architecture schemas..."
docker exec pagila-source-db psql -U postgres -d pagila -c "
CREATE SCHEMA IF NOT EXISTS staging_pagila;
CREATE SCHEMA IF NOT EXISTS silver_pagila;
CREATE SCHEMA IF NOT EXISTS gold_pagila;
"
echo "   ✅ Created staging_pagila, silver_pagila, gold_pagila schemas"

# Set up Airflow Variables
echo ""
echo "📋 STEP 6: Configuring Airflow Variables..."
docker-compose exec -T airflow-webserver airflow variables set pagila_source_connection "postgresql://postgres:pagila_demo_password@pagila-source-db:5432/pagila"
docker-compose exec -T airflow-webserver airflow variables set bronze_target_connection "postgresql://postgres:pagila_demo_password@pagila-source-db:5432/pagila"
docker-compose exec -T airflow-webserver airflow variables set silver_target_connection "postgresql://postgres:pagila_demo_password@pagila-source-db:5432/pagila"
docker-compose exec -T airflow-webserver airflow variables set gold_target_connection "postgresql://postgres:pagila_demo_password@pagila-source-db:5432/pagila"
echo "   ✅ Airflow Variables configured"

# Final status
echo ""
echo "🎉 COMPLETE DEMONSTRATION READY!"
echo "================================"
echo ""
echo "🌐 Airflow Web UI:     http://localhost:18080"
echo "   Username: airflow"
echo "   Password: airflow"
echo ""
echo "🗄️ Database Access:"
echo "   Pagila (source):    localhost:15432"
echo "   Airflow (metadata): localhost:15433"
echo "   Username: postgres"
echo "   Password: pagila_demo_password (Pagila) / airflow_password (Airflow)"
echo ""
echo "📊 Available DAGs:"
echo "   • pagila_bronze_silver_gold_pipeline"
echo ""
echo "🎯 Next Steps:"
echo "   1. Open Airflow UI at http://localhost:18080"
echo "   2. Enable the 'pagila_bronze_silver_gold_pipeline' DAG"
echo "   3. Trigger a manual run to see Bronze→Silver→Gold data flow"
echo "   4. Monitor task execution and logs"
echo ""
echo "🛑 To stop everything: docker-compose down -v"
echo ""