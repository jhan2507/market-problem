# Lý thuyết phân tích kỹ thuật (Theories)

Module `theories.py` chứa các hàm phân tích dựa trên các lý thuyết phân tích kỹ thuật nâng cao.

## Các lý thuyết

### 1. Wyckoff Method

#### `analyze_wyckoff(df)`
Phân tích Wyckoff để xác định giai đoạn tích lũy (accumulation) hoặc phân phối (distribution).

**Tham số:**
- `df` (pandas.DataFrame): DataFrame chứa ['close', 'high', 'low', 'volume']
  - Cần ít nhất 50 nến để phân tích chính xác

**Trả về:**
- `dict`: Dictionary chứa:
  - `phase`: Giai đoạn hiện tại ('ACCUMULATION', 'MARKUP', 'DISTRIBUTION', 'MARKDOWN', None)
  - `strength`: Độ mạnh của tín hiệu (0-1)
  - `price_position`: Vị trí giá trong range (0-1, 0=đáy, 1=đỉnh)
  - `volume_ratio`: Tỷ lệ volume hiện tại so với trung bình
  - `None` nếu không đủ dữ liệu

**4 Giai đoạn của Wyckoff:**

1. **Accumulation (Tích lũy)**
   - Dấu hiệu: Giá ở vùng thấp, volume thấp khi giảm, tăng khi giá tăng
   - Tín hiệu: Chuẩn bị tăng giá
   - Hành động: Cơ hội mua vào

2. **Markup (Tăng giá)**
   - Dấu hiệu: Giá tăng với volume tăng mạnh
   - Tín hiệu: Xu hướng tăng đang diễn ra
   - Hành động: Giữ vị thế long

3. **Distribution (Phân phối)**
   - Dấu hiệu: Giá ở vùng cao, volume giảm
   - Tín hiệu: Chuẩn bị giảm giá
   - Hành động: Cân nhắc chốt lời

4. **Markdown (Giảm giá)**
   - Dấu hiệu: Giá giảm với volume tăng mạnh
   - Tín hiệu: Xu hướng giảm đang diễn ra
   - Hành động: Tránh mua vào

**Ví dụ:**
```python
from theories import analyze_wyckoff
import utils

# Lấy dữ liệu kline
df = utils.get_klines_binance('BTCUSDT', interval='4h', limit=200)

if df is not None:
    wyckoff = analyze_wyckoff(df)
    
    if wyckoff and wyckoff['phase']:
        phase = wyckoff['phase']
        strength = wyckoff['strength']
        
        print(f"Giai đoạn: {phase}")
        print(f"Độ mạnh: {strength:.2f}")
        print(f"Vị trí giá: {wyckoff['price_position']:.2f}")
        
        if phase == 'ACCUMULATION':
            print("💡 Cơ hội mua vào")
        elif phase == 'MARKUP':
            print("📈 Xu hướng tăng - giữ long")
        elif phase == 'DISTRIBUTION':
            print("⚠️ Cân nhắc chốt lời")
        elif phase == 'MARKDOWN':
            print("📉 Xu hướng giảm - tránh mua")
```

### 2. Dow Theory

#### `analyze_dow_theory(df)`
Phân tích Lý thuyết Dow để xác định xu hướng đa khung thời gian.

**Tham số:**
- `df` (pandas.DataFrame): DataFrame chứa ['close']
  - Cần ít nhất 100 nến để phân tích chính xác

**Trả về:**
- `dict`: Dictionary chứa:
  - `primary_trend`: Xu hướng chính ('BULLISH', 'BEARISH', 'NEUTRAL')
  - `primary_strength`: Độ mạnh xu hướng chính (0-1)
  - `secondary_trend`: Xu hướng phụ ('BULLISH', 'BEARISH', 'NEUTRAL')
  - `secondary_strength`: Độ mạnh xu hướng phụ (0-1)
  - `minor_trend`: Xu hướng nhỏ ('BULLISH', 'BEARISH', 'NEUTRAL')
  - `minor_strength`: Độ mạnh xu hướng nhỏ (0-1)
  - `trend_alignment`: Mức độ đồng thuận (0-1, 1=tất cả đồng thuận)
  - `None` nếu không đủ dữ liệu

