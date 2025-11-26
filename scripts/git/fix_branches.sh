#!/bin/bash
# Script fix branches nếu có vấn đề

set -e

echo "🔧 Fixing Git Branches"
echo "======================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed"
    exit 1
fi

# Check if .git exists
if [ ! -d .git ]; then
    echo "❌ Not a git repository"
    exit 1
fi

# Check current status
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")
HAS_COMMITS=$(git rev-parse --verify HEAD >/dev/null 2>&1 && echo "yes" || echo "no")

echo "Current branch: ${CURRENT_BRANCH:-none}"
echo "Has commits: $HAS_COMMITS"
echo ""

# If no commits, make initial commit
if [ "$HAS_COMMITS" = "no" ]; then
    echo "📝 Making initial commit..."
    git add -A
    git commit -m "Initial commit: Crypto Market Monitoring System" || {
        echo "⚠️  No files to commit or commit failed"
    }
    HAS_COMMITS="yes"
fi

# Ensure master branch exists
if ! git show-ref --verify --quiet refs/heads/master; then
    echo "🌿 Creating master branch..."
    if [ "$HAS_COMMITS" = "yes" ]; then
        git checkout -b master 2>/dev/null || git branch master
        git checkout master
    else
        git branch master
        git checkout master
    fi
    echo "✅ master branch created"
else
    echo "✅ master branch exists"
    git checkout master 2>/dev/null || true
fi

# Ensure staging branch exists
if ! git show-ref --verify --quiet refs/heads/staging; then
    echo "🌿 Creating staging branch..."
    git checkout master
    git checkout -b staging
    echo "✅ staging branch created"
else
    echo "✅ staging branch exists"
fi

# Ensure develop branch exists
if ! git show-ref --verify --quiet refs/heads/develop; then
    echo "🌿 Creating develop branch..."
    git checkout master
    git checkout -b develop
    echo "✅ develop branch created"
else
    echo "✅ develop branch exists"
fi

# Return to original branch
if [ ! -z "$CURRENT_BRANCH" ] && git show-ref --verify --quiet refs/heads/"$CURRENT_BRANCH"; then
    git checkout "$CURRENT_BRANCH"
    echo "✅ Returned to $CURRENT_BRANCH"
else
    git checkout master
    echo "✅ Switched to master"
fi

echo ""
echo "📋 Branch status:"
git branch -a

echo ""
echo "✅ Branch fix completed!"

