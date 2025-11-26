# Release Management Guide

Hướng dẫn quản lý và triển khai releases cho hệ thống.

## Versioning

Hệ thống sử dụng [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (ví dụ: 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

## Quản lý Version

### Xem version hiện tại
```bash
./scripts/release/version.sh show
```

### Set version cụ thể
```bash
./scripts/release/version.sh set 1.2.3
```

### Bump version
```bash
# Patch (0.0.X) - Bug fixes
./scripts/release/version.sh bump patch

# Minor (0.X.0) - New features
./scripts/release/version.sh bump minor

# Major (X.0.0) - Breaking changes
./scripts/release/version.sh bump major
```

## Release Process

### 🚀 Go Live (Quick - Khuyến nghị)

Cách nhanh nhất để golive code lên production:

```bash
./scripts/release/golive.sh staging
```

Script này tự động thực hiện:
1. ✅ Validate environment
2. ✅ Bump version (patch/minor/major)
3. ✅ Merge staging vào master
4. ✅ Tạo git tag
5. ✅ Build Docker images
6. ✅ Generate release notes
7. ✅ Push to remote
8. ✅ Deploy to production

**⚠️ Safety:** Yêu cầu xác nhận "GOLIVE" trước khi thực hiện.

**Examples:**
```bash
# Go live từ staging (khuyến nghị)
./scripts/release/golive.sh staging

# Go live từ develop
./scripts/release/golive.sh develop

# Go live và skip build
./scripts/release/golive.sh staging true
```

### 1. Tạo Release mới (Manual)

```bash
./scripts/release/release.sh
```

Script sẽ:
- Hỏi loại bump (patch/minor/major)
- Bump version tự động
- Build Docker images
- Tạo git tag
- Generate release notes

### 2. Build Images

```bash
# Build với version hiện tại
./scripts/release/build.sh

# Hoặc build với custom registry
DOCKER_REGISTRY=registry.example.com IMAGE_PREFIX=myapp ./scripts/release/build.sh
```

### 3. Push Images (nếu dùng registry)

```bash
# Set registry
export DOCKER_REGISTRY=registry.example.com
export IMAGE_PREFIX=myapp

# Push images
./scripts/release/push.sh
```

### 4. Deploy

#### Staging
```bash
./scripts/release/deploy.sh staging
```

#### Production
```bash
./scripts/release/deploy.sh production
```

**Lưu ý:** Production deployment yêu cầu xác nhận.

## Environments

### Staging
- File config: `.env.staging`
- Compose override: `docker-compose.staging.yml`
- Log level: DEBUG
- Restart: unless-stopped

### Production
- File config: `.env.production`
- Compose override: `docker-compose.production.yml`
- Log level: INFO
- Restart: always
- Resource limits: Enabled

## Rollback

### Rollback về version trước
```bash
./scripts/release/rollback.sh production
```

### Rollback về version cụ thể
```bash
./scripts/release/rollback.sh production 1.2.0
```

## CI/CD

### Automated Pipeline

```bash
./scripts/ci.sh staging
./scripts/ci.sh production
```

Pipeline tự động:
1. Run tests
2. Build images
3. Push images (nếu có registry)
4. Deploy
5. Health check

### Git Hooks

Có thể setup git hooks để tự động:
- Bump version khi merge PR
- Create release khi tag
- Deploy khi push tag

## Release Notes

Release notes được tự động generate trong `releases/v{VERSION}.md`

### Manual Release Notes

```bash
./scripts/release_notes.sh 1.2.3 1.2.2 > releases/v1.2.3.md
```

## Best Practices

### 1. Version Management
- ✅ Luôn bump version trước khi release
- ✅ Sử dụng semantic versioning
- ✅ Tag git với format `v{VERSION}`
- ✅ Tạo release notes cho mỗi version

### 2. Staging Deployment
- ✅ Deploy mọi thay đổi lên staging trước
- ✅ Test kỹ trên staging
- ✅ Verify health checks
- ✅ Monitor logs

### 3. Production Deployment
- ✅ Chỉ deploy từ staging đã test
- ✅ Deploy trong giờ làm việc (nếu có thể)
- ✅ Có rollback plan sẵn
- ✅ Monitor sau deployment
- ✅ Document mọi thay đổi

### 4. Rollback
- ✅ Test rollback process trên staging
- ✅ Giữ backup của production data
- ✅ Document rollback steps
- ✅ Verify sau rollback

## Workflow Example

### Development → Staging → Production

```bash
# 1. Develop và test locally
git checkout -b feature/new-feature
# ... make changes ...

# 2. Merge to develop/staging branch
git checkout staging
git merge feature/new-feature

# 3. Create release
./scripts/release/release.sh
# Select: Minor bump

# 4. Deploy to staging
./scripts/release/deploy.sh staging

# 5. Test staging
./scripts/monitor/monitor.sh
./scripts/monitor/health.sh

# 6. Merge to main
git checkout main
git merge staging

# 7. Deploy to production
./scripts/release/deploy.sh production

# 8. Monitor production
./scripts/monitor/monitor.sh
```

## Environment Variables

### Build & Deploy
```bash
# Docker Registry
export DOCKER_REGISTRY=registry.example.com

# Image prefix
export IMAGE_PREFIX=market

# Image version (auto from VERSION file)
export IMAGE_VERSION=1.2.3
```

### Environment-specific
- `.env.staging` - Staging configuration
- `.env.production` - Production configuration

## Troubleshooting

### Version không update
```bash
# Check VERSION file
cat VERSION

# Manually set
./scripts/version.sh set 1.2.3
```

### Images không build
```bash
# Check Docker
docker --version
docker-compose --version

# Build manually
docker-compose build
```

### Deployment failed
```bash
# Check logs
./scripts/logs.sh [service_name]

# Check health
./scripts/health.sh

# Rollback
./scripts/rollback.sh [environment]
```

### Registry push failed
```bash
# Check registry credentials
docker login registry.example.com

# Check images
docker images | grep market

# Push manually
docker push registry.example.com/market-service:1.2.3
```

## Security

### Production Secrets
- ❌ Không commit secrets vào git
- ✅ Sử dụng environment variables
- ✅ Sử dụng secret management (Vault, AWS Secrets Manager)
- ✅ Rotate credentials định kỳ

### Image Security
- ✅ Scan images for vulnerabilities
- ✅ Use specific version tags (không dùng `latest` trong production)
- ✅ Keep base images updated

## Monitoring

Sau mỗi deployment:
1. Check health: `./scripts/monitor/health.sh`
2. Monitor logs: `./scripts/monitor/logs.sh`
3. Check stats: `./scripts/monitor/stats.sh`
4. Monitor real-time: `./scripts/monitor/monitor.sh`

