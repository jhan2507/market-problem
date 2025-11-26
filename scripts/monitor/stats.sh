#!/bin/bash
# Script xem thống kê hệ thống

echo "📊 System Statistics"
echo "===================="
echo ""

# MongoDB Statistics
echo "🗄️  MongoDB Statistics:"
echo "----------------------"
docker-compose exec -T mongodb mongosh --quiet --eval "
    db = db.getSiblingDB('market');
    
    print('Collections:');
    print('  market_data:', db.market_data.countDocuments(), 'documents');
    print('  analysis:', db.analysis.countDocuments(), 'documents');
    print('  signals:', db.signals.countDocuments(), 'documents');
    print('  price_updates:', db.price_updates.countDocuments(), 'documents');
    print('  logs:', db.logs.countDocuments(), 'documents');
    print('');
    
    print('Latest Data:');
    latest_market = db.market_data.find().sort({timestamp: -1}).limit(1).toArray();
    if (latest_market.length > 0) {
        print('  Last market data:', latest_market[0].timestamp);
    }
    
    latest_analysis = db.analysis.find().sort({timestamp: -1}).limit(1).toArray();
    if (latest_analysis.length > 0) {
        print('  Last analysis:', latest_analysis[0].timestamp);
        print('  Sentiment:', latest_analysis[0].sentiment);
        print('  Trend strength:', latest_analysis[0].trend_strength);
    }
    
    latest_signal = db.signals.find().sort({timestamp: -1}).limit(1).toArray();
    if (latest_signal.length > 0) {
        print('  Last signal:', latest_signal[0].timestamp);
        print('  Asset:', latest_signal[0].asset);
        print('  Type:', latest_signal[0].type);
        print('  Score:', latest_signal[0].score);
    }
    
    print('');
    print('Signal Statistics:');
    long_count = db.signals.countDocuments({type: 'LONG'});
    short_count = db.signals.countDocuments({type: 'SHORT'});
    high_conf = db.signals.countDocuments({confidence: 'HIGH'});
    medium_conf = db.signals.countDocuments({confidence: 'MEDIUM'});
    print('  LONG signals:', long_count);
    print('  SHORT signals:', short_count);
    print('  HIGH confidence:', high_conf);
    print('  MEDIUM confidence:', medium_conf);
"

echo ""

# Redis Statistics
echo "📮 Redis Statistics:"
echo "-------------------"
docker-compose exec -T redis redis-cli --raw KEYS "events:*" | while read key; do
    if [ ! -z "$key" ]; then
        count=$(docker-compose exec -T redis redis-cli XLEN "$key" 2>/dev/null)
        echo "  $key: $count messages"
    fi
done

echo ""

# Container Statistics
echo "🐳 Container Statistics:"
echo "-----------------------"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

echo ""
echo "💡 View detailed stats: docker stats"

