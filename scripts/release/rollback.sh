#!/bin/bash
# Script rollback về version trước

set -e

ENVIRONMENT=${1:-""}
TARGET_VERSION=${2:-""}

if [ -z "$ENVIRONMENT" ]; then
    echo "❌ Usage: ./scripts/release/rollback.sh <environment> [version]"
    echo ""
    echo "Environments:"
    echo "  - staging"
    echo "  - production"
    echo ""
    echo "If version is not specified, will rollback to previous version"
    exit 1
fi

if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "❌ Invalid environment. Use: staging or production"
    exit 1
fi

# Get current version
VERSION_FILE="../VERSION"
CURRENT_VERSION=$(cat "$VERSION_FILE" 2>/dev/null || echo "unknown")

if [ -z "$TARGET_VERSION" ]; then
    # Get previous version from git tags
    if git rev-parse --git-dir > /dev/null 2>&1; then
        PREV_TAG=$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo "")
        if [ ! -z "$PREV_TAG" ]; then
            TARGET_VERSION=$(echo "$PREV_TAG" | sed 's/^v//')
        fi
    fi
    
    if [ -z "$TARGET_VERSION" ]; then
        echo "❌ Could not determine previous version"
        echo "   Please specify version: ./scripts/release/rollback.sh $ENVIRONMENT <version>"
        exit 1
    fi
fi

echo "⚠️  ROLLBACK WARNING"
echo "==================="
echo "Environment: $ENVIRONMENT"
echo "Current version: $CURRENT_VERSION"
echo "Target version: $TARGET_VERSION"
echo ""

if [ "$ENVIRONMENT" = "production" ]; then
    echo "⚠️  WARNING: You are about to rollback PRODUCTION!"
    read -p "Are you sure? Type 'yes' to confirm: " confirm
    if [ "$confirm" != "yes" ]; then
        echo "❌ Rollback cancelled"
        exit 0
    fi
else
    read -p "Continue with rollback? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        echo "❌ Rollback cancelled"
        exit 0
    fi
fi

# Update version file
echo "$TARGET_VERSION" > "$VERSION_FILE"
echo "✅ Version file updated to $TARGET_VERSION"

# Deploy với version cũ
echo ""
echo "🔄 Rolling back to v$TARGET_VERSION..."
./scripts/release/deploy.sh "$ENVIRONMENT"

echo ""
echo "✅ Rollback completed!"
echo ""
echo "📊 Verify deployment: ./scripts/monitor/status.sh"
echo "📈 Monitor: ./scripts/monitor/monitor.sh"

