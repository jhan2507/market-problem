FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules and service code
COPY shared/ ./shared/
COPY services/market_analyzer_service/ ./services/market_analyzer_service/

# Set Python path
ENV PYTHONPATH=/app

# Run service
CMD ["python", "services/market_analyzer_service/main.py"]

