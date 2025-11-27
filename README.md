# Crypto Market Monitoring & Futures Signal System

Hệ thống microservice theo dõi thị trường crypto và phát tín hiệu giao dịch futures dựa trên phân tích kỹ thuật nâng cao.

## Kiến trúc hệ thống

Hệ thống gồm 5 microservices độc lập + API Gateway:

1. **Market Data Service** - Thu thập dữ liệu giá, candlesticks, và metrics thị trường
2. **Crypto Market Analyzer** - Phân tích thị trường sử dụng Dow Theory, Wyckoff, Gann
3. **Price Service** - Theo dõi giá real-time và phát hiện biến động
4. **Signal Service** - Tạo tín hiệu LONG/SHORT với hệ thống scoring (0-100)
5. **Notification Service** - Gửi thông báo qua Telegram
6. **API Gateway** - Single entry point với service discovery và rate limiting

### Architecture Overview

Xem chi tiết kiến trúc tại [docs/architecture/](docs/architecture/):
- [System Architecture](docs/architecture/architecture.md) - High-level system overview
- [Service Interaction](docs/architecture/service-interaction.md) - Event-driven communication
- [Data Flow](docs/architecture/data-flow.md) - Data flow through the system
- [Deployment](docs/architecture/deployment.md) - Deployment architecture

## Công nghệ sử dụng

- **Python 3.11** - Ngôn ngữ chính
- **MongoDB** - Lưu trữ dữ liệu
- **Redis Streams** - Event-driven communication
- **Docker & Docker Compose** - Containerization
- **Telegram Bot API** - Thông báo

## Cài đặt

### Yêu cầu

- Docker và Docker Compose
- CoinMarketCap API key (cho dominance data)
- Telegram Bot Token

### Bước 1: Clone repository

```bash
git clone <repository-url>
cd market-problem
```

### Bước 2: Cấu hình môi trường

Tạo file `.env` từ `.env.example`:

```bash
cp .env.example .env
```

Chỉnh sửa `.env` với thông tin của bạn:

```env
CMC_API_KEY=your_actual_cmc_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_PRICE_CHAT_ID=@your_price_channel
TELEGRAM_SIGNAL_CHAT_ID=@your_signal_channel
COINS=BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT
```

### Bước 3: Chạy hệ thống

```bash
docker-compose up -d
```

Xem logs:

```bash
docker-compose logs -f
```

## Cấu trúc thư mục

