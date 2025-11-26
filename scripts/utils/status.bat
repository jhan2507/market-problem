@echo off
REM Script kiểm tra trạng thái hệ thống (Windows)

echo 📈 System Status
echo ================
echo.

REM Kiểm tra containers
echo 🐳 Docker Containers:
docker-compose ps
echo.

REM Kiểm tra MongoDB
echo 🗄️  MongoDB Status:
docker-compose exec -T mongodb mongosh --quiet --eval "db.adminCommand('ping')" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ MongoDB is running
    echo.
    echo 📊 Database Statistics:
    docker-compose exec -T mongodb mongosh --quiet --eval "db = db.getSiblingDB('market'); print('market_data:', db.market_data.countDocuments()); print('analysis:', db.analysis.countDocuments()); print('signals:', db.signals.countDocuments()); print('price_updates:', db.price_updates.countDocuments()); print('logs:', db.logs.countDocuments());"
) else (
    echo ❌ MongoDB is not accessible
)
echo.

REM Kiểm tra Redis
echo 📮 Redis Status:
docker-compose exec -T redis redis-cli ping >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Redis is running
) else (
    echo ❌ Redis is not accessible
)
echo.

REM Kiểm tra services
echo 🔧 Services Status:
docker-compose ps market_data_service | findstr "Up" >nul && echo ✅ market_data_service: Running || echo ❌ market_data_service: Not running
docker-compose ps market_analyzer_service | findstr "Up" >nul && echo ✅ market_analyzer_service: Running || echo ❌ market_analyzer_service: Not running
docker-compose ps price_service | findstr "Up" >nul && echo ✅ price_service: Running || echo ❌ price_service: Not running
docker-compose ps signal_service | findstr "Up" >nul && echo ✅ signal_service: Running || echo ❌ signal_service: Not running
docker-compose ps notification_service | findstr "Up" >nul && echo ✅ notification_service: Running || echo ❌ notification_service: Not running

echo.
echo 💡 Tips:
echo   - View logs: scripts\logs.bat [service_name]
echo   - Restart service: docker-compose restart [service_name]
echo   - View detailed logs: docker-compose logs --tail=100 [service_name]

