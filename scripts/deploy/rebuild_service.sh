#!/bin/bash
# Script rebuild và restart một service cụ thể với code mới

if [ -z "$1" ]; then
    echo "❌ Usage: ./scripts/deploy/rebuild_service.sh <service_name>"
    echo ""
    echo "Available services:"
    echo "  - market_data_service"
    echo "  - market_analyzer_service"
    echo "  - price_service"
    echo "  - signal_service"
    echo "  - notification_service"
    exit 1
fi

SERVICE=$1

echo "🔨 Rebuilding $SERVICE..."

# Build lại image cho service
echo "📦 Building Docker image for $SERVICE..."
docker-compose build --no-cache "$SERVICE"

if [ $? -ne 0 ]; then
    echo "❌ Failed to build $SERVICE"
    exit 1
fi

# Stop service
echo "🛑 Stopping $SERVICE..."
docker-compose stop "$SERVICE"

# Remove container cũ (nếu có)
echo "🗑️  Removing old container..."
docker-compose rm -f "$SERVICE"

# Start lại với image mới
echo "🚀 Starting $SERVICE with new image..."
docker-compose up -d "$SERVICE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ $SERVICE rebuilt and restarted successfully!"
    echo ""
    echo "📊 View logs: ./scripts/monitor/logs.sh $SERVICE"
    echo "📈 Check status: docker-compose ps $SERVICE"
else
    echo "❌ Failed to restart $SERVICE"
    exit 1
fi

