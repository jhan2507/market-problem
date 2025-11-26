#!/bin/bash
# =============================================================================
# Script Name: restart.sh
# Description: Restart the entire Crypto Market Monitoring System (no rebuild)
# Category: DEPLOY
# Usage: ./scripts/deploy/restart.sh
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
    echo "🔄 Restarting Crypto Market Monitoring System..."
    
    cd "$PROJECT_ROOT"
    docker-compose restart
    
    echo ""
    log_success "System restarted successfully!"
    echo ""
    echo "📊 View logs: ./scripts/monitor/logs.sh"
}

# Run main function
main "$@"

