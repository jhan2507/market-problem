@echo off
REM Script restart hệ thống (Windows)

echo 🔄 Restarting Crypto Market Monitoring System...

docker-compose restart

echo.
echo ✅ System restarted successfully!
echo.
echo 📊 View logs: scripts\logs.bat

