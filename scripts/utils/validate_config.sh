#!/bin/bash
# Script validate configuration files

echo "✅ Validating Configuration"
echo "============================"
echo ""

ERRORS=0

# Check .env file
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ .env file exists"
    
    # Check required variables
    REQUIRED_VARS=("TELEGRAM_BOT_TOKEN" "CMC_API_KEY")
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^${var}=" .env && ! grep -q "^${var}=$" .env && ! grep -q "^${var}=your_" .env; then
            echo "✅ $var: Set"
        else
            echo "⚠️  $var: Not set or using placeholder"
        fi
    done
fi
echo ""

# Check docker-compose.yml
if [ ! -f docker-compose.yml ]; then
    echo "❌ docker-compose.yml not found"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ docker-compose.yml exists"
    
    # Validate YAML syntax
    if docker-compose config > /dev/null 2>&1; then
        echo "✅ docker-compose.yml: Valid syntax"
    else
        echo "❌ docker-compose.yml: Invalid syntax"
        ERRORS=$((ERRORS + 1))
    fi
fi
echo ""

# Check VERSION file
if [ ! -f VERSION ]; then
    echo "⚠️  VERSION file not found (will use default)"
else
    VERSION=$(cat VERSION)
    if [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "✅ VERSION: $VERSION (valid format)"
    else
        echo "⚠️  VERSION: $VERSION (invalid format, should be X.Y.Z)"
    fi
fi
echo ""

# Check required directories
REQUIRED_DIRS=("shared" "services" "scripts")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ Directory: $dir"
    else
        echo "❌ Directory missing: $dir"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Check service directories
SERVICES=("market_data_service" "market_analyzer_service" "price_service" "signal_service" "notification_service")
for service in "${SERVICES[@]}"; do
    if [ -d "services/$service" ]; then
        if [ -f "services/$service/main.py" ]; then
            echo "✅ Service: $service (main.py exists)"
        else
            echo "⚠️  Service: $service (main.py missing)"
        fi
        if [ -f "services/$service/Dockerfile" ]; then
            echo "✅ Service: $service (Dockerfile exists)"
        else
            echo "⚠️  Service: $service (Dockerfile missing)"
        fi
    else
        echo "❌ Service directory missing: $service"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "✅ Configuration validation passed!"
else
    echo "❌ Configuration validation failed with $ERRORS error(s)"
    exit 1
fi

