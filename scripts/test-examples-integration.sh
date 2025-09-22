#!/bin/bash
# Examples Integration Test Runner
# Tests platform + example data composite functionality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLATFORM_REPO="/home/troubladore/repos/airflow-data-platform"
COMPOSE_FILE="$PLATFORM_REPO/layer1-platform/docker/test-postgres.yml"
TEST_DB_CONTAINER="datakit-test-db"

# Logging functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Global variable to track if we need to cleanup the container
CLEANUP_CONTAINER=false

print_banner() {
    echo -e "${BLUE}"
    echo "🧪 =================================================="
    echo "   EXAMPLES INTEGRATION TEST RUNNER"
    echo "   Platform + Examples Composite Validation"
    echo "=================================================="
    echo -e "${NC}"
}

# Cleanup function
cleanup() {
    if [ "$CLEANUP_CONTAINER" = true ]; then
        log_info "Starting cleanup process..."
        log_info "Stopping PostgreSQL test sandbox..."
        cd "$PLATFORM_REPO"
        if docker compose -f "$COMPOSE_FILE" down --volumes &> /dev/null; then
            log_success "Test sandbox cleaned up"
        else
            log_warning "Cleanup may not have completed fully"
        fi
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Check if test container is already running
check_existing_container() {
    docker ps --format "table {{.Names}}" | grep -q "^${TEST_DB_CONTAINER}$"
}

# Bootstrap PostgreSQL test database
bootstrap_sandbox() {
    log_info "Bootstrapping PostgreSQL test sandbox for examples integration..."

    # Check if already running - if so, we'll use it but ensure cleanup
    if check_existing_container; then
        log_info "Using existing test database container"
        CLEANUP_CONTAINER=true  # Always clean up test containers for resource conservation
        return 0
    fi

    # Check Docker availability
    if ! command -v docker &> /dev/null; then
        log_error "Docker not available - cannot start test sandbox"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon not running - please start Docker Desktop"
        exit 1
    fi

    # Start the container
    log_info "Starting fresh test database container..."
    cd "$PLATFORM_REPO"
    if ! docker compose -f "$COMPOSE_FILE" up -d; then
        log_error "Failed to start test database container"
        exit 1
    fi

    CLEANUP_CONTAINER=true

    # Wait for database to be ready using netcat-like approach
    log_info "Waiting for database to be ready..."
    for i in {1..60}; do
        if timeout 1 bash -c "</dev/tcp/localhost/15444" 2>/dev/null; then
            # Give PostgreSQL a moment to fully initialize after port opens
            sleep 3
            break
        fi
        if [ $i -eq 60 ]; then
            log_error "Database failed to start within 60 seconds"
            exit 1
        fi
        sleep 1
    done

    log_success "Database is ready!"
    log_success "PostgreSQL test sandbox bootstrapped successfully"
    log_info "Connection: localhost:15444, database: datakit_tests, user: test_user"
}

# Run integration tests
run_integration_tests() {
    log_info "Running examples integration tests..."

    cd "$REPO_ROOT"

    # Test 1: Pagila SQLModel Basic Integration
    log_info "Test 1: Pagila SQLModel Basic deployment integration..."
    cd "$REPO_ROOT/pagila-implementations/pagila-sqlmodel-basic"

    # Ensure dependencies are installed
    if ! command -v uv &> /dev/null; then
        log_error "uv not available - install with: pip install uv"
        exit 1
    fi

    # Install dependencies
    log_info "Installing example dependencies..."
    uv sync

    # Use platform's deployment script to test integration
    log_info "Testing platform + example integration..."
    PYTHONPATH="$PLATFORM_REPO/data-platform/sqlmodel-workspace/sqlmodel-framework/src:$PYTHONPATH" \
    uv run python "$PLATFORM_REPO/data-platform/sqlmodel-workspace/sqlmodel-framework/scripts/deploy_datakit.py" \
        datakits/datakit_pagila_source \
        --target-type postgres \
        --host localhost \
        --port 15444 \
        --database datakit_tests \
        --user test_user \
        --validate
    log_success "Pagila SQLModel Basic integration test passed"

    log_success "All integration tests passed! 🎉"
}

# Main execution
main() {
    print_banner

    bootstrap_sandbox
    echo
    run_integration_tests
    echo

    # Cleanup happens automatically via trap
}

# Run main function
main "$@"