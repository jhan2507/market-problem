#!/bin/bash
# Script restart hệ thống

echo "🔄 Restarting Crypto Market Monitoring System..."

docker-compose restart

echo ""
echo "✅ System restarted successfully!"
echo ""
echo "📊 View logs: ./scripts/monitor/logs.sh"

