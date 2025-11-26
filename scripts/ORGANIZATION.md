# Scripts Organization

Scripts được tổ chức theo tính năng để dễ quản lý và sử dụng.

## Cấu trúc thư mục

```
scripts/
├── index.sh                    # Main entry point - menu chính
├── quick_start.sh              # Quick start guide
│
├── deploy/                     # 📦 DEPLOYMENT
│   ├── start.sh               # Khởi động hệ thống
│   ├── stop.sh                # Dừng hệ thống
│   ├── restart.sh             # Restart hệ thống
│   ├── rebuild.sh             # Rebuild hệ thống với code mới
│   ├── restart_service.sh     # Restart một service
│   ├── rebuild_service.sh     # Rebuild một service với code mới
│   └── *.bat                  # Windows versions
│
├── monitor/                    # 📊 MONITORING
│   ├── logs.sh               # Xem logs
│   ├── status.sh             # System status
│   ├── health.sh              # Health check
│   ├── stats.sh              # Statistics
│   ├── monitor.sh            # Real-time monitor
│   ├── metrics.sh             # Detailed metrics
│   └── test_connection.sh     # Test connections
│
├── utils/                      # 🔧 UTILITIES
│   ├── backup.sh             # Backup database
│   ├── restore.sh            # Restore database
│   ├── export_data.sh        # Export data
│   ├── import_data.sh        # Import data
│   ├── validate_config.sh    # Validate configuration
│   ├── check_dependencies.sh # Check dependencies
│   └── scale.sh              # Scale services
│
└── release/                    # 🚀 RELEASE MANAGEMENT
    ├── version.sh            # Version management
    ├── build.sh              # Build images
    ├── push.sh               # Push images
    ├── release.sh            # Create release
    ├── deploy.sh             # Deploy to environment
    ├── rollback.sh           # Rollback version
    ├── release_notes.sh      # Generate release notes
    └── ci.sh                 # CI/CD pipeline
```

## Sử dụng

### Cách 1: Menu chính (Khuyến nghị)
```bash
./scripts/index.sh
```

### Cách 2: Chạy trực tiếp theo category
```bash
# Deployment
./scripts/deploy/start.sh

# Monitoring
./scripts/monitor/status.sh

# Utilities
./scripts/utils/backup.sh

# Release
./scripts/release/version.sh show
```

## Migration từ cấu trúc cũ

Nếu scripts vẫn ở thư mục gốc, có thể sử dụng:

```bash
# Old way (vẫn hoạt động)
./scripts/start.sh

# New way (khuyến nghị)
./scripts/deploy/start.sh
```

Hoặc sử dụng `index.sh` để truy cập tất cả scripts qua menu.

## Benefits

1. **Tổ chức rõ ràng** - Scripts được nhóm theo chức năng
2. **Dễ tìm kiếm** - Biết category là tìm được script
3. **Dễ maintain** - Thêm script mới vào đúng category
4. **Menu thống nhất** - Một entry point cho tất cả

