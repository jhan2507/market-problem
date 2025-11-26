#!/bin/bash
# Script golive code mới lên production (master)

set -e

SOURCE_BRANCH=${1:-staging}
SKIP_BUILD=${2:-false}

echo "🚀 Go Live - Deploy to Production"
echo "================================="
echo "Source branch: $SOURCE_BRANCH"
echo "Target: master (Production)"
echo ""

# Final confirmation
echo "⚠️  WARNING: This will deploy to PRODUCTION!"
echo "   Source: $SOURCE_BRANCH"
echo "   Target: master"
echo ""
read -p "Type 'GOLIVE' to confirm: " confirm
if [ "$confirm" != "GOLIVE" ]; then
    echo "❌ Deployment cancelled"
    exit 0
fi

# Step 1: Validate environment
echo ""
echo "📋 Step 1: Validating environment..."
if [ ! -f .env.production ]; then
    echo "⚠️  .env.production not found"
    read -p "Continue anyway? (y/n): " continue
    if [ "$continue" != "y" ]; then
        echo "❌ Cancelled"
        exit 0
    fi
else
    echo "✅ Production config found"
fi

# Step 2: Get current version
echo ""
echo "📋 Step 2: Version management..."
if [ -f VERSION ]; then
    CURRENT_VERSION=$(cat VERSION)
    echo "Current version: $CURRENT_VERSION"
    
    # Ask for version bump
    echo ""
    echo "Select version bump:"
    echo "  1. Patch (0.0.X) - Bug fixes"
    echo "  2. Minor (0.X.0) - New features"
    echo "  3. Major (X.0.0) - Breaking changes"
    echo "  4. Keep current version"
    read -p "Choice [1-4]: " version_choice
    
    case $version_choice in
        1)
            NEW_VERSION=$(./scripts/release/version.sh bump patch)
            ;;
        2)
            NEW_VERSION=$(./scripts/release/version.sh bump minor)
            ;;
        3)
            NEW_VERSION=$(./scripts/release/version.sh bump major)
            ;;
        4)
            NEW_VERSION=$CURRENT_VERSION
            ;;
        *)
            echo "❌ Invalid choice, keeping current version"
            NEW_VERSION=$CURRENT_VERSION
            ;;
    esac
    
    echo "✅ Version: $NEW_VERSION"
else
    echo "⚠️  VERSION file not found, using timestamp"
    NEW_VERSION="release-$(date +%Y%m%d-%H%M%S)"
fi

# Step 3: Merge to master
echo ""
echo "📋 Step 3: Merging $SOURCE_BRANCH to master..."

# Check if source branch exists
if ! git show-ref --verify --quiet refs/heads/"$SOURCE_BRANCH"; then
    echo "❌ Source branch '$SOURCE_BRANCH' does not exist"
    exit 1
fi

# Ensure we're on master
CURRENT_BRANCH=$(git branch --show-current)
git checkout master
git pull origin master 2>/dev/null || true

# Merge
if git merge "$SOURCE_BRANCH" --no-ff -m "Go Live: Merge $SOURCE_BRANCH to master (v$NEW_VERSION)"; then
    echo "✅ Merge successful"
else
    echo "❌ Merge failed (conflicts?)"
    echo "   Resolve conflicts and commit manually:"
    echo "   1. Fix conflicts in files"
    echo "   2. git add ."
    echo "   3. git commit"
    echo "   4. Run this script again"
    exit 1
fi

# Step 4: Create git tag
echo ""
echo "📋 Step 4: Creating git tag..."
if git rev-parse "v$NEW_VERSION" >/dev/null 2>&1; then
    echo "⚠️  Tag v$NEW_VERSION already exists"
    read -p "Delete and recreate? (y/n): " recreate
    if [ "$recreate" = "y" ]; then
        git tag -d "v$NEW_VERSION" 2>/dev/null || true
        git push origin ":refs/tags/v$NEW_VERSION" 2>/dev/null || true
    else
        echo "❌ Tag conflict, cancelling"
        exit 1
    fi
fi

git tag -a "v$NEW_VERSION" -m "Production release v$NEW_VERSION"
echo "✅ Tag v$NEW_VERSION created"

# Step 5: Build images (if not skipped)
if [ "$SKIP_BUILD" != "true" ]; then
    echo ""
    echo "📋 Step 5: Building Docker images..."
    if ./scripts/release/build.sh; then
        echo "✅ Images built"
        
        # Ask to push images
        if [ ! -z "$DOCKER_REGISTRY" ]; then
            read -p "Push images to registry? (y/n): " push_images
            if [ "$push_images" = "y" ]; then
                ./scripts/release/push.sh
                echo "✅ Images pushed"
            fi
        fi
    else
        echo "⚠️  Build failed, continuing anyway..."
        read -p "Continue with deployment? (y/n): " continue
        if [ "$continue" != "y" ]; then
            echo "❌ Cancelled"
            exit 1
        fi
    fi
else
    echo ""
    echo "⏭️  Step 5: Skipping build (as requested)"
fi

# Step 6: Generate release notes
echo ""
echo "📋 Step 6: Generating release notes..."
mkdir -p releases
./scripts/release/release_notes.sh "$NEW_VERSION" > "releases/v${NEW_VERSION}.md" 2>/dev/null || true
echo "✅ Release notes created: releases/v${NEW_VERSION}.md"

# Step 7: Push to remote
echo ""
echo "📋 Step 7: Pushing to remote..."
read -p "Push master and tag to remote? (y/n): " push_remote
if [ "$push_remote" = "y" ]; then
    git push origin master
    git push origin "v$NEW_VERSION"
    echo "✅ Pushed to remote"
else
    echo "⚠️  Skipped push (push manually later)"
fi

# Step 8: Deploy to production
echo ""
echo "📋 Step 8: Deploying to production..."
read -p "Deploy to production now? (y/n): " deploy_now
if [ "$deploy_now" = "y" ]; then
    ./scripts/release/deploy.sh production
    echo "✅ Deployed to production"
else
    echo "⚠️  Skipped deployment (deploy manually: ./scripts/release/deploy.sh production)"
fi

# Summary
echo ""
echo "✅ Go Live completed!"
echo "===================="
echo ""
echo "📋 Summary:"
echo "  Version: $NEW_VERSION"
echo "  Source: $SOURCE_BRANCH"
echo "  Target: master"
echo "  Tag: v$NEW_VERSION"
echo ""
echo "📝 Next steps:"
echo "  1. Monitor production: ./scripts/monitor/monitor.sh"
echo "  2. Check health: ./scripts/monitor/health.sh"
echo "  3. View logs: ./scripts/monitor/logs.sh"
echo ""
echo "📄 Release notes: releases/v${NEW_VERSION}.md"

