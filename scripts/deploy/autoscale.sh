#!/bin/bash
# Auto-scaling script based on metrics

set -e

SERVICE=${1:-all}
MIN_REPLICAS=${2:-1}
MAX_REPLICAS=${3:-5}
CPU_THRESHOLD=${4:-70}
MEMORY_THRESHOLD=${5:-80}

echo "📈 Auto-scaling"
echo "Service: $SERVICE"
echo "Min replicas: $MIN_REPLICAS"
echo "Max replicas: $MAX_REPLICAS"
echo "CPU threshold: $CPU_THRESHOLD%"
echo "Memory threshold: $MEMORY_THRESHOLD%"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

get_service_metrics() {
    SERVICE_NAME=$1
    
    # Get CPU and memory usage from docker stats
    STATS=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemPerc}}" $(docker-compose ps -q $SERVICE_NAME) 2>/dev/null | head -1)
    
    if [ -z "$STATS" ]; then
        echo "0,0"
        return
    fi
    
    # Calculate average
    CPU_AVG=$(echo "$STATS" | awk -F',' '{sum+=$1; count++} END {print sum/count}')
    MEM_AVG=$(echo "$STATS" | awk -F',' '{sum+=$2; count++} END {print sum/count}')
    
    # Remove % sign and convert to number
    CPU_AVG=$(echo "$CPU_AVG" | sed 's/%//')
    MEM_AVG=$(echo "$MEM_AVG" | sed 's/%//')
    
    echo "${CPU_AVG},${MEM_AVG}"
}

scale_service() {
    SERVICE_NAME=$1
    CURRENT_REPLICAS=$(docker-compose ps $SERVICE_NAME | grep -c "Up" || echo "$MIN_REPLICAS")
    
    METRICS=$(get_service_metrics $SERVICE_NAME)
    CPU=$(echo $METRICS | cut -d',' -f1)
    MEM=$(echo $METRICS | cut -d',' -f2)
    
    echo "Service: $SERVICE_NAME"
    echo "Current replicas: $CURRENT_REPLICAS"
    echo "CPU usage: ${CPU}%"
    echo "Memory usage: ${MEM}%"
    
    # Determine scaling action
    NEW_REPLICAS=$CURRENT_REPLICAS
    
    # Scale up if CPU or memory is high
    if (( $(echo "$CPU > $CPU_THRESHOLD" | bc -l) )) || (( $(echo "$MEM > $MEMORY_THRESHOLD" | bc -l) )); then
        if [ $CURRENT_REPLICAS -lt $MAX_REPLICAS ]; then
            NEW_REPLICAS=$((CURRENT_REPLICAS + 1))
            echo -e "${YELLOW}Scaling UP to $NEW_REPLICAS replicas${NC}"
            docker-compose up -d --scale $SERVICE_NAME=$NEW_REPLICAS $SERVICE_NAME
        else
            echo "Already at max replicas ($MAX_REPLICAS)"
        fi
    # Scale down if CPU and memory are low
    elif (( $(echo "$CPU < $((CPU_THRESHOLD / 2))" | bc -l) )) && (( $(echo "$MEM < $((MEMORY_THRESHOLD / 2))" | bc -l) )); then
        if [ $CURRENT_REPLICAS -gt $MIN_REPLICAS ]; then
            NEW_REPLICAS=$((CURRENT_REPLICAS - 1))
            echo -e "${YELLOW}Scaling DOWN to $NEW_REPLICAS replicas${NC}"
            docker-compose up -d --scale $SERVICE_NAME=$NEW_REPLICAS $SERVICE_NAME
        else
            echo "Already at min replicas ($MIN_REPLICAS)"
        fi
    else
        echo -e "${GREEN}No scaling needed${NC}"
    fi
    
    echo ""
}

if [ "$SERVICE" == "all" ]; then
    SERVICES="market_data_service market_analyzer_service price_service signal_service notification_service"
    for svc in $SERVICES; do
        scale_service $svc
    done
else
    scale_service $SERVICE
fi

echo -e "${GREEN}✅ Auto-scaling check completed${NC}"

