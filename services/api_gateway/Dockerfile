FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules and service code
COPY shared/ ./shared/
COPY services/api_gateway/ ./services/api_gateway/

# Set Python path
ENV PYTHONPATH=/app

# Expose HTTP port
EXPOSE 8080

# Run service
CMD ["python", "services/api_gateway/main.py"]

