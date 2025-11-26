"""
Các chỉ báo kỹ thuật (Technical Indicators).

Module này chứa các hàm tính toán các chỉ báo kỹ thuật phổ biến:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Volume Profile
"""

import numpy as np
import pandas as pd


def calculate_rsi(prices, period=14):
    """
    Tính RSI (Relative Strength Index).
    
    RSI là chỉ báo đo lường sức mạnh tương đối của giá, dao động từ 0-100.
    - RSI > 70: Quá mua (overbought) - có thể giảm giá
    - RSI < 30: Quá bán (oversold) - có thể tăng giá
    - RSI 30-70: Vùng trung tính
    
    Args:
        prices (array-like): Mảng giá đóng cửa
        period (int): Chu kỳ tính toán (mặc định 14)
    
    Returns:
        float: Giá trị RSI (0-100) hoặc None nếu không đủ dữ liệu
    """
    if len(prices) < period + 1:
        return None
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """
    Tính MACD (Moving Average Convergence Divergence).
    
    MACD là chỉ báo xu hướng sử dụng 2 đường EMA:
    - MACD Line = EMA(fast) - EMA(slow)
    - Signal Line = EMA của MACD Line
    - Histogram = MACD Line - Signal Line
    
    Tín hiệu:
    - MACD > Signal và Histogram > 0: Bullish (tăng giá)
    - MACD < Signal và Histogram < 0: Bearish (giảm giá)
    
    Args:
        prices (array-like): Mảng giá đóng cửa
        fast (int): Chu kỳ EMA nhanh (mặc định 12)
        slow (int): Chu kỳ EMA chậm (mặc định 26)
        signal (int): Chu kỳ Signal line (mặc định 9)
    
    Returns:
        tuple: (macd_line, signal_line, histogram)
               - macd_line: Giá trị MACD line
               - signal_line: Giá trị Signal line (None nếu không đủ dữ liệu)
               - histogram: Giá trị Histogram (None nếu không đủ dữ liệu)
    """
    if len(prices) < slow:
        return None, None, None
    
    ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean().iloc[-1]
    ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean().iloc[-1]
    macd_line = ema_fast - ema_slow
    
    # Tính signal line (EMA của MACD)
    if len(prices) >= slow + signal:
        macd_series = pd.Series(prices).ewm(span=fast, adjust=False).mean() - pd.Series(prices).ewm(span=slow, adjust=False).mean()
        signal_line = macd_series.ewm(span=signal, adjust=False).mean().iloc[-1]
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    return macd_line, None, None


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """
    Tính Bollinger Bands.
    
    Bollinger Bands gồm 3 đường:
    - Upper Band = SMA + (std_dev * std)
    - Middle Band = SMA (Simple Moving Average)
    - Lower Band = SMA - (std_dev * std)
    
    Tín hiệu:
    - Giá chạm dải trên: Có thể quá mua, chuẩn bị giảm
    - Giá chạm dải dưới: Có thể quá bán, chuẩn bị tăng
    - Giá trong dải: Thị trường ổn định
    
    Args:
        prices (array-like): Mảng giá đóng cửa
        period (int): Chu kỳ tính SMA (mặc định 20)
        std_dev (float): Độ lệch chuẩn (mặc định 2)
    
    Returns:
        tuple: (upper_band, middle_band, lower_band)
               Tất cả đều None nếu không đủ dữ liệu
    """
    if len(prices) < period:
        return None, None, None
    
    sma = np.mean(prices[-period:])
    std = np.std(prices[-period:])
    upper_band = sma + (std_dev * std)
    lower_band = sma - (std_dev * std)
    return upper_band, sma, lower_band


def calculate_volume_profile(df, num_levels=10):
    """
    Tính Volume Profile để xác định vùng giá có volume cao.
    
    Volume Profile phân tích volume theo từng mức giá để tìm:
    - POC (Point of Control): Mức giá có volume cao nhất
    - Vùng giá có volume cao: Vùng hỗ trợ/kháng cự mạnh
    
    Args:
        df (pandas.DataFrame): DataFrame chứa ['high', 'low', 'close', 'volume']
        num_levels (int): Số mức giá cần phân tích (mặc định 10)
    
    Returns:
        tuple: (poc_level, volume_by_level)
               - poc_level: Mức giá có volume cao nhất
               - volume_by_level: Dictionary {level: volume}
               Tất cả đều None nếu không có dữ liệu
    """
    if df is None or len(df) == 0:
        return None
    
    price_range = df['high'].max() - df['low'].min()
    if price_range == 0:
        return None
    
    level_size = price_range / num_levels
    volume_by_level = {}
    
    for _, row in df.iterrows():
        level = int((row['close'] - df['low'].min()) / level_size)
        level = max(0, min(num_levels - 1, level))
        volume_by_level[level] = volume_by_level.get(level, 0) + row['volume']
    
    # Tìm POC (Point of Control) - level có volume cao nhất
    if volume_by_level:
        poc_level = max(volume_by_level, key=volume_by_level.get)
        return poc_level, volume_by_level
    return None


