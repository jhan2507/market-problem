@echo off
REM Script rebuild và restart toàn bộ hệ thống với code mới (Windows)

echo 🔨 Rebuilding Crypto Market Monitoring System...

REM Kiểm tra file .env
if not exist .env (
    echo ⚠️  .env file not found. Creating from env.example...
    if exist env.example (
        copy env.example .env
        echo ✅ Created .env file. Please edit it with your configuration.
        exit /b 1
    ) else (
        echo ❌ env.example not found. Cannot create .env file.
        exit /b 1
    )
)

REM Build lại tất cả images
echo 📦 Building all Docker images...
docker-compose build --no-cache

if errorlevel 1 (
    echo ❌ Failed to build images
    exit /b 1
)

REM Stop tất cả services
echo 🛑 Stopping all services...
docker-compose down

REM Start lại với images mới
echo 🚀 Starting services with new images...
docker-compose up -d

REM Đợi services khởi động
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Kiểm tra health
echo 🔍 Checking service health...
docker-compose ps

echo.
echo ✅ System rebuilt and restarted successfully!
echo.
echo 📊 View logs: scripts\monitor\logs.bat
echo 📈 Monitor services: scripts\monitor\status.bat
echo 🛑 Stop system: scripts\deploy\stop.bat

