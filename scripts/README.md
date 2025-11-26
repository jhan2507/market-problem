# Scripts Documentation

Tài liệu hướng dẫn sử dụng các scripts quản lý và theo dõi hệ thống.

> **📋 Standards**: Xem [STANDARDS.md](./STANDARDS.md) để biết các chuẩn coding và best practices.
> **📝 Template**: Xem [TEMPLATE.sh](./TEMPLATE.sh) để có template chuẩn cho scripts mới.

## Cấu trúc thư mục

Scripts được tổ chức theo tính năng:

```
scripts/
├── index.sh              # Main entry point - menu chính
├── quick_start.sh        # Quick start guide
├── TEMPLATE.sh           # Template chuẩn cho scripts mới
├── STANDARDS.md          # Coding standards và best practices
│
├── deploy/               # Deployment scripts
│   ├── start.sh
│   ├── stop.sh
│   ├── restart.sh
│   ├── rebuild.sh        # Rebuild system with new code
│   ├── restart_service.sh
│   ├── rebuild_service.sh # Rebuild service with new code
│   └── *.bat (Windows versions)
│
├── monitor/              # Monitoring scripts
│   ├── logs.sh
│   ├── status.sh
│   ├── health.sh
│   ├── stats.sh
│   ├── monitor.sh
│   ├── metrics.sh
│   └── test_connection.sh
│
├── utils/                # Utility scripts
│   ├── backup.sh
│   ├── restore.sh
│   ├── export_data.sh
│   ├── import_data.sh
│   ├── validate_config.sh
│   ├── check_dependencies.sh
│   ├── scale.sh
│   ├── exec.sh           # Execute commands in containers
│   ├── shell.sh          # Open shell in containers
│   └── access.sh         # Interactive container access menu
│
└── release/              # Release management
    ├── version.sh
    ├── build.sh
    ├── push.sh
    ├── release.sh
    ├── deploy.sh
    ├── rollback.sh
    ├── release_notes.sh
    └── ci.sh
```

## Sử dụng

### Menu chính (Khuyến nghị)

```bash
./scripts/index.sh
```

Menu tương tác với tất cả các tùy chọn được phân loại.

### Hoặc chạy trực tiếp

```bash
# Deployment
./scripts/deploy/start.sh
./scripts/deploy/stop.sh

# Monitoring
./scripts/monitor/status.sh
./scripts/monitor/logs.sh [service]

# Utilities
./scripts/utils/backup.sh
./scripts/utils/validate_config.sh

# Release
./scripts/release/version.sh show
./scripts/release/deploy.sh staging
```

## 📦 DEPLOYMENT

### Start System
```bash
./scripts/deploy/start.sh
```
Khởi động toàn bộ hệ thống.

### Stop System
```bash
./scripts/deploy/stop.sh
```
Dừng toàn bộ hệ thống.

### Restart System
```bash
./scripts/deploy/restart.sh
```
Restart toàn bộ hệ thống (không rebuild images).

### Rebuild System (with new code)
```bash
./scripts/deploy/rebuild.sh
```
Rebuild tất cả Docker images với code mới và restart hệ thống.
- Build lại tất cả images với `--no-cache`
- Stop tất cả services
- Start lại với images mới

**Lưu ý:** Sử dụng script này sau khi bạn đã cập nhật code và muốn áp dụng code mới.

### Restart Service
```bash
./scripts/deploy/restart_service.sh [service_name]
```
Restart một service cụ thể (không rebuild image).

### Rebuild Service (with new code)
```bash
./scripts/deploy/rebuild_service.sh [service_name]
```
Rebuild Docker image cho một service cụ thể với code mới và restart service.
- Build lại image với `--no-cache`
- Stop service
- Remove container cũ
- Start lại với image mới

**Lưu ý:** Sử dụng script này khi bạn chỉ sửa một service và muốn áp dụng code mới nhanh hơn.

**Ví dụ:**
```bash
# Rebuild notification_service sau khi sửa code
./scripts/deploy/rebuild_service.sh notification_service
```

## 📊 MONITORING

### View Logs
```bash
# Tất cả services
./scripts/monitor/logs.sh

# Một service cụ thể
./scripts/monitor/logs.sh market_data_service
```

### System Status
```bash
./scripts/monitor/status.sh
```
Hiển thị:
- Container status
- MongoDB statistics
- Redis statistics
- Service health

### Health Check
```bash
./scripts/monitor/health.sh
```
Kiểm tra health của từng service và connections.

### Statistics
```bash
./scripts/monitor/stats.sh
```
Xem thống kê chi tiết:
- MongoDB collections
- Redis streams
- Container resource usage

### Real-time Monitor
```bash
./scripts/monitor/monitor.sh
```
Monitor real-time với auto-refresh (Ctrl+C để thoát).

