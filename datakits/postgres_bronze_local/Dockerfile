FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install framework from git
RUN pip install --no-cache-dir git+https://github.com/Troubladore/airflow-data-platform.git@main#subdirectory=sqlmodel-framework

# Copy source code
COPY src/ src/

# Create data directory
RUN mkdir -p /data/bronze

# Set Python path
ENV PYTHONPATH=/app

# Run the extraction
CMD ["python", "src/extract.py"]