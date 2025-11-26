# Access Docker Containers

Hướng dẫn sử dụng các script để truy cập và thao tác với Docker containers.

## Scripts

### 1. `access.sh` - Interactive Menu

Script menu tương tác để truy cập các container một cách dễ dàng.

```bash
./scripts/utils/access.sh
```

**Menu options:**
1. MongoDB Shell (mongosh) - Truy cập MongoDB database
2. Redis CLI - Truy cập Redis
3-7. Service Shells - Mở shell trong các service containers
8. List containers - Xem danh sách containers đang chạy
9. Execute custom command - Thực thi lệnh tùy chỉnh
0. Exit

### 2. `exec.sh` - Execute Command

Thực thi một lệnh trong container.

```bash
./scripts/utils/exec.sh <container_name> <command>
```

**Examples:**

```bash
# MongoDB - Ping database
./scripts/utils/exec.sh market_mongodb 'mongosh --eval "db.adminCommand(\"ping\")"'

# MongoDB - List databases
./scripts/utils/exec.sh market_mongodb 'mongosh --eval "db.adminCommand(\"listDatabases\")"'

# Redis - Ping
./scripts/utils/exec.sh market_redis 'redis-cli ping'

# Redis - Get all keys
./scripts/utils/exec.sh market_redis 'redis-cli keys "*"'

# Service - Check Python version
./scripts/utils/exec.sh signal_service 'python --version'

# Service - List files
./scripts/utils/exec.sh signal_service 'ls -la'

# Service - Check environment variables
./scripts/utils/exec.sh signal_service 'env | grep -E "MONGODB|REDIS"'
```

### 3. `shell.sh` - Open Shell

Mở interactive shell trong container.

```bash
./scripts/utils/shell.sh <container_name> [shell]
```

**Parameters:**
- `container_name`: Tên container (required)
- `shell`: Loại shell (`sh` hoặc `bash`, default: `sh`)

**Examples:**

```bash
# Open sh shell
./scripts/utils/shell.sh market_mongodb

# Open bash shell (if available)
./scripts/utils/shell.sh signal_service bash

# Open Redis CLI (alternative)
./scripts/utils/shell.sh market_redis
```

## Available Containers

- `market_mongodb` - MongoDB database
- `market_redis` - Redis cache/streams
- `market_data_service` - Market data collection service
- `market_analyzer_service` - Market analysis service
- `price_service` - Price monitoring service
- `signal_service` - Signal generation service
- `notification_service` - Telegram notification service

## Common Use Cases

### MongoDB Operations

```bash
# Access MongoDB shell
./scripts/utils/access.sh
# Select option 1

# Or directly
./scripts/utils/exec.sh market_mongodb 'mongosh --authenticationDatabase admin -u admin -p password'

# Query signals collection
./scripts/utils/exec.sh market_mongodb 'mongosh --authenticationDatabase admin -u admin -p password --eval "db.signals.find().sort({timestamp: -1}).limit(5).pretty()"'

# Count documents
./scripts/utils/exec.sh market_mongodb 'mongosh --authenticationDatabase admin -u admin -p password --eval "db.signals.countDocuments()"'
```

### Redis Operations

```bash
# Access Redis CLI
./scripts/utils/access.sh
# Select option 2

# Or directly
./scripts/utils/shell.sh market_redis

# Check Redis info
./scripts/utils/exec.sh market_redis 'redis-cli info'

# List all streams
./scripts/utils/exec.sh market_redis 'redis-cli XINFO STREAM market_analysis_completed'
```

### Service Debugging

```bash
# Check service logs from inside container
./scripts/utils/exec.sh signal_service 'ls -la /app'

# Check Python environment
./scripts/utils/exec.sh signal_service 'python -c "import sys; print(sys.path)"'

# Check installed packages
./scripts/utils/exec.sh signal_service 'pip list'

# View environment variables
./scripts/utils/exec.sh signal_service 'env'
```

### Interactive Debugging

```bash
# Open shell in service for interactive debugging
./scripts/utils/shell.sh signal_service bash

# Inside container, you can:
# - Run Python scripts
# - Check files
# - Test imports
# - Debug issues
```

## Windows Users

Sử dụng các file `.bat` tương ứng:

```cmd
scripts\utils\exec.bat market_mongodb "mongosh --eval \"db.adminCommand('ping')\""
scripts\utils\shell.bat signal_service
```

## Tips

1. **Check container status first:**
   ```bash
   docker ps
   ```

2. **Use interactive menu for convenience:**
   ```bash
   ./scripts/utils/access.sh
   ```

3. **For complex commands, use shell:**
   ```bash
   ./scripts/utils/shell.sh signal_service bash
   ```

4. **Escape quotes properly in exec.sh:**
   ```bash
   # Use single quotes for outer, double quotes for inner
   ./scripts/utils/exec.sh market_mongodb 'mongosh --eval "db.adminCommand(\"ping\")"'
   ```

## Troubleshooting

**Container not running:**
```bash
# Check status
docker ps

# Start container if needed
docker-compose start <container_name>
```

**Permission denied:**
```bash
# Make scripts executable
chmod +x scripts/utils/*.sh
```

**Command not found in container:**
```bash
# Check available commands
./scripts/utils/exec.sh <container_name> 'which <command>'

# Use sh instead of bash
./scripts/utils/shell.sh <container_name> sh
```

