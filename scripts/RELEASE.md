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
./scripts/version.sh show
```

### Set version cụ thể
```bash
./scripts/version.sh set 1.2.3
```

### Bump version
```bash
# Patch (0.0.X) - Bug fixes
./scripts/version.sh bump patch

# Minor (0.X.0) - New features
./scripts/version.sh bump minor

# Major (X.0.0) - Breaking changes
./scripts/version.sh bump major
```

## Release Process

### 1. Tạo Release mới

```bash
./scripts/release.sh
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
./scripts/build.sh

# Hoặc build với custom registry
DOCKER_REGISTRY=registry.example.com IMAGE_PREFIX=myapp ./scripts/build.sh
```

### 3. Push Images (nếu dùng registry)

```bash
# Set registry
export DOCKER_REGISTRY=registry.example.com
export IMAGE_PREFIX=myapp

# Push images
./scripts/push.sh
```

### 4. Deploy

#### Staging
```bash
./scripts/deploy.sh staging
```

#### Production
```bash
./scripts/deploy.sh production
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
./scripts/rollback.sh production
```

### Rollback về version cụ thể
```bash
./scripts/rollback.sh production 1.2.0
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
./scripts/release.sh
# Select: Minor bump

# 4. Deploy to staging
./scripts/deploy.sh staging

# 5. Test staging
./scripts/monitor.sh
./scripts/health.sh

# 6. Merge to main
git checkout main
git merge staging

# 7. Deploy to production
./scripts/deploy.sh production

# 8. Monitor production
./scripts/monitor.sh
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
1. Check health: `./scripts/health.sh`
2. Monitor logs: `./scripts/logs.sh`
3. Check stats: `./scripts/stats.sh`
4. Monitor real-time: `./scripts/monitor.sh`

