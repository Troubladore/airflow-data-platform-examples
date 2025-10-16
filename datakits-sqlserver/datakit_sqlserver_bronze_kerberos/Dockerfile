# Layer 2: Bronze Datakit Image
# ==============================
# Built on top of Layer 1 platform base image

ARG REGISTRY_URL=registry.localhost
FROM ${REGISTRY_URL}/platform/astronomer-kerberos:latest

USER root

# Install additional dependencies for Bronze processing
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create datakit directory
RUN mkdir -p /opt/datakit && chown astro:astro /opt/datakit

USER astro

# Copy datakit source code
COPY --chown=astro:astro pyproject.toml /opt/datakit/
COPY --chown=astro:astro src/ /opt/datakit/src/

# Install datakit
WORKDIR /opt/datakit
RUN pip install --no-cache-dir -e .

# Set environment variables
ENV PYTHONPATH="/opt/datakit/src:${PYTHONPATH}"
ENV DATAKIT_TYPE="bronze"
ENV DATAKIT_SOURCE="sqlserver"

# Default command
CMD ["datakit-sqlserver", "--help"]