#!/bin/bash
# =============================================================================
# Script Name: stop.sh
# Description: Stop the entire Crypto Market Monitoring System
# Category: DEPLOY
# Usage: ./scripts/deploy/stop.sh
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# =============================================================================
# Functions
# =============================================================================

log_success() {
    echo "✅ $*"
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo "🛑 Stopping Crypto Market Monitoring System..."
    
    cd "$PROJECT_ROOT"
    docker-compose down
    
    echo ""
    log_success "System stopped successfully!"
}

# Run main function
main "$@"

