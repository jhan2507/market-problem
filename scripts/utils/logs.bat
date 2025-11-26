@echo off
REM Script xem logs của hệ thống (Windows)

set SERVICE=%1

if "%SERVICE%"=="" (
    echo 📊 Viewing logs for all services...
    echo Usage: scripts\logs.bat [service_name]
    echo.
    echo Available services:
    echo   - market_data_service
    echo   - market_analyzer_service
    echo   - price_service
    echo   - signal_service
    echo   - notification_service
    echo   - mongodb
    echo   - redis
    echo.
    echo Showing all services logs (Ctrl+C to exit)...
    docker-compose logs -f
) else (
    echo 📊 Viewing logs for %SERVICE%...
    docker-compose logs -f %SERVICE%
)

