FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY parse_resorts.py .

# Create output directory
RUN mkdir -p /app/output

# Set the entrypoint
ENTRYPOINT ["python", "parse_resorts.py"]
