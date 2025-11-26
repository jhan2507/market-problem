#!/bin/bash
# Script kiểm tra trạng thái hệ thống

echo "📈 System Status"
echo "================"
echo ""

# Kiểm tra containers
echo "🐳 Docker Containers:"
docker-compose ps
echo ""

# Kiểm tra MongoDB
echo "🗄️  MongoDB Status:"
if docker-compose exec -T mongodb mongosh --quiet --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo "✅ MongoDB is running"
    
    # Đếm documents trong collections
    echo ""
    echo "📊 Database Statistics:"
    docker-compose exec -T mongodb mongosh --quiet --eval "
        db = db.getSiblingDB('market');
        print('market_data:', db.market_data.countDocuments());
        print('analysis:', db.analysis.countDocuments());
        print('signals:', db.signals.countDocuments());
        print('price_updates:', db.price_updates.countDocuments());
        print('logs:', db.logs.countDocuments());
    "
else
    echo "❌ MongoDB is not accessible"
fi
echo ""

# Kiểm tra Redis
echo "📮 Redis Status:"
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
    
    # Đếm streams
    echo ""
    echo "📊 Redis Streams:"
    docker-compose exec -T redis redis-cli --raw KEYS "events:*" | while read key; do
        if [ ! -z "$key" ]; then
            count=$(docker-compose exec -T redis redis-cli XLEN "$key" 2>/dev/null)
            echo "  $key: $count messages"
        fi
    done
else
    echo "❌ Redis is not accessible"
fi
echo ""

# Kiểm tra services
echo "🔧 Services Status:"
services=("market_data_service" "market_analyzer_service" "price_service" "signal_service" "notification_service")

for service in "${services[@]}"; do
    if docker-compose ps "$service" | grep -q "Up"; then
        echo "✅ $service: Running"
    else
        echo "❌ $service: Not running"
    fi
done

echo ""
echo "💡 Tips:"
echo "  - View logs: ./scripts/logs.sh [service_name]"
echo "  - Restart service: docker-compose restart [service_name]"
echo "  - View detailed logs: docker-compose logs --tail=100 [service_name]"

