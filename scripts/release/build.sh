#!/bin/bash
# Script build Docker images với version

set -e

VERSION_FILE="../VERSION"
VERSION=$(cat "$VERSION_FILE" 2>/dev/null || echo "0.0.0")
REGISTRY=${DOCKER_REGISTRY:-""}
IMAGE_PREFIX=${IMAGE_PREFIX:-"market"}

echo "🔨 Building Docker images..."
echo "Version: $VERSION"
echo ""

# Build images với tags
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
    
    if [ ! -z "$REGISTRY" ]; then
        full_image="${REGISTRY}/${image_name}"
    else
        full_image="$image_name"
    fi
    
    echo "📦 Building $service..."
    echo "   Image: ${full_image}:${VERSION}"
    echo "   Image: ${full_image}:latest"
    
    docker build \
        -f "services/${service}/Dockerfile" \
        -t "${full_image}:${VERSION}" \
        -t "${full_image}:latest" \
        .
    
    echo "✅ $service built successfully"
    echo ""
done

echo "✅ All images built successfully!"
echo ""
echo "📋 Built images:"
for service in "${SERVICES[@]}"; do
    service_name=$(echo "$service" | tr '_' '-')
    image_name="${IMAGE_PREFIX}-${service_name}"
    if [ ! -z "$REGISTRY" ]; then
        full_image="${REGISTRY}/${image_name}"
    else
        full_image="$image_name"
    fi
    echo "  - ${full_image}:${VERSION}"
    echo "  - ${full_image}:latest"
done

echo ""
echo "💡 To push images: ./scripts/release/push.sh"
echo "💡 To deploy: ./scripts/release/deploy.sh <environment>"

