# Hàm tiện ích (Utils)

Module `utils.py` chứa các hàm tiện ích hỗ trợ cho bot, bao gồm gửi tin nhắn, lấy dữ liệu từ API, và quản lý lịch sử.

## Các hàm chính

### 1. Gửi tin nhắn Telegram

#### `send_telegram_message(text)`
Gửi tin nhắn đến Telegram channel chính.

**Tham số:**
- `text` (str): Nội dung tin nhắn (có thể dùng HTML)

**Ví dụ:**
```python
import utils
utils.send_telegram_message("📊 <b>Thông báo:</b> Giá BTC tăng!")
```

#### `send_signal_message(text)`
Gửi tin nhắn tín hiệu long/short vào channel riêng.

**Tham số:**
- `text` (str): Nội dung tin nhắn tín hiệu (có thể dùng HTML)

**Ví dụ:**
```python
import utils
utils.send_signal_message("📈 <b>TÍN HIỆU LONG:</b> BTC")
```

### 2. Format tin nhắn

#### `format_trading_signal(signal, btc_dom, usdt_dom, fear_index, technical_details)`
Format tín hiệu long/short với thông tin đầy đủ.

**Tham số:**
- `signal` (dict): Dictionary chứa thông tin tín hiệu
- `btc_dom` (float, optional): BTC Dominance hiện tại
- `usdt_dom` (float, optional): USDT Dominance hiện tại
- `fear_index` (int, optional): Fear & Greed Index hiện tại
- `technical_details` (dict, optional): Chi tiết phân tích kỹ thuật

**Ví dụ:**
```python
signal = {
    'action': 'LONG_BTC_SHORT_ALT',
    'confidence': 'high',
    'reason': 'BTC dominance tăng mạnh'
}
message = utils.format_trading_signal(signal, btc_dom=55.5, usdt_dom=4.2, fear_index=25)
```

### 3. Lấy giá từ API

#### `get_price_binance(symbol)`
Lấy giá hiện tại của coin từ Binance API.

**Tham số:**
- `symbol` (str): Symbol coin trên Binance (ví dụ: 'BTCUSDT')

**Trả về:**
- `float`: Giá hiện tại hoặc `None` nếu có lỗi

**Ví dụ:**
```python
price = utils.get_price_binance('BTCUSDT')
print(f"Giá BTC: ${price}")
```

#### `get_klines_binance(symbol, interval='1h', limit=200)`
Lấy dữ liệu kline (OHLCV) từ Binance để phân tích kỹ thuật.

**Tham số:**
- `symbol` (str): Symbol coin trên Binance
- `interval` (str): Khung thời gian ('1h', '4h', '1d', etc.)
- `limit` (int): Số lượng nến cần lấy

**Trả về:**
- `pandas.DataFrame`: DataFrame chứa ['timestamp', 'open', 'high', 'low', 'close', 'volume']

**Ví dụ:**
```python
df = utils.get_klines_binance('BTCUSDT', interval='4h', limit=200)
print(df.head())
```

### 4. Lấy chỉ số thị trường

#### `get_fear_and_greed()`
Lấy Fear & Greed Index từ Alternative.me API.

**Trả về:**
- `tuple`: (value, classification, timestamp) hoặc (None, None, None)

**Ví dụ:**
```python
value, label, timestamp = utils.get_fear_and_greed()
print(f"Fear & Greed: {value} ({label})")
```

#### `get_btc_dominance_and_total_marketcap(api_key, max_retries=3)`
Lấy BTC Dominance và Total Market Cap từ CoinMarketCap API.

**Tham số:**
- `api_key` (str): API key của CoinMarketCap
- `max_retries` (int): Số lần retry tối đa

**Trả về:**
- `tuple`: (btc_dominance, total_market_cap) hoặc (None, None)

**Ví dụ:**
```python
import config
btc_dom, total_mcap = utils.get_btc_dominance_and_total_marketcap(config.YOUR_CMC_API_KEY)
print(f"BTC Dominance: {btc_dom}%")
```

#### `get_usdt_market_cap(api_key, max_retries=3)`
Lấy USDT Market Cap từ CoinMarketCap API.

