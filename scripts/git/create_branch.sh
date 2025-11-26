#!/bin/bash
# Script tạo branch mới

BRANCH_NAME=$1
BASE_BRANCH=${2:-develop}
BRANCH_TYPE=${3:-feature}

if [ -z "$BRANCH_NAME" ]; then
    echo "❌ Usage: ./scripts/git/create_branch.sh <branch_name> [base_branch] [type]"
    echo ""
    echo "Types:"
    echo "  feature  - New feature (default)"
    echo "  bugfix   - Bug fix"
    echo "  hotfix   - Hotfix for production"
    echo "  release  - Release preparation"
    echo ""
    echo "Examples:"
    echo "  ./scripts/git/create_branch.sh new-signal-feature develop feature"
    echo "  ./scripts/git/create_branch.sh fix-price-bug master bugfix"
    exit 1
fi

# Format branch name
FULL_BRANCH_NAME="${BRANCH_TYPE}/${BRANCH_NAME}"

echo "🌿 Creating branch: $FULL_BRANCH_NAME"
echo "Base branch: $BASE_BRANCH"
echo ""

# Check if base branch exists
if ! git show-ref --verify --quiet refs/heads/"$BASE_BRANCH"; then
    echo "❌ Base branch '$BASE_BRANCH' does not exist"
    exit 1
fi

# Check if branch already exists
if git show-ref --verify --quiet refs/heads/"$FULL_BRANCH_NAME"; then
    echo "⚠️  Branch '$FULL_BRANCH_NAME' already exists"
    read -p "Switch to it? (y/n): " switch
    if [ "$switch" = "y" ]; then
        git checkout "$FULL_BRANCH_NAME"
        echo "✅ Switched to $FULL_BRANCH_NAME"
    fi
    exit 0
fi

# Create and switch to new branch
CURRENT_BRANCH=$(git branch --show-current)
git checkout "$BASE_BRANCH"
git pull origin "$BASE_BRANCH" 2>/dev/null || true
git checkout -b "$FULL_BRANCH_NAME"

echo "✅ Created and switched to $FULL_BRANCH_NAME"
echo ""
echo "💡 Next steps:"
echo "  1. Make your changes"
echo "  2. Commit: git add . && git commit -m 'Your message'"
echo "  3. Push: ./scripts/git/push.sh $FULL_BRANCH_NAME"

