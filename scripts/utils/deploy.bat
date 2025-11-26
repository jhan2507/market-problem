@echo off
REM Script deploy lên environment (Windows)

setlocal enabledelayedexpansion

set ENVIRONMENT=%1
set VERSION_FILE=..\VERSION
if exist "%VERSION_FILE%" (
    set /p VERSION=<"%VERSION_FILE%"
) else (
    set VERSION=latest
)

set REGISTRY=%DOCKER_REGISTRY%
set IMAGE_PREFIX=%IMAGE_PREFIX%
if "%IMAGE_PREFIX%"=="" set IMAGE_PREFIX=market

if "%ENVIRONMENT%"=="" (
    echo ❌ Usage: scripts\deploy.bat ^<environment^>
    echo.
    echo Environments:
    echo   - staging
    echo   - production
    exit /b 1
)

if not "%ENVIRONMENT%"=="staging" if not "%ENVIRONMENT%"=="production" (
    echo ❌ Invalid environment. Use: staging or production
    exit /b 1
)

echo 🚀 Deploying to %ENVIRONMENT%...
echo Version: %VERSION%
echo.

if "%ENVIRONMENT%"=="production" (
    echo ⚠️  WARNING: You are about to deploy to PRODUCTION!
    set /p confirm="Are you sure? Type 'yes' to confirm: "
    if not "!confirm!"=="yes" (
        echo ❌ Deployment cancelled
        exit /b 0
    )
)

set ENV_FILE=.env.%ENVIRONMENT%
if not exist "%ENV_FILE%" (
    echo ⚠️  Environment file not found: %ENV_FILE%
    echo    Using default .env file
    set ENV_FILE=.env
)

set COMPOSE_FILE=docker-compose.yml
if exist "docker-compose.%ENVIRONMENT%.yml" (
    set COMPOSE_FILE=-f docker-compose.yml -f docker-compose.%ENVIRONMENT%.yml
)

set IMAGE_VERSION=%VERSION%
if not "%REGISTRY%"=="" (
    set IMAGE_REGISTRY=%REGISTRY%
    set IMAGE_PREFIX=%IMAGE_PREFIX%
)

echo 🚀 Deploying services...
docker-compose %COMPOSE_FILE% --env-file "%ENV_FILE%" up -d

echo.
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak >nul

echo.
echo 📊 Deployment status:
docker-compose %COMPOSE_FILE% ps

echo.
echo ✅ Deployment to %ENVIRONMENT% completed!

