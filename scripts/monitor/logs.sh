#!/bin/bash
# Script xem logs của hệ thống

SERVICE=${1:-""}

if [ -z "$SERVICE" ]; then
    echo "📊 Viewing logs for all services..."
    echo "Usage: ./scripts/monitor/logs.sh [service_name]"
    echo ""
    echo "Available services:"
    echo "  - market_data_service"
    echo "  - market_analyzer_service"
    echo "  - price_service"
    echo "  - signal_service"
    echo "  - notification_service"
    echo "  - mongodb"
    echo "  - redis"
    echo ""
    echo "Showing all services logs (Ctrl+C to exit)..."
    docker-compose logs -f
else
    echo "📊 Viewing logs for $SERVICE..."
    docker-compose logs -f "$SERVICE"
fi

