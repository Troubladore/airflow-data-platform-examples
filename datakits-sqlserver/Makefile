# Makefile for SQL Server Datakit Stack
# ======================================
# Orchestrates all three layers:
# - Layer 1: Platform (from main repo)
# - Layer 2: Datakits (build and push here)
# - Layer 3: Warehouse (deploy here)

.PHONY: help all build push deploy clean

# Configuration
REGISTRY_URL ?= registry.localhost
PLATFORM_REPO := ../../airflow-data-platform
VERSION := 0.1.0

# Image names
LAYER1_SIDECAR := $(REGISTRY_URL)/platform/kerberos-sidecar:$(VERSION)
LAYER1_AIRFLOW := $(REGISTRY_URL)/platform/astronomer-kerberos:$(VERSION)
LAYER2_SOURCE := $(REGISTRY_URL)/datakits/sqlserver-source:$(VERSION)
LAYER2_BRONZE := $(REGISTRY_URL)/datakits/sqlserver-bronze:$(VERSION)

help: ## Show this help message
	@echo "SQL Server Datakit Full Stack Deployment"
	@echo "========================================"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
	@echo ""
	@echo "Deployment Order:"
	@echo "  1. make layer1-build  # Build platform images"
	@echo "  2. make layer1-push   # Push to registry"
	@echo "  3. make layer2-build  # Build datakit images"
	@echo "  4. make layer2-push   # Push to registry"
	@echo "  5. make layer3-deploy # Deploy warehouse"
	@echo "  6. make deploy        # Start full stack"

# ==========================================
# LAYER 1: Platform (Airflow + Kerberos)
# ==========================================

layer1-build: ## Build Layer 1 platform images
	@echo "Building Layer 1 Platform images..."
	cd $(PLATFORM_REPO)/kerberos-astronomer && \
		docker build -f Dockerfile.kerberos-sidecar -t kerberos-sidecar:$(VERSION) . && \
		docker build -f Dockerfile.astronomer-kerberos -t astronomer-kerberos:$(VERSION) .
	@echo "✓ Layer 1 images built"

layer1-push: ## Push Layer 1 images to registry
	@echo "Pushing Layer 1 to registry $(REGISTRY_URL)..."
	docker tag kerberos-sidecar:$(VERSION) $(LAYER1_SIDECAR)
	docker tag astronomer-kerberos:$(VERSION) $(LAYER1_AIRFLOW)
	docker push $(LAYER1_SIDECAR)
	docker push $(LAYER1_AIRFLOW)
	@echo "✓ Layer 1 images pushed to registry"

layer1-status: ## Check Layer 1 images in registry
	@echo "Checking Layer 1 images in registry..."
	@docker pull $(LAYER1_SIDECAR) >/dev/null 2>&1 && echo "✓ Sidecar: $(LAYER1_SIDECAR)" || echo "✗ Sidecar not found"
	@docker pull $(LAYER1_AIRFLOW) >/dev/null 2>&1 && echo "✓ Airflow: $(LAYER1_AIRFLOW)" || echo "✗ Airflow not found"

# ==========================================
# LAYER 2: Datakits (Source & Bronze)
# ==========================================

layer2-build: layer1-status ## Build Layer 2 datakit images
	@echo "Building Layer 2 Datakit images..."
	# Build source connector
	docker build \
		--build-arg REGISTRY_URL=$(REGISTRY_URL) \
		-f datakit_sqlserver_source/Dockerfile \
		-t sqlserver-source:$(VERSION) \
		datakit_sqlserver_source
	# Build bronze processor
	docker build \
		--build-arg REGISTRY_URL=$(REGISTRY_URL) \
		-f datakit_sqlserver_bronze_kerberos/Dockerfile \
		-t sqlserver-bronze:$(VERSION) \
		datakit_sqlserver_bronze_kerberos
	@echo "✓ Layer 2 images built"

layer2-push: ## Push Layer 2 images to registry
	@echo "Pushing Layer 2 to registry $(REGISTRY_URL)..."
	docker tag sqlserver-source:$(VERSION) $(LAYER2_SOURCE)
	docker tag sqlserver-bronze:$(VERSION) $(LAYER2_BRONZE)
	docker push $(LAYER2_SOURCE)
	docker push $(LAYER2_BRONZE)
	@echo "✓ Layer 2 images pushed to registry"

layer2-status: ## Check Layer 2 images in registry
	@echo "Checking Layer 2 images in registry..."
	@docker pull $(LAYER2_SOURCE) >/dev/null 2>&1 && echo "✓ Source: $(LAYER2_SOURCE)" || echo "✗ Source not found"
	@docker pull $(LAYER2_BRONZE) >/dev/null 2>&1 && echo "✓ Bronze: $(LAYER2_BRONZE)" || echo "✗ Bronze not found"

# ==========================================
# LAYER 3: Warehouse Deployment
# ==========================================

layer3-deploy: ## Deploy Layer 3 warehouse
	@echo "Deploying Layer 3 Warehouse..."
	docker-compose -f layer3-warehouse/docker-compose.warehouse.yml up -d
	@echo "Waiting for warehouse initialization..."
	@sleep 10
	@echo "✓ Layer 3 warehouse deployed"

layer3-status: ## Check Layer 3 warehouse status
	@echo "Checking Layer 3 warehouse status..."
	@docker-compose -f layer3-warehouse/docker-compose.warehouse.yml ps

layer3-logs: ## View Layer 3 warehouse logs
	docker-compose -f layer3-warehouse/docker-compose.warehouse.yml logs -f

# ==========================================
# Full Stack Deployment
# ==========================================

