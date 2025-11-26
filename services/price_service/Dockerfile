FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules and service code
COPY shared/ ./shared/
COPY services/price_service/ ./services/price_service/

# Set Python path
ENV PYTHONPATH=/app

# Run service
CMD ["python", "services/price_service/main.py"]