```
.
├── shared/                    # Shared modules
│   ├── config.py              # Configuration
│   ├── database.py            # MongoDB client
│   ├── events.py              # Redis Streams events
│   ├── logger.py              # Logging setup
│   └── theories.py            # Technical analysis theories
├── services/
│   ├── market_data_service/   # Market data collection
│   ├── market_analyzer_service/ # Market analysis
│   ├── price_service/         # Live price monitoring
│   ├── signal_service/        # Signal generation
│   └── notification_service/  # Telegram notifications
├── docker-compose.yml         # Docker Compose configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Hệ thống Scoring (0-100)

Tín hiệu được tạo dựa trên hệ thống scoring:

1. **Multi-timeframe trend (Dow Theory)** - 30 điểm
   - Primary trend (1D, 3D, 1W): 15 điểm
   - Secondary trend (4H, 8H): 10 điểm
   - Minor trend (1H): 5 điểm

2. **Wyckoff pattern** - 15 điểm
   - SOS/Spring/SOW/Upthrust detection

3. **Indicators** - 20 điểm
   - RSI: 7 điểm
   - MACD: 7 điểm
   - EMA alignment: 6 điểm

4. **Volume confirmation** - 10 điểm

5. **Dominance effects** - 15 điểm
   - BTC.D, USDT.D, TOTAL2 analysis

6. **Safety checks** - 10 điểm
   - Funding, OI, Liquidity

### Ngưỡng tín hiệu

- **Score ≥ 75** → HIGH confidence signal
- **60-74** → MEDIUM confidence (optional or reduce size)
- **< 60** → NO SIGNAL

## Quy tắc tín hiệu

### BTC Signals

**LONG (BTC):**
- Primary trend: Uptrend hoặc neutral + BOS upward
- Secondary trend: Uptrend hoặc Neutral
- RSI > 50 (prefer 4H > 50)
- MACD cross up
- EMA: price > EMA20 > EMA50
- Wyckoff: SOS hoặc Spring
- BTC.D falling improves score

**SHORT (BTC):**
- Primary: Downtrend
- Secondary: Downtrend hoặc Neutral
- RSI < 50
- MACD cross down
- EMA bearish
- Wyckoff: SOW hoặc Upthrust
- BTC.D rising improves score

### ALTCOIN Signals

**LONG (ALT):**
- Primary: Uptrend hoặc neutral + TOTAL2 rising + BTC.D falling
- BTC.D falling is **REQUIRED** (rising kills signal)
- USDT.D must NOT be rising
- RSI 4H > 50 (prefer 55+)
- Wyckoff: SOS hoặc Spring

**SHORT (ALT):**
- Primary: Downtrend hoặc neutral + BTC.D rising
- BTC.D rising hoặc USDT.D rising → strong short support
- RSI 4H < 50
- Wyckoff: SOW hoặc Upthrust

### Guardrails

- ❌ No long signals nếu USDT.D rising sharply (risk-off)
- ❌ No long ALT nếu BTC.D rising
- ❌ No signals nếu liquidity dưới threshold
- ❌ No signals trong BTC crash (>X% trong 15m)
- ❌ No conflicting signals

## Scripts Quản Lý

Hệ thống có sẵn các scripts được tổ chức theo tính năng:

### Menu chính (Khuyến nghị)

```bash
./scripts/index.sh
```

Menu tương tác với tất cả các tùy chọn được phân loại theo:
- 📦 **Deployment** - Khởi động, dừng, restart
- 📊 **Monitoring** - Logs, status, health, metrics
- 🔧 **Utilities** - Backup, restore, validate, scale
- 🚀 **Release** - Version, build, deploy, rollback

### Khởi động hệ thống

```bash
# Sử dụng menu (khuyến nghị)
./scripts/index.sh

# Hoặc chạy trực tiếp
./scripts/deploy/start.sh

# Windows
scripts\deploy\start.bat
```

### Xem logs

```bash
# Tất cả services
./scripts/monitor/logs.sh

# Một service cụ thể
./scripts/monitor/logs.sh market_data_service
./scripts/monitor/logs.sh signal_service
```

### Kiểm tra trạng thái

```bash
# System status
./scripts/monitor/status.sh

# Health check
./scripts/monitor/health.sh

# Statistics
./scripts/monitor/stats.sh

# Real-time monitor
./scripts/monitor/monitor.sh

# Detailed metrics
./scripts/monitor/metrics.sh

# Test connections
./scripts/monitor/test_connection.sh
```

### Quản lý services

```bash
# Restart toàn bộ
./scripts/deploy/restart.sh

# Restart một service
./scripts/deploy/restart_service.sh signal_service

# Scale service
./scripts/utils/scale.sh price_service 3
```

### Backup & Restore

```bash
# Backup database
./scripts/utils/backup.sh

# Restore database
./scripts/utils/restore.sh backups/market_backup_20240101_120000.archive.gz

# Export data
./scripts/utils/export_data.sh

# Import data
./scripts/utils/import_data.sh exports/export_20240101_120000.tar.gz
```

### Utilities

```bash
# Validate configuration
./scripts/utils/validate_config.sh

# Check dependencies
./scripts/utils/check_dependencies.sh

# Cleanup
./scripts/utils/cleanup.sh
```

Xem chi tiết trong [scripts/README.md](scripts/README.md) và [scripts/QUICK_REFERENCE.md](scripts/QUICK_REFERENCE.md)

## Monitoring

### Xem logs từng service

```bash
# Market Data Service
docker-compose logs -f market_data_service

# Market Analyzer
docker-compose logs -f market_analyzer_service

# Price Service
docker-compose logs -f price_service

# Signal Service
docker-compose logs -f signal_service

