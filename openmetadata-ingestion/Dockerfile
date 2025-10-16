# OpenMetadata Ingestion Example
# ===============================
# Astronomer Airflow project for programmatic metadata ingestion
#
# This Dockerfile extends Astronomer Runtime with OpenMetadata Python SDK
# for running metadata ingestion DAGs.

FROM quay.io/astronomer/astro-runtime:11.10.0-base

# Install OpenMetadata Ingestion SDK
# This provides the Python API for programmatic metadata ingestion
USER root
RUN pip install --no-cache-dir \
    openmetadata-ingestion[postgres,mssql]==1.2.0

# For SQL Server with Kerberos
# Install Microsoft ODBC drivers and Kerberos client
RUN apt-get update && apt-get install -y \
    krb5-user \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft SQL Server ODBC Driver 18
# Note: In corporate environments, this may need to pull from Artifactory
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

USER astro
