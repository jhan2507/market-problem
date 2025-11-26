@echo off
REM Script cleanup hệ thống (Windows)

echo 🧹 Cleaning up system...

REM Dừng và xóa containers
echo 🛑 Stopping containers...
docker-compose down

echo.
set /p confirm="⚠️  Delete volumes? This will remove all data! (yes/no): "
if /i "%confirm%"=="yes" (
    echo 🗑️  Removing volumes...
    docker-compose down -v
    echo ✅ Volumes removed
) else (
    echo ℹ️  Volumes kept
)

echo.
set /p confirm="🗑️  Remove Docker images? (yes/no): "
if /i "%confirm%"=="yes" (
    echo 🗑️  Removing images...
    docker-compose down --rmi all
    echo ✅ Images removed
) else (
    echo ℹ️  Images kept
)

REM Xóa old logs
echo 🧹 Cleaning old logs...
docker system prune -f

echo.
echo ✅ Cleanup completed!

