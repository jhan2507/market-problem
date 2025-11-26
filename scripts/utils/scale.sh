#!/bin/bash
# Script scale services (tăng/giảm số lượng instances)

SERVICE=$1
REPLICAS=${2:-1}

if [ -z "$SERVICE" ]; then
    echo "❌ Usage: ./scripts/scale.sh <service_name> [replicas]"
    echo ""
    echo "Available services:"
    echo "  - market_data_service"
    echo "  - market_analyzer_service"
    echo "  - price_service"
    echo "  - signal_service"
    echo "  - notification_service"
    echo ""
    echo "Example: ./scripts/scale.sh price_service 3"
    exit 1
fi

echo "📈 Scaling $SERVICE to $REPLICAS instance(s)..."

# Note: Docker Compose v2+ supports scale
docker-compose up -d --scale "$SERVICE=$REPLICAS" --no-recreate "$SERVICE"

if [ $? -eq 0 ]; then
    echo "✅ $SERVICE scaled to $REPLICAS instance(s)"
    echo ""
    echo "📊 Current status:"
    docker-compose ps "$SERVICE"
else
    echo "❌ Failed to scale $SERVICE"
    exit 1
fi

