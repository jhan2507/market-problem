"""
Các lý thuyết phân tích kỹ thuật nâng cao.

Module này chứa các hàm phân tích dựa trên các lý thuyết:
- Wyckoff Method: Phân tích tích lũy/phân phối
- Dow Theory: Phân tích xu hướng đa khung thời gian
"""

import numpy as np


def analyze_wyckoff(df):
    """
    Phân tích Wyckoff: Xác định giai đoạn tích lũy (accumulation) hoặc phân phối (distribution).
    
    Wyckoff Method có 4 giai đoạn:
    1. Accumulation (Tích lũy): Giá ở đáy, volume giảm, sau đó tăng
       - Dấu hiệu: Giá ở vùng thấp, volume thấp khi giảm, tăng khi giá tăng
       - Tín hiệu: Chuẩn bị tăng giá
    
    2. Markup (Tăng giá): Giá tăng với volume tăng
       - Dấu hiệu: Giá tăng, volume tăng mạnh
       - Tín hiệu: Xu hướng tăng đang diễn ra
    
    3. Distribution (Phân phối): Giá ở đỉnh, volume giảm
       - Dấu hiệu: Giá ở vùng cao, volume giảm
       - Tín hiệu: Chuẩn bị giảm giá
    
    4. Markdown (Giảm giá): Giá giảm với volume tăng
       - Dấu hiệu: Giá giảm, volume tăng mạnh
       - Tín hiệu: Xu hướng giảm đang diễn ra
    
    Args:
        df (pandas.DataFrame): DataFrame chứa ['close', 'high', 'low', 'volume']
                               Cần ít nhất 50 nến để phân tích chính xác
    
    Returns:
        dict: Dictionary chứa:
            - 'phase': Giai đoạn hiện tại ('ACCUMULATION', 'MARKUP', 'DISTRIBUTION', 'MARKDOWN', None)
            - 'strength': Độ mạnh của tín hiệu (0-1)
            - 'price_position': Vị trí giá trong range (0-1, 0=đáy, 1=đỉnh)
            - 'volume_ratio': Tỷ lệ volume hiện tại so với trung bình
            None nếu không đủ dữ liệu
    """
    if df is None or len(df) < 50:
        return None
    
    # Tính các chỉ số cần thiết
    prices = df['close'].values
    volumes = df['volume'].values
    
    # Tính trung bình giá và volume
    price_ma = np.mean(prices[-20:])
    volume_ma = np.mean(volumes[-20:])
    
    current_price = prices[-1]
    current_volume = volumes[-1]
    
    # Phân tích price action
    recent_high = np.max(prices[-20:])
    recent_low = np.min(prices[-20:])
    price_range = recent_high - recent_low
    
    # Xác định vị trí giá hiện tại trong range
    price_position = (current_price - recent_low) / price_range if price_range > 0 else 0.5
    
    # Phân tích volume
    volume_ratio = current_volume / volume_ma if volume_ma > 0 else 1
    
    # Phân tích xu hướng
    short_ma = np.mean(prices[-10:])
    long_ma = np.mean(prices[-30:])
    
    wyckoff_phase = None
    signal_strength = 0
    
    # Giai đoạn 1: Accumulation (Tích lũy) - giá ở đáy, volume giảm, sau đó tăng
    if price_position < 0.3 and short_ma < long_ma:
        # Kiểm tra volume pattern: volume thấp khi giá giảm, tăng khi giá tăng
        recent_volume_trend = np.mean(volumes[-5:]) / np.mean(volumes[-20:-5]) if len(volumes) >= 20 else 1
        if recent_volume_trend > 1.2:  # Volume đang tăng
            wyckoff_phase = 'ACCUMULATION'
            signal_strength = min(0.8, price_position * 2)  # Càng gần đáy càng mạnh
    
    # Giai đoạn 2: Markup (Tăng giá) - giá tăng với volume tăng
    elif price_position > 0.3 and short_ma > long_ma and volume_ratio > 1.1:
        wyckoff_phase = 'MARKUP'
        signal_strength = min(0.9, price_position)
    
    # Giai đoạn 3: Distribution (Phân phối) - giá ở đỉnh, volume giảm
    elif price_position > 0.7 and short_ma > long_ma:
        recent_volume_trend = np.mean(volumes[-5:]) / np.mean(volumes[-20:-5]) if len(volumes) >= 20 else 1
        if recent_volume_trend < 0.9:  # Volume đang giảm
            wyckoff_phase = 'DISTRIBUTION'
            signal_strength = min(0.8, (1 - price_position) * 2)
    
    # Giai đoạn 4: Markdown (Giảm giá) - giá giảm với volume tăng
    elif price_position < 0.7 and short_ma < long_ma and volume_ratio > 1.1:
        wyckoff_phase = 'MARKDOWN'
        signal_strength = min(0.9, 1 - price_position)
    
    return {
        'phase': wyckoff_phase,
        'strength': signal_strength,
        'price_position': price_position,
        'volume_ratio': volume_ratio
    }


