@echo off
REM Script rebuild và restart một service cụ thể với code mới (Windows)

if "%~1"=="" (
    echo ❌ Usage: scripts\deploy\rebuild_service.bat ^<service_name^>
    echo.
    echo Available services:
    echo   - market_data_service
    echo   - market_analyzer_service
    echo   - price_service
    echo   - signal_service
    echo   - notification_service
    exit /b 1
)

set SERVICE=%~1

echo 🔨 Rebuilding %SERVICE%...

REM Build lại image cho service
echo 📦 Building Docker image for %SERVICE%...
docker-compose build --no-cache %SERVICE%

if errorlevel 1 (
    echo ❌ Failed to build %SERVICE%
    exit /b 1
)

REM Stop service
echo 🛑 Stopping %SERVICE%...
docker-compose stop %SERVICE%

REM Remove container cũ (nếu có)
echo 🗑️  Removing old container...
docker-compose rm -f %SERVICE%

REM Start lại với image mới
echo 🚀 Starting %SERVICE% with new image...
docker-compose up -d %SERVICE%

if errorlevel 1 (
    echo ❌ Failed to restart %SERVICE%
    exit /b 1
)

echo.
echo ✅ %SERVICE% rebuilt and restarted successfully!
echo.
echo 📊 View logs: scripts\monitor\logs.bat %SERVICE%
echo 📈 Check status: docker-compose ps %SERVICE%

