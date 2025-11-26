#!/bin/bash
# Script test kết nối giữa các services

echo "🔍 Testing Service Connections"
echo "============================="
echo ""

# Test MongoDB
echo "🗄️  Testing MongoDB..."
if docker-compose exec -T mongodb mongosh --quiet --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo "✅ MongoDB: Connected"
    
    # Test database access
    DB_TEST=$(docker-compose exec -T mongodb mongosh --quiet --eval "db = db.getSiblingDB('market'); db.getName()" 2>/dev/null)
    if [ ! -z "$DB_TEST" ]; then
        echo "✅ MongoDB Database: Accessible"
    else
        echo "⚠️  MongoDB Database: Access issue"
    fi
else
    echo "❌ MongoDB: Connection failed"
fi
echo ""

# Test Redis
echo "📮 Testing Redis..."
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis: Connected"
    
    # Test stream access
    STREAM_TEST=$(docker-compose exec -T redis redis-cli KEYS "events:*" 2>/dev/null | head -1)
    if [ ! -z "$STREAM_TEST" ]; then
        echo "✅ Redis Streams: Accessible"
    else
        echo "ℹ️  Redis Streams: No streams yet (normal if no events)"
    fi
else
    echo "❌ Redis: Connection failed"
fi
echo ""

# Test Services
echo "🔧 Testing Services..."
SERVICES=("market_data_service" "market_analyzer_service" "price_service" "signal_service" "notification_service")

for service in "${SERVICES[@]}"; do
    if docker-compose ps "$service" | grep -q "Up"; then
        # Check if service can connect to MongoDB
        if docker-compose exec -T "$service" python -c "
import sys
sys.path.insert(0, '/app')
try:
    from shared.database import get_database
    db = get_database()
    db.admin.command('ping')
    sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; then
            echo "✅ $service: Running & MongoDB connected"
        else
            echo "⚠️  $service: Running but MongoDB connection issue"
        fi
    else
        echo "❌ $service: Not running"
    fi
done

echo ""
echo "✅ Connection test completed!"

