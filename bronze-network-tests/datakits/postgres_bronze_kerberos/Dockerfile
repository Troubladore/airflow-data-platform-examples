FROM python:3.11-slim

# Install Kerberos client libraries and PostgreSQL client
RUN apt-get update && apt-get install -y \
    krb5-user \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy extraction script
COPY src/extract.py .

# Create Bronze output directory
RUN mkdir -p /data/bronze

# Copy Kerberos configuration from host (will be mounted)
# Expected mounts:
# - /etc/krb5.conf (Kerberos config)
# - /tmp/krb5cc_* or credential cache directory

# Environment variables for Kerberos
ENV KRB5_CONFIG=/etc/krb5.conf

# Default command
CMD ["python", "extract.py"]