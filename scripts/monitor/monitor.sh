#!/bin/bash
# Script monitor hệ thống real-time

echo "📊 Real-time System Monitor"
echo "=========================="
echo "Press Ctrl+C to exit"
echo ""

# Function để hiển thị stats
show_stats() {
    clear
    echo "📊 Real-time System Monitor - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================================"
    echo ""
    
    # Container status
    echo "🐳 Container Status:"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    
    # MongoDB stats
    echo "🗄️  MongoDB:"
    docker-compose exec -T mongodb mongosh --quiet --eval "
        db = db.getSiblingDB('market');
        print('  Documents:');
        print('    market_data:', db.market_data.countDocuments());
        print('    analysis:', db.analysis.countDocuments());
        print('    signals:', db.signals.countDocuments());
        print('    price_updates:', db.price_updates.countDocuments());
    " 2>/dev/null || echo "  ❌ Not accessible"
    echo ""
    
    # Redis stats
    echo "📮 Redis:"
    docker-compose exec -T redis redis-cli INFO stats | grep -E "total_commands_processed|total_connections_received" 2>/dev/null || echo "  ❌ Not accessible"
    echo ""
    
    # Recent signals
    echo "🎯 Recent Signals (last 5):"
    docker-compose exec -T mongodb mongosh --quiet --eval "
        db = db.getSiblingDB('market');
        db.signals.find().sort({timestamp: -1}).limit(5).forEach(function(s) {
            print('  ' + s.timestamp + ' | ' + s.asset + ' | ' + s.type + ' | Score: ' + s.score);
        });
    " 2>/dev/null || echo "  No signals found"
    echo ""
    
    # Service health
    echo "🏥 Service Health:"
    for service in market_data_service market_analyzer_service price_service signal_service notification_service; do
        if docker-compose ps "$service" | grep -q "Up"; then
            ERROR_COUNT=$(docker-compose logs --tail=20 "$service" 2>&1 | grep -i "error\|exception\|failed" | wc -l)
            if [ "$ERROR_COUNT" -gt 0 ]; then
                echo "  ⚠️  $service: $ERROR_COUNT recent errors"
            else
                echo "  ✅ $service: Healthy"
            fi
        else
            echo "  ❌ $service: Not running"
        fi
    done
}

# Monitor loop
while true; do
    show_stats
    sleep 5
done

