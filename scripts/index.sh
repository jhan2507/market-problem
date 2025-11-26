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
    echo "  4. Rebuild System (with new code)"
    echo "  5. Restart Service"
    echo "  6. Rebuild Service (with new code)"
    echo ""
    echo "📊 MONITORING"
    echo "  7. View Logs"
    echo "  8. System Status"
    echo "  9. Health Check"
    echo "  10. Statistics"
    echo "  11. Real-time Monitor"
    echo "  12. Metrics"
    echo "  13. Test Connections"
    echo ""
    echo "🔧 UTILITIES"
    echo "  14. Backup Database"
    echo "  15. Restore Database"
    echo "  16. Export Data"
    echo "  17. Import Data"
    echo "  18. Validate Config"
    echo "  19. Check Dependencies"
    echo "  20. Scale Service"
    echo "  21. Access Containers (Interactive)"
    echo "  22. Execute Command in Container"
    echo "  23. Open Shell in Container"
    echo ""
    echo "🚀 RELEASE"
    echo "  24. Version Management"
    echo "  25. Build Images"
    echo "  26. Push Images"
    echo "  27. Create Release"
    echo "  28. Deploy to Environment"
    echo "  29. Rollback"
    echo ""
    echo "  30. Quick Start Guide"
    echo "  31. Exit"
    echo ""
    read -p "Select option [1-31]: " choice
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
        4) run_script "deploy" "rebuild.sh" ;;
        5) 
            read -p "Service name: " service
            run_script "deploy" "restart_service.sh" "$service"
            ;;
        6)
            read -p "Service name: " service
            run_script "deploy" "rebuild_service.sh" "$service"
            ;;
        7)
            read -p "Service name (optional): " service
            run_script "monitor" "logs.sh" "$service"
            ;;
        8) run_script "monitor" "status.sh" ;;
        9) run_script "monitor" "health.sh" ;;
        10) run_script "monitor" "stats.sh" ;;
        11) run_script "monitor" "monitor.sh" ;;
        12) run_script "monitor" "metrics.sh" ;;
        13) run_script "monitor" "test_connection.sh" ;;
        14) run_script "utils" "backup.sh" ;;
        15)
            read -p "Backup file: " backup_file
            run_script "utils" "restore.sh" "$backup_file"
            ;;
        16) run_script "utils" "export_data.sh" ;;
        17)
            read -p "Export file: " export_file
            run_script "utils" "import_data.sh" "$export_file"
            ;;
        18) run_script "utils" "validate_config.sh" ;;
        19) run_script "utils" "check_dependencies.sh" ;;
        20)
            read -p "Service name: " service
            read -p "Replicas: " replicas
            run_script "utils" "scale.sh" "$service" "$replicas"
            ;;
        21) run_script "utils" "access.sh" ;;
        22)
            read -p "Container name: " container
            read -p "Command: " cmd
            run_script "utils" "exec.sh" "$container" "$cmd"
            ;;
        23)
            read -p "Container name: " container
            read -p "Shell (sh/bash, default: sh): " shell
            run_script "utils" "shell.sh" "$container" "${shell:-sh}"
            ;;
        24)
            read -p "Command (get/set/bump/show): " cmd
            read -p "Value (optional): " value
            run_script "release" "version.sh" "$cmd" "$value"
            ;;
        25) run_script "release" "build.sh" ;;
        26) run_script "release" "push.sh" ;;
        27) run_script "release" "release.sh" ;;
        28)
            read -p "Environment (staging/production): " env
            run_script "release" "deploy.sh" "$env"
            ;;
        29)
            read -p "Environment (staging/production): " env
            read -p "Version (optional): " version
            run_script "release" "rollback.sh" "$env" "$version"
            ;;
        30) bash "$SCRIPT_DIR/quick_start.sh" ;;
        31)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option"
            sleep 1
            ;;
    esac
    
    if [ $? -ne 0 ] && [ "$choice" != "31" ]; then
        read -p "Press Enter to continue..."
    fi
done

