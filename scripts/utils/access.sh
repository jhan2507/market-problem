#!/bin/bash
# Interactive script to access Docker containers

set -e

show_menu() {
    echo "🐳 Docker Container Access"
    echo "=========================="
    echo ""
    echo "1. MongoDB Shell (mongosh)"
    echo "2. Redis CLI"
    echo "3. Market Data Service Shell"
    echo "4. Market Analyzer Service Shell"
    echo "5. Price Service Shell"
    echo "6. Signal Service Shell"
    echo "7. Notification Service Shell"
    echo "8. List all running containers"
    echo "9. Execute custom command"
    echo "0. Exit"
    echo ""
}

mongodb_shell() {
    echo "🗄️  Opening MongoDB Shell..."
    echo ""
    docker-compose exec market_mongodb mongosh \
        --authenticationDatabase admin \
        -u admin \
        -p password
}

redis_cli() {
    echo "🔴 Opening Redis CLI..."
    echo ""
    docker-compose exec market_redis redis-cli
}

service_shell() {
    local service_name=$1
    echo "🐚 Opening shell in $service_name..."
    echo ""
    
    # Try bash first, fallback to sh
    if docker-compose exec "$service_name" which bash > /dev/null 2>&1; then
        docker-compose exec "$service_name" bash
    else
        docker-compose exec "$service_name" sh
    fi
}

list_containers() {
    echo "📋 Running Containers:"
    echo ""
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAMES|market_"
    echo ""
}

custom_command() {
    echo "Enter container name:"
    read -r container_name
    
    if ! docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
        echo "❌ Container '$container_name' is not running"
        return
    fi
    
    echo "Enter command to execute:"
    read -r command
    
    echo ""
    echo "🔧 Executing: $command"
    echo ""
    docker-compose exec "$container_name" sh -c "$command"
}

main() {
    while true; do
        show_menu
        read -p "Select option: " choice
        echo ""
        
        case $choice in
            1)
                mongodb_shell
                ;;
            2)
                redis_cli
                ;;
            3)
                service_shell "market_data_service"
                ;;
            4)
                service_shell "market_analyzer_service"
                ;;
            5)
                service_shell "price_service"
                ;;
            6)
                service_shell "signal_service"
                ;;
            7)
                service_shell "notification_service"
                ;;
            8)
                list_containers
                read -p "Press Enter to continue..."
                ;;
            9)
                custom_command
                read -p "Press Enter to continue..."
                ;;
            0)
                echo "👋 Goodbye!"
                exit 0
                ;;
            *)
                echo "❌ Invalid option. Please try again."
                sleep 1
                ;;
        esac
        echo ""
    done
}

main