def calculate_technical_score(df, btc_dom=None):
    """
    Tính điểm tổng hợp từ các chỉ báo kỹ thuật.
    
    Hàm này kết hợp nhiều chỉ báo để đưa ra điểm tổng hợp:
    - RSI (trọng số 0.2)
    - MACD (trọng số 0.25)
    - Bollinger Bands (trọng số 0.15)
    - Volume Analysis (trọng số 0.15)
    - Wyckoff Analysis (trọng số 0.15) - từ theories module
    - Dow Theory (trọng số 0.1) - từ theories module
    
    Args:
        df (pandas.DataFrame): DataFrame chứa ['close', 'high', 'low', 'volume']
        btc_dom (float, optional): BTC Dominance (chưa sử dụng)
    
    Returns:
        tuple: (final_score, scores_dict)
               - final_score: Điểm tổng hợp từ -1 (rất bearish) đến +1 (rất bullish)
               - scores_dict: Dictionary chứa điểm từng chỉ báo
    """
    from theories import analyze_wyckoff, analyze_dow_theory
    
    if df is None or len(df) < 50:
        return None, {}
    
    prices = df['close'].values
    volumes = df['volume'].values
    
    scores = {}
    total_score = 0
    weight_sum = 0
    
    # 1. RSI (trọng số 0.2)
    rsi = calculate_rsi(prices)
    if rsi is not None:
        if rsi < 30:
            rsi_score = 0.8  # Quá bán - bullish
        elif rsi > 70:
            rsi_score = -0.8  # Quá mua - bearish
        elif rsi < 50:
            rsi_score = (50 - rsi) / 50 * 0.5  # Từ 0 đến 0.5
        else:
            rsi_score = -(rsi - 50) / 50 * 0.5  # Từ 0 đến -0.5
        scores['rsi'] = rsi_score
        total_score += rsi_score * 0.2
        weight_sum += 0.2
    
    # 2. MACD (trọng số 0.25)
    macd, signal, histogram = calculate_macd(prices)
    if macd is not None:
        if signal is not None:
            if macd > signal and histogram > 0:
                macd_score = 0.7  # Bullish crossover
            elif macd < signal and histogram < 0:
                macd_score = -0.7  # Bearish crossover
            else:
                macd_score = histogram * 10  # Normalize
        else:
            macd_score = 0.5 if macd > 0 else -0.5
        scores['macd'] = macd_score
        total_score += macd_score * 0.25
        weight_sum += 0.25
    
    # 3. Bollinger Bands (trọng số 0.15)
    upper, middle, lower = calculate_bollinger_bands(prices)
    if upper is not None:
        current_price = prices[-1]
        if current_price < lower:
            bb_score = 0.6  # Giá ở dưới dải dưới - có thể bounce
        elif current_price > upper:
            bb_score = -0.6  # Giá ở trên dải trên - có thể pullback
        else:
            # Vị trí trong dải
            bb_position = (current_price - lower) / (upper - lower) if (upper - lower) > 0 else 0.5
            bb_score = (bb_position - 0.5) * 2  # Từ -1 đến +1
        scores['bollinger'] = bb_score
        total_score += bb_score * 0.15
        weight_sum += 0.15
    
    # 4. Volume Analysis (trọng số 0.15)
    if len(volumes) >= 20:
        current_volume = volumes[-1]
        avg_volume = np.mean(volumes[-20:])
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        price_change = (prices[-1] - prices[-2]) / prices[-2] if len(prices) >= 2 else 0
        
        # Volume tăng cùng với giá tăng = bullish
        if price_change > 0 and volume_ratio > 1.2:
            volume_score = 0.6
        elif price_change < 0 and volume_ratio > 1.2:
            volume_score = -0.6  # Volume tăng với giá giảm = bearish
        else:
            volume_score = (volume_ratio - 1) * 0.3  # Normalize
        scores['volume'] = volume_score
        total_score += volume_score * 0.15
        weight_sum += 0.15
    
    # 5. Wyckoff Analysis (trọng số 0.15)
    wyckoff = analyze_wyckoff(df)
    if wyckoff and wyckoff['phase']:
        if wyckoff['phase'] in ['ACCUMULATION', 'MARKUP']:
            wyckoff_score = wyckoff['strength'] * 0.7
        elif wyckoff['phase'] in ['DISTRIBUTION', 'MARKDOWN']:
            wyckoff_score = -wyckoff['strength'] * 0.7
        else:
            wyckoff_score = 0
        scores['wyckoff'] = wyckoff_score
        total_score += wyckoff_score * 0.15
        weight_sum += 0.15
    
    # 6. Dow Theory (trọng số 0.1)
    dow = analyze_dow_theory(df)
    if dow:
        if dow['trend_alignment'] > 0.7:
            if dow['primary_trend'] == 'BULLISH':
                dow_score = 0.6 * dow['trend_alignment']
            else:
                dow_score = -0.6 * dow['trend_alignment']
        else:
            dow_score = 0
        scores['dow'] = dow_score
        total_score += dow_score * 0.1
        weight_sum += 0.1
    
    # Normalize score
    final_score = total_score / weight_sum if weight_sum > 0 else 0
    
    return final_score, scores

