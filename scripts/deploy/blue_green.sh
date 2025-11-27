#!/bin/bash
# Blue-Green deployment script

set -e

ENVIRONMENT=${1:-production}
SERVICE=${2:-all}

echo "🔄 Blue-Green Deployment"
echo "Environment: $ENVIRONMENT"
echo "Service: $SERVICE"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

deploy_service() {
    SERVICE_NAME=$1
    GREEN_NAME="${SERVICE_NAME}_green"
    BLUE_NAME="${SERVICE_NAME}_blue"
    
    echo -e "${BLUE}Deploying $SERVICE_NAME...${NC}"
    
    # Check which version is currently active
    if docker-compose ps | grep -q "${SERVICE_NAME}_green"; then
        CURRENT="green"
        NEW="blue"
        CURRENT_NAME=$GREEN_NAME
        NEW_NAME=$BLUE_NAME
    else
        CURRENT="blue"
        NEW="green"
        CURRENT_NAME=$BLUE_NAME
        NEW_NAME=$GREEN_NAME
    fi
    
    echo -e "Current active: ${CURRENT}"
    echo -e "Deploying to: ${NEW}"
    
    # Build new version
    echo -e "${YELLOW}Building new version...${NC}"
    docker-compose build $SERVICE_NAME
    
    # Start new version with different name
    echo -e "${YELLOW}Starting new version...${NC}"
    docker-compose -f docker-compose.yml -f docker-compose.${ENVIRONMENT}.yml \
        --project-name market_${NEW} \
        up -d --scale ${SERVICE_NAME}=0 ${SERVICE_NAME}
    
    # Wait for health check
    echo -e "${YELLOW}Waiting for health check...${NC}"
    sleep 10
    
    # Check health
    PORT=$(docker-compose port ${SERVICE_NAME} 8000 2>/dev/null | cut -d: -f2 || echo "")
    if [ -n "$PORT" ]; then
        if curl -f http://localhost:$PORT/health > /dev/null 2>&1; then
            echo -e "${GREEN}New version is healthy${NC}"
        else
            echo -e "${YELLOW}Health check failed, rolling back...${NC}"
            docker-compose -f docker-compose.yml -f docker-compose.${ENVIRONMENT}.yml \
                --project-name market_${NEW} \
                down
            exit 1
        fi
    fi
    
    # Switch traffic (stop old, rename new)
    echo -e "${YELLOW}Switching traffic...${NC}"
    docker-compose stop $SERVICE_NAME
    docker-compose rm -f $SERVICE_NAME
    
    # Start new as main
    docker-compose -f docker-compose.yml -f docker-compose.${ENVIRONMENT}.yml \
        up -d $SERVICE_NAME
    
    # Stop old version
    docker-compose -f docker-compose.yml -f docker-compose.${ENVIRONMENT}.yml \
        --project-name market_${CURRENT} \
        down
    
    echo -e "${GREEN}$SERVICE_NAME deployed successfully${NC}"
}

if [ "$SERVICE" == "all" ]; then
    SERVICES="market_data_service market_analyzer_service price_service signal_service notification_service"
    for svc in $SERVICES; do
        deploy_service $svc
    done
else
    deploy_service $SERVICE
fi

echo ""
echo -e "${GREEN}✅ Blue-Green deployment completed${NC}"

