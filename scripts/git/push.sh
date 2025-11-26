#!/bin/bash
# Script push code lên remote repository

set -e

BRANCH=${1:-$(git branch --show-current)}
REMOTE=${2:-origin}

if [ -z "$BRANCH" ]; then
    echo "❌ No branch specified and cannot detect current branch"
    exit 1
fi

echo "📤 Pushing to $REMOTE/$BRANCH"
echo "=============================="
echo ""

# Check if branch exists locally
if ! git show-ref --verify --quiet refs/heads/"$BRANCH"; then
    echo "❌ Branch '$BRANCH' does not exist locally"
    exit 1
fi

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  You have uncommitted changes"
    read -p "Commit before push? (y/n): " commit
    if [ "$commit" = "y" ]; then
        read -p "Commit message: " message
        if [ -z "$message" ]; then
            message="Update $(date '+%Y-%m-%d %H:%M:%S')"
        fi
        git add -A
        git commit -m "$message"
        echo "✅ Changes committed"
    else
        echo "❌ Push cancelled"
        exit 1
    fi
fi

# Switch to branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    echo "🔄 Switching to $BRANCH branch..."
    git checkout "$BRANCH"
fi

# Push
echo "📤 Pushing $BRANCH to $REMOTE..."
if git push -u "$REMOTE" "$BRANCH"; then
    echo "✅ Successfully pushed $BRANCH to $REMOTE"
else
    echo "❌ Push failed"
    exit 1
fi

# Return to original branch if different
if [ "$CURRENT_BRANCH" != "$BRANCH" ] && [ ! -z "$CURRENT_BRANCH" ]; then
    git checkout "$CURRENT_BRANCH"
fi

echo ""
echo "✅ Push completed!"

