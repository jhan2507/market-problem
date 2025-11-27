#!/bin/bash
# Basic load testing script

SERVICE=${1:-market_data_service}
ENDPOINT=${2:-/health}
CONCURRENT=${3:-10}
REQUESTS=${4:-100}

echo "📊 Load Testing"
echo "Service: $SERVICE"
echo "Endpoint: $ENDPOINT"
echo "Concurrent requests: $CONCURRENT"
echo "Total requests: $REQUESTS"
echo ""

# Get service port
case $SERVICE in
    market_data_service)
        PORT=8000
        ;;
    market_analyzer_service)
        PORT=8001
        ;;
    price_service)
        PORT=8002
        ;;
    signal_service)
        PORT=8003
        ;;
    notification_service)
        PORT=8004
        ;;
    *)
        echo "Unknown service: $SERVICE"
        exit 1
        ;;
esac

URL="http://localhost:${PORT}${ENDPOINT}"

echo "Testing: $URL"
echo ""

# Use ab (Apache Bench) if available, otherwise use curl
if command -v ab &> /dev/null; then
    ab -n $REQUESTS -c $CONCURRENT $URL
elif command -v curl &> /dev/null; then
    echo "Using curl for basic testing..."
    echo ""
    
    SUCCESS=0
    FAILED=0
    TOTAL_TIME=0
    
    for i in $(seq 1 $REQUESTS); do
        START=$(date +%s%N)
        if curl -s -f $URL > /dev/null 2>&1; then
            SUCCESS=$((SUCCESS + 1))
        else
            FAILED=$((FAILED + 1))
        fi
        END=$(date +%s%N)
        DURATION=$((END - START))
        TOTAL_TIME=$((TOTAL_TIME + DURATION))
    done
    
    AVG_TIME=$(echo "scale=2; $TOTAL_TIME / $REQUESTS / 1000000" | bc)
    
    echo "Results:"
    echo "  Success: $SUCCESS"
    echo "  Failed: $FAILED"
    echo "  Average time: ${AVG_TIME}ms"
else
    echo "Neither ab nor curl found. Please install Apache Bench or curl."
    exit 1
fi

