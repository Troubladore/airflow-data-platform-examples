# Layer 2: Source Datakit Image
# ==============================
# Lightweight connector for SQL Server source system

ARG REGISTRY_URL=registry.localhost
FROM ${REGISTRY_URL}/platform/astronomer-kerberos:latest

USER root

# Source-specific tools
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

USER astro

# Copy source connector code
COPY --chown=astro:astro pyproject.toml /opt/datakit/
COPY --chown=astro:astro src/ /opt/datakit/src/

WORKDIR /opt/datakit

# Install minimal dependencies
RUN pip install --no-cache-dir -e .

# Environment
ENV DATAKIT_TYPE="source"
ENV DATAKIT_SOURCE="sqlserver"

# Health check for source connectivity
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "from src.connector import test_connection; exit(0 if test_connection() else 1)"

CMD ["python", "-m", "src.main"]