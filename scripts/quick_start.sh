#!/bin/bash
# Quick start guide script

echo "🚀 Crypto Market Monitoring System - Quick Start"
echo "=============================================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "   Install from: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "✅ Docker installed"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    echo "   Install from: https://docs.docker.com/compose/install/"
    exit 1
fi
echo "✅ Docker Compose installed"

# Check .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found"
    if [ -f env.example ]; then
        echo "   Creating .env from env.example..."
        cp env.example .env
        echo "✅ .env created"
        echo ""
        echo "⚠️  IMPORTANT: Edit .env file with your configuration:"
        echo "   - CMC_API_KEY"
        echo "   - TELEGRAM_BOT_TOKEN"
        echo "   - TELEGRAM_PRICE_CHAT_ID"
        echo "   - TELEGRAM_SIGNAL_CHAT_ID"
        echo ""
        read -p "Press Enter after editing .env file..."
    else
        echo "❌ env.example not found"
        exit 1
    fi
else
    echo "✅ .env file exists"
fi

echo ""
echo "🎯 What would you like to do?"
echo ""
echo "1. Start system (development)"
echo "2. Create release and deploy to staging"
echo "3. Deploy to production"
echo "4. View documentation"
echo "5. Exit"
echo ""
read -p "Choice [1-5]: " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting development environment..."
        ./scripts/start.sh
        ;;
    2)
        echo ""
        echo "📦 Creating release..."
        ./scripts/release.sh
        echo ""
        echo "🚀 Deploying to staging..."
        ./scripts/deploy.sh staging
        ;;
    3)
        echo ""
        echo "⚠️  WARNING: Production deployment!"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            ./scripts/deploy.sh production
        else
            echo "❌ Cancelled"
        fi
        ;;
    4)
        echo ""
        echo "📚 Documentation:"
        echo "   - README.md - Main documentation"
        echo "   - scripts/README.md - Scripts documentation"
        echo "   - scripts/RELEASE.md - Release management"
        ;;
    5)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

