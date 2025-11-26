#!/bin/bash
# Script cleanup hệ thống

echo "🧹 Cleaning up system..."

# Dừng và xóa containers
echo "🛑 Stopping containers..."
docker-compose down

# Xóa volumes (dữ liệu sẽ bị mất!)
read -p "⚠️  Delete volumes? This will remove all data! (yes/no): " confirm
if [ "$confirm" == "yes" ]; then
    echo "🗑️  Removing volumes..."
    docker-compose down -v
    echo "✅ Volumes removed"
else
    echo "ℹ️  Volumes kept"
fi

# Xóa images
read -p "🗑️  Remove Docker images? (yes/no): " confirm
if [ "$confirm" == "yes" ]; then
    echo "🗑️  Removing images..."
    docker-compose down --rmi all
    echo "✅ Images removed"
else
    echo "ℹ️  Images kept"
fi

# Xóa old logs
echo "🧹 Cleaning old logs..."
docker system prune -f

echo ""
echo "✅ Cleanup completed!"

