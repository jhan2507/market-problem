@echo off
REM Script build Docker images với version (Windows)

setlocal enabledelayedexpansion

set VERSION_FILE=..\VERSION
if exist "%VERSION_FILE%" (
    set /p VERSION=<"%VERSION_FILE%"
) else (
    set VERSION=0.0.0
)

set REGISTRY=%DOCKER_REGISTRY%
set IMAGE_PREFIX=%IMAGE_PREFIX%
if "%IMAGE_PREFIX%"=="" set IMAGE_PREFIX=market

echo 🔨 Building Docker images...
echo Version: %VERSION%
echo.

set SERVICES=market_data_service market_analyzer_service price_service signal_service notification_service

for %%s in (%SERVICES%) do (
    set service=%%s
    set service_name=!service:_=-!
    set image_name=%IMAGE_PREFIX%-!service_name!
    
    if not "%REGISTRY%"=="" (
        set full_image=%REGISTRY%\!image_name!
    ) else (
        set full_image=!image_name!
    )
    
    echo 📦 Building %%s...
    echo    Image: !full_image!:%VERSION%
    echo    Image: !full_image!:latest
    
    docker build -f services\%%s\Dockerfile -t !full_image!:%VERSION% -t !full_image!:latest .
    
    echo ✅ %%s built successfully
    echo.
)

echo ✅ All images built successfully!

