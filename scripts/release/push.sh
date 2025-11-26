#!/bin/bash
# Script push Docker images lên registry

set -e

VERSION_FILE="../VERSION"
VERSION=$(cat "$VERSION_FILE" 2>/dev/null || echo "0.0.0")
REGISTRY=${DOCKER_REGISTRY:-""}
IMAGE_PREFIX=${IMAGE_PREFIX:-"market"}

if [ -z "$REGISTRY" ]; then
    echo "❌ DOCKER_REGISTRY environment variable is not set"
    echo "   Set it to your registry (e.g., docker.io/username or registry.example.com)"
    exit 1
fi

echo "📤 Pushing Docker images to $REGISTRY..."
echo "Version: $VERSION"
echo ""

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
    full_image="${REGISTRY}/${image_name}"
    
    echo "📤 Pushing $service..."
    echo "   ${full_image}:${VERSION}"
    docker push "${full_image}:${VERSION}"
    
    echo "   ${full_image}:latest"
    docker push "${full_image}:latest"
    
    echo "✅ $service pushed successfully"
    echo ""
done

echo "✅ All images pushed successfully!"

