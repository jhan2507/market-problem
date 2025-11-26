@echo off
REM Script xem thống kê hệ thống (Windows)

echo 📊 System Statistics
echo ====================
echo.

REM MongoDB Statistics
echo 🗄️  MongoDB Statistics:
echo ----------------------
docker-compose exec -T mongodb mongosh --quiet --eval "db = db.getSiblingDB('market'); print('market_data:', db.market_data.countDocuments()); print('analysis:', db.analysis.countDocuments()); print('signals:', db.signals.countDocuments()); print('price_updates:', db.price_updates.countDocuments()); print('logs:', db.logs.countDocuments());"

echo.
echo 💡 View detailed stats: docker stats

