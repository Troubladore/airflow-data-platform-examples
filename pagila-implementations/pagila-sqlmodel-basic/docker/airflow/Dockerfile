# Platform-compatible Airflow image with Pagila transformation modules
FROM apache/airflow:2.10.4-python3.12

# Switch to root to install system dependencies
USER root

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Install Python dependencies for transformation modules
COPY docker/airflow/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy transformation modules into the image
COPY --chown=airflow:root datakits/ /opt/pagila/datakits/
COPY --chown=airflow:root pyproject.toml /opt/pagila/pyproject.toml

# Set Python path to include transformation modules
ENV PYTHONPATH="/opt/pagila:$PYTHONPATH"

# Create directories for Airflow
RUN mkdir -p /opt/airflow/dags /opt/airflow/logs /opt/airflow/plugins

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8080/health || exit 1