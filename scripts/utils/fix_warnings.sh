#!/bin/bash
# Script fix các warnings thường gặp

echo "🔧 Fixing Common Warnings"
echo "========================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found"
    echo "   Creating from env.example..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ Created .env file"
    else
        echo "❌ env.example not found"
        exit 1
    fi
fi

# Add IMAGE_REGISTRY if not exists
if ! grep -q "^IMAGE_REGISTRY=" .env && ! grep -q "^# IMAGE_REGISTRY=" .env; then
    echo ""
    echo "📝 Adding IMAGE_REGISTRY to .env..."
    echo "" >> .env
    echo "# Docker Image Configuration (optional)" >> .env
    echo "# IMAGE_REGISTRY=                    # Docker registry URL (leave empty for local)" >> .env
    echo "IMAGE_REGISTRY=" >> .env
    echo "✅ Added IMAGE_REGISTRY"
fi

# Add IMAGE_PREFIX if not exists
if ! grep -q "^IMAGE_PREFIX=" .env && ! grep -q "^# IMAGE_PREFIX=" .env; then
    echo "📝 Adding IMAGE_PREFIX to .env..."
    echo "IMAGE_PREFIX=market" >> .env
    echo "✅ Added IMAGE_PREFIX"
fi

# Add IMAGE_VERSION if not exists
if ! grep -q "^IMAGE_VERSION=" .env && ! grep -q "^# IMAGE_VERSION=" .env; then
    echo "📝 Adding IMAGE_VERSION to .env..."
    echo "IMAGE_VERSION=latest" >> .env
    echo "✅ Added IMAGE_VERSION"
fi

echo ""
echo "✅ Warnings fixed!"
echo ""
echo "💡 To apply changes, restart services:"
echo "   ./scripts/deploy/restart.sh"

