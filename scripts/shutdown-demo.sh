#!/bin/bash

set -euo pipefail

echo "🛑 SHUTTING DOWN COMPLETE PLATFORM DEMONSTRATION"
echo "================================================="
echo ""

echo "🔧 Stopping Airflow services..."
docker rm -f pagila-airflow-webserver 2>/dev/null || echo "   ℹ️ Webserver not running"
docker rm -f pagila-airflow-scheduler 2>/dev/null || echo "   ℹ️ Scheduler not running"
docker rm -f pagila-airflow-db 2>/dev/null || echo "   ℹ️ Airflow DB not running"
echo "   ✅ Airflow services stopped"

echo ""
echo "🗄️ Stopping data services..."
docker rm -f pagila-source-db 2>/dev/null || echo "   ℹ️ Pagila DB not running"
echo "   ✅ Data services stopped"

echo ""
echo "🏗️ Stopping Layer 1 platform services..."
# Stop Ansible-generated services first (preferred)
if [[ -f "$HOME/platform-services/traefik/docker-compose.yml" ]]; then
    cd "$HOME/platform-services/traefik"
    docker compose down 2>/dev/null || echo "   ℹ️ Ansible platform services not running"
    cd - > /dev/null
fi
# Stop static services (fallback)
cd /home/troubladore/repos/airflow-data-platform
docker-compose -f prerequisites/traefik-registry/docker-compose.yml down 2>/dev/null || echo "   ℹ️ Static platform services not running"
echo "   ✅ Platform services stopped"

echo ""
echo "🧹 Cleaning up resources..."
docker volume rm -f pagila-source-data 2>/dev/null || echo "   ℹ️ Pagila volume not found"
docker volume rm -f airflow-db-data 2>/dev/null || echo "   ℹ️ Airflow volume not found"
docker image rm -f localhost:5000/pagila/airflow:latest 2>/dev/null || echo "   ℹ️ Airflow image not found"

# Remove networks if empty
docker network rm data-processing-network 2>/dev/null || echo "   ℹ️ Data processing network in use or not found"
docker network rm edge 2>/dev/null || echo "   ℹ️ Edge network in use or not found"

echo ""
echo "🎯 Shutdown Summary:"
echo "   • Airflow UI:       https://airflow.localhost (offline)"
echo "   • Pagila Database:  localhost:15432 (offline)"
echo "   • Traefik Proxy:    https://traefik.localhost (offline)"
echo ""
echo "✅ COMPLETE PLATFORM DEMONSTRATION: STOPPED"
echo ""
echo "💡 To restart everything:"
echo "   Run: ./scripts/demo-everything-working.sh"
echo ""