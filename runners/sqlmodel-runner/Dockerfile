# SQLModel Runner - Pre-built image for Bronze/Silver/Gold transformations
# This runner includes all dependencies needed for temporal table operations
# Code is mounted at runtime, not baked into the image

# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    pip install --no-cache-dir \
        sqlmodel \
        "psycopg[binary,pool]>=3.1.0" \
        pandas>=2.0.0 \
        openpyxl \
        python-dotenv \
        pydantic>=2.0.0 \
        alembic \
        rich \
        typer && \
    find /opt/venv -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name '*.pyc' -delete

# Stage 2: Final runtime image
FROM python:3.11-slim

USER root

# Install only runtime dependencies (no gcc/g++)
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    krb5-user \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set virtual environment path
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/src:/app/lib \
    KRB5_CONFIG=/etc/krb5.conf \
    KRB5CCNAME=/var/krb5/cache/ccache

# Create mount points for code and configuration
RUN mkdir -p /app/src /app/config /app/lib /var/krb5/cache

# Create a basic krb5.conf file (will be overridden by mounted config in production)
RUN echo '[libdefaults]\n\
    default_realm = EXAMPLE.COM\n\
    ticket_lifetime = 24h\n\
    renew_lifetime = 7d\n\
    forwardable = true\n\
[realms]\n\
    EXAMPLE.COM = {\n\
        kdc = kerberos.example.com\n\
        admin_server = kerberos.example.com\n\
    }\n\
[domain_realm]\n\
    .example.com = EXAMPLE.COM\n\
    example.com = EXAMPLE.COM' > /etc/krb5.conf

# Default working directory
WORKDIR /app

# Entry point expects mounted code at /app/src/main.py
# Can be overridden in KubernetesPodOperator
ENTRYPOINT ["python"]
CMD ["/app/src/main.py"]