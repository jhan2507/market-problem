# Phân tích thị trường (Market Analysis)

Module `market_analysis.py` chứa các hàm phân tích thị trường nâng cao và phát hiện tín hiệu giao dịch.

## Tổng quan

Module này thực hiện:
- Phân tích đa khung thời gian (1h, 4h, 1d, 3d, 1w, 1M)
- Phát hiện xu hướng và momentum
- Multi-confirmation từ nhiều chỉ báo
- Phát hiện tín hiệu long/short
- Phân tích tổng hợp và tương quan

## Các hàm chính

### 1. Tính toán thống kê

#### `calculate_stats(key, arr)`
Tính toán thống kê nâng cao cho một chỉ số.

**Tham số:**
- `key` (str): Key trong dictionary (ví dụ: 'btc_dom', 'usdt_dom', 'fear_index')
- `arr` (list): Danh sách dictionary chứa lịch sử thị trường

**Trả về:**
- `dict`: Dictionary chứa các thống kê:
  - `mean`: Giá trị trung bình
  - `std`: Độ lệch chuẩn
  - `min`: Giá trị nhỏ nhất
  - `max`: Giá trị lớn nhất
  - `momentum`: Momentum (xu hướng)
  - `recent_momentum`: Momentum gần đây
  - `trend`: Xu hướng ('up', 'down', 'neutral')
  - `trend_strength`: Độ mạnh xu hướng (0-1)
  - `current`: Giá trị hiện tại
  - `values`: Mảng giá trị
  - `count`: Số lượng điểm dữ liệu

**Ví dụ:**
```python
from market_analysis import calculate_stats
import utils

history = utils.load_market_history(days=14)
history_3d = [h for h in history if h['timestamp'] >= int(time.time()) - 3*86400]

stats = calculate_stats('btc_dom', history_3d)
if stats:
    print(f"Mean: {stats['mean']:.2f}%")
    print(f"Std: {stats['std']:.2f}%")
    print(f"Trend: {stats['trend']}")
    print(f"Momentum: {stats['momentum']:.4f}")
```

### 2. Phát hiện bất thường

#### `detect_anomaly(current, stats, threshold_std=2.5)`
Phát hiện giá trị bất thường với ngưỡng cao để giảm tín hiệu giả.

**Tham số:**
- `current` (float): Giá trị hiện tại
- `stats` (dict): Dictionary thống kê từ calculate_stats
- `threshold_std` (float): Ngưỡng độ lệch chuẩn (mặc định 2.5)

**Trả về:**
- `tuple`: (severity, z_score)
  - `severity`: 'high', 'medium', 'low' hoặc None
  - `z_score`: Z-score của giá trị hiện tại

**Ví dụ:**
```python
from market_analysis import detect_anomaly, calculate_stats

stats = calculate_stats('btc_dom', history_3d)
severity, z_score = detect_anomaly(btc_dom, stats, threshold_std=2.0)

if severity == 'high':
    print(f"Giá trị bất thường cao! Z-score: {z_score:.2f}")
```

### 3. Kiểm tra tính nhất quán xu hướng

#### `check_trend_consistency(stats_list)`
Kiểm tra tính nhất quán của xu hướng qua nhiều khung thời gian.

**Tham số:**
- `stats_list` (list): Danh sách stats từ nhiều khung thời gian

**Trả về:**
- `tuple`: (is_consistent, consistency_ratio)
  - `is_consistent`: True nếu xu hướng nhất quán (>=60% đồng thuận)
  - `consistency_ratio`: Tỷ lệ đồng thuận (0-1)

**Ví dụ:**
```python
from market_analysis import check_trend_consistency, calculate_stats

stats_4h = calculate_stats('btc_dom', history_4h)
stats_1d = calculate_stats('btc_dom', history_1d)
stats_3d = calculate_stats('btc_dom', history_3d)

is_consistent, ratio = check_trend_consistency([stats_4h, stats_1d, stats_3d])
if is_consistent:
    print(f"Xu hướng nhất quán: {ratio:.0%}")
```

### 4. Tính điểm xác nhận

#### `calculate_confirmation_score(btc_stats, usdt_stats, fear_stats, current_btc, current_usdt, current_fear, technical_score=None, technical_details=None)`
Tính điểm xác nhận từ nhiều chỉ báo (multi-confirmation).

**Tham số:**
- `btc_stats` (dict): Stats của BTC Dominance
- `usdt_stats` (dict): Stats của USDT Dominance
- `fear_stats` (dict): Stats của Fear & Greed Index
- `current_btc` (float): BTC Dominance hiện tại
- `current_usdt` (float): USDT Dominance hiện tại
- `current_fear` (int): Fear & Greed Index hiện tại
- `technical_score` (float, optional): Technical score từ -1 đến +1
- `technical_details` (dict, optional): Chi tiết các chỉ báo kỹ thuật

**Trả về:**
- `tuple`: (score, confirmations)
  - `score`: Tổng điểm xác nhận
  - `confirmations`: Danh sách các xác nhận

