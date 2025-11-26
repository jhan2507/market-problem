#!/bin/bash
# Script tạo release mới

set -e

VERSION_FILE="../VERSION"
CURRENT_VERSION=$(cat "$VERSION_FILE" 2>/dev/null || echo "0.0.0")

echo "🚀 Creating new release..."
echo "Current version: $CURRENT_VERSION"
echo ""

# Hỏi loại bump
echo "Select version bump type:"
echo "1. Patch (0.0.X) - Bug fixes"
echo "2. Minor (0.X.0) - New features"
echo "3. Major (X.0.0) - Breaking changes"
read -p "Choice [1-3]: " choice

case $choice in
    1) BUMP_TYPE="patch" ;;
    2) BUMP_TYPE="minor" ;;
    3) BUMP_TYPE="major" ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Bump version
NEW_VERSION=$(./scripts/release/version.sh bump "$BUMP_TYPE")
echo ""
echo "✅ New version: $NEW_VERSION"

# Build images
echo ""
read -p "Build Docker images? (y/n): " build_choice
if [ "$build_choice" = "y" ]; then
    ./scripts/release/build.sh
fi

# Create git tag
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo ""
    read -p "Create git tag? (y/n): " tag_choice
    if [ "$tag_choice" = "y" ]; then
        read -p "Tag message (optional): " tag_message
        if [ -z "$tag_message" ]; then
            tag_message="Release v$NEW_VERSION"
        fi
        
        git tag -a "v$NEW_VERSION" -m "$tag_message"
        echo "✅ Git tag created: v$NEW_VERSION"
        
        read -p "Push tag to remote? (y/n): " push_choice
        if [ "$push_choice" = "y" ]; then
            git push origin "v$NEW_VERSION"
            echo "✅ Tag pushed to remote"
        fi
    fi
fi

# Generate release notes
echo ""
read -p "Generate release notes? (y/n): " notes_choice
if [ "$notes_choice" = "y" ]; then
    ./scripts/release/release_notes.sh "$NEW_VERSION" > "releases/v${NEW_VERSION}.md"
    echo "✅ Release notes created: releases/v${NEW_VERSION}.md"
fi

echo ""
echo "🎉 Release v$NEW_VERSION created successfully!"
echo ""
echo "Next steps:"
echo "  1. Review release notes"
echo "  2. Build and push images: ./scripts/release/push.sh"
echo "  3. Deploy to staging: ./scripts/release/deploy.sh staging"
echo "  4. Test staging environment"
echo "  5. Deploy to production: ./scripts/release/deploy.sh production"