# Notification Service
docker-compose logs -f notification_service
```

Hoặc sử dụng script:
```bash
./scripts/monitor/logs.sh [service_name]
```

### MongoDB Collections

- `market_data` - Dữ liệu giá và candlesticks
- `analysis` - Kết quả phân tích thị trường
- `signals` - Tín hiệu giao dịch đã tạo
- `price_updates` - Cập nhật giá real-time
- `logs` - System logs

### Redis Streams

Events được publish vào Redis Streams:
- `events:market_data_updated`
- `events:market_analysis_completed`
- `events:price_update_ready`
- `events:signal_generated`

## Dừng hệ thống

```bash
docker-compose down
```

Xóa dữ liệu (volumes):

```bash
docker-compose down -v
```

## Release Management

Hệ thống hỗ trợ quản lý version và deployment lên staging/production.

### Version Management

```bash
# Xem version hiện tại
./scripts/release/version.sh show

# Bump version
./scripts/release/version.sh bump patch   # 0.0.X
./scripts/release/version.sh bump minor   # 0.X.0
./scripts/release/version.sh bump major   # X.0.0
```

### Tạo Release

```bash
./scripts/release/release.sh
```

### Deploy

```bash
# Deploy lên staging
./scripts/release/deploy.sh staging

# Deploy lên production
./scripts/release/deploy.sh production
```

### Go Live (Quick)

```bash
# Go live từ staging lên production (khuyến nghị)
./scripts/release/golive.sh staging
```

Script này tự động:
- Bump version
- Merge vào master
- Build images
- Create git tag
- Generate release notes
- Deploy to production

### Rollback

```bash
# Rollback về version trước
./scripts/release/rollback.sh production

# Rollback về version cụ thể
./scripts/release/rollback.sh production 1.2.0
```

Xem chi tiết trong [scripts/release/README.md](scripts/release/README.md)

## Phát triển

### Development Setup

Xem [Developer Guide](docs/DEVELOPER_GUIDE.md) để biết chi tiết về:
- Setup development environment
- Code style guidelines
- Testing guidelines
- How to add new service
- How to add new event type
- Debugging tips

### Quick Start for Development

```bash
# Install dependencies
pip install -r requirements.txt

# Setup pre-commit hooks
pre-commit install

# Copy environment file
cp env.example .env
# Edit .env with your configuration

# Start dependencies (MongoDB, Redis)
docker-compose up -d mongodb redis

# Run service locally
export MONGODB_URI="mongodb://admin:password@localhost:27017/market?authSource=admin"
export REDIS_HOST="localhost"
python services/market_data_service/main.py
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=shared --cov=services --cov-report=html

# Run specific test types
pytest tests/unit -m unit
pytest tests/integration -m integration
```

### Code Quality

```bash
# Format code
black --line-length=100 .

# Lint code
flake8 .

# Type checking
mypy .

# Sort imports
isort --profile=black .

# Run all checks (via pre-commit)
pre-commit run --all-files
```

## Lưu ý

- Hệ thống này chỉ phục vụ mục đích giáo dục và nghiên cứu
- Không đảm bảo lợi nhuận trong giao dịch thực tế
- Luôn quản lý rủi ro và sử dụng stop-loss
- Test kỹ trước khi sử dụng với tiền thật

## Git Repository

Repository: `git@personal:jhan2507/market-problem.git`

### Branch Structure

- **master** → Production (live system)
- **staging** → Test/Staging environment
- **develop** → Development (integration)
- **feature/*** → Feature branches
- **bugfix/*** → Bug fix branches
- **hotfix/*** → Hotfix for production

### Initial Setup

```bash
# Setup repository và push lần đầu
./scripts/git/initial_push.sh

# Hoặc setup thủ công
./scripts/git/setup_repo.sh
git add .
git commit -m "Initial commit"
./scripts/git/push.sh master
```

### Workflow

Xem chi tiết trong [scripts/git/README.md](scripts/git/README.md)

```bash
# Tạo feature branch
./scripts/git/create_branch.sh my-feature develop feature

# Merge to staging
./scripts/git/merge_to_staging.sh develop

# Merge to production
./scripts/git/merge_to_production.sh staging
```

## Documentation

- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Complete development guide
- [Architecture Diagrams](docs/architecture/) - System architecture documentation
- [API Documentation](docs/api/openapi.yaml) - OpenAPI specification

## Contributing

1. Follow code style guidelines (Black, flake8, mypy)
2. Write tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting

See [Developer Guide](docs/DEVELOPER_GUIDE.md) for detailed contribution guidelines.

## License

MIT License