**Tham số:**
- `api_key` (str): API key của CoinMarketCap
- `max_retries` (int): Số lần retry tối đa

**Trả về:**
- `float`: USDT Market Cap hoặc `None`

**Ví dụ:**
```python
import config
usdt_mcap = utils.get_usdt_market_cap(config.YOUR_CMC_API_KEY)
print(f"USDT Market Cap: ${usdt_mcap:,.0f}")
```

#### `get_usdt_dominance(usdt_market_cap, total_market_cap)`
Tính USDT Dominance từ USDT Market Cap và Total Market Cap.

**Tham số:**
- `usdt_market_cap` (float): USDT Market Cap
- `total_market_cap` (float): Total Market Cap

**Trả về:**
- `float`: USDT Dominance (%) hoặc `None`

**Ví dụ:**
```python
usdt_dom = utils.get_usdt_dominance(usdt_mcap, total_mcap)
print(f"USDT Dominance: {usdt_dom}%")
```

### 5. Quản lý lịch sử

#### `save_market_history(ts, btc_dom, usdt_dom, fear_index)`
Lưu lịch sử thị trường vào file CSV.

**Tham số:**
- `ts` (int): Unix timestamp
- `btc_dom` (float): BTC Dominance
- `usdt_dom` (float): USDT Dominance
- `fear_index` (int): Fear & Greed Index

**Ví dụ:**
```python
import time
now_ts = int(time.time())
utils.save_market_history(now_ts, 55.5, 4.2, 25)
```

#### `load_market_history(days=30)`
Đọc lịch sử thị trường từ file CSV.

**Tham số:**
- `days` (int): Số ngày lịch sử cần đọc (mặc định 30)

**Trả về:**
- `list`: Danh sách dictionary chứa lịch sử

**Ví dụ:**
```python
history = utils.load_market_history(days=14)
for record in history:
    print(f"BTC Dom: {record['btc_dom']}%")
```

### 6. Quản lý Signal

#### `should_emit_signal(signal_type, action, confidence, current_value, now_ts)`
Kiểm tra xem có nên phát tín hiệu hay không dựa trên:
- Phát tín hiệu mới nếu chưa từng phát
- Phát lại nếu tín hiệu đã hết hạn
- Phát lại nếu tín hiệu đảo chiều
- Phát lại nếu giá trị thay đổi đáng kể
- Phát lại nếu confidence tăng từ medium lên high

**Tham số:**
- `signal_type` (str): Loại tín hiệu
- `action` (str): Hành động (ví dụ: 'LONG_BTC_SHORT_ALT')
- `confidence` (str): Độ tin cậy ('high' hoặc 'medium')
- `current_value` (float): Giá trị hiện tại của chỉ số
- `now_ts` (int): Unix timestamp hiện tại

**Trả về:**
- `tuple`: (should_emit (bool), reason (str))

**Ví dụ:**
```python
import time
should_emit, reason = utils.should_emit_signal(
    'BTC_DOM_SPIKE_UP',
    'LONG_BTC_SHORT_ALT',
    'high',
    55.5,
    int(time.time())
)
if should_emit:
    print(f"Phát tín hiệu: {reason}")
```

### 7. Phát hiện biến động giá

#### `detect_price_spike(symbol)`
Phát hiện biến động giá mạnh trong 5 phút gần nhất.

**Tham số:**
- `symbol` (str): Symbol coin trên Binance

**Trả về:**
- `str`: Tin nhắn cảnh báo hoặc `None`

**Ví dụ:**
```python
alert = utils.detect_price_spike('BTCUSDT')
if alert:
    utils.send_telegram_message(alert)
```

## Biến toàn cục

- `price_history`: Dictionary lưu trữ lịch sử giá (key: symbol, value: list of (timestamp, price))
- `signal_history`: Dictionary lưu trữ các tín hiệu đã phát ra (key: signal_type, value: dict)

## Lưu ý

- Tất cả các hàm API đều có retry mechanism khi gặp lỗi 429 (Too Many Requests)
- Lịch sử giá được giới hạn 100 điểm gần nhất cho mỗi coin
- Signal history được quản lý tự động để tránh spam