**3 Loại xu hướng:**

1. **Primary Trend (Xu hướng chính)**
   - Thời gian: Dài hạn (1-3 năm)
   - Sử dụng: MA dài hạn (50-200 periods)
   - Ý nghĩa: Xác định xu hướng chính của thị trường

2. **Secondary Trend (Xu hướng phụ)**
   - Thời gian: Trung hạn (3 tuần - 3 tháng)
   - Sử dụng: MA trung hạn (20-50 periods)
   - Ý nghĩa: Điều chỉnh trong xu hướng chính

3. **Minor Trend (Xu hướng nhỏ)**
   - Thời gian: Ngắn hạn (vài ngày - 3 tuần)
   - Sử dụng: MA ngắn hạn (5-20 periods)
   - Ý nghĩa: Biến động ngắn hạn

**Trend Alignment:**
- `1.0`: Tất cả 3 xu hướng đồng thuận - tín hiệu rất mạnh
- `0.7`: Chính và phụ đồng thuận - tín hiệu mạnh
- `0.5`: Phụ và nhỏ đồng thuận - tín hiệu trung bình

**Ví dụ:**
```python
from theories import analyze_dow_theory
import utils

# Lấy dữ liệu kline
df = utils.get_klines_binance('BTCUSDT', interval='1d', limit=200)

if df is not None:
    dow = analyze_dow_theory(df)
    
    if dow:
        print(f"Xu hướng chính: {dow['primary_trend']} (độ mạnh: {dow['primary_strength']:.2f})")
        print(f"Xu hướng phụ: {dow['secondary_trend']} (độ mạnh: {dow['secondary_strength']:.2f})")
        print(f"Xu hướng nhỏ: {dow['minor_trend']} (độ mạnh: {dow['minor_strength']:.2f})")
        print(f"Đồng thuận: {dow['trend_alignment']:.2f}")
        
        if dow['trend_alignment'] > 0.7:
            if dow['primary_trend'] == 'BULLISH':
                print("🟢 Tất cả xu hướng đồng thuận BULLISH - tín hiệu rất mạnh")
            else:
                print("🔴 Tất cả xu hướng đồng thuận BEARISH - tín hiệu rất mạnh")
```

## Sử dụng kết hợp

```python
from theories import analyze_wyckoff, analyze_dow_theory
from indicators import calculate_technical_score
import utils

# Lấy dữ liệu
df = utils.get_klines_binance('BTCUSDT', interval='4h', limit=200)

if df is not None:
    # Phân tích Wyckoff
    wyckoff = analyze_wyckoff(df)
    
    # Phân tích Dow Theory
    dow = analyze_dow_theory(df)
    
    # Tính điểm tổng hợp (bao gồm cả Wyckoff và Dow Theory)
    technical_score, details = calculate_technical_score(df)
    
    # Đưa ra nhận định
    if wyckoff and wyckoff['phase']:
        print(f"Wyckoff: {wyckoff['phase']} (strength: {wyckoff['strength']:.2f})")
    
    if dow:
        print(f"Dow Theory: Primary={dow['primary_trend']}, Alignment={dow['trend_alignment']:.2f}")
    
    if technical_score:
        print(f"Technical Score: {technical_score:.2f} ({'Bullish' if technical_score > 0 else 'Bearish'})")
```

## Lưu ý

- Wyckoff Method cần ít nhất 50 nến để phân tích chính xác
- Dow Theory cần ít nhất 100 nến để phân tích chính xác
- Kết hợp nhiều lý thuyết sẽ cho kết quả chính xác hơn
- Trend alignment > 0.7 là tín hiệu mạnh, nên chú ý

## Tài liệu tham khảo

- **Wyckoff Method**: Phương pháp phân tích tích lũy/phân phối của Richard Wyckoff
- **Dow Theory**: Lý thuyết xu hướng thị trường của Charles Dow

