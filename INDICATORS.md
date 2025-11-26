# Chỉ báo kỹ thuật (Indicators)

Module `indicators.py` chứa các hàm tính toán các chỉ báo kỹ thuật phổ biến được sử dụng trong phân tích thị trường.

## Các chỉ báo

### 1. RSI (Relative Strength Index)

#### `calculate_rsi(prices, period=14)`
Tính RSI - chỉ báo đo lường sức mạnh tương đối của giá.

**Tham số:**
- `prices` (array-like): Mảng giá đóng cửa
- `period` (int): Chu kỳ tính toán (mặc định 14)

**Trả về:**
- `float`: Giá trị RSI (0-100) hoặc `None` nếu không đủ dữ liệu

**Ý nghĩa:**
- RSI > 70: Quá mua (overbought) - có thể giảm giá
- RSI < 30: Quá bán (oversold) - có thể tăng giá
- RSI 30-70: Vùng trung tính

**Ví dụ:**
```python
from indicators import calculate_rsi
import numpy as np

prices = np.array([50000, 51000, 52000, 51500, 53000, 52500, 54000])
rsi = calculate_rsi(prices, period=14)
if rsi:
    if rsi > 70:
        print("Quá mua - có thể giảm")
    elif rsi < 30:
        print("Quá bán - có thể tăng")
```

### 2. MACD (Moving Average Convergence Divergence)

#### `calculate_macd(prices, fast=12, slow=26, signal=9)`
Tính MACD - chỉ báo xu hướng sử dụng 2 đường EMA.

**Tham số:**
- `prices` (array-like): Mảng giá đóng cửa
- `fast` (int): Chu kỳ EMA nhanh (mặc định 12)
- `slow` (int): Chu kỳ EMA chậm (mặc định 26)
- `signal` (int): Chu kỳ Signal line (mặc định 9)

**Trả về:**
- `tuple`: (macd_line, signal_line, histogram)
  - `macd_line`: Giá trị MACD line
  - `signal_line`: Giá trị Signal line (None nếu không đủ dữ liệu)
  - `histogram`: Giá trị Histogram (None nếu không đủ dữ liệu)

**Ý nghĩa:**
- MACD > Signal và Histogram > 0: Bullish (tăng giá)
- MACD < Signal và Histogram < 0: Bearish (giảm giá)

**Ví dụ:**
```python
from indicators import calculate_macd

macd, signal, histogram = calculate_macd(prices)
if macd and signal:
    if macd > signal and histogram > 0:
        print("Tín hiệu Bullish")
    elif macd < signal and histogram < 0:
        print("Tín hiệu Bearish")
```

### 3. Bollinger Bands

#### `calculate_bollinger_bands(prices, period=20, std_dev=2)`
Tính Bollinger Bands - 3 đường bao quanh giá.

**Tham số:**
- `prices` (array-like): Mảng giá đóng cửa
- `period` (int): Chu kỳ tính SMA (mặc định 20)
- `std_dev` (float): Độ lệch chuẩn (mặc định 2)

**Trả về:**
- `tuple`: (upper_band, middle_band, lower_band)

**Ý nghĩa:**
- Giá chạm dải trên: Có thể quá mua, chuẩn bị giảm
- Giá chạm dải dưới: Có thể quá bán, chuẩn bị tăng
- Giá trong dải: Thị trường ổn định

**Ví dụ:**
```python
from indicators import calculate_bollinger_bands

upper, middle, lower = calculate_bollinger_bands(prices)
current_price = prices[-1]

if current_price < lower:
    print("Giá ở dưới dải dưới - có thể bounce")
elif current_price > upper:
    print("Giá ở trên dải trên - có thể pullback")
```

### 4. Volume Profile

#### `calculate_volume_profile(df, num_levels=10)`
Tính Volume Profile để xác định vùng giá có volume cao.

**Tham số:**
- `df` (pandas.DataFrame): DataFrame chứa ['high', 'low', 'close', 'volume']
- `num_levels` (int): Số mức giá cần phân tích (mặc định 10)

**Trả về:**
- `tuple`: (poc_level, volume_by_level)
  - `poc_level`: Mức giá có volume cao nhất (POC - Point of Control)
  - `volume_by_level`: Dictionary {level: volume}

**Ý nghĩa:**
- POC: Mức giá có volume cao nhất - vùng hỗ trợ/kháng cự mạnh
- Vùng giá có volume cao: Vùng hỗ trợ/kháng cự quan trọng

**Ví dụ:**
```python
from indicators import calculate_volume_profile
import pandas as pd

# df là DataFrame chứa OHLCV data
poc_level, volume_by_level = calculate_volume_profile(df, num_levels=10)
print(f"POC Level: {poc_level}")
print(f"Volume distribution: {volume_by_level}")
```

### 5. Technical Score (Tổng hợp)

#### `calculate_technical_score(df, btc_dom=None)`
Tính điểm tổng hợp từ các chỉ báo kỹ thuật.

**Tham số:**
- `df` (pandas.DataFrame): DataFrame chứa ['close', 'high', 'low', 'volume']
- `btc_dom` (float, optional): BTC Dominance (chưa sử dụng)

**Trả về:**
- `tuple`: (final_score, scores_dict)
  - `final_score`: Điểm tổng hợp từ -1 (rất bearish) đến +1 (rất bullish)
  - `scores_dict`: Dictionary chứa điểm từng chỉ báo

**Trọng số:**
- RSI: 0.2 (20%)
- MACD: 0.25 (25%)
- Bollinger Bands: 0.15 (15%)
- Volume Analysis: 0.15 (15%)
- Wyckoff Analysis: 0.15 (15%) - từ theories module
- Dow Theory: 0.1 (10%) - từ theories module

**Ví dụ:**
```python
from indicators import calculate_technical_score

score, details = calculate_technical_score(df)
if score:
    if score > 0.5:
        print("Rất Bullish")
    elif score < -0.5:
        print("Rất Bearish")
    else:
        print("Trung tính")
    
    print(f"RSI score: {details.get('rsi', 0)}")
    print(f"MACD score: {details.get('macd', 0)}")
```

## Sử dụng kết hợp

```python
from indicators import calculate_rsi, calculate_macd, calculate_bollinger_bands, calculate_technical_score
import utils

# Lấy dữ liệu kline
df = utils.get_klines_binance('BTCUSDT', interval='4h', limit=200)

if df is not None:
    prices = df['close'].values
    
    # Tính các chỉ báo riêng lẻ
    rsi = calculate_rsi(prices)
    macd, signal, histogram = calculate_macd(prices)
    upper, middle, lower = calculate_bollinger_bands(prices)
    
    # Hoặc tính điểm tổng hợp
    technical_score, details = calculate_technical_score(df)
    
    print(f"RSI: {rsi}")
    print(f"MACD: {macd}, Signal: {signal}, Histogram: {histogram}")
    print(f"Bollinger: Upper={upper}, Middle={middle}, Lower={lower}")
    print(f"Technical Score: {technical_score}")
```

## Lưu ý

- Tất cả các chỉ báo đều yêu cầu đủ dữ liệu lịch sử
- RSI cần ít nhất `period + 1` điểm dữ liệu
- MACD cần ít nhất `slow` điểm dữ liệu
- Bollinger Bands cần ít nhất `period` điểm dữ liệu
- Technical Score cần ít nhất 50 điểm dữ liệu

