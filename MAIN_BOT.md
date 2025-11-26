# Bot chính (Main Bot)

File `claim_price_bot.py` là file chính chạy bot, điều phối tất cả các module và thực hiện các tác vụ định kỳ.

## Chức năng

Bot thực hiện các tác vụ sau:

1. **Cập nhật Fear & Greed Index** - Mỗi ngày một lần
2. **Cập nhật Dominance** - Mỗi 5 phút
3. **Cập nhật giá coin** - Mỗi 30 giây
4. **Phát hiện và gửi tín hiệu** - Khi có tín hiệu giao dịch

## Cấu trúc

```python
def main():
    # Khởi tạo biến
    last_fng_date = None
    last_dom_time = 0
    fear_index = None
    fear_label = None
    
    while True:
        # 1. Cập nhật Fear & Greed Index (mỗi ngày)
        # 2. Cập nhật Dominance (mỗi 5 phút)
        # 3. Phân tích thị trường và phát tín hiệu
        # 4. Cập nhật giá coin (mỗi 30 giây)
        # 5. Phát hiện biến động giá
        time.sleep(30)
```

## Quy trình hoạt động

### 1. Cập nhật Fear & Greed Index

```python
if last_fng_date != today:
    f_index, f_label, f_ts = utils.get_fear_and_greed()
    if f_index is not None:
        fear_index, fear_label = f_index, f_label
        msg = f"📊 <b>Fear & Greed Index:</b> {fear_index} ({fear_label})"
        utils.send_telegram_message(msg)
        last_fng_date = today
```

**Tần suất:** Mỗi ngày một lần

### 2. Cập nhật Dominance và Phân tích

```python
if now_ts - last_dom_time >= 300:  # 5 phút
    # Lấy BTC Dominance và Total Market Cap
    btc_dom, total_market_cap = utils.get_btc_dominance_and_total_marketcap(api_key)
    
    # Lấy USDT Market Cap và tính USDT Dominance
    usdt_market_cap = utils.get_usdt_market_cap(api_key)
    usdt_dom = utils.get_usdt_dominance(usdt_market_cap, total_market_cap)
    
    # Gửi thông báo Dominance
    msg = f"📈 <b>Dominance:</b>\nBTC: {btc_dom:.3f}% | USDT: {usdt_dom:.3f}%"
    utils.send_telegram_message(msg)
    
    # Phân tích thị trường
    if fear_index is not None:
        analysis = market_analysis.analyze_market(btc_dom, usdt_dom, fear_index, fear_label)
        utils.send_telegram_message("🧠 <b>Nhận định thị trường:</b>\n" + analysis)
    
    # Phát hiện tín hiệu giao dịch
    alerts, trading_signals = market_analysis.detect_strong_market_move(btc_dom, usdt_dom, fear_index)
    
    # Gửi alerts vào channel chính
    for alert in alerts:
        utils.send_telegram_message(alert)
    
    # Gửi tín hiệu vào channel riêng
    for signal in trading_signals:
        technical_details = signal.get('technical_details', None)
        signal_message = utils.format_trading_signal(signal, btc_dom, usdt_dom, fear_index, technical_details)
        utils.send_signal_message(signal_message)
    
    # Lưu lịch sử
    utils.save_market_history(now_ts, btc_dom, usdt_dom, fear_index)
    last_dom_time = now_ts
```

**Tần suất:** Mỗi 5 phút

### 3. Cập nhật giá coin

```python
price_msg = "💰 <b>Giá coin cập nhật:</b>\n"

for sym in config.COINS:
    price = utils.get_price_binance(sym)
    if price is not None:
        price_msg += f"{config.COINS[sym]}: {price:.3f} | "
        utils.price_history[sym].append((now_ts, price))
        utils.price_history[sym] = utils.price_history[sym][-100:]  # Giữ 100 điểm gần nhất
        
        # Phát hiện biến động giá mạnh
        alert = utils.detect_price_spike(sym)
        if alert:
            utils.send_telegram_message("🚨 <b>Cảnh báo biến động giá:</b>\n" + alert)

price_msg = price_msg.rstrip(" | ")
if price_msg:
    utils.send_telegram_message(price_msg)
```

**Tần suất:** Mỗi 30 giây

## Chạy bot

### Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Chạy bot

```bash
python claim_price_bot.py
```

### Chạy trong background (Linux/Mac)

```bash
nohup python claim_price_bot.py > bot.log 2>&1 &
```

### Chạy với systemd (Linux)

Tạo file `/etc/systemd/system/coin-bot.service`:

```ini
[Unit]
Description=Coin Price Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/living-coin-price
ExecStart=/usr/bin/python3 /path/to/living-coin-price/claim_price_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Sau đó:

```bash
sudo systemctl enable coin-bot
sudo systemctl start coin-bot
sudo systemctl status coin-bot
```

## Cấu hình

Tất cả cấu hình được đặt trong `config.py`:

- `TELEGRAM_BOT_TOKEN`: Token của bot
- `TELEGRAM_CHAT_ID`: Channel chính
- `TELEGRAM_SIGNAL_CHAT_ID`: Channel tín hiệu
- `YOUR_CMC_API_KEY`: API key CoinMarketCap
- `COINS`: Danh sách coin theo dõi

## Logs

Bot sẽ in ra console các thông tin:
- Lỗi khi gọi API
- Thông báo khi gửi tin nhắn thành công
- Cảnh báo khi có biến động giá

## Xử lý lỗi

Bot có cơ chế xử lý lỗi:
- Retry khi gặp lỗi 429 (Too Many Requests)
- Bỏ qua nếu API không trả về dữ liệu
- Tiếp tục chạy ngay cả khi một coin lỗi

## Tối ưu hóa

- Lịch sử giá chỉ giữ 100 điểm gần nhất
- Signal history được quản lý tự động
- Cooldown để tránh spam tín hiệu

## Lưu ý

- Bot cần chạy liên tục để có dữ liệu lịch sử đầy đủ
- Cần ít nhất 20 điểm dữ liệu để phân tích chính xác
- API rate limits có thể ảnh hưởng đến tần suất cập nhật

