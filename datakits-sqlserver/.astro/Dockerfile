# Astronomer-Native Dockerfile
# =============================
# Extends Astronomer's certified image with enterprise requirements

# Build arguments for flexibility
ARG ARTIFACTORY_URL=artifactory.company.com
ARG ASTRONOMER_VERSION=11.10.0
ARG PYTHON_VERSION=3.10

# Pull certified Astronomer image from your Artifactory
FROM ${ARTIFACTORY_URL}/astronomer-certified/ap-airflow:${ASTRONOMER_VERSION}-python-${PYTHON_VERSION}

# Switch to root for system packages
USER root

# Install Kerberos support (missing from base image)
RUN apt-get update && apt-get install -y \
    krb5-user \
    libkrb5-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install ODBC drivers for SQL Server (if not using pure Python)
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Microsoft ODBC Driver (optional - for better performance)
# Only if your security team has vetted it
# RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
#     && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
#     && apt-get update \
#     && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
#     && rm -rf /var/lib/apt/lists/*

# Switch back to astro user
USER astro

# Copy requirements first (for better caching)
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy DAGs and plugins
COPY --chown=astro:astro dags /usr/local/airflow/dags
COPY --chown=astro:astro plugins /usr/local/airflow/plugins

# Copy datakit configurations (not the code - that's in images)
COPY --chown=astro:astro datakit-config /usr/local/airflow/datakit-config

# Set environment variables for Astronomer platform
ENV AIRFLOW__ASTRONOMER__UPDATE_CHECK=false \
    AIRFLOW__CORE__LAZY_LOAD_PLUGINS=false \
    AIRFLOW__WEBSERVER__EXPOSE_CONFIG=false

# Environment variables for Kerberos
ENV KRB5_CONFIG=/etc/krb5.conf \
    KRB5CCNAME=/tmp/krb5cc

# Labels for Astronomer platform
LABEL io.astronomer.docker.airflow.version="${ASTRONOMER_VERSION}" \
      io.astronomer.docker.python.version="${PYTHON_VERSION}" \
      io.astronomer.docker.platform="self-hosted" \
      io.company.artifactory.source="${ARTIFACTORY_URL}"

# Health check (Astronomer handles this, but good to have)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD airflow db check || exit 1