### Metrics
```bash
./scripts/monitor/metrics.sh
```
Xem metrics chi tiết:
- Container CPU/Memory
- MongoDB storage stats
- Redis performance metrics

### Test Connections
```bash
./scripts/monitor/test_connection.sh
```
Test kết nối giữa các services:
- MongoDB connection
- Redis connection
- Service-to-service connections

## 🔧 UTILITIES

### Backup Database
```bash
./scripts/utils/backup.sh
```
Tạo backup MongoDB, tự động nén và giữ 10 backups gần nhất.

### Restore Database
```bash
./scripts/utils/restore.sh backups/market_backup_20240101_120000.archive.gz
```

### Export Data
```bash
./scripts/utils/export_data.sh
```
Export tất cả collections ra JSON files.

### Import Data
```bash
./scripts/utils/import_data.sh exports/export_20240101_120000.tar.gz
```

### Validate Config
```bash
./scripts/utils/validate_config.sh
```
Kiểm tra:
- .env file
- docker-compose.yml syntax
- VERSION file format
- Required directories
- Service files

### Check Dependencies
```bash
./scripts/utils/check_dependencies.sh
```
Kiểm tra:
- Docker & Docker Compose
- Python & packages
- Git
- Disk space
- Docker resources

### Scale Service
```bash
./scripts/utils/scale.sh price_service 3
```
Tăng/giảm số lượng instances của một service.

### Access Containers

#### Interactive Menu
```bash
./scripts/utils/access.sh
```
Menu tương tác để access các container:
- MongoDB Shell (mongosh)
- Redis CLI
- Service shells (bash/sh)
- List running containers
- Execute custom commands

#### Execute Command in Container
```bash
./scripts/utils/exec.sh <container_name> <command>
```
Thực thi lệnh trong container.

**Examples:**
```bash
# MongoDB
./scripts/utils/exec.sh market_mongodb 'mongosh --eval "db.adminCommand(\"ping\")"'

# Redis
./scripts/utils/exec.sh market_redis 'redis-cli ping'

# Service
./scripts/utils/exec.sh signal_service 'python --version'
```

**Available containers:**
- `market_mongodb`
- `market_redis`
- `market_data_service`
- `market_analyzer_service`
- `price_service`
- `signal_service`
- `notification_service`

#### Open Shell in Container
```bash
./scripts/utils/shell.sh <container_name> [shell]
```
Mở interactive shell trong container (mặc định: `sh`, có thể dùng `bash`).

**Examples:**
```bash
./scripts/utils/shell.sh market_mongodb
./scripts/utils/shell.sh signal_service bash
./scripts/utils/shell.sh market_redis
```

## 🚀 RELEASE

Xem chi tiết trong [RELEASE.md](RELEASE.md)

### Version Management
```bash
./scripts/release/version.sh show
./scripts/release/version.sh bump patch
```

### Build Images
```bash
./scripts/release/build.sh
```

### Push Images
```bash
./scripts/release/push.sh
```

### Create Release
```bash
./scripts/release/release.sh
```

### Deploy
```bash
./scripts/release/deploy.sh staging
./scripts/release/deploy.sh production
```

### Rollback
```bash
./scripts/release/rollback.sh production
```

## Quick Reference

### Khởi động nhanh
```bash
./scripts/index.sh
# Hoặc
./scripts/quick_start.sh
```

### Kiểm tra hệ thống
```bash
./scripts/utils/validate_config.sh
./scripts/utils/check_dependencies.sh
./scripts/monitor/test_connection.sh
./scripts/monitor/health.sh
```

### Backup trước khi deploy
```bash
./scripts/utils/backup.sh
./scripts/release/deploy.sh production
```

### Monitor sau deploy
```bash
./scripts/monitor/monitor.sh
./scripts/monitor/metrics.sh
```

## Troubleshooting

### Service không start
1. Validate config: `./scripts/utils/validate_config.sh`
2. Check dependencies: `./scripts/utils/check_dependencies.sh`
3. Test connections: `./scripts/monitor/test_connection.sh`
4. View logs: `./scripts/monitor/logs.sh [service]`

### Deployment failed
1. Check config: `./scripts/utils/validate_config.sh`
2. Check health: `./scripts/monitor/health.sh`
3. View logs: `./scripts/monitor/logs.sh`
4. Rollback: `./scripts/release/rollback.sh [environment]`

### Performance issues
1. Check metrics: `./scripts/monitor/metrics.sh`
2. Check resources: `docker stats`
3. Scale service: `./scripts/utils/scale.sh [service] [replicas]`

## Best Practices

1. **Trước khi deploy:**
   - Validate config
   - Check dependencies
   - Backup database
   - Test connections

2. **Sau khi deploy:**
   - Health check
   - Monitor logs
   - Check metrics
   - Verify functionality

3. **Regular maintenance:**
   - Backup định kỳ
   - Monitor metrics
   - Check disk space
   - Review logs
