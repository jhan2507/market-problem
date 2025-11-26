#!/bin/bash
# Script push code lên remote repository với nhiều options

set -e

# Parse options
MODE="normal"  # normal, pull, sync, force
BRANCH=""
REMOTE="origin"

while [[ $# -gt 0 ]]; do
    case $1 in
        --pull|--sync|--force)
            MODE="${1#--}"
            shift
            ;;
        --branch|-b)
            BRANCH="$2"
            shift 2
            ;;
        --remote|-r)
            REMOTE="$2"
            shift 2
            ;;
        *)
            if [ -z "$BRANCH" ]; then
                BRANCH="$1"
            elif [ "$REMOTE" = "origin" ] && [ "$1" != "origin" ]; then
                REMOTE="$1"
            fi
            shift
            ;;
    esac
done

# Default to current branch if not specified
if [ -z "$BRANCH" ]; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "")
fi

if [ -z "$BRANCH" ]; then
    echo "❌ No branch specified and cannot detect current branch"
    echo ""
    echo "Usage: ./scripts/git/push.sh [options] [branch] [remote]"
    echo ""
    echo "Options:"
    echo "  --pull      Pull from remote before pushing (safe)"
    echo "  --sync      Sync with remote (handles conflicts)"
    echo "  --force     Force push (dangerous, overwrites remote)"
    echo "  -b, --branch  Specify branch"
    echo "  -r, --remote  Specify remote (default: origin)"
    exit 1
fi

echo "📤 Pushing to $REMOTE/$BRANCH"
echo "Mode: $MODE"
echo "=============================="
echo ""

# Check if branch exists locally
if ! git show-ref --verify --quiet refs/heads/"$BRANCH"; then
    echo "❌ Branch '$BRANCH' does not exist locally"
    exit 1
fi

# Check if remote exists
if ! git remote get-url "$REMOTE" > /dev/null 2>&1; then
    echo "❌ Remote '$REMOTE' does not exist"
    exit 1
fi

# Switch to branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    echo "🔄 Switching to $BRANCH branch..."
    git checkout "$BRANCH"
fi

# Check for uncommitted changes
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
    elif [ "$MODE" != "force" ]; then
        echo "❌ Push cancelled"
        exit 1
    fi
fi

# Fetch from remote
echo "📥 Fetching from remote..."
git fetch "$REMOTE" 2>/dev/null || true

