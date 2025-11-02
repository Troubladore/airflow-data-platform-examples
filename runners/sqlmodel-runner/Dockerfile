# SQLModel Runner - Pre-built image for Bronze/Silver/Gold transformations
# This runner includes all dependencies needed for temporal table operations
# Code is mounted at runtime, not baked into the image

ARG ASTRONOMER_VERSION=11.10.0-python-3.11
ARG ASTRONOMER_REGISTRY=quay.io/astronomer/ap-airflow

FROM ${ASTRONOMER_REGISTRY}:${ASTRONOMER_VERSION}

USER root

# Install system dependencies for PostgreSQL and Kerberos
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    krb5-user \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch to astro user for Python packages
USER astro

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install sqlmodel-framework from sibling repo (will be from artifactory in production)
# For now, we'll install the dependencies that would come with it
RUN pip install --no-cache-dir \
    sqlmodel \
    psycopg[binary,pool] \
    pandas>=2.0.0 \
    openpyxl \
    python-dotenv \
    pydantic>=2.0.0 \
    alembic \
    rich \
    typer

# Set up environment for mounted code
ENV PYTHONPATH=/app/src:/app/lib \
    KRB5_CONFIG=/etc/krb5.conf \
    KRB5CCNAME=/var/krb5/cache/ccache

# Create mount points for code and configuration
RUN mkdir -p /app/src /app/config /app/lib /var/krb5/cache

# Default working directory
WORKDIR /app

# Entry point expects mounted code at /app/src/main.py
# Can be overridden in KubernetesPodOperator
ENTRYPOINT ["python"]
CMD ["/app/src/main.py"]