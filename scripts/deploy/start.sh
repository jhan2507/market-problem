#!/bin/bash
# Script khởi động hệ thống

echo "🚀 Starting Crypto Market Monitoring System..."

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
        echo "⚠️  You need to set:"
        echo "   - CMC_API_KEY"
        echo "   - TELEGRAM_BOT_TOKEN"
        echo "   - TELEGRAM_PRICE_CHAT_ID"
        echo "   - TELEGRAM_SIGNAL_CHAT_ID"
        exit 1
    else
        echo "❌ env.example not found. Cannot create .env file."
        exit 1
    fi
fi

# Build và start services
echo "📦 Building and starting services..."
docker-compose up -d --build

# Đợi services khởi động
echo "⏳ Waiting for services to start..."
sleep 10

# Kiểm tra health
echo "🔍 Checking service health..."
docker-compose ps

echo ""
echo "✅ System started successfully!"
echo ""
echo "📊 View logs: ./scripts/monitor/logs.sh"
echo "📈 Monitor services: ./scripts/monitor/status.sh"
echo "🛑 Stop system: ./scripts/deploy/stop.sh"

