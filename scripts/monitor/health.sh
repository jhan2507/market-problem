#!/bin/bash
# Script kiểm tra health của từng service

echo "🏥 Health Check"
echo "=============="
echo ""

check_service() {
    SERVICE=$1
    if docker-compose ps "$SERVICE" | grep -q "Up"; then
        # Kiểm tra logs gần đây có lỗi không
        ERROR_COUNT=$(docker-compose logs --tail=50 "$SERVICE" 2>&1 | grep -i "error\|exception\|failed" | wc -l)
        if [ "$ERROR_COUNT" -gt 0 ]; then
            echo "⚠️  $SERVICE: Running but has $ERROR_COUNT recent errors"
        else
            echo "✅ $SERVICE: Healthy"
        fi
    else
        echo "❌ $SERVICE: Not running"
    fi
}

# Kiểm tra từng service
check_service "mongodb"
check_service "redis"
check_service "market_data_service"
check_service "market_analyzer_service"
check_service "price_service"
check_service "signal_service"
check_service "notification_service"

echo ""

# Kiểm tra kết nối MongoDB
echo "🔍 MongoDB Connection Test:"
if docker-compose exec -T mongodb mongosh --quiet --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo "✅ MongoDB connection: OK"
else
    echo "❌ MongoDB connection: FAILED"
fi

# Kiểm tra kết nối Redis
echo "🔍 Redis Connection Test:"
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis connection: OK"
else
    echo "❌ Redis connection: FAILED"
fi

echo ""
echo "📊 Recent Errors (last 50 lines per service):"
echo "----------------------------------------------"
for service in market_data_service market_analyzer_service price_service signal_service notification_service; do
    ERRORS=$(docker-compose logs --tail=50 "$service" 2>&1 | grep -i "error\|exception\|failed" | head -3)
    if [ ! -z "$ERRORS" ]; then
        echo ""
        echo "⚠️  $service:"
        echo "$ERRORS"
    fi
done

