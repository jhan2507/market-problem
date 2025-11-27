FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules and service code
COPY shared/ ./shared/
COPY services/market_data_service/ ./services/market_data_service/

# Set Python path
ENV PYTHONPATH=/app

# Expose HTTP port for health checks
EXPOSE 8000

# Run service
CMD ["python", "services/market_data_service/main.py"]

