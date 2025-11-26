#!/bin/bash
# Script restart một service cụ thể

if [ -z "$1" ]; then
    echo "❌ Usage: ./scripts/restart_service.sh <service_name>"
    echo ""
    echo "Available services:"
    echo "  - market_data_service"
    echo "  - market_analyzer_service"
    echo "  - price_service"
    echo "  - signal_service"
    echo "  - notification_service"
    echo "  - mongodb"
    echo "  - redis"
    exit 1
fi

SERVICE=$1

echo "🔄 Restarting $SERVICE..."

docker-compose restart "$SERVICE"

if [ $? -eq 0 ]; then
    echo "✅ $SERVICE restarted successfully"
    echo ""
    echo "📊 View logs: ./scripts/monitor/logs.sh $SERVICE"
else
    echo "❌ Failed to restart $SERVICE"
    exit 1
fi

