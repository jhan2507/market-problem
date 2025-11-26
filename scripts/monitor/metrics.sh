#!/bin/bash
# Script xem metrics chi tiết của hệ thống

echo "📊 Detailed System Metrics"
echo "=========================="
echo ""

# Container metrics
echo "🐳 Container Metrics:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
echo ""

# MongoDB metrics
echo "🗄️  MongoDB Metrics:"
if docker-compose exec -T mongodb mongosh --quiet --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    docker-compose exec -T mongodb mongosh --quiet --eval "
        db = db.getSiblingDB('market');
        
        print('Collections:');
        db.getCollectionNames().forEach(function(name) {
            var count = db[name].countDocuments();
            var size = db[name].stats().size;
            print('  ' + name + ': ' + count + ' docs, ' + (size / 1024 / 1024).toFixed(2) + ' MB');
        });
        
        print('');
        print('Database Stats:');
        var stats = db.stats();
        print('  Data Size: ' + (stats.dataSize / 1024 / 1024).toFixed(2) + ' MB');
        print('  Storage Size: ' + (stats.storageSize / 1024 / 1024).toFixed(2) + ' MB');
        print('  Index Size: ' + (stats.indexSize / 1024 / 1024).toFixed(2) + ' MB');
    " 2>/dev/null
else
    echo "❌ MongoDB not accessible"
fi
echo ""

# Redis metrics
echo "📮 Redis Metrics:"
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    docker-compose exec -T redis redis-cli INFO stats | grep -E "total_commands_processed|total_connections_received|keyspace_hits|keyspace_misses" | while read line; do
        echo "  $line"
    done
    
    echo ""
    echo "  Streams:"
    docker-compose exec -T redis redis-cli --raw KEYS "events:*" | while read key; do
        if [ ! -z "$key" ]; then
            count=$(docker-compose exec -T redis redis-cli XLEN "$key" 2>/dev/null)
            echo "    $key: $count messages"
        fi
    done
else
    echo "❌ Redis not accessible"
fi
echo ""

# Service-specific metrics
echo "🔧 Service Metrics:"
SERVICES=("market_data_service" "market_analyzer_service" "price_service" "signal_service" "notification_service")

for service in "${SERVICES[@]}"; do
    if docker-compose ps "$service" | grep -q "Up"; then
        # Get container stats
        CONTAINER_ID=$(docker-compose ps -q "$service")
        if [ ! -z "$CONTAINER_ID" ]; then
            STATS=$(docker stats --no-stream --format "{{.CPUPerc}}\t{{.MemUsage}}" "$CONTAINER_ID")
            echo "  $service: $STATS"
        fi
    fi
done

echo ""
echo "💡 For real-time metrics: docker stats"

