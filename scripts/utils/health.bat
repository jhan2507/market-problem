@echo off
REM Script kiểm tra health của từng service (Windows)

echo 🏥 Health Check
echo ==============
echo.

REM Kiểm tra containers
docker-compose ps

echo.
echo 🔍 Connection Tests:
echo.

REM Kiểm tra MongoDB
docker-compose exec -T mongodb mongosh --quiet --eval "db.adminCommand('ping')" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ MongoDB connection: OK
) else (
    echo ❌ MongoDB connection: FAILED
)

REM Kiểm tra Redis
docker-compose exec -T redis redis-cli ping >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Redis connection: OK
) else (
    echo ❌ Redis connection: FAILED
)

echo.
echo 📊 Recent Errors:
echo ----------------------------------------------
for %%s in (market_data_service market_analyzer_service price_service signal_service notification_service) do (
    docker-compose logs --tail=50 %%s 2>&1 | findstr /i "error exception failed" >nul
    if !ERRORLEVEL! EQU 0 (
        echo.
        echo ⚠️  %%s:
        docker-compose logs --tail=50 %%s 2>&1 | findstr /i "error exception failed" | findstr /n "^" | findstr "^[1-3]:"
    )
)

