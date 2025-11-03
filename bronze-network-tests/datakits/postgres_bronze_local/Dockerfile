FROM python:3.11-slim

# Install PostgreSQL client libraries
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    netcat-traditional \
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

# Default environment variables for local testing
ENV POSTGRES_HOST=host.docker.internal
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=pagila
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

# Default command
CMD ["python", "extract.py"]