**Ví dụ:**
```python
from market_analysis import calculate_confirmation_score, calculate_stats

btc_stats = calculate_stats('btc_dom', history_3d)
usdt_stats = calculate_stats('usdt_dom', history_3d)
fear_stats = calculate_stats('fear_index', history_3d)

score, confirmations = calculate_confirmation_score(
    btc_stats, usdt_stats, fear_stats,
    btc_dom, usdt_dom, fear_index,
    technical_score=0.5, technical_details={'rsi': 0.6}
)

print(f"Confirmation score: {score}")
print(f"Confirmations: {confirmations}")
```

### 5. Phát hiện tín hiệu giao dịch

#### `detect_strong_market_move(btc_dom, usdt_dom, fear_index)`
Phân tích thị trường nâng cao và phát hiện tín hiệu giao dịch.

**Tham số:**
- `btc_dom` (float): BTC Dominance hiện tại
- `usdt_dom` (float): USDT Dominance hiện tại
- `fear_index` (int): Fear & Greed Index hiện tại

**Trả về:**
- `tuple`: (alerts, trading_signals)
  - `alerts`: Danh sách cảnh báo thông thường
  - `trading_signals`: Danh sách tín hiệu giao dịch long/short

**Các loại tín hiệu:**

1. **BTC Dominance:**
   - `BTC_DOM_SPIKE_UP`: BTC dominance tăng mạnh → LONG BTC, SHORT Altcoin
   - `BTC_DOM_SPIKE_DOWN`: BTC dominance giảm mạnh → SHORT BTC, LONG Altcoin

2. **USDT Dominance:**
   - `USDT_DOM_SPIKE_UP`: USDT dominance tăng mạnh → SHORT toàn thị trường
   - `USDT_DOM_SPIKE_DOWN`: USDT dominance giảm mạnh → LONG toàn thị trường

3. **Fear & Greed:**
   - `FEAR_SPIKE`: Fear index giảm mạnh → LONG dần từng phần
   - `GREED_SPIKE`: Greed index tăng mạnh → SHORT hoặc chốt lời

4. **Tổng hợp:**
   - `CAPITAL_OUTFLOW`: BTC dom + USDT dom cùng tăng → SHORT toàn thị trường
   - `BUYING_OPPORTUNITY`: BTC dom + USDT dom + Fear cùng giảm → LONG toàn thị trường

**Ví dụ:**
```python
from market_analysis import detect_strong_market_move
import utils

btc_dom = 55.5
usdt_dom = 4.2
fear_index = 25

alerts, trading_signals = detect_strong_market_move(btc_dom, usdt_dom, fear_index)

# Gửi alerts vào channel chính
for alert in alerts:
    utils.send_telegram_message(alert)

# Gửi tín hiệu vào channel riêng
for signal in trading_signals:
    message = utils.format_trading_signal(signal, btc_dom, usdt_dom, fear_index)
    utils.send_signal_message(message)
```

### 6. Phân tích thị trường

#### `analyze_market(btc_dom, usdt_dom, fear_index, fear_label)`
Phân tích thị trường và đưa ra nhận định ngắn hạn, trung hạn, dài hạn.

**Tham số:**
- `btc_dom` (float): BTC Dominance hiện tại
- `usdt_dom` (float): USDT Dominance hiện tại
- `fear_index` (int): Fear & Greed Index hiện tại
- `fear_label` (str): Nhãn của Fear & Greed Index

**Trả về:**
- `str`: Chuỗi nhận định thị trường

**Ví dụ:**
```python
from market_analysis import analyze_market
import utils

analysis = analyze_market(btc_dom, usdt_dom, fear_index, fear_label)
utils.send_telegram_message("🧠 <b>Nhận định thị trường:</b>\n" + analysis)
```

## Quy trình phân tích

1. **Thu thập dữ liệu:**
   - Lấy lịch sử thị trường (14 ngày)
   - Lấy dữ liệu kline BTC (4h, 1d)

2. **Phân tích đa khung thời gian:**
   - Tính stats cho từng khung (1h, 4h, 1d, 3d, 1w, 1M)
   - Kiểm tra tính nhất quán xu hướng

3. **Phát hiện bất thường:**
   - Tính Z-score cho từng chỉ số
   - Phát hiện giá trị bất thường (>= 2.0 std)

4. **Multi-confirmation:**
   - Kiểm tra sự đồng thuận của nhiều chỉ báo
   - Yêu cầu ít nhất 2 chỉ báo đồng thuận (hoặc 1.5 nếu có technical confirmation)

5. **Phát tín hiệu:**
   - Kiểm tra cooldown và signal history
   - Phát tín hiệu nếu đủ điều kiện

## Lưu ý

- Cần ít nhất 20 điểm dữ liệu để phân tích
- Ngưỡng Z-score cao (>= 2.0) để giảm tín hiệu giả
- Multi-confirmation giúp tăng độ chính xác
- Technical analysis có thể giảm yêu cầu confirmation xuống 1.5

