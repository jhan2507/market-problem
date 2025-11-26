#!/bin/bash
# Script to execute commands in Docker containers

set -e

CONTAINER_NAME=""
COMMAND=""

# Parse arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <container_name> <command>"
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
    echo "  $0 market_mongodb 'mongosh --eval \"db.adminCommand(\\\"ping\\\")\"'"
    echo "  $0 market_redis 'redis-cli ping'"
    echo "  $0 signal_service 'python --version'"
    exit 1
fi

CONTAINER_NAME=$1
shift
COMMAND="$@"

# Check if container is running
if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container '$CONTAINER_NAME' is not running"
    echo ""
    echo "Running containers:"
    docker ps --format "  - {{.Names}}"
    exit 1
fi

# Execute command
echo "🔧 Executing command in container: $CONTAINER_NAME"
echo "   Command: $COMMAND"
echo ""

docker-compose exec "$CONTAINER_NAME" sh -c "$COMMAND"