# Handle different modes
case $MODE in
    pull)
        # Pull mode: pull then push
        if git show-ref --verify --quiet "refs/remotes/${REMOTE}/${BRANCH}"; then
            echo "📥 Pulling from remote..."
            if git pull "$REMOTE" "$BRANCH" --no-rebase --no-edit; then
                echo "✅ Pulled successfully"
            else
                echo "❌ Pull failed (merge conflicts?)"
                echo ""
                echo "Resolve conflicts:"
                echo "  1. Fix conflicts in files"
                echo "  2. git add ."
                echo "  3. git commit"
                echo "  4. Run: ./scripts/git/push.sh --sync $BRANCH"
                exit 1
            fi
        else
            echo "ℹ️  Remote branch does not exist, will create on push"
        fi
        ;;
    
    sync)
        # Sync mode: handle conflicts intelligently
        if git show-ref --verify --quiet "refs/remotes/${REMOTE}/${BRANCH}"; then
            LOCAL=$(git rev-parse "$BRANCH" 2>/dev/null || echo "")
            REMOTE_REF=$(git rev-parse "refs/remotes/${REMOTE}/${BRANCH}" 2>/dev/null || echo "")
            
            if [ ! -z "$LOCAL" ] && [ ! -z "$REMOTE_REF" ] && [ "$LOCAL" != "$REMOTE_REF" ]; then
                BASE=$(git merge-base "$LOCAL" "$REMOTE_REF" 2>/dev/null || echo "")
                
                if [ -z "$BASE" ]; then
                    # Completely diverged
                    echo "⚠️  Branches have completely diverged"
                    echo ""
                    echo "Options:"
                    echo "  1. Merge remote changes"
                    echo "  2. Force push (overwrite remote)"
                    echo "  3. Cancel"
                    read -p "Choice [1-3]: " choice
                    
                    case $choice in
                        1)
                            git merge "${REMOTE}/${BRANCH}" --no-edit || {
                                echo "❌ Merge conflict - resolve manually"
                                exit 1
                            }
                            ;;
                        2)
                            read -p "Type 'FORCE' to confirm: " confirm
                            if [ "$confirm" = "FORCE" ]; then
                                git push -f "$REMOTE" "$BRANCH"
                                echo "✅ Force pushed"
                                exit 0
                            else
                                echo "❌ Cancelled"
                                exit 0
                            fi
                            ;;
                        3)
                            echo "❌ Cancelled"
                            exit 0
                            ;;
                    esac
                elif [ "$LOCAL" = "$BASE" ]; then
                    # Local is behind
                    echo "📥 Local is behind remote, pulling..."
                    git pull "$REMOTE" "$BRANCH" --no-edit
                elif [ "$REMOTE_REF" = "$BASE" ]; then
                    # Local is ahead
                    echo "📤 Local is ahead, will push..."
                else
                    # Diverged
                    echo "🔄 Branches diverged, merging..."
                    git pull "$REMOTE" "$BRANCH" --no-rebase --no-edit || {
                        echo "❌ Merge conflict - resolve manually"
                        exit 1
                    }
                fi
            fi
        fi
        ;;
    
    force)
        # Force mode: force push
        echo "⚠️  WARNING: Force push will overwrite remote!"
        read -p "Type 'FORCE' to confirm: " confirm
        if [ "$confirm" != "FORCE" ]; then
            echo "❌ Cancelled"
            exit 0
        fi
        git push -f "$REMOTE" "$BRANCH"
        echo "✅ Force pushed"
        exit 0
        ;;
    
    normal)
        # Normal mode: check conflicts before push
        if git show-ref --verify --quiet "refs/remotes/${REMOTE}/${BRANCH}"; then
            LOCAL=$(git rev-parse "$BRANCH" 2>/dev/null || echo "")
            REMOTE_REF=$(git rev-parse "refs/remotes/${REMOTE}/${BRANCH}" 2>/dev/null || echo "")
            
            if [ ! -z "$LOCAL" ] && [ ! -z "$REMOTE_REF" ] && [ "$LOCAL" != "$REMOTE_REF" ]; then
                BASE=$(git merge-base "$LOCAL" "$REMOTE_REF" 2>/dev/null || echo "")
                if [ ! -z "$BASE" ] && [ "$BASE" != "$REMOTE_REF" ]; then
                    echo "❌ Remote has changes you don't have locally"
                    echo ""
                    echo "💡 Use one of these:"
                    echo "  ./scripts/git/push.sh --pull $BRANCH    (pull then push)"
                    echo "  ./scripts/git/push.sh --sync $BRANCH    (sync with remote)"
                    echo "  ./scripts/git/push.sh --force $BRANCH   (force push - dangerous)"
                    exit 1
                fi
            fi
        fi
        ;;
esac

# Push
echo "📤 Pushing $BRANCH to $REMOTE..."
if git push -u "$REMOTE" "$BRANCH"; then
    echo "✅ Successfully pushed $BRANCH to $REMOTE"
else
    echo "❌ Push failed"
    echo ""
    echo "💡 Try:"
    echo "  ./scripts/git/push.sh --pull $BRANCH"
    echo "  ./scripts/git/push.sh --sync $BRANCH"
    exit 1
fi

# Return to original branch if different
if [ "$CURRENT_BRANCH" != "$BRANCH" ] && [ ! -z "$CURRENT_BRANCH" ]; then
    git checkout "$CURRENT_BRANCH"
fi

echo ""
echo "✅ Push completed!"
