#!/bin/bash
# =============================================================================
# Script Name: [SCRIPT_NAME]
# Description: [DESCRIPTION]
# Category: [DEPLOY|MONITOR|UTILS|RELEASE]
# Usage: ./scripts/[category]/[script_name].sh [arguments]
# =============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# =============================================================================
# Configuration
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# =============================================================================
# Functions
# =============================================================================

check_dependencies() {
    # Check required commands
    local missing_deps=()
    
    for cmd in docker docker-compose; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo "❌ Missing dependencies: ${missing_deps[*]}"
        echo "   Please install them first."
        exit 1
    fi
}

check_env_file() {
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo "⚠️  .env file not found."
        if [ -f "$PROJECT_ROOT/env.example" ]; then
            echo "   Creating from env.example..."
            cp "$PROJECT_ROOT/env.example" "$PROJECT_ROOT/.env"
            echo "✅ Created .env file. Please edit it with your configuration."
        else
            echo "❌ env.example not found. Cannot create .env file."
        fi
        exit 1
    fi
}

log_info() {
    echo "ℹ️  $*"
}

log_success() {
    echo "✅ $*"
}

log_error() {
    echo "❌ $*" >&2
}

log_warning() {
    echo "⚠️  $*"
}

# =============================================================================
# Main
# =============================================================================

main() {
    # Add your script logic here
    echo "🚀 [SCRIPT_NAME] starting..."
    
    # Example: check_dependencies
    # Example: check_env_file
    
    # Your code here
    
    log_success "[SCRIPT_NAME] completed successfully!"
}

# Run main function
main "$@"

