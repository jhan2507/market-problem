#!/bin/bash
# Script merge staging vào production (master)

set -e

SOURCE_BRANCH=${1:-staging}
TARGET_BRANCH="master"

echo "🚀 Merging $SOURCE_BRANCH → $TARGET_BRANCH (PRODUCTION)"
echo "======================================================"
echo ""

# Safety check
if [ "$SOURCE_BRANCH" != "staging" ]; then
    echo "⚠️  WARNING: You are merging from $SOURCE_BRANCH (not staging)"
    read -p "Are you sure? Type 'yes' to confirm: " confirm
    if [ "$confirm" != "yes" ]; then
        echo "❌ Merge cancelled"
        exit 0
    fi
fi

# Check if branches exist
if ! git show-ref --verify --quiet refs/heads/"$SOURCE_BRANCH"; then
    echo "❌ Source branch '$SOURCE_BRANCH' does not exist"
    exit 1
fi

if ! git show-ref --verify --quiet refs/heads/"$TARGET_BRANCH"; then
    echo "❌ Target branch '$TARGET_BRANCH' does not exist"
    exit 1
fi

# Final confirmation
echo "⚠️  WARNING: This will deploy to PRODUCTION!"
echo "   Source: $SOURCE_BRANCH"
echo "   Target: $TARGET_BRANCH"
read -p "Type 'DEPLOY' to confirm: " confirm
if [ "$confirm" != "DEPLOY" ]; then
    echo "❌ Merge cancelled"
    exit 0
fi

# Ensure we're on target branch
CURRENT_BRANCH=$(git branch --show-current)
git checkout "$TARGET_BRANCH"
git pull origin "$TARGET_BRANCH" 2>/dev/null || true

# Merge
echo ""
echo "🔄 Merging..."
if git merge "$SOURCE_BRANCH" --no-ff -m "Deploy to production: Merge $SOURCE_BRANCH into $TARGET_BRANCH"; then
    echo "✅ Merge successful"
else
    echo "❌ Merge failed (conflicts?)"
    exit 1
fi

# Create version tag if VERSION file exists
if [ -f VERSION ]; then
    VERSION=$(cat VERSION)
    if git rev-parse "v$VERSION" >/dev/null 2>&1; then
        echo "ℹ️  Tag v$VERSION already exists"
    else
        read -p "Create tag v$VERSION? (y/n): " create_tag
        if [ "$create_tag" = "y" ]; then
            git tag -a "v$VERSION" -m "Production release v$VERSION"
            echo "✅ Tag v$VERSION created"
        fi
    fi
fi

# Push
echo ""
read -p "Push to remote? (y/n): " push
if [ "$push" = "y" ]; then
    git push origin "$TARGET_BRANCH"
    if [ ! -z "$VERSION" ] && git rev-parse "v$VERSION" >/dev/null 2>&1; then
        git push origin "v$VERSION"
    fi
    echo "✅ Pushed to remote"
fi

# Return to original branch
if [ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ] && [ ! -z "$CURRENT_BRANCH" ]; then
    git checkout "$CURRENT_BRANCH"
fi

echo ""
echo "✅ Production deployment completed!"
echo ""
echo "Next steps:"
echo "  1. Deploy to production: ./scripts/release/deploy.sh production"
echo "  2. Monitor: ./scripts/monitor/monitor.sh"

