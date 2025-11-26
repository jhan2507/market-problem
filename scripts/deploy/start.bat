@echo off
REM Script khởi động hệ thống (Windows)

echo 🚀 Starting Crypto Market Monitoring System...

REM Kiểm tra Docker
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker is not installed. Please install Docker first.
    exit /b 1
)

where docker-compose >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Kiểm tra file .env
if not exist .env (
    echo ⚠️  .env file not found. Creating from env.example...
    if exist env.example (
        copy env.example .env >nul
        echo ✅ Created .env file. Please edit it with your configuration.
        echo ⚠️  You need to set:
        echo    - CMC_API_KEY
        echo    - TELEGRAM_BOT_TOKEN
        echo    - TELEGRAM_PRICE_CHAT_ID
        echo    - TELEGRAM_SIGNAL_CHAT_ID
        exit /b 1
    ) else (
        echo ❌ env.example not found. Cannot create .env file.
        exit /b 1
    )
)

REM Build và start services
echo 📦 Building and starting services...
docker-compose up -d --build

REM Đợi services khởi động
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Kiểm tra health
echo 🔍 Checking service health...
docker-compose ps

echo.
echo ✅ System started successfully!
echo.
echo 📊 View logs: scripts\logs.bat
echo 📈 Monitor services: scripts\status.bat
echo 🛑 Stop system: scripts\stop.bat

