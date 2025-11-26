# CÔNG THỨC VÀ LOGIC QUYẾT ĐỊNH LONG/SHORT

## 📊 CÁC CHỈ SỐ ĐƯỢC SỬ DỤNG

### 1. BTC Dominance (BTC_DOM)
- **Định nghĩa**: Tỷ lệ % vốn hóa thị trường của BTC so với tổng vốn hóa crypto
- **Ý nghĩa**: 
  - BTC_DOM tăng → Vốn chảy vào BTC, altcoin yếu
  - BTC_DOM giảm → Vốn chảy ra altcoin, altcoin mạnh

### 2. USDT Dominance (USDT_DOM)
- **Định nghĩa**: Tỷ lệ % vốn hóa USDT so với tổng vốn hóa crypto
- **Ý nghĩa**:
  - USDT_DOM tăng → Rút vốn khỏi thị trường (bán coin → USDT)
  - USDT_DOM giảm → Vốn vào thị trường (bán USDT → mua coin)

### 3. Fear & Greed Index (FEAR_INDEX)
- **Định nghĩa**: Chỉ số tâm lý từ 0-100 (0 = cực sợ, 100 = cực tham)
- **Ý nghĩa**:
  - Fear thấp (< 30) → Cơ hội mua vào
  - Greed cao (> 70) → Cảnh báo bán/chốt lời

---

## 🔢 CÔNG THỨC TÍNH TOÁN

### Bước 1: Tính Thống Kê (Stats) cho từng khung thời gian
```
Khung thời gian: 1h, 6h, 24h, 2 ngày (2d)

Mean (Trung bình) = Σ(values) / n
Std (Độ lệch chuẩn) = √(Σ(xi - mean)² / n)
Momentum = (giá_trị_cuối - giá_trị_đầu) / số_lượng_mẫu
Trend = 'up' nếu momentum > 0, 'down' nếu < 0, 'neutral' nếu = 0
```

### Bước 2: Phát hiện Anomaly (Bất thường)
```
Z-Score = (giá_trị_hiện_tại - Mean) / Std

Severity:
- 'high' nếu |Z-Score| >= threshold_std
- 'medium' nếu |Z-Score| >= threshold_std * 0.7
- 'low' nếu |Z-Score| < threshold_std * 0.7
```

### Bước 3: Tính % thay đổi
```
Change_PCT = ((giá_trị_hiện_tại - Mean) / Mean) * 100
```

---

## 📈 LOGIC QUYẾT ĐỊNH LONG/SHORT

### 1. TÍN HIỆU BTC DOMINANCE

#### 🚨 LONG BTC, SHORT ALTCOIN
**Điều kiện:**
```
BTC_DOM > Mean_2d + Std_2d * 1.5
VÀ
|Z-Score| >= 1.5 (severity = 'high' hoặc 'medium')
```

**Công thức:**
```
Z-Score = (BTC_DOM - Mean_2d) / Std_2d
Change_PCT = ((BTC_DOM - Mean_2d) / Mean_2d) * 100
```

**Lý do:**
- BTC_DOM tăng đột biến → Vốn đổ vào BTC, altcoin bị bán
- Confidence: 'high' nếu |Z-Score| >= 1.5, 'medium' nếu >= 1.05

**Action:** `LONG_BTC_SHORT_ALT`

---

#### 🚀 SHORT BTC, LONG ALTCOIN TOP
**Điều kiện:**
```
BTC_DOM < Mean_2d - Std_2d * 1.5
VÀ
|Z-Score| >= 1.5 (severity = 'high' hoặc 'medium')
```

**Công thức:**
```
Z-Score = (BTC_DOM - Mean_2d) / Std_2d
Change_PCT = ((BTC_DOM - Mean_2d) / Mean_2d) * 100
```

**Lý do:**
- BTC_DOM giảm mạnh → Vốn chảy ra altcoin, altcoin mạnh lên
- Confidence: 'high' nếu |Z-Score| >= 1.5, 'medium' nếu >= 1.05

**Action:** `SHORT_BTC_LONG_ALT`

---

### 2. TÍN HIỆU USDT DOMINANCE

