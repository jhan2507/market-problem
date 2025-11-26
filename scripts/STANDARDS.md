# Script Standards

Tài liệu chuẩn hóa cho tất cả scripts trong hệ thống.

## 📋 Cấu trúc Script

### Header Template
```bash
#!/bin/bash
# =============================================================================
# Script Name: [script_name].sh
# Description: [Mô tả ngắn gọn chức năng]
# Category: [DEPLOY|MONITOR|UTILS|RELEASE]
# Usage: ./scripts/[category]/[script_name].sh [arguments]
# =============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures
```

### Sections
1. **Header** - Thông tin script
2. **Configuration** - Biến và constants
3. **Functions** - Helper functions
4. **Main** - Logic chính
5. **Error Handling** - Xử lý lỗi

## 🎯 Naming Conventions

### File Names
- **Lowercase** với underscores: `rebuild_service.sh`
- **Descriptive**: Tên file phải mô tả rõ chức năng
- **Consistent**: Cùng pattern cho cùng loại script

### Variables
- **UPPERCASE** cho constants: `BACKUP_DIR`, `TIMESTAMP`
- **lowercase** cho variables: `service_name`, `backup_file`
- **Descriptive names**: Tránh `x`, `tmp`, `var1`

## 📝 Code Style

### Error Handling
```bash
# Always check return codes
if [ $? -ne 0 ]; then
    log_error "Operation failed"
    exit 1
fi

# Or use set -e (recommended)
set -euo pipefail
```

### Logging Functions
```bash
log_info() {
    echo "ℹ️  $*"
}

log_success() {
    echo "✅ $*"
}

log_error() {
    echo "❌ $*" >&2
}

log_warning() {
    echo "⚠️  $*"
}
```

### Dependency Checks
```bash
check_dependencies() {
    local missing_deps=()
    
    for cmd in docker docker-compose; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        exit 1
    fi
}
```

## 🔧 Common Patterns

### Check .env file
```bash
check_env_file() {
    if [ ! -f .env ]; then
        log_warning ".env file not found"
        if [ -f env.example ]; then
            cp env.example .env
            log_success "Created .env from env.example"
        else
            log_error "env.example not found"
            exit 1
        fi
    fi
}
```

### Usage Messages
```bash
show_usage() {
    echo "Usage: $0 [options] [arguments]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Verbose output"
    echo ""
    echo "Examples:"
    echo "  $0 service_name"
    echo "  $0 --help"
}
```

### Service Validation
```bash
VALID_SERVICES=(
    "market_data_service"
    "market_analyzer_service"
    "price_service"
    "signal_service"
    "notification_service"
)

validate_service() {
    local service=$1
    if [[ ! " ${VALID_SERVICES[@]} " =~ " ${service} " ]]; then
        log_error "Invalid service: $service"
        echo "Available services:"
        printf "  - %s\n" "${VALID_SERVICES[@]}"
        exit 1
    fi
}
```

## 📦 File Organization

### Directory Structure
```
scripts/
├── deploy/          # Deployment scripts
├── monitor/         # Monitoring scripts
├── utils/           # Utility scripts
├── release/         # Release management
└── git/             # Git management
```

### Windows Support
- Mỗi script `.sh` nên có version `.bat` tương ứng
- Đặt cùng thư mục với script `.sh`
- Giữ cùng logic và output format

## ✅ Best Practices

1. **Always use `set -euo pipefail`** - Fail fast, catch errors early
2. **Check dependencies** - Verify required tools are installed
3. **Validate inputs** - Check arguments and options
4. **Use functions** - Break code into reusable functions
5. **Consistent logging** - Use log functions, not raw echo
6. **Error messages** - Clear, actionable error messages
7. **Exit codes** - Use appropriate exit codes (0=success, 1=error)
8. **Documentation** - Comment complex logic
9. **No hardcoded paths** - Use variables and relative paths
10. **Idempotent** - Scripts should be safe to run multiple times

## 🚫 Anti-patterns

❌ **Don't:**
- Use `set +e` without good reason
- Ignore error codes
- Hardcode paths
- Use unclear variable names
- Mix concerns (one script, one purpose)
- Skip input validation
- Use `rm -rf` without confirmation
- Assume environment setup

✅ **Do:**
- Fail fast on errors
- Check all dependencies
- Use relative paths
- Clear, descriptive names
- Single responsibility
- Validate all inputs
- Safe operations
- Explicit environment checks

## 📚 Examples

Xem `scripts/TEMPLATE.sh` để có template đầy đủ.

Xem các scripts trong `scripts/deploy/` để có ví dụ thực tế.

