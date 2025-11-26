#!/bin/bash
# Script kiểm tra dependencies và prerequisites

echo "🔍 Checking Dependencies"
echo "========================"
echo ""

ERRORS=0
WARNINGS=0

# Check Docker
echo "🐳 Docker:"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "✅ Installed: $DOCKER_VERSION"
    
    # Check if Docker daemon is running
    if docker info > /dev/null 2>&1; then
        echo "✅ Daemon: Running"
    else
        echo "❌ Daemon: Not running"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "❌ Not installed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check Docker Compose
echo "🐙 Docker Compose:"
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo "✅ Installed: $COMPOSE_VERSION"
else
    echo "❌ Not installed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check Python (for local development)
echo "🐍 Python:"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Installed: $PYTHON_VERSION"
    
    # Check required packages
    if python3 -c "import pymongo, redis, pandas, numpy" 2>/dev/null; then
        echo "✅ Required packages: Installed"
    else
        echo "⚠️  Required packages: Some missing (install with: pip install -r requirements.txt)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "⚠️  Not installed (optional for local development)"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check Git (for version management)
echo "📦 Git:"
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    echo "✅ Installed: $GIT_VERSION"
else
    echo "⚠️  Not installed (optional for version management)"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check disk space
echo "💾 Disk Space:"
DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo "✅ Available: ${DISK_USAGE}% used"
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo "⚠️  Warning: ${DISK_USAGE}% used"
    WARNINGS=$((WARNINGS + 1))
else
    echo "❌ Critical: ${DISK_USAGE}% used"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check Docker resources
echo "🔧 Docker Resources:"
if docker info > /dev/null 2>&1; then
    # Check if enough memory
    MEMORY_GB=$(docker info 2>/dev/null | grep "Total Memory" | awk '{print $3}' | sed 's/GiB//')
    if [ ! -z "$MEMORY_GB" ]; then
        if (( $(echo "$MEMORY_GB >= 2" | bc -l) )); then
            echo "✅ Memory: ${MEMORY_GB}GB (sufficient)"
        else
            echo "⚠️  Memory: ${MEMORY_GB}GB (recommend at least 2GB)"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
fi
echo ""

# Summary
echo "================================"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ All checks passed!"
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Checks passed with $WARNINGS warning(s)"
else
    echo "❌ Checks failed with $ERRORS error(s) and $WARNINGS warning(s)"
    exit 1
fi

