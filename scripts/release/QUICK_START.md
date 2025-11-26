# Quick Start - Go Live

Hướng dẫn nhanh để golive code lên production.

## 🚀 Go Live từ Staging

```bash
./scripts/release/golive.sh staging
```

Script sẽ tự động:
1. ✅ Validate environment
2. ✅ Bump version (bạn chọn patch/minor/major)
3. ✅ Merge staging → master
4. ✅ Tạo git tag
5. ✅ Build Docker images
6. ✅ Generate release notes
7. ✅ Push to remote
8. ✅ Deploy to production

## 📋 Workflow

```
develop → staging → master (production)
           ↓
    Test trên staging
           ↓
    ./scripts/release/golive.sh staging
           ↓
    Production live!
```

## ⚠️ Safety Checks

Script có các safety checks:
- ✅ Yêu cầu xác nhận "GOLIVE"
- ✅ Validate production config
- ✅ Check conflicts trước khi merge
- ✅ Confirm trước khi push và deploy

## 🔄 Rollback (nếu cần)

Nếu có vấn đề sau khi golive:

```bash
./scripts/release/rollback.sh production [version]
```

## 📊 Monitor sau Go Live

```bash
# Real-time monitor
./scripts/monitor/monitor.sh

# Health check
./scripts/monitor/health.sh

# View logs
./scripts/monitor/logs.sh
```

