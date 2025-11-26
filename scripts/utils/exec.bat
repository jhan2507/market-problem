@echo off
REM Script to execute commands in Docker containers

if "%1"=="" (
    echo Usage: %0 ^<container_name^> ^<command^>
    echo.
    echo Available containers:
    echo   - market_mongodb
    echo   - market_redis
    echo   - market_data_service
    echo   - market_analyzer_service
    echo   - price_service
    echo   - signal_service
    echo   - notification_service
    echo.
    echo Examples:
    echo   %0 market_mongodb "mongosh --eval \"db.adminCommand('ping')\""
    echo   %0 market_redis "redis-cli ping"
    exit /b 1
)

set CONTAINER_NAME=%1
shift
set COMMAND=%*

docker-compose exec %CONTAINER_NAME% sh -c "%COMMAND%"

