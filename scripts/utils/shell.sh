#!/bin/bash
# Script to open interactive shell in Docker containers

set -e

CONTAINER_NAME=""

# Parse arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <container_name> [shell]"
    echo ""
    echo "Available containers:"
    echo "  - market_mongodb"
    echo "  - market_redis"
    echo "  - market_data_service"
    echo "  - market_analyzer_service"
    echo "  - price_service"
    echo "  - signal_service"
    echo "  - notification_service"
    echo ""
    echo "Examples:"
    echo "  $0 market_mongodb"
    echo "  $0 market_redis"
    echo "  $0 signal_service"
    echo ""
    echo "Note: Default shell is 'sh'. Use 'bash' as second argument if available."
    exit 1
fi

CONTAINER_NAME=$1
SHELL_TYPE=${2:-sh}

# Check if container is running
if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container '$CONTAINER_NAME' is not running"
    echo ""
    echo "Running containers:"
    docker ps --format "  - {{.Names}}"
    exit 1
fi

# Open shell
echo "🐚 Opening $SHELL_TYPE shell in container: $CONTAINER_NAME"
echo "   Type 'exit' to return to host"
echo ""

docker-compose exec "$CONTAINER_NAME" "$SHELL_TYPE"

