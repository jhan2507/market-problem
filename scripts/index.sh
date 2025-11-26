#!/bin/bash
# Main index script - entry point for all scripts

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

show_menu() {
    clear
    echo "╔════════════════════════════════════════════════╗"
    echo "║  Crypto Market Monitoring System              ║"
    echo "║  Scripts Management                           ║"
    echo "╚════════════════════════════════════════════════╝"
    echo ""
    echo "📦 DEPLOYMENT"
    echo "  1. Start System"
    echo "  2. Stop System"
    echo "  3. Restart System"
    echo "  4. Restart Service"
    echo ""
    echo "📊 MONITORING"
    echo "  5. View Logs"
    echo "  6. System Status"
    echo "  7. Health Check"
    echo "  8. Statistics"
    echo "  9. Real-time Monitor"
    echo "  10. Metrics"
    echo "  11. Test Connections"
    echo ""
    echo "🔧 UTILITIES"
    echo "  12. Backup Database"
    echo "  13. Restore Database"
    echo "  14. Export Data"
    echo "  15. Import Data"
    echo "  16. Validate Config"
    echo "  17. Check Dependencies"
    echo "  18. Scale Service"
    echo ""
    echo "🚀 RELEASE"
    echo "  19. Version Management"
    echo "  20. Build Images"
    echo "  21. Push Images"
    echo "  22. Create Release"
    echo "  23. Deploy to Environment"
    echo "  24. Rollback"
    echo ""
    echo "  25. Quick Start Guide"
    echo "  26. Exit"
    echo ""
    read -p "Select option [1-26]: " choice
}

run_script() {
    local category=$1
    local script=$2
    local full_path="$SCRIPT_DIR/$category/$script"
    
    if [ -f "$full_path" ]; then
        bash "$full_path" "${@:3}"
    else
        echo "❌ Script not found: $full_path"
        return 1
    fi
}

while true; do
    show_menu
    
    case $choice in
        1) run_script "deploy" "start.sh" ;;
        2) run_script "deploy" "stop.sh" ;;
        3) run_script "deploy" "restart.sh" ;;
        4) 
            read -p "Service name: " service
            run_script "deploy" "restart_service.sh" "$service"
            ;;
        5)
            read -p "Service name (optional): " service
            run_script "monitor" "logs.sh" "$service"
            ;;
        6) run_script "monitor" "status.sh" ;;
        7) run_script "monitor" "health.sh" ;;
        8) run_script "monitor" "stats.sh" ;;
        9) run_script "monitor" "monitor.sh" ;;
        10) run_script "monitor" "metrics.sh" ;;
        11) run_script "monitor" "test_connection.sh" ;;
        12) run_script "utils" "backup.sh" ;;
        13)
            read -p "Backup file: " backup_file
            run_script "utils" "restore.sh" "$backup_file"
            ;;
        14) run_script "utils" "export_data.sh" ;;
        15)
            read -p "Export file: " export_file
            run_script "utils" "import_data.sh" "$export_file"
            ;;
        16) run_script "utils" "validate_config.sh" ;;
        17) run_script "utils" "check_dependencies.sh" ;;
        18)
            read -p "Service name: " service
            read -p "Replicas: " replicas
            run_script "utils" "scale.sh" "$service" "$replicas"
            ;;
        19)
            read -p "Command (get/set/bump/show): " cmd
            read -p "Value (optional): " value
            run_script "release" "version.sh" "$cmd" "$value"
            ;;
        20) run_script "release" "build.sh" ;;
        21) run_script "release" "push.sh" ;;
        22) run_script "release" "release.sh" ;;
        23)
            read -p "Environment (staging/production): " env
            run_script "release" "deploy.sh" "$env"
            ;;
        24)
            read -p "Environment (staging/production): " env
            read -p "Version (optional): " version
            run_script "release" "rollback.sh" "$env" "$version"
            ;;
        25) bash "$SCRIPT_DIR/quick_start.sh" ;;
        26)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option"
            sleep 1
            ;;
    esac
    
    if [ $? -ne 0 ] && [ "$choice" != "26" ]; then
        read -p "Press Enter to continue..."
    fi
done

