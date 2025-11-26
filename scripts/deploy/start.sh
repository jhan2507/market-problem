#!/bin/bash
# =============================================================================
# Script Name: start.sh
# Description: Start the entire Crypto Market Monitoring System
# Category: DEPLOY
# Usage: ./scripts/deploy/start.sh
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

check_dependencies() {
    local missing_deps=()
    
    for cmd in docker docker-compose; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_error "Please install them first."
        exit 1
    fi
}

check_env_file() {
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_warning ".env file not found. Creating from env.example..."
        if [ -f "$PROJECT_ROOT/env.example" ]; then
            cp "$PROJECT_ROOT/env.example" "$PROJECT_ROOT/.env"
            log_success "Created .env file. Please edit it with your configuration."
            log_warning "You need to set:"
            echo "   - CMC_API_KEY"
            echo "   - TELEGRAM_BOT_TOKEN"
            echo "   - TELEGRAM_PRICE_CHAT_ID"
            echo "   - TELEGRAM_SIGNAL_CHAT_ID"
            exit 1
        else
            log_error "env.example not found. Cannot create .env file."
            exit 1
        fi
    fi
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo "🚀 Starting Crypto Market Monitoring System..."
    
    check_dependencies
    check_env_file
    
    cd "$PROJECT_ROOT"

    # Build và start services
    log_info "Building and starting services..."
    docker-compose up -d --build
    
    # Đợi services khởi động
    log_info "Waiting for services to start..."
    sleep 10
    
    # Kiểm tra health
    log_info "Checking service health..."
    docker-compose ps
    
    echo ""
    log_success "System started successfully!"
    echo ""
    echo "📊 View logs: ./scripts/monitor/logs.sh"
    echo "📈 Monitor services: ./scripts/monitor/status.sh"
    echo "🛑 Stop system: ./scripts/deploy/stop.sh"
}

# Run main function
main "$@"

