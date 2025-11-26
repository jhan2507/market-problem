#!/bin/bash
# Script push lần đầu lên remote repository

set -e

REPO_URL="git@personal:jhan2507/market-problem.git"

echo "🚀 Initial Push to Repository"
echo "=============================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed"
    exit 1
fi

# Check if .git exists
if [ ! -d .git ]; then
    echo "📦 Initializing Git repository..."
    git init
fi

# Setup repository
echo "🔧 Setting up repository..."
./scripts/git/setup_repo.sh

# Check current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "master")

# Add all files
echo ""
echo "📝 Adding files..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "ℹ️  No changes to commit"
else
    echo "💾 Committing changes..."
    git commit -m "Initial commit: Crypto Market Monitoring System"
    echo "✅ Changes committed"
fi

# Push branches
echo ""
echo "📤 Pushing branches to remote..."

BRANCHES=("master" "staging" "develop")
for branch in "${BRANCHES[@]}"; do
    if git show-ref --verify --quiet refs/heads/"$branch"; then
        echo "📤 Pushing $branch..."
        git push -u origin "$branch" || echo "⚠️  Failed to push $branch (may need to pull first)"
    fi
done

# Return to original branch
if [ "$CURRENT_BRANCH" != "master" ]; then
    git checkout "$CURRENT_BRANCH" 2>/dev/null || true
fi

echo ""
echo "✅ Initial push completed!"
echo ""
echo "📋 Repository: $REPO_URL"
echo "📋 Branches pushed:"
for branch in "${BRANCHES[@]}"; do
    if git show-ref --verify --quiet refs/heads/"$branch"; then
        echo "   - $branch"
    fi
done

