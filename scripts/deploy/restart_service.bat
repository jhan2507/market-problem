@echo off
REM Script restart một service cụ thể (Windows)

if "%1"=="" (
    echo ❌ Usage: scripts\restart_service.bat ^<service_name^>
    echo.
    echo Available services:
    echo   - market_data_service
    echo   - market_analyzer_service
    echo   - price_service
    echo   - signal_service
    echo   - notification_service
    echo   - mongodb
    echo   - redis
    exit /b 1
)

set SERVICE=%1

echo 🔄 Restarting %SERVICE%...

docker-compose restart %SERVICE%

if %ERRORLEVEL% EQU 0 (
    echo ✅ %SERVICE% restarted successfully
    echo.
    echo 📊 View logs: scripts\logs.bat %SERVICE%
) else (
    echo ❌ Failed to restart %SERVICE%
    exit /b 1
)

