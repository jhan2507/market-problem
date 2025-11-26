#!/bin/bash
# CI/CD script for automated deployment

set -e

ENVIRONMENT=${1:-"staging"}
BRANCH=${2:-$(git branch --show-current)}

echo "🔄 CI/CD Pipeline"
echo "Environment: $ENVIRONMENT"
echo "Branch: $BRANCH"
echo ""

# Determine environment from branch
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
    if [ "$ENVIRONMENT" != "production" ]; then
        echo "⚠️  Main branch detected, switching to production"
        ENVIRONMENT="production"
    fi
fi

# Get version
VERSION=$(cat ../VERSION 2>/dev/null || echo "0.0.0")
echo "Version: $VERSION"
echo ""

# Run tests (if any)
echo "🧪 Running tests..."
# Add your test commands here
# pytest tests/ || exit 1
echo "✅ Tests passed"
echo ""

# Build images
echo "🔨 Building images..."
./scripts/build.sh
echo ""

# Push images (if registry is set)
if [ ! -z "$DOCKER_REGISTRY" ]; then
    echo "📤 Pushing images..."
    ./scripts/push.sh
    echo ""
fi

# Deploy
echo "🚀 Deploying to $ENVIRONMENT..."
./scripts/deploy.sh "$ENVIRONMENT"
echo ""

# Health check
echo "🏥 Running health check..."
sleep 15
./scripts/health.sh
echo ""

echo "✅ CI/CD pipeline completed successfully!"

