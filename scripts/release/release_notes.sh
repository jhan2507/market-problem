#!/bin/bash
# Script tạo release notes

VERSION=$1
PREV_VERSION=$2

if [ -z "$VERSION" ]; then
    VERSION=$(cat ../VERSION 2>/dev/null || echo "0.0.0")
fi

if [ -z "$PREV_VERSION" ]; then
    # Get previous version from git
    if git rev-parse --git-dir > /dev/null 2>&1; then
        PREV_TAG=$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo "")
        if [ ! -z "$PREV_TAG" ]; then
            PREV_VERSION=$(echo "$PREV_TAG" | sed 's/^v//')
        fi
    fi
fi

echo "# Release v$VERSION"
echo ""
echo "**Release Date:** $(date '+%Y-%m-%d')"
echo ""

if [ ! -z "$PREV_VERSION" ]; then
    echo "## Changes since v$PREV_VERSION"
    echo ""
    
    # Get git commits if available
    if git rev-parse --git-dir > /dev/null 2>&1; then
        if git rev-parse "v$PREV_VERSION" > /dev/null 2>&1; then
            echo "### Commits"
            echo ""
            git log --pretty=format:"- %s (%h)" "v$PREV_VERSION"..HEAD | head -20
            echo ""
        fi
    fi
fi

echo "## Services"
echo ""
echo "- Market Data Service"
echo "- Market Analyzer Service"
echo "- Price Service"
echo "- Signal Service"
echo "- Notification Service"
echo ""

echo "## Deployment"
echo ""
echo "### Staging"
echo "\`\`\`bash"
echo "./scripts/release/deploy.sh staging"
echo "\`\`\`"
echo ""
echo "### Production"
echo "\`\`\`bash"
echo "./scripts/release/deploy.sh production"
echo "\`\`\`"
echo ""

echo "## Rollback"
echo ""
echo "If needed, rollback with:"
echo "\`\`\`bash"
echo "./scripts/release/rollback.sh production $PREV_VERSION"
echo "\`\`\`"

