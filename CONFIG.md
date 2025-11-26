# Cấu hình (Config)

Module `config.py` chứa tất cả các cấu hình, constants và danh sách coin được sử dụng trong toàn bộ ứng dụng.

## Nội dung

### 1. Cấu hình Telegram
- `TELEGRAM_BOT_TOKEN`: Token của Telegram bot
- `TELEGRAM_CHAT_ID`: Channel chính để gửi thông báo
- `TELEGRAM_SIGNAL_CHAT_ID`: Channel riêng để gửi tín hiệu long/short

### 2. Cấu hình API
- `YOUR_CMC_API_KEY`: API key của CoinMarketCap
- `URL_FNG`: URL API của Fear & Greed Index

### 3. Danh sách Coin
- `COINS`: Dictionary chứa các coin được theo dõi
  - Key: Symbol trên Binance (ví dụ: 'BTCUSDT')
  - Value: Tên hiển thị (ví dụ: 'BTC')

### 4. Cấu hình Timezone
- `TZ`: Timezone sử dụng (mặc định: 'Asia/Bangkok')

### 5. Cấu hình File
- `HISTORY_FILE`: Tên file lưu lịch sử thị trường (mặc định: 'market_history.csv')

### 6. Cấu hình Signal
- `SIGNAL_COOLDOWN`: Thời gian chờ trước khi phát lại tín hiệu cùng loại (mặc định: 6 giờ)
- `SIGNAL_VALUE_THRESHOLD`: Ngưỡng thay đổi giá trị để phát lại tín hiệu (mặc định: 40%)

### 7. Cấu hình độ chính xác
- `MIN_CONFIRMATION_SCORE`: Điểm xác nhận tối thiểu để phát tín hiệu (mặc định: 2)
- `MIN_CONFIRMATION_WITH_TECH`: Điểm xác nhận tối thiểu khi có technical analysis (mặc định: 1.5)
- `TREND_CONFIRMATION_PERIODS`: Số khung thời gian cần xác nhận xu hướng (mặc định: 3)

## Cách sử dụng

```python
import config

# Sử dụng cấu hình
bot_token = config.TELEGRAM_BOT_TOKEN
chat_id = config.TELEGRAM_CHAT_ID

# Truy cập danh sách coin
for symbol, name in config.COINS.items():
    print(f"{name}: {symbol}")
```

## Lưu ý

- Không commit file `config.py` lên git nếu chứa thông tin nhạy cảm (API keys, tokens)
- Nên sử dụng biến môi trường hoặc file `.env` để bảo mật
- Có thể thêm/bớt coin trong `COINS` dictionary

