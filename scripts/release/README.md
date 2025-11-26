# Release Management Scripts

Scripts quản lý release và deployment.

## 🚀 Go Live (Quick Start)

### golive.sh
**Script nhanh nhất để golive code lên production**

```bash
./scripts/release/golive.sh [source_branch] [skip_build]
```

**Workflow tự động:**
1. ✅ Validate environment
2. ✅ Bump version (patch/minor/major)
3. ✅ Merge source branch vào master
4. ✅ Tạo git tag
5. ✅ Build Docker images
6. ✅ Generate release notes
7. ✅ Push to remote
8. ✅ Deploy to production

**Examples:**
```bash
# Go live từ staging (khuyến nghị)
./scripts/release/golive.sh staging

# Go live từ develop
./scripts/release/golive.sh develop

# Go live và skip build
./scripts/release/golive.sh staging true
```

**⚠️ Safety:** Yêu cầu xác nhận "GOLIVE" trước khi thực hiện.

## 📋 Manual Release Process

### 1. Version Management

```bash
# Xem version
./scripts/release/version.sh show

# Bump version
./scripts/release/version.sh bump patch   # 0.0.X
./scripts/release/version.sh bump minor   # 0.X.0
./scripts/release/version.sh bump major   # X.0.0
```

### 2. Build Images

```bash
./scripts/release/build.sh
```

### 3. Push Images (nếu dùng registry)

```bash
export DOCKER_REGISTRY=registry.example.com
./scripts/release/push.sh
```

### 4. Deploy

```bash
# Staging
./scripts/release/deploy.sh staging

# Production
./scripts/release/deploy.sh production
```

### 5. Rollback (nếu cần)

```bash
./scripts/release/rollback.sh production [version]
```

## Workflow Comparison

### Quick Go Live (Khuyến nghị)
```bash
./scripts/release/golive.sh staging
```
→ Tự động tất cả các bước

### Manual Process
```bash
# 1. Bump version
./scripts/release/version.sh bump patch

# 2. Merge to master
./scripts/git/merge_to_production.sh staging

# 3. Build
./scripts/release/build.sh

# 4. Deploy
./scripts/release/deploy.sh production
```

## Best Practices

1. ✅ **Luôn test trên staging trước**
2. ✅ **Sử dụng golive.sh** để đảm bảo không bỏ sót bước
3. ✅ **Review release notes** trước khi deploy
4. ✅ **Monitor sau deploy** bằng `./scripts/monitor/monitor.sh`
5. ✅ **Có rollback plan** sẵn sàng

