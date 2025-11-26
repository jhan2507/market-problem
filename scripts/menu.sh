#!/bin/bash
# Script menu chính để quản lý hệ thống

show_menu() {
    clear
    echo "╔════════════════════════════════════════╗"
    echo "║  Crypto Market Monitoring System      ║"
    echo "║  Management Menu                      ║"
    echo "╚════════════════════════════════════════╝"
    echo ""
    echo "1. 🚀 Start System"
    echo "2. 🛑 Stop System"
    echo "3. 🔄 Restart System"
    echo "4. 🔨 Rebuild System (with new code)"
    echo "5. 📊 View Logs"
    echo "6. 📈 System Status"
    echo "7. 🏥 Health Check"
    echo "8. 📊 Statistics"
    echo "9. 📺 Real-time Monitor"
    echo "10. 🔄 Restart Service"
    echo "11. 🔨 Rebuild Service (with new code)"
    echo "12. 💾 Backup Database"
    echo "13. 🔄 Restore Database"
    echo "14. 🧹 Cleanup"
    echo "15. 🐳 Access Containers"
    echo "16. ❌ Exit"
    echo ""
    read -p "Select option [1-16]: " choice
}

while true; do
    show_menu
    
    case $choice in
        1)
            ./scripts/deploy/start.sh
            read -p "Press Enter to continue..."
            ;;
        2)
            ./scripts/deploy/stop.sh
            read -p "Press Enter to continue..."
            ;;
        3)
            ./scripts/deploy/restart.sh
            read -p "Press Enter to continue..."
            ;;
        4)
            ./scripts/deploy/rebuild.sh
            read -p "Press Enter to continue..."
            ;;
        5)
            echo ""
            echo "Available services:"
            echo "  1. market_data_service"
            echo "  2. market_analyzer_service"
            echo "  3. price_service"
            echo "  4. signal_service"
            echo "  5. notification_service"
            echo "  6. mongodb"
            echo "  7. redis"
            echo "  8. All services"
            read -p "Select service [1-8]: " service_choice
            case $service_choice in
                1) SERVICE="market_data_service" ;;
                2) SERVICE="market_analyzer_service" ;;
                3) SERVICE="price_service" ;;
                4) SERVICE="signal_service" ;;
                5) SERVICE="notification_service" ;;
                6) SERVICE="mongodb" ;;
                7) SERVICE="redis" ;;
                8) SERVICE="" ;;
                *) SERVICE="" ;;
            esac
            ./scripts/monitor/logs.sh "$SERVICE"
            read -p "Press Enter to continue..."
            ;;
        6)
            ./scripts/monitor/status.sh
            read -p "Press Enter to continue..."
            ;;
        7)
            ./scripts/monitor/health.sh
            read -p "Press Enter to continue..."
            ;;
        8)
            ./scripts/monitor/stats.sh
            read -p "Press Enter to continue..."
            ;;
        9)
            ./scripts/monitor/monitor.sh
            ;;
        10)
            echo ""
            echo "Available services:"
            echo "  1. market_data_service"
            echo "  2. market_analyzer_service"
            echo "  3. price_service"
            echo "  4. signal_service"
            echo "  5. notification_service"
            read -p "Select service [1-5]: " service_choice
            case $service_choice in
                1) SERVICE="market_data_service" ;;
                2) SERVICE="market_analyzer_service" ;;
                3) SERVICE="price_service" ;;
                4) SERVICE="signal_service" ;;
                5) SERVICE="notification_service" ;;
                *) SERVICE="" ;;
            esac
            if [ ! -z "$SERVICE" ]; then
                ./scripts/deploy/restart_service.sh "$SERVICE"
            fi
            read -p "Press Enter to continue..."
            ;;
        11)
            echo ""
            echo "Available services:"
            echo "  1. market_data_service"
            echo "  2. market_analyzer_service"
            echo "  3. price_service"
            echo "  4. signal_service"
            echo "  5. notification_service"
            read -p "Select service [1-5]: " service_choice
            case $service_choice in
                1) SERVICE="market_data_service" ;;
                2) SERVICE="market_analyzer_service" ;;
                3) SERVICE="price_service" ;;
                4) SERVICE="signal_service" ;;
                5) SERVICE="notification_service" ;;
                *) SERVICE="" ;;
            esac
            if [ ! -z "$SERVICE" ]; then
                ./scripts/deploy/rebuild_service.sh "$SERVICE"
            fi
            read -p "Press Enter to continue..."
            ;;
        12)
            ./scripts/utils/backup.sh
            read -p "Press Enter to continue..."
            ;;
        13)
            echo ""
            echo "Available backups:"
            ls -lh backups/*.gz 2>/dev/null || echo "  No backups found"
            echo ""
            read -p "Enter backup file path: " backup_file
            if [ ! -z "$backup_file" ]; then
                ./scripts/utils/restore.sh "$backup_file"
            fi
            read -p "Press Enter to continue..."
            ;;
        14)
            ./scripts/utils/cleanup.sh
            read -p "Press Enter to continue..."
            ;;
        15)
            ./scripts/utils/access.sh
            ;;
        16)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option"
            sleep 1
            ;;
    esac
done

