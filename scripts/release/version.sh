#!/bin/bash
# Script quản lý version

VERSION_FILE="../VERSION"

get_version() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE"
    else
        echo "0.0.0"
    fi
}

set_version() {
    echo "$1" > "$VERSION_FILE"
    echo "✅ Version set to $1"
}

increment_version() {
    local version=$(get_version)
    local part=$1  # major, minor, patch
    
    IFS='.' read -ra ADDR <<< "$version"
    local major=${ADDR[0]}
    local minor=${ADDR[1]}
    local patch=${ADDR[2]}
    
    case $part in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            ;;
        patch)
            patch=$((patch + 1))
            ;;
        *)
            echo "❌ Invalid part. Use: major, minor, or patch"
            exit 1
            ;;
    esac
    
    local new_version="$major.$minor.$patch"
    set_version "$new_version"
    echo "$new_version"
}

show_version() {
    local version=$(get_version)
    echo "Current version: $version"
    
    # Check git tag
    if git rev-parse --git-dir > /dev/null 2>&1; then
        local git_tag=$(git describe --tags --abbrev=0 2>/dev/null)
        if [ ! -z "$git_tag" ]; then
            echo "Git tag: $git_tag"
        fi
    fi
}

case "$1" in
    get)
        get_version
        ;;
    set)
        if [ -z "$2" ]; then
            echo "❌ Usage: ./scripts/version.sh set <version>"
            echo "   Example: ./scripts/version.sh set 1.2.3"
            exit 1
        fi
        set_version "$2"
        ;;
    bump)
        if [ -z "$2" ]; then
            echo "❌ Usage: ./scripts/version.sh bump <major|minor|patch>"
            exit 1
        fi
        increment_version "$2"
        ;;
    show)
        show_version
        ;;
    *)
        echo "Usage: ./scripts/version.sh {get|set|bump|show}"
        echo ""
        echo "Commands:"
        echo "  get              - Get current version"
        echo "  set <version>    - Set version (e.g., 1.2.3)"
        echo "  bump <part>      - Increment version (major|minor|patch)"
        echo "  show             - Show current version and git tag"
        exit 1
        ;;
esac

