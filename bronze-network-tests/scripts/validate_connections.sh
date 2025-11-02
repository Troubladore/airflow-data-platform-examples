#!/bin/bash
#
# Validate all connection patterns before running full tests
#

set -e

echo "=========================================="
echo "Validating Bronze Network Connections"
echo "=========================================="

# Function to test a connection
test_connection() {
    local name=$1
    local host=$2
    local port=$3

    echo ""
    echo "Testing $name..."
    if nc -zv $host $port 2>&1 | grep -q succeeded; then
        echo "  ✓ $host:$port is reachable"
        return 0
    else
        echo "  ✗ $host:$port is not reachable"
        return 1
    fi
}

# Test remote Kerberos Postgres
echo ""
echo "1. REMOTE KERBEROS POSTGRES"
echo "----------------------------"
if grep -q "sqlpg.eruditis.lab" /etc/hosts; then
    echo "  ✓ Host entry found for sqlpg.eruditis.lab"
    test_connection "Remote Pagila" "sqlpg.eruditis.lab" 5432 || true
else
    echo "  ✗ No host entry for sqlpg.eruditis.lab"
    echo "    Add to /etc/hosts: 10.50.50.13 sqlpg.eruditis.lab"
fi

# Check Kerberos ticket
if klist 2>/dev/null | grep -q "emaynard@ERUDITIS.LAB"; then
    echo "  ✓ Kerberos ticket found"
else
    echo "  ✗ No Kerberos ticket (run: kinit emaynard@ERUDITIS.LAB)"
fi

# Test local Postgres
echo ""
echo "2. LOCAL POSTGRES"
echo "-----------------"
if command -v psql >/dev/null 2>&1; then
    # Check if local Postgres is running
    if pgrep postgres >/dev/null 2>&1; then
        echo "  ✓ Local Postgres process found"
        test_connection "Local Postgres" "localhost" 5432 || true
    else
        echo "  ℹ No local Postgres process running"
    fi
else
    echo "  ℹ psql not installed locally"
fi

# Test Docker daemon
echo ""
echo "3. DOCKER ENVIRONMENT"
echo "---------------------"
if docker info >/dev/null 2>&1; then
    echo "  ✓ Docker daemon is running"

    # Check if we can build images
    if docker images >/dev/null 2>&1; then
        echo "  ✓ Docker images accessible"
    fi

    # Check network
    if docker network ls | grep -q bronze-network; then
        echo "  ✓ bronze-network already exists"
    else
        echo "  ℹ bronze-network will be created by docker-compose"
    fi
else
    echo "  ✗ Docker daemon not accessible"
    exit 1
fi

# Check for required files
echo ""
echo "4. REQUIRED FILES"
echo "-----------------"
files_ok=true

if [ -f /etc/krb5.conf ]; then
    echo "  ✓ /etc/krb5.conf exists"
else
    echo "  ✗ /etc/krb5.conf missing"
    files_ok=false
fi

if [ -d ~/.krb5-cache/dev ]; then
    echo "  ✓ Credential cache directory exists"
else
    echo "  ℹ Credential cache directory not found (will use default)"
fi

echo ""
echo "=========================================="
if [ "$files_ok" = true ]; then
    echo "✓ Validation complete. Ready to run tests!"
    echo ""
    echo "Run tests with:"
    echo "  docker-compose up --build"
    echo ""
    echo "Or test individually:"
    echo "  docker-compose run test-local      # Local patterns"
    echo "  docker-compose run test-kerberos   # Kerberos auth"
    echo "  docker-compose run test-host-network # Host networking"
else
    echo "✗ Some requirements are missing. Please fix before running tests."
    exit 1
fi