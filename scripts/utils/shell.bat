@echo off
REM Script to open interactive shell in Docker containers

if "%1"=="" (
    echo Usage: %0 ^<container_name^> [shell]
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
    echo   %0 market_mongodb
    echo   %0 market_redis
    echo   %0 signal_service
    exit /b 1
)

set CONTAINER_NAME=%1
set SHELL_TYPE=%2
if "%SHELL_TYPE%"=="" set SHELL_TYPE=sh

docker-compose exec %CONTAINER_NAME% %SHELL_TYPE%