build: layer1-build layer2-build ## Build all layers locally

push: layer1-push layer2-push ## Push all layers to registry

pull-all: ## Pull all required images from registry
	@echo "Pulling all images from registry..."
	docker pull $(LAYER1_SIDECAR)
	docker pull $(LAYER1_AIRFLOW)
	docker pull $(LAYER2_SOURCE)
	docker pull $(LAYER2_BRONZE)
	@echo "✓ All images pulled"

deploy: layer3-deploy ## Deploy full stack with all layers
	@echo "Deploying full stack..."
	# Update .env with registry URL
	@echo "REGISTRY_URL=$(REGISTRY_URL)" > .env.deploy
	@cat .env.template >> .env.deploy
	# Deploy with registry images
	docker-compose \
		--env-file .env.deploy \
		-f docker-compose.full-stack.yml \
		up -d
	@echo "✓ Full stack deployed"
	@echo ""
	@echo "Access points:"
	@echo "  Airflow UI: http://localhost:8080 (admin/admin)"
	@echo "  Bronze DB:  postgresql://localhost:5432/bronze"
	@echo "  Silver DB:  postgresql://localhost:5433/silver"
	@echo "  Gold DB:    postgresql://localhost:5434/gold"

status: ## Check status of all layers
	@echo "=== Layer Status Check ==="
	@echo ""
	@echo "Layer 1 (Platform):"
	@make layer1-status
	@echo ""
	@echo "Layer 2 (Datakits):"
	@make layer2-status
	@echo ""
	@echo "Layer 3 (Warehouse):"
	@make layer3-status
	@echo ""
	@echo "Full Stack:"
	@docker-compose -f docker-compose.full-stack.yml ps

logs: ## View logs from all services
	docker-compose -f docker-compose.full-stack.yml logs -f

stop: ## Stop all services
	docker-compose -f docker-compose.full-stack.yml down
	docker-compose -f layer3-warehouse/docker-compose.warehouse.yml down

clean: stop ## Clean up everything (including volumes)
	docker-compose -f docker-compose.full-stack.yml down -v
	docker-compose -f layer3-warehouse/docker-compose.warehouse.yml down -v
	@echo "✓ All services and volumes cleaned"

# ==========================================
# Testing
# ==========================================

test-connection: ## Test SQL Server connection through datakit
	docker-compose -f docker-compose.full-stack.yml \
		exec datakit-sqlserver-bronze \
		datakit-sqlserver test-connection

test-discover: ## Discover tables in SQL Server
	docker-compose -f docker-compose.full-stack.yml \
		exec datakit-sqlserver-bronze \
		datakit-sqlserver discover

test-ingest: ## Test ingestion of a single table
	docker-compose -f docker-compose.full-stack.yml \
		exec datakit-sqlserver-bronze \
		datakit-sqlserver ingest-table Customer

# ==========================================
# Development
# ==========================================

dev-mock: ## Start mock SQL Server for development
	docker-compose -f examples/docker-compose.mock.yml up -d
	@echo "Mock SQL Server started at localhost:1433"

dev-shell: ## Get shell in bronze datakit container
	docker-compose -f docker-compose.full-stack.yml \
		exec datakit-sqlserver-bronze /bin/bash

# ==========================================
# Registry Management
# ==========================================

registry-start: ## Start local registry
	cd $(PLATFORM_REPO)/prerequisites/traefik-registry && \
		docker-compose up -d registry
	@echo "Registry available at $(REGISTRY_URL)"

registry-list: ## List images in registry
	@echo "Images in registry $(REGISTRY_URL):"
	@curl -s http://$(REGISTRY_URL)/v2/_catalog | jq .

# ==========================================
# Documentation
# ==========================================

diagram: ## Generate architecture diagram
	@echo "Generating architecture diagram..."
	@echo ""
	@echo "┌─────────────────────────────────────────────────────┐"
	@echo "│                    LAYER 1: PLATFORM                 │"
	@echo "│  ┌──────────────┐        ┌──────────────────────┐   │"
	@echo "│  │   Kerberos   │───────▶│  Astronomer Airflow  │   │"
	@echo "│  │   Sidecar    │        │   (with Kerberos)    │   │"
	@echo "│  └──────────────┘        └──────────────────────┘   │"
	@echo "│         ▲                           │                │"
	@echo "└─────────┼───────────────────────────┼────────────────┘"
	@echo "          │     Registry Images       │"
	@echo "┌─────────┼───────────────────────────┼────────────────┐"
	@echo "│         ▼                           ▼                │"
	@echo "│                    LAYER 2: DATAKITS                 │"
	@echo "│  ┌──────────────┐        ┌──────────────────────┐   │"
	@echo "│  │  SQL Server  │───────▶│   Bronze Processor   │   │"
	@echo "│  │   Source     │        │    (with transform)   │   │"
	@echo "│  └──────────────┘        └──────────────────────┘   │"
	@echo "│                                     │                │"
	@echo "└─────────────────────────────────────┼────────────────┘"
	@echo "                                      │"
	@echo "┌─────────────────────────────────────┼────────────────┐"
	@echo "│                                     ▼                │"
	@echo "│                   LAYER 3: WAREHOUSE                 │"
	@echo "│  ┌──────────┐    ┌──────────┐    ┌──────────┐      │"
	@echo "│  │  Bronze  │───▶│  Silver  │───▶│   Gold   │      │"
	@echo "│  │   Store  │    │   Store  │    │   Store  │      │"
	@echo "│  └──────────┘    └──────────┘    └──────────┘      │"
	@echo "└──────────────────────────────────────────────────────┘"