#### ⚠️ SHORT TOÀN THỊ TRƯỜNG
**Điều kiện:**
```
USDT_DOM > Mean_2d + Std_2d * 1.2
VÀ
|Z-Score| >= 1.2 (severity = 'high' hoặc 'medium')
```

**Công thức:**
```
Z-Score = (USDT_DOM - Mean_2d) / Std_2d
Change_PCT = ((USDT_DOM - Mean_2d) / Mean_2d) * 100
```

**Lý do:**
- USDT_DOM tăng → Rút vốn khỏi thị trường (bán coin → USDT)
- Dấu hiệu điều chỉnh/giảm giá
- Confidence: 'high' nếu |Z-Score| >= 1.2, 'medium' nếu >= 0.84

**Action:** `SHORT_MARKET`

---

#### 🚀 LONG TOÀN THỊ TRƯỜNG
**Điều kiện:**
```
USDT_DOM < Mean_2d - Std_2d * 1.2
VÀ
|Z-Score| >= 1.2 (severity = 'high' hoặc 'medium')
```

**Công thức:**
```
Z-Score = (USDT_DOM - Mean_2d) / Std_2d
Change_PCT = ((USDT_DOM - Mean_2d) / Mean_2d) * 100
```

**Lý do:**
- USDT_DOM giảm → Vốn vào thị trường (bán USDT → mua coin)
- Dấu hiệu tăng giá
- Confidence: 'high' nếu |Z-Score| >= 1.2, 'medium' nếu >= 0.84

**Action:** `LONG_MARKET`

---

### 3. TÍN HIỆU FEAR & GREED INDEX

#### 💡 LONG DẦN TỪNG PHẦN (FEAR SPIKE)
**Điều kiện:**
```
FEAR_INDEX < Mean_2d - Std_2d * 1.5
VÀ
|Z-Score| >= 1.5 (severity = 'high' hoặc 'medium')
```

**Công thức:**
```
Z-Score = (FEAR_INDEX - Mean_2d) / Std_2d
Change = FEAR_INDEX - Mean_2d
```

**Lý do:**
- Fear tăng mạnh → Tâm lý sợ hãi cực độ → Cơ hội mua vào
- Confidence: 'high' nếu |Z-Score| >= 1.5, 'medium' nếu >= 1.05

**Action:** `LONG_ACCUMULATE`

---

#### ⚠️ SHORT HOẶC CHỐT LỜI (GREED SPIKE)
**Điều kiện:**
```
FEAR_INDEX > Mean_2d + Std_2d * 1.5
VÀ
|Z-Score| >= 1.5 (severity = 'high' hoặc 'medium')
```

**Công thức:**
```
Z-Score = (FEAR_INDEX - Mean_2d) / Std_2d
Change = FEAR_INDEX - Mean_2d
```

**Lý do:**
- Greed tăng mạnh → Tâm lý tham lam cực độ → Cảnh báo bán/chốt lời
- Confidence: 'high' nếu |Z-Score| >= 1.5, 'medium' nếu >= 1.05

**Action:** `SHORT_OR_TAKE_PROFIT`

---

### 4. PHÂN TÍCH TỔNG HỢP

#### 🔴 CẢNH BÁO: RÚT VỐN MẠNH
**Điều kiện:**
```
BTC_DOM > Mean_2d + Std_2d * 0.8
VÀ
USDT_DOM > Mean_2d + Std_2d * 0.8
```

**Công thức:**
```
Combined_Value = BTC_DOM + USDT_DOM
```

**Lý do:**
- Cả BTC_DOM và USDT_DOM cùng tăng → Rút vốn mạnh khỏi thị trường
- Thị trường điều chỉnh mạnh
- Confidence: luôn 'high'

**Action:** `SHORT_ALL`

---

#### 🟢 CƠ HỘI MUA VÀO
**Điều kiện:**
```
BTC_DOM < Mean_2d - Std_2d * 0.8
VÀ
USDT_DOM < Mean_2d - Std_2d * 0.8
VÀ
FEAR_INDEX < Mean_2d - Std_2d * 0.8
```

**Công thức:**
```
Combined_Value = BTC_DOM + USDT_DOM + FEAR_INDEX
```

