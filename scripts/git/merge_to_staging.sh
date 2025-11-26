#!/bin/bash
# Script merge branch vào staging

set -e

SOURCE_BRANCH=${1:-$(git branch --show-current)}
TARGET_BRANCH="staging"

if [ -z "$SOURCE_BRANCH" ]; then
    echo "❌ No source branch specified"
    exit 1
fi

echo "🔄 Merging $SOURCE_BRANCH → $TARGET_BRANCH"
echo "=========================================="
echo ""

# Check if source branch exists
if ! git show-ref --verify --quiet refs/heads/"$SOURCE_BRANCH"; then
    echo "❌ Source branch '$SOURCE_BRANCH' does not exist"
    exit 1
fi

# Check if target branch exists
if ! git show-ref --verify --quiet refs/heads/"$TARGET_BRANCH"; then
    echo "❌ Target branch '$TARGET_BRANCH' does not exist"
    exit 1
fi

# Confirm
echo "⚠️  This will merge $SOURCE_BRANCH into $TARGET_BRANCH"
read -p "Continue? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "❌ Merge cancelled"
    exit 0
fi

# Switch to target branch
CURRENT_BRANCH=$(git branch --show-current)
git checkout "$TARGET_BRANCH"
git pull origin "$TARGET_BRANCH" 2>/dev/null || true

# Merge
echo ""
echo "🔄 Merging..."
if git merge "$SOURCE_BRANCH" --no-ff -m "Merge $SOURCE_BRANCH into $TARGET_BRANCH"; then
    echo "✅ Merge successful"
else
    echo "❌ Merge failed (conflicts?)"
    echo "   Resolve conflicts and commit manually"
    exit 1
fi

# Push
echo ""
read -p "Push to remote? (y/n): " push
if [ "$push" = "y" ]; then
    git push origin "$TARGET_BRANCH"
    echo "✅ Pushed to remote"
fi

# Return to original branch
if [ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ] && [ ! -z "$CURRENT_BRANCH" ]; then
    git checkout "$CURRENT_BRANCH"
fi

echo ""
echo "✅ Merge completed!"

