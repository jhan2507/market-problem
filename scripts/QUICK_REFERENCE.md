# Quick Reference Guide

## 🚀 Quick Start

```bash
# Menu chính
./scripts/index.sh

# Hoặc quick start
./scripts/quick_start.sh
```

## 📋 Common Tasks

### Start/Stop/Rebuild
```bash
./scripts/deploy/start.sh              # Start system
./scripts/deploy/stop.sh               # Stop system
./scripts/deploy/restart.sh            # Restart (no rebuild)
./scripts/deploy/rebuild.sh            # Rebuild all with new code
./scripts/deploy/rebuild_service.sh [service]  # Rebuild one service
```

### Monitor
```bash
./scripts/monitor/status.sh      # Quick status
./scripts/monitor/health.sh      # Health check
./scripts/monitor/monitor.sh     # Real-time
```

### Logs
```bash
./scripts/monitor/logs.sh                    # All services
./scripts/monitor/logs.sh signal_service     # One service
```

### Backup
```bash
./scripts/utils/backup.sh
./scripts/utils/restore.sh [file]
```

### Release
```bash
./scripts/release/release.sh              # Create release
./scripts/release/deploy.sh staging       # Deploy staging
./scripts/release/deploy.sh production    # Deploy production
./scripts/release/rollback.sh production  # Rollback
```

## 🔍 Troubleshooting

| Problem | Solution |
|---------|----------|
| Service not starting | `./scripts/utils/validate_config.sh` |
| Code changes not applied | `./scripts/deploy/rebuild.sh` or `./scripts/deploy/rebuild_service.sh [service]` |
| Connection issues | `./scripts/monitor/test_connection.sh` |
| Health problems | `./scripts/monitor/health.sh` |
| Need to rollback | `./scripts/release/rollback.sh [env]` |
| Check dependencies | `./scripts/utils/check_dependencies.sh` |

## 📊 Monitoring Checklist

- [ ] `./scripts/monitor/status.sh` - System status
- [ ] `./scripts/monitor/health.sh` - Health check
- [ ] `./scripts/monitor/metrics.sh` - Resource usage
- [ ] `./scripts/monitor/test_connection.sh` - Connections
- [ ] `./scripts/monitor/logs.sh` - Recent logs

## 🚀 Deployment Checklist

- [ ] `./scripts/utils/validate_config.sh` - Validate config
- [ ] `./scripts/utils/check_dependencies.sh` - Check deps
- [ ] `./scripts/utils/backup.sh` - Backup database
- [ ] `./scripts/release/release.sh` - Create release
- [ ] `./scripts/release/deploy.sh staging` - Deploy staging
- [ ] Test staging environment
- [ ] `./scripts/release/deploy.sh production` - Deploy production
- [ ] Monitor after deployment