**Lý do:**
- Cả 3 chỉ số đều tích cực:
  - BTC_DOM giảm → Altcoin mạnh
  - USDT_DOM giảm → Vốn vào thị trường
  - Fear thấp → Tâm lý sợ hãi, cơ hội mua
- Confidence: luôn 'high'

**Action:** `LONG_ALL`

---

## 🔄 CƠ CHẾ PHÁT TÍN HIỆU (Signal Emission)

### Điều kiện phát tín hiệu:
1. **Tín hiệu mới**: Chưa từng phát tín hiệu này → Phát ngay
2. **Đảo chiều**: Action khác với tín hiệu trước → Phát ngay
3. **Thay đổi giá trị > 30%**: Giá trị thay đổi > 30% so với lần trước → Phát lại
4. **Confidence tăng**: Từ 'medium' lên 'high' → Phát lại
5. **Hết hạn**: Sau 4 giờ (SIGNAL_COOLDOWN) → Phát lại
6. **Trong cooldown**: Không phát lại nếu không có thay đổi đáng kể

### Công thức kiểm tra:
```
Time_Since_Last = Current_Time - Last_Signal_Time

IF Time_Since_Last < SIGNAL_COOLDOWN (4 giờ):
    IF Action != Last_Action:
        → Phát (Đảo chiều)
    ELIF Value_Change > 30%:
        → Phát (Thay đổi đáng kể)
    ELIF Confidence tăng từ medium → high:
        → Phát (Tăng độ tin cậy)
    ELSE:
        → Không phát (Trong cooldown)
ELSE:
    → Phát (Hết hạn)
```

---

## 📋 TÓM TẮT BẢNG QUYẾT ĐỊNH

| Chỉ số | Điều kiện | Threshold | Action | Confidence |
|--------|-----------|-----------|--------|------------|
| BTC_DOM | Tăng đột biến | Mean + 1.5*Std | LONG_BTC_SHORT_ALT | High/Medium |
| BTC_DOM | Giảm mạnh | Mean - 1.5*Std | SHORT_BTC_LONG_ALT | High/Medium |
| USDT_DOM | Tăng mạnh | Mean + 1.2*Std | SHORT_MARKET | High/Medium |
| USDT_DOM | Giảm mạnh | Mean - 1.2*Std | LONG_MARKET | High/Medium |
| FEAR_INDEX | Fear tăng (giảm giá trị) | Mean - 1.5*Std | LONG_ACCUMULATE | High/Medium |
| FEAR_INDEX | Greed tăng (tăng giá trị) | Mean + 1.5*Std | SHORT_OR_TAKE_PROFIT | High/Medium |
| BTC_DOM + USDT_DOM | Cùng tăng | Mean + 0.8*Std (cả 2) | SHORT_ALL | High |
| BTC_DOM + USDT_DOM + FEAR | Cùng giảm | Mean - 0.8*Std (cả 3) | LONG_ALL | High |

---

## ⚙️ THAM SỐ CẤU HÌNH

- **SIGNAL_COOLDOWN**: 4 giờ (14400 giây)
- **SIGNAL_VALUE_THRESHOLD**: 30% (0.3)
- **BTC_DOM Threshold**: 1.5 * Std
- **USDT_DOM Threshold**: 1.2 * Std
- **FEAR_INDEX Threshold**: 1.5 * Std
- **Tổng hợp Threshold**: 0.8 * Std

---

## 🎯 LOGIC ĐẰNG SAU

### Tại sao BTC_DOM tăng → LONG BTC?
- Khi BTC_DOM tăng, nghĩa là vốn đổ vào BTC
- Altcoin bị bán để mua BTC
- → LONG BTC, SHORT altcoin

### Tại sao USDT_DOM tăng → SHORT?
- USDT_DOM tăng = Nhiều người bán coin → USDT
- Dấu hiệu rút vốn khỏi thị trường
- → SHORT toàn thị trường

### Tại sao Fear tăng → LONG?
- Fear tăng = Tâm lý sợ hãi cực độ
- Thị trường oversold → Cơ hội mua vào
- → LONG dần từng phần

### Tại sao Greed tăng → SHORT?
- Greed tăng = Tâm lý tham lam cực độ
- Thị trường overbought → Cảnh báo bán
- → SHORT hoặc chốt lời

