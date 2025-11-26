#!/bin/bash
# Script deploy lên environment (staging/production)

set -e

ENVIRONMENT=${1:-""}
VERSION_FILE="../VERSION"
VERSION=$(cat "$VERSION_FILE" 2>/dev/null || echo "latest")
REGISTRY=${DOCKER_REGISTRY:-""}
IMAGE_PREFIX=${IMAGE_PREFIX:-"market"}

if [ -z "$ENVIRONMENT" ]; then
    echo "❌ Usage: ./scripts/deploy.sh <environment>"
    echo ""
    echo "Environments:"
    echo "  - staging"
    echo "  - production"
    exit 1
fi

if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "❌ Invalid environment. Use: staging or production"
    exit 1
fi

echo "🚀 Deploying to $ENVIRONMENT..."
echo "Version: $VERSION"
echo ""

# Confirm deployment
if [ "$ENVIRONMENT" = "production" ]; then
    echo "⚠️  WARNING: You are about to deploy to PRODUCTION!"
    read -p "Are you sure? Type 'yes' to confirm: " confirm
    if [ "$confirm" != "yes" ]; then
        echo "❌ Deployment cancelled"
        exit 0
    fi
fi

# Load environment-specific config
ENV_FILE=".env.${ENVIRONMENT}"
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  Environment file not found: $ENV_FILE"
    echo "   Using default .env file"
    ENV_FILE=".env"
fi

# Create docker-compose override file
COMPOSE_FILE="docker-compose.yml"
if [ -f "docker-compose.${ENVIRONMENT}.yml" ]; then
    COMPOSE_FILE="-f docker-compose.yml -f docker-compose.${ENVIRONMENT}.yml"
fi

# Set image tags
export IMAGE_VERSION=$VERSION
if [ ! -z "$REGISTRY" ]; then
    export IMAGE_REGISTRY=$REGISTRY
    export IMAGE_PREFIX=$IMAGE_PREFIX
fi

# Pull latest images if using registry
if [ ! -z "$REGISTRY" ]; then
    echo "📥 Pulling images from registry..."
    SERVICES=(
        "market_data_service"
        "market_analyzer_service"
        "price_service"
        "signal_service"
        "notification_service"
    )
    
    for service in "${SERVICES[@]}"; do
        service_name=$(echo "$service" | tr '_' '-')
        image_name="${IMAGE_PREFIX}-${service_name}"
        full_image="${REGISTRY}/${image_name}:${VERSION}"
        
        echo "📥 Pulling ${full_image}..."
        docker pull "${full_image}" || echo "⚠️  Failed to pull ${full_image}, using local image"
    done
    echo ""
fi

# Deploy
echo "🚀 Deploying services..."
docker-compose $COMPOSE_FILE --env-file "$ENV_FILE" up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Health check
echo ""
echo "🏥 Running health check..."
./scripts/health.sh

# Show status
echo ""
echo "📊 Deployment status:"
docker-compose $COMPOSE_FILE ps

echo ""
echo "✅ Deployment to $ENVIRONMENT completed!"
echo ""
echo "📊 View logs: ./scripts/logs.sh"
echo "📈 Monitor: ./scripts/monitor.sh"

