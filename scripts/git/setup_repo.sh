#!/bin/bash
# Script setup Git repository và các nhánh

set -e

REPO_URL="git@personal:jhan2507/market-problem.git"

echo "🔧 Setting up Git Repository"
echo "============================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed"
    exit 1
fi

# Check if already a git repo
if [ -d .git ]; then
    echo "⚠️  Git repository already exists"
    read -p "Continue with setup? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        exit 0
    fi
else
    echo "📦 Initializing Git repository..."
    git init
fi

# Add remote if not exists
if git remote get-url origin > /dev/null 2>&1; then
    echo "📡 Remote 'origin' already exists"
    CURRENT_URL=$(git remote get-url origin)
    if [ "$CURRENT_URL" != "$REPO_URL" ]; then
        echo "   Current: $CURRENT_URL"
        echo "   New: $REPO_URL"
        read -p "Update remote? (y/n): " update
        if [ "$update" = "y" ]; then
            git remote set-url origin "$REPO_URL"
            echo "✅ Remote updated"
        fi
    else
        echo "✅ Remote URL is correct"
    fi
else
    echo "📡 Adding remote origin..."
    git remote add origin "$REPO_URL"
    echo "✅ Remote added"
fi

# Create branches
echo ""
echo "🌿 Creating branches..."

# Check current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")

# Check if we have any commits
HAS_COMMITS=$(git rev-parse --verify HEAD >/dev/null 2>&1 && echo "yes" || echo "no")

# Create master branch (Production)
if git show-ref --verify --quiet refs/heads/master; then
    echo "✅ master branch already exists"
    # Try to checkout master, but don't fail if we can't
    git checkout master 2>/dev/null || true
else
    # Create master branch
    if [ "$HAS_COMMITS" = "no" ]; then
        # No commits yet, create initial branch
        git checkout -b master 2>/dev/null || git branch master
        git checkout master 2>/dev/null || true
        echo "✅ Created master branch (Production)"
        
        # Make initial commit if there are untracked files
        UNTRACKED=$(git ls-files --others --exclude-standard | wc -l)
        if [ "$UNTRACKED" -gt 0 ]; then
            echo "📝 Making initial commit..."
            git add -A
            git commit -m "Initial commit: Crypto Market Monitoring System" || true
            HAS_COMMITS="yes"
        fi
    else
        # We have commits, create master branch from current
        git checkout -b master 2>/dev/null || git branch master
        git checkout master 2>/dev/null || true
        echo "✅ Created master branch (Production)"
    fi
fi

# Ensure we're on master before creating other branches
if [ "$HAS_COMMITS" = "yes" ]; then
    git checkout master 2>/dev/null || true
fi

# Create staging branch (Test)
if git show-ref --verify --quiet refs/heads/staging; then
    echo "✅ staging branch already exists"
else
    # Create staging from master
    if [ "$HAS_COMMITS" = "yes" ]; then
        git checkout master 2>/dev/null || true
        git checkout -b staging
    else
        git branch staging 2>/dev/null || true
        git checkout staging 2>/dev/null || true
    fi
    echo "✅ Created staging branch (Test)"
fi

# Create develop branch
if git show-ref --verify --quiet refs/heads/develop; then
    echo "✅ develop branch already exists"
else
    # Create develop from master
    if [ "$HAS_COMMITS" = "yes" ]; then
        git checkout master 2>/dev/null || true
        git checkout -b develop
    else
        git branch develop 2>/dev/null || true
        git checkout develop 2>/dev/null || true
    fi
    echo "✅ Created develop branch"
fi

# Return to original branch or master
if [ ! -z "$CURRENT_BRANCH" ] && git show-ref --verify --quiet refs/heads/"$CURRENT_BRANCH"; then
    git checkout "$CURRENT_BRANCH" 2>/dev/null || git checkout master 2>/dev/null || true
else
    git checkout master 2>/dev/null || git checkout -b master 2>/dev/null || true
fi

echo ""
echo "📋 Branch structure:"
echo "  master   → Production"
echo "  staging  → Test/Staging"
echo "  develop  → Development"
echo ""

# Create .gitattributes if not exists
if [ ! -f .gitattributes ]; then
    echo "📝 Creating .gitattributes..."
    cat > .gitattributes << 'EOF'
# Auto detect text files and perform LF normalization
* text=auto

# Shell scripts
*.sh text eol=lf

# Batch files
*.bat text eol=crlf

# Python files
*.py text eol=lf

# Config files
*.yml text eol=lf
*.yaml text eol=lf
*.json text eol=lf
*.md text eol=lf
*.txt text eol=lf
*.env text eol=lf
*.env.* text eol=lf

# Binary files
*.pyc binary
*.pyo binary
*.pyd binary
*.so binary
*.dll binary
*.exe binary
*.zip binary
*.tar.gz binary
*.archive binary
*.archive.gz binary
EOF
    echo "✅ .gitattributes created"
fi

echo ""
echo "✅ Git repository setup completed!"
echo ""
echo "Next steps:"
echo "  1. Review and commit your changes"
echo "  2. Push to remote: ./scripts/git/push.sh [branch]"
echo "  3. Or use: git push -u origin master"

