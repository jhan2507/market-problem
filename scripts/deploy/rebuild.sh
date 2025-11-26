#!/bin/bash
# Script rebuild và restart toàn bộ hệ thống với code mới

echo "🔨 Rebuilding Crypto Market Monitoring System..."

# Kiểm tra Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Kiểm tra file .env
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from env.example..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ Created .env file. Please edit it with your configuration."
        exit 1
    else
        echo "❌ env.example not found. Cannot create .env file."
        exit 1
    fi
fi

# Build lại tất cả images
echo "📦 Building all Docker images..."
docker-compose build --no-cache

if [ $? -ne 0 ]; then
    echo "❌ Failed to build images"
    exit 1
fi

# Stop tất cả services
echo "🛑 Stopping all services..."
docker-compose down

# Start lại với images mới
echo "🚀 Starting services with new images..."
docker-compose up -d

# Đợi services khởi động
echo "⏳ Waiting for services to start..."
sleep 10

# Kiểm tra health
echo "🔍 Checking service health..."
docker-compose ps

echo ""
echo "✅ System rebuilt and restarted successfully!"
echo ""
echo "📊 View logs: ./scripts/monitor/logs.sh"
echo "📈 Monitor services: ./scripts/monitor/status.sh"
echo "🛑 Stop system: ./scripts/deploy/stop.sh"