def analyze_dow_theory(df):
    """
    Phân tích Lý thuyết Dow.
    
    Dow Theory xác định 3 loại xu hướng:
    1. Primary Trend (Xu hướng chính): Dài hạn (1-3 năm)
       - Sử dụng MA dài hạn (50-200 periods)
       - Xác định xu hướng chính của thị trường
    
    2. Secondary Trend (Xu hướng phụ): Trung hạn (3 tuần - 3 tháng)
       - Sử dụng MA trung hạn (20-50 periods)
       - Điều chỉnh trong xu hướng chính
    
    3. Minor Trend (Xu hướng nhỏ): Ngắn hạn (vài ngày - 3 tuần)
       - Sử dụng MA ngắn hạn (5-20 periods)
       - Biến động ngắn hạn
    
    Tín hiệu mạnh khi cả 3 xu hướng đồng thuận (trend alignment > 0.7).
    
    Args:
        df (pandas.DataFrame): DataFrame chứa ['close']
                               Cần ít nhất 100 nến để phân tích chính xác
    
    Returns:
        dict: Dictionary chứa:
            - 'primary_trend': Xu hướng chính ('BULLISH', 'BEARISH', 'NEUTRAL')
            - 'primary_strength': Độ mạnh xu hướng chính (0-1)
            - 'secondary_trend': Xu hướng phụ ('BULLISH', 'BEARISH', 'NEUTRAL')
            - 'secondary_strength': Độ mạnh xu hướng phụ (0-1)
            - 'minor_trend': Xu hướng nhỏ ('BULLISH', 'BEARISH', 'NEUTRAL')
            - 'minor_strength': Độ mạnh xu hướng nhỏ (0-1)
            - 'trend_alignment': Mức độ đồng thuận (0-1, 1=tất cả đồng thuận)
            None nếu không đủ dữ liệu
    """
    if df is None or len(df) < 100:
        return None
    
    prices = df['close'].values
    
    # Xu hướng chính: sử dụng MA dài hạn (50-200 periods)
    if len(prices) >= 50:
        ma_50 = np.mean(prices[-50:])
        ma_200 = np.mean(prices[-min(200, len(prices)):])
        primary_trend = 'BULLISH' if ma_50 > ma_200 else 'BEARISH'
        primary_strength = abs(ma_50 - ma_200) / ma_200 if ma_200 > 0 else 0
    else:
        primary_trend = 'NEUTRAL'
        primary_strength = 0
    
    # Xu hướng phụ: sử dụng MA trung hạn (20-50 periods)
    if len(prices) >= 20:
        ma_20 = np.mean(prices[-20:])
        ma_50 = np.mean(prices[-min(50, len(prices)):])
        secondary_trend = 'BULLISH' if ma_20 > ma_50 else 'BEARISH'
        secondary_strength = abs(ma_20 - ma_50) / ma_50 if ma_50 > 0 else 0
    else:
        secondary_trend = 'NEUTRAL'
        secondary_strength = 0
    
    # Xu hướng nhỏ: sử dụng MA ngắn hạn (5-20 periods)
    if len(prices) >= 5:
        ma_5 = np.mean(prices[-5:])
        ma_20 = np.mean(prices[-min(20, len(prices)):])
        minor_trend = 'BULLISH' if ma_5 > ma_20 else 'BEARISH'
        minor_strength = abs(ma_5 - ma_20) / ma_20 if ma_20 > 0 else 0
    else:
        minor_trend = 'NEUTRAL'
        minor_strength = 0
    
    # Xác định tính nhất quán của xu hướng
    trend_alignment = 0
    if primary_trend == secondary_trend == minor_trend:
        trend_alignment = 1.0  # Tất cả đồng thuận
    elif primary_trend == secondary_trend:
        trend_alignment = 0.7  # Chính và phụ đồng thuận
    elif secondary_trend == minor_trend:
        trend_alignment = 0.5  # Phụ và nhỏ đồng thuận
    
    return {
        'primary_trend': primary_trend,
        'primary_strength': primary_strength,
        'secondary_trend': secondary_trend,
        'secondary_strength': secondary_strength,
        'minor_trend': minor_trend,
        'minor_strength': minor_strength,
        'trend_alignment': trend_alignment
    }

