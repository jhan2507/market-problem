"""
Phân tích thị trường và phát hiện tín hiệu giao dịch.

Module này chứa các hàm phân tích thị trường nâng cao:
- Phân tích đa khung thời gian (1h, 4h, 1d, 3d, 1w, 1M)
- Phát hiện xu hướng và momentum
- Multi-confirmation từ nhiều chỉ báo
- Phát hiện tín hiệu long/short
"""

import time
import numpy as np
import config
import utils
from indicators import calculate_technical_score


def calculate_stats(key, arr):
    """
    Tính toán thống kê nâng cao: trung bình, độ lệch chuẩn, min, max, momentum, trend strength.
    
    Args:
        key (str): Key trong dictionary (ví dụ: 'btc_dom', 'usdt_dom', 'fear_index')
        arr (list): Danh sách dictionary chứa lịch sử thị trường
    
    Returns:
        dict: Dictionary chứa các thống kê:
            - 'mean': Giá trị trung bình
            - 'std': Độ lệch chuẩn
            - 'min': Giá trị nhỏ nhất
            - 'max': Giá trị lớn nhất
            - 'momentum': Momentum (xu hướng)
            - 'recent_momentum': Momentum gần đây
            - 'trend': Xu hướng ('up', 'down', 'neutral')
            - 'trend_strength': Độ mạnh xu hướng (0-1)
            - 'current': Giá trị hiện tại
            - 'values': Mảng giá trị
            - 'count': Số lượng điểm dữ liệu
            None nếu không đủ dữ liệu
    """
    vals = [h[key] for h in arr if h[key] is not None]
    if not vals or len(vals) < 3:  # Cần ít nhất 3 điểm để tính toán đáng tin cậy
        return None
    vals_array = np.array(vals)
    mean = np.mean(vals_array)
    std = np.std(vals_array)
    min_val = np.min(vals_array)
    max_val = np.max(vals_array)
    
    # Momentum cải tiến: sử dụng linear regression để tính slope chính xác hơn
    if len(vals) >= 3:
        # Tính momentum bằng cách so sánh nửa đầu và nửa sau
        mid = len(vals) // 2
        first_half_mean = np.mean(vals_array[:mid])
        second_half_mean = np.mean(vals_array[mid:])
        momentum = (second_half_mean - first_half_mean) / len(vals) if len(vals) > 0 else 0
        
        # Tính momentum gần đây (2/3 cuối so với 1/3 đầu)
        recent_start = len(vals) // 3
        recent_mean = np.mean(vals_array[recent_start:])
        early_mean = np.mean(vals_array[:recent_start])
        recent_momentum = (recent_mean - early_mean) / len(vals) if len(vals) > 0 else 0
        
        # Trend strength: tỷ lệ điểm tăng/giảm
        increases = sum(1 for i in range(1, len(vals)) if vals[i] > vals[i-1])
        trend_strength = increases / (len(vals) - 1) if len(vals) > 1 else 0.5
    else:
        momentum = 0
        recent_momentum = 0
        trend_strength = 0.5
    
    # Xu hướng: xác định dựa trên momentum và trend strength
    if momentum > std * 0.1 and trend_strength > 0.6:
        trend = 'up'
    elif momentum < -std * 0.1 and trend_strength < 0.4:
        trend = 'down'
    else:
        trend = 'neutral'
    
    return {
        'mean': mean,
        'std': std,
        'min': min_val,
        'max': max_val,
        'momentum': momentum,
        'recent_momentum': recent_momentum,
        'trend': trend,
        'trend_strength': trend_strength,
        'current': vals[-1] if vals else None,
        'values': vals,
        'count': len(vals)
    }


def detect_anomaly(current, stats, threshold_std=2.5):
    """
    Phát hiện giá trị bất thường với ngưỡng cao hơn để giảm tín hiệu giả.
    
    Args:
        current (float): Giá trị hiện tại
        stats (dict): Dictionary thống kê từ calculate_stats
        threshold_std (float): Ngưỡng độ lệch chuẩn (mặc định 2.5)
    
    Returns:
        tuple: (severity, z_score)
               - severity: 'high', 'medium', 'low' hoặc None
               - z_score: Z-score của giá trị hiện tại
    """
    if stats is None or stats['std'] == 0:
        return None, 0
    z_score = (current - stats['mean']) / stats['std'] if stats['std'] > 0 else 0
    # Tăng ngưỡng: high >= 2.5 std, medium >= 2.0 std (thay vì 2.0 và 1.4)
    severity = 'high' if abs(z_score) >= threshold_std else 'medium' if abs(z_score) >= threshold_std * 0.8 else 'low'
    return severity, z_score


def check_trend_consistency(stats_list):
    """
    Kiểm tra tính nhất quán của xu hướng qua nhiều khung thời gian.
    
    Args:
        stats_list (list): Danh sách stats từ nhiều khung thời gian
    
    Returns:
        tuple: (is_consistent, consistency_ratio)
               - is_consistent: True nếu xu hướng nhất quán (>=60% đồng thuận)
               - consistency_ratio: Tỷ lệ đồng thuận (0-1)
    """
    if not stats_list or len(stats_list) < 2:
        return False, 0
    
    trends = [s['trend'] for s in stats_list if s is not None]
    if len(trends) < 2:
        return False, 0
    
    # Đếm số khung thời gian có cùng xu hướng
    up_count = trends.count('up')
    down_count = trends.count('down')
    total = len(trends)
    
    # Cần ít nhất 60% khung thời gian đồng thuận
    consistency_ratio = max(up_count, down_count) / total if total > 0 else 0
    is_consistent = consistency_ratio >= 0.6
    
    dominant_trend = 'up' if up_count > down_count else 'down' if down_count > up_count else 'neutral'
    return is_consistent, consistency_ratio


def calculate_confirmation_score(btc_stats, usdt_stats, fear_stats, current_btc, current_usdt, current_fear, technical_score=None, technical_details=None):
    """
    Tính điểm xác nhận từ nhiều chỉ báo (multi-confirmation) bao gồm phân tích kỹ thuật.
    
    Hàm này kiểm tra sự đồng thuận của nhiều chỉ báo:
    - BTC Dominance
    - USDT Dominance
    - Fear & Greed Index
    - Technical Analysis (RSI, MACD, Wyckoff, Dow Theory)
    
    Args:
        btc_stats (dict): Stats của BTC Dominance
        usdt_stats (dict): Stats của USDT Dominance
        fear_stats (dict): Stats của Fear & Greed Index
        current_btc (float): BTC Dominance hiện tại
        current_usdt (float): USDT Dominance hiện tại
        current_fear (int): Fear & Greed Index hiện tại
        technical_score (float, optional): Technical score từ -1 đến +1
        technical_details (dict, optional): Chi tiết các chỉ báo kỹ thuật
    
    Returns:
        tuple: (score, confirmations)
               - score: Tổng điểm xác nhận
               - confirmations: Danh sách các xác nhận (ví dụ: ['BTC_DOM_UP', 'TECH_BULLISH'])
    """
    score = 0
    confirmations = []
    technical_confirmations = []
    
    # BTC Dominance confirmation
    if btc_stats:
        if current_btc > btc_stats['mean'] + btc_stats['std'] * 2.0:
            score += 1
            confirmations.append('BTC_DOM_UP')
        elif current_btc < btc_stats['mean'] - btc_stats['std'] * 2.0:
            score += 1
            confirmations.append('BTC_DOM_DOWN')
    
    # USDT Dominance confirmation
    if usdt_stats:
        if current_usdt > usdt_stats['mean'] + usdt_stats['std'] * 1.8:
            score += 1
            confirmations.append('USDT_DOM_UP')
        elif current_usdt < usdt_stats['mean'] - usdt_stats['std'] * 1.8:
            score += 1
            confirmations.append('USDT_DOM_DOWN')
    
    # Fear & Greed confirmation
    if fear_stats:
        if current_fear < fear_stats['mean'] - fear_stats['std'] * 2.0:
            score += 1
            confirmations.append('FEAR_HIGH')
        elif current_fear > fear_stats['mean'] + fear_stats['std'] * 2.0:
            score += 1
            confirmations.append('GREED_HIGH')
    
    # Technical Analysis confirmation (RSI, MACD, Bollinger, Wyckoff, Dow Theory)
    if technical_score is not None:
        # Technical score từ -1 (bearish) đến +1 (bullish)
        if technical_score > 0.3:  # Bullish signal
            score += 1
            technical_confirmations.append('TECH_BULLISH')
        elif technical_score < -0.3:  # Bearish signal
            score += 1
            technical_confirmations.append('TECH_BEARISH')
        
        # Chi tiết từng chỉ báo
        if technical_details:
            if 'rsi' in technical_details:
                rsi_val = technical_details['rsi']
                if rsi_val > 0.5:
                    technical_confirmations.append('RSI_BULLISH')
                elif rsi_val < -0.5:
                    technical_confirmations.append('RSI_BEARISH')
            
            if 'macd' in technical_details:
                macd_val = technical_details['macd']
                if macd_val > 0.5:
                    technical_confirmations.append('MACD_BULLISH')
                elif macd_val < -0.5:
                    technical_confirmations.append('MACD_BEARISH')
            
            if 'wyckoff' in technical_details:
                wyckoff_val = technical_details['wyckoff']
                if wyckoff_val > 0.3:
                    technical_confirmations.append('WYCKOFF_ACCUMULATION')
                elif wyckoff_val < -0.3:
                    technical_confirmations.append('WYCKOFF_DISTRIBUTION')
            
            if 'dow' in technical_details:
                dow_val = technical_details['dow']
                if dow_val > 0.3:
                    technical_confirmations.append('DOW_BULLISH')
                elif dow_val < -0.3:
                    technical_confirmations.append('DOW_BEARISH')
    
    all_confirmations = confirmations + technical_confirmations
    return score, all_confirmations


def detect_strong_market_move(btc_dom, usdt_dom, fear_index):
    """
    Phân tích thị trường nâng cao với:
    - Phân tích nhiều khung thời gian (1h, 4h, 1d, 3d, 1w, 1M)
    - Phát hiện xu hướng và momentum với xác nhận đa khung thời gian
    - Sử dụng độ lệch chuẩn với ngưỡng cao hơn để giảm tín hiệu giả
    - Multi-confirmation: cần nhiều chỉ báo đồng thuận
    - Bộ lọc nhiễu: kiểm tra tính nhất quán của xu hướng
    - Đưa ra gợi ý long/short với mức độ tin cậy cao hơn
    
    Args:
        btc_dom (float): BTC Dominance hiện tại
        usdt_dom (float): USDT Dominance hiện tại
        fear_index (int): Fear & Greed Index hiện tại
    
    Returns:
        tuple: (alerts, trading_signals)
               - alerts: Danh sách cảnh báo thông thường
               - trading_signals: Danh sách tín hiệu giao dịch long/short
    """
    now_ts = int(time.time())
    history = utils.load_market_history(days=14)  # Tăng lên 14 ngày để có dữ liệu tốt hơn
    if not history or len(history) < 20:  # Cần ít nhất 20 điểm dữ liệu
        return [], []
    
    alerts = []
    trading_signals = []
    
    # Lấy dữ liệu kline của BTC để phân tích kỹ thuật (Wyckoff, Dow Theory, Technical Indicators)
    btc_kline_4h = utils.get_klines_binance('BTCUSDT', interval='4h', limit=200)
    btc_kline_1d = utils.get_klines_binance('BTCUSDT', interval='1d', limit=200)
    
    # Tính technical score từ phân tích kỹ thuật
    technical_score_4h = None
    technical_details_4h = None
    technical_score_1d = None
    technical_details_1d = None
    
    if btc_kline_4h is not None:
        technical_score_4h, technical_details_4h = calculate_technical_score(btc_kline_4h, btc_dom)
    
    if btc_kline_1d is not None:
        technical_score_1d, technical_details_1d = calculate_technical_score(btc_kline_1d, btc_dom)
    
    # Sử dụng technical score từ khung 4h làm chính, 1d làm xác nhận
    primary_technical_score = technical_score_4h if technical_score_4h is not None else technical_score_1d
    primary_technical_details = technical_details_4h if technical_details_4h else technical_details_1d
    
    # Phân chia lịch sử theo khung thời gian (1h, 4h, 1d, 3d, 1w, 1M)
    history_1h = [h for h in history if h['timestamp'] >= now_ts - 1*3600]  # 1 giờ
    history_4h = [h for h in history if h['timestamp'] >= now_ts - 4*3600]  # 4 giờ
    history_1d = [h for h in history if h['timestamp'] >= now_ts - 24*3600]  # 1 ngày (24 giờ)
    history_3d = [h for h in history if h['timestamp'] >= now_ts - 3*86400]  # 3 ngày
    history_1w = [h for h in history if h['timestamp'] >= now_ts - 7*86400]  # 1 tuần (7 ngày)
    history_1M = [h for h in history if h['timestamp'] >= now_ts - 30*86400]  # 1 tháng (30 ngày)
    
    # === PHÂN TÍCH BTC DOMINANCE ===
    if btc_dom is not None:
        stats_1h = calculate_stats('btc_dom', history_1h)
        stats_4h = calculate_stats('btc_dom', history_4h)
        stats_1d = calculate_stats('btc_dom', history_1d)
        stats_3d = calculate_stats('btc_dom', history_3d)
        stats_1w = calculate_stats('btc_dom', history_1w)
        stats_1M = calculate_stats('btc_dom', history_1M)
        
        # Kiểm tra tính nhất quán xu hướng qua nhiều khung thời gian
        trend_stats = [s for s in [stats_4h, stats_1d, stats_3d, stats_1w] if s is not None]
        is_trend_consistent, consistency_ratio = check_trend_consistency(trend_stats)
        
        # Phát hiện biến động bất thường với ngưỡng cao hơn (2.0 std thay vì 1.5)
        if stats_3d:  # Sử dụng 3 ngày làm baseline
            severity, z_score = detect_anomaly(btc_dom, stats_3d, threshold_std=2.0)
            # Chỉ phát tín hiệu nếu severity là high HOẶC (medium VÀ xu hướng nhất quán)
            if severity == 'high' or (severity == 'medium' and is_trend_consistent and abs(z_score) >= 1.8):
                change_pct = ((btc_dom - stats_3d['mean']) / stats_3d['mean']) * 100
                trend_4h = stats_4h['trend'] if stats_4h else 'unknown'
                trend_1d = stats_1d['trend'] if stats_1d else 'unknown'
                
                # Kiểm tra momentum mạnh và nhất quán
                momentum_strong = False
                if stats_4h and stats_1d:
                    momentum_4h = abs(stats_4h['recent_momentum'])
                    momentum_1d = abs(stats_1d['recent_momentum'])
                    momentum_strong = (momentum_4h > stats_4h['std'] * 0.05 and 
                                      momentum_1d > stats_1d['std'] * 0.03 and
                                      stats_4h['trend'] == stats_1d['trend'])
                
                # Chỉ phát tín hiệu nếu có momentum mạnh hoặc z-score rất cao
                if abs(z_score) >= 2.5 or (abs(z_score) >= 2.0 and momentum_strong):
                    if btc_dom > stats_3d['mean'] + stats_3d['std'] * 2.0:
                        # Kiểm tra multi-confirmation (bao gồm phân tích kỹ thuật)
                        usdt_stats_3d = calculate_stats('usdt_dom', history_3d) if usdt_dom is not None else None
                        fear_stats_3d = calculate_stats('fear_index', history_3d) if fear_index is not None else None
                        confirmation_score, confirmations = calculate_confirmation_score(
                            stats_3d, usdt_stats_3d, fear_stats_3d, btc_dom, usdt_dom, fear_index,
                            primary_technical_score, primary_technical_details
                        )
                        
                        # Chỉ phát tín hiệu nếu có đủ điểm xác nhận
                        # Nếu có technical confirmation, yêu cầu thấp hơn
                        has_tech_confirmation = any('TECH' in c or 'RSI' in c or 'MACD' in c or 'WYCKOFF' in c or 'DOW' in c for c in confirmations)
                        min_required = config.MIN_CONFIRMATION_WITH_TECH if has_tech_confirmation else config.MIN_CONFIRMATION_SCORE
                        if confirmation_score >= min_required or abs(z_score) >= 2.8:
                            signal_type = 'BTC_DOM_SPIKE_UP'
                            action = 'LONG_BTC_SHORT_ALT'
                            # Confidence cao hơn nếu có nhiều xác nhận
                            if abs(z_score) >= 2.8 or confirmation_score >= 3:
                                confidence = 'high'
                            elif abs(z_score) >= 2.3 or confirmation_score >= 2:
                                confidence = 'high' if momentum_strong else 'medium'
                            else:
                                confidence = 'medium'
                            
                            should_emit, reason = utils.should_emit_signal(signal_type, action, confidence, btc_dom, now_ts)
                            
                            if should_emit:
                                signal_strength = "MẠNH" if confidence == 'high' else "TRUNG BÌNH"
                                reason_text = {
                                    'new': 'TÍN HIỆU MỚI',
                                    'reversal': 'ĐẢO CHIỀU XU HƯỚNG',
                                    'value_change': 'THAY ĐỔI GIÁ TRỊ ĐÁNG KỂ',
                                    'confidence_upgrade': 'TĂNG ĐỘ TIN CẬY',
                                    'expired': 'TÍN HIỆU HẾT HẠN'
                                }.get(reason, '')
                                
                                consistency_text = f" | Nhất quán: {consistency_ratio:.0%}" if is_trend_consistent else ""
                                max_confirmations = 4  # BTC_DOM + USDT_DOM + FEAR + Technical
                                confirmation_text = f" | Xác nhận: {confirmation_score}/{max_confirmations}" if confirmations else ""
                                
                                alerts.append(
                                    f"🚨 <b>BTC Dominance TĂNG ĐỘT BIẾN</b> ({signal_strength}) [{reason_text}]\n"
                                    f"📊 Giá trị: {btc_dom:.2f}% (+{change_pct:.2f}% so TB 3d) | Z-score: {z_score:.2f}{consistency_text}{confirmation_text}\n"
                                    f"📈 Xu hướng 4h: {trend_4h.upper()} | 1d: {trend_1d.upper()}\n"
                                    f"💡 <b>GỢI Ý:</b> LONG BTC, SHORT Altcoin (tránh altcoin nhỏ)"
                                )
                                trading_signals.append({
                                    'type': signal_type,
                                    'action': action,
                                    'confidence': confidence,
                                    'reason': f'BTC dominance tăng {change_pct:.2f}% so với trung bình (Z-score: {z_score:.2f}, Xác nhận: {confirmation_score})'
                                })
                    elif btc_dom < stats_3d['mean'] - stats_3d['std'] * 2.0:
                        # Kiểm tra multi-confirmation (bao gồm phân tích kỹ thuật)
                        usdt_stats_3d = calculate_stats('usdt_dom', history_3d) if usdt_dom is not None else None
                        fear_stats_3d = calculate_stats('fear_index', history_3d) if fear_index is not None else None
                        confirmation_score, confirmations = calculate_confirmation_score(
                            stats_3d, usdt_stats_3d, fear_stats_3d, btc_dom, usdt_dom, fear_index,
                            primary_technical_score, primary_technical_details
                        )
                        
                        # Chỉ phát tín hiệu nếu có đủ điểm xác nhận
                        # Nếu có technical confirmation, yêu cầu thấp hơn
                        has_tech_confirmation = any('TECH' in c or 'RSI' in c or 'MACD' in c or 'WYCKOFF' in c or 'DOW' in c for c in confirmations)
                        min_required = config.MIN_CONFIRMATION_WITH_TECH if has_tech_confirmation else config.MIN_CONFIRMATION_SCORE
                        if confirmation_score >= min_required or abs(z_score) >= 2.8:
                            signal_type = 'BTC_DOM_SPIKE_DOWN'
                            action = 'SHORT_BTC_LONG_ALT'
                            # Confidence cao hơn nếu có nhiều xác nhận
                            if abs(z_score) >= 2.8 or confirmation_score >= 3:
                                confidence = 'high'
                            elif abs(z_score) >= 2.3 or confirmation_score >= 2:
                                confidence = 'high' if momentum_strong else 'medium'
                            else:
                                confidence = 'medium'
                            
                            should_emit, reason = utils.should_emit_signal(signal_type, action, confidence, btc_dom, now_ts)
                            
                            if should_emit:
                                signal_strength = "MẠNH" if confidence == 'high' else "TRUNG BÌNH"
                                reason_text = {
                                    'new': 'TÍN HIỆU MỚI',
                                    'reversal': 'ĐẢO CHIỀU XU HƯỚNG',
                                    'value_change': 'THAY ĐỔI GIÁ TRỊ ĐÁNG KỂ',
                                    'confidence_upgrade': 'TĂNG ĐỘ TIN CẬY',
                                    'expired': 'TÍN HIỆU HẾT HẠN'
                                }.get(reason, '')
                                
                                consistency_text = f" | Nhất quán: {consistency_ratio:.0%}" if is_trend_consistent else ""
                                max_confirmations = 4  # BTC_DOM + USDT_DOM + FEAR + Technical
                                confirmation_text = f" | Xác nhận: {confirmation_score}/{max_confirmations}" if confirmations else ""
                                
                                alerts.append(
                                    f"🚀 <b>BTC Dominance GIẢM MẠNH</b> ({signal_strength}) [{reason_text}]\n"
                                    f"📊 Giá trị: {btc_dom:.2f}% ({change_pct:.2f}% so TB 3d) | Z-score: {z_score:.2f}{consistency_text}{confirmation_text}\n"
                                    f"📈 Xu hướng 4h: {trend_4h.upper()} | 1d: {trend_1d.upper()}\n"
                                    f"💡 <b>GỢI Ý:</b> SHORT BTC, LONG Altcoin top (ETH, SOL, LINK)"
                                )
                                trading_signals.append({
                                    'type': signal_type,
                                    'action': action,
                                    'confidence': confidence,
                                    'reason': f'BTC dominance giảm {abs(change_pct):.2f}% so với trung bình (Z-score: {z_score:.2f}, Xác nhận: {confirmation_score})',
                                    'technical_details': primary_technical_details
                                })
        
        # Phân tích xu hướng và momentum
        if stats_4h and stats_1d:
            momentum_4h = stats_4h['momentum']
            momentum_1d = stats_1d['momentum']
            
            # Phát hiện đảo chiều xu hướng
            if stats_4h['trend'] != stats_1d['trend']:
                if stats_4h['trend'] == 'up' and stats_1d['trend'] == 'down':
                    alerts.append(
                        f"🔄 <b>BTC Dominance ĐẢO CHIỀU TĂNG</b>\n"
                        f"📊 Giá trị: {btc_dom:.2f}%\n"
                        f"📈 Momentum 4h: {momentum_4h*100:.3f}% | 1d: {momentum_1d*100:.3f}%\n"
                        f"💡 <b>GỢI Ý:</b> Cân nhắc LONG BTC, giảm tỷ trọng altcoin"
                    )
                elif stats_4h['trend'] == 'down' and stats_1d['trend'] == 'up':
                    alerts.append(
                        f"🔄 <b>BTC Dominance ĐẢO CHIỀU GIẢM</b>\n"
                        f"📊 Giá trị: {btc_dom:.2f}%\n"
                        f"📈 Momentum 4h: {momentum_4h*100:.3f}% | 1d: {momentum_1d*100:.3f}%\n"
                        f"💡 <b>GỢI Ý:</b> Cân nhắc SHORT BTC, tăng tỷ trọng altcoin top"
                    )
    
    # === PHÂN TÍCH USDT DOMINANCE ===
    if usdt_dom is not None:
        stats_1h = calculate_stats('usdt_dom', history_1h)
        stats_4h = calculate_stats('usdt_dom', history_4h)
        stats_1d = calculate_stats('usdt_dom', history_1d)
        stats_3d = calculate_stats('usdt_dom', history_3d)
        stats_1w = calculate_stats('usdt_dom', history_1w)
        stats_1M = calculate_stats('usdt_dom', history_1M)
        
        # Kiểm tra tính nhất quán xu hướng
        trend_stats = [s for s in [stats_4h, stats_1d, stats_3d, stats_1w] if s is not None]
        is_trend_consistent, consistency_ratio = check_trend_consistency(trend_stats)
        
        if stats_3d:
            severity, z_score = detect_anomaly(usdt_dom, stats_3d, threshold_std=1.8)
            if severity == 'high' or (severity == 'medium' and is_trend_consistent and abs(z_score) >= 1.6):
                change_pct = ((usdt_dom - stats_3d['mean']) / stats_3d['mean']) * 100
                trend_4h = stats_4h['trend'] if stats_4h else 'unknown'
                
                # Kiểm tra momentum mạnh
                momentum_strong = False
                if stats_4h and stats_1d:
                    momentum_4h = abs(stats_4h['recent_momentum'])
                    momentum_1d = abs(stats_1d['recent_momentum'])
                    momentum_strong = (momentum_4h > stats_4h['std'] * 0.05 and 
                                      momentum_1d > stats_1d['std'] * 0.03 and
                                      stats_4h['trend'] == stats_1d['trend'])
                
                if abs(z_score) >= 2.2 or (abs(z_score) >= 1.8 and momentum_strong):
                    if usdt_dom > stats_3d['mean'] + stats_3d['std'] * 1.8:
                        btc_stats_3d = calculate_stats('btc_dom', history_3d) if btc_dom is not None else None
                        fear_stats_3d = calculate_stats('fear_index', history_3d) if fear_index is not None else None
                        confirmation_score, confirmations = calculate_confirmation_score(
                            btc_stats_3d, stats_3d, fear_stats_3d, btc_dom, usdt_dom, fear_index
                        )
                        
                        if confirmation_score >= config.MIN_CONFIRMATION_SCORE or abs(z_score) >= 2.2:
                            signal_type = 'USDT_DOM_SPIKE_UP'
                            action = 'SHORT_MARKET'
                            if abs(z_score) >= 2.2 or confirmation_score >= 3:
                                confidence = 'high'
                            elif abs(z_score) >= 1.9 or confirmation_score >= 2:
                                confidence = 'high' if momentum_strong else 'medium'
                            else:
                                confidence = 'medium'
                            
                            should_emit, reason = utils.should_emit_signal(signal_type, action, confidence, usdt_dom, now_ts)
                            
                            if should_emit:
                                signal_strength = "MẠNH" if confidence == 'high' else "TRUNG BÌNH"
                                reason_text = {
                                    'new': 'TÍN HIỆU MỚI',
                                    'reversal': 'ĐẢO CHIỀU XU HƯỚNG',
                                    'value_change': 'THAY ĐỔI GIÁ TRỊ ĐÁNG KỂ',
                                    'confidence_upgrade': 'TĂNG ĐỘ TIN CẬY',
                                    'expired': 'TÍN HIỆU HẾT HẠN'
                                }.get(reason, '')
                                
                                consistency_text = f" | Nhất quán: {consistency_ratio:.0%}" if is_trend_consistent else ""
                                max_confirmations = 4
                                confirmation_text = f" | Xác nhận: {confirmation_score}/{max_confirmations}" if confirmations else ""
                                
                                alerts.append(
                                    f"⚠️ <b>USDT Dominance TĂNG MẠNH</b> ({signal_strength}) [{reason_text}]\n"
                                    f"📊 Giá trị: {usdt_dom:.2f}% (+{change_pct:.2f}% so TB 3d) | Z-score: {z_score:.2f}{consistency_text}{confirmation_text}\n"
                                    f"📈 Xu hướng 4h: {trend_4h.upper()}\n"
                                    f"💡 <b>GỢI Ý:</b> SHORT toàn thị trường, tăng tỷ trọng stablecoin - Thị trường có thể điều chỉnh!"
                                )
                                trading_signals.append({
                                    'type': signal_type,
                                    'action': action,
                                    'confidence': confidence,
                                    'reason': f'USDT dominance tăng {change_pct:.2f}% - dấu hiệu rút vốn (Z-score: {z_score:.2f}, Xác nhận: {confirmation_score})'
                                })
                    elif usdt_dom < stats_3d['mean'] - stats_3d['std'] * 1.8:
                        btc_stats_3d = calculate_stats('btc_dom', history_3d) if btc_dom is not None else None
                        fear_stats_3d = calculate_stats('fear_index', history_3d) if fear_index is not None else None
                        confirmation_score, confirmations = calculate_confirmation_score(
                            btc_stats_3d, stats_3d, fear_stats_3d, btc_dom, usdt_dom, fear_index
                        )
                        
                        if confirmation_score >= config.MIN_CONFIRMATION_SCORE or abs(z_score) >= 2.2:
                            signal_type = 'USDT_DOM_SPIKE_DOWN'
                            action = 'LONG_MARKET'
                            if abs(z_score) >= 2.2 or confirmation_score >= 3:
                                confidence = 'high'
                            elif abs(z_score) >= 1.9 or confirmation_score >= 2:
                                confidence = 'high' if momentum_strong else 'medium'
                            else:
                                confidence = 'medium'
                            
                            should_emit, reason = utils.should_emit_signal(signal_type, action, confidence, usdt_dom, now_ts)
                            
                            if should_emit:
                                signal_strength = "MẠNH" if confidence == 'high' else "TRUNG BÌNH"
                                reason_text = {
                                    'new': 'TÍN HIỆU MỚI',
                                    'reversal': 'ĐẢO CHIỀU XU HƯỚNG',
                                    'value_change': 'THAY ĐỔI GIÁ TRỊ ĐÁNG KỂ',
                                    'confidence_upgrade': 'TĂNG ĐỘ TIN CẬY',
                                    'expired': 'TÍN HIỆU HẾT HẠN'
                                }.get(reason, '')
                                
                                consistency_text = f" | Nhất quán: {consistency_ratio:.0%}" if is_trend_consistent else ""
                                max_confirmations = 4
                                confirmation_text = f" | Xác nhận: {confirmation_score}/{max_confirmations}" if confirmations else ""
                                
                                alerts.append(
                                    f"🚀 <b>USDT Dominance GIẢM MẠNH</b> ({signal_strength}) [{reason_text}]\n"
                                    f"📊 Giá trị: {usdt_dom:.2f}% ({change_pct:.2f}% so TB 3d) | Z-score: {z_score:.2f}{consistency_text}{confirmation_text}\n"
                                    f"📈 Xu hướng 4h: {trend_4h.upper()}\n"
                                    f"💡 <b>GỢI Ý:</b> LONG toàn thị trường - Vốn đang chảy vào thị trường!"
                                )
                                trading_signals.append({
                                    'type': signal_type,
                                    'action': action,
                                    'confidence': confidence,
                                    'reason': f'USDT dominance giảm {abs(change_pct):.2f}% - dấu hiệu vốn vào (Z-score: {z_score:.2f}, Xác nhận: {confirmation_score})'
                                })
    
    # === PHÂN TÍCH FEAR & GREED INDEX ===
    if fear_index is not None:
        stats_1h = calculate_stats('fear_index', history_1h)
        stats_4h = calculate_stats('fear_index', history_4h)
        stats_1d = calculate_stats('fear_index', history_1d)
        stats_3d = calculate_stats('fear_index', history_3d)
        stats_1w = calculate_stats('fear_index', history_1w)
        stats_1M = calculate_stats('fear_index', history_1M)
        
        # Kiểm tra tính nhất quán xu hướng
        trend_stats = [s for s in [stats_4h, stats_1d, stats_3d, stats_1w] if s is not None]
        is_trend_consistent, consistency_ratio = check_trend_consistency(trend_stats)
        
        if stats_3d:
            severity, z_score = detect_anomaly(fear_index, stats_3d, threshold_std=2.0)
            if severity == 'high' or (severity == 'medium' and is_trend_consistent and abs(z_score) >= 1.8):
                change = fear_index - stats_3d['mean']
                trend_4h = stats_4h['trend'] if stats_4h else 'unknown'
                
                # Kiểm tra momentum mạnh
                momentum_strong = False
                if stats_4h and stats_1d:
                    momentum_4h = abs(stats_4h['recent_momentum'])
                    momentum_1d = abs(stats_1d['recent_momentum'])
                    momentum_strong = (momentum_4h > stats_4h['std'] * 0.05 and 
                                      momentum_1d > stats_1d['std'] * 0.03 and
                                      stats_4h['trend'] == stats_1d['trend'])
                
                if abs(z_score) >= 2.5 or (abs(z_score) >= 2.0 and momentum_strong):
                    if fear_index < stats_3d['mean'] - stats_3d['std'] * 2.0:
                        btc_stats_3d = calculate_stats('btc_dom', history_3d) if btc_dom is not None else None
                        usdt_stats_3d = calculate_stats('usdt_dom', history_3d) if usdt_dom is not None else None
                        confirmation_score, confirmations = calculate_confirmation_score(
                            btc_stats_3d, usdt_stats_3d, stats_3d, btc_dom, usdt_dom, fear_index
                        )
                        
                        if confirmation_score >= config.MIN_CONFIRMATION_SCORE or abs(z_score) >= 2.5:
                            signal_type = 'FEAR_SPIKE'
                            action = 'LONG_ACCUMULATE'
                            if abs(z_score) >= 2.5 or confirmation_score >= 3:
                                confidence = 'high'
                            elif abs(z_score) >= 2.2 or confirmation_score >= 2:
                                confidence = 'high' if momentum_strong else 'medium'
                            else:
                                confidence = 'medium'
                            
                            should_emit, reason = utils.should_emit_signal(signal_type, action, confidence, fear_index, now_ts)
                            
                            if should_emit:
                                signal_strength = "MẠNH" if confidence == 'high' else "TRUNG BÌNH"
                                reason_text = {
                                    'new': 'TÍN HIỆU MỚI',
                                    'reversal': 'ĐẢO CHIỀU XU HƯỚNG',
                                    'value_change': 'THAY ĐỔI GIÁ TRỊ ĐÁNG KỂ',
                                    'confidence_upgrade': 'TĂNG ĐỘ TIN CẬY',
                                    'expired': 'TÍN HIỆU HẾT HẠN'
                                }.get(reason, '')
                                
                                consistency_text = f" | Nhất quán: {consistency_ratio:.0%}" if is_trend_consistent else ""
                                max_confirmations = 4
                                confirmation_text = f" | Xác nhận: {confirmation_score}/{max_confirmations}" if confirmations else ""
                                
                                alerts.append(
                                    f"💡 <b>FEAR & GREED GIẢM MẠNH</b> ({signal_strength}) [{reason_text}]\n"
                                    f"📊 Giá trị: {fear_index} (giảm {abs(change):.1f} so TB 3d) | Z-score: {z_score:.2f}{consistency_text}{confirmation_text}\n"
                                    f"📈 Xu hướng 4h: {trend_4h.upper()}\n"
                                    f"💡 <b>GỢI Ý:</b> LONG dần từng phần - Cơ hội mua vào khi thị trường sợ hãi!"
                                )
                                trading_signals.append({
                                    'type': signal_type,
                                    'action': action,
                                    'confidence': confidence,
                                    'reason': f'Fear index giảm {abs(change):.1f} - tâm lý sợ hãi cực độ (Z-score: {z_score:.2f}, Xác nhận: {confirmation_score})'
                                })
                    elif fear_index > stats_3d['mean'] + stats_3d['std'] * 2.0:
                        btc_stats_3d = calculate_stats('btc_dom', history_3d) if btc_dom is not None else None
                        usdt_stats_3d = calculate_stats('usdt_dom', history_3d) if usdt_dom is not None else None
                        confirmation_score, confirmations = calculate_confirmation_score(
                            btc_stats_3d, usdt_stats_3d, stats_3d, btc_dom, usdt_dom, fear_index
                        )
                        
                        if confirmation_score >= config.MIN_CONFIRMATION_SCORE or abs(z_score) >= 2.5:
                            signal_type = 'GREED_SPIKE'
                            action = 'SHORT_OR_TAKE_PROFIT'
                            if abs(z_score) >= 2.5 or confirmation_score >= 3:
                                confidence = 'high'
                            elif abs(z_score) >= 2.2 or confirmation_score >= 2:
                                confidence = 'high' if momentum_strong else 'medium'
                            else:
                                confidence = 'medium'
                            
                            should_emit, reason = utils.should_emit_signal(signal_type, action, confidence, fear_index, now_ts)
                            
                            if should_emit:
                                signal_strength = "MẠNH" if confidence == 'high' else "TRUNG BÌNH"
                                reason_text = {
                                    'new': 'TÍN HIỆU MỚI',
                                    'reversal': 'ĐẢO CHIỀU XU HƯỚNG',
                                    'value_change': 'THAY ĐỔI GIÁ TRỊ ĐÁNG KỂ',
                                    'confidence_upgrade': 'TĂNG ĐỘ TIN CẬY',
                                    'expired': 'TÍN HIỆU HẾT HẠN'
                                }.get(reason, '')
                                
                                consistency_text = f" | Nhất quán: {consistency_ratio:.0%}" if is_trend_consistent else ""
                                max_confirmations = 4
                                confirmation_text = f" | Xác nhận: {confirmation_score}/{max_confirmations}" if confirmations else ""
                                
                                alerts.append(
                                    f"⚠️ <b>FEAR & GREED TĂNG MẠNH</b> ({signal_strength}) [{reason_text}]\n"
                                    f"📊 Giá trị: {fear_index} (tăng {change:.1f} so TB 3d) | Z-score: {z_score:.2f}{consistency_text}{confirmation_text}\n"
                                    f"📈 Xu hướng 4h: {trend_4h.upper()}\n"
                                    f"💡 <b>GỢI Ý:</b> SHORT hoặc chốt lời dần - Tâm lý tham lam cực độ, thận trọng!"
                                )
                                trading_signals.append({
                                    'type': signal_type,
                                    'action': action,
                                    'confidence': confidence,
                                    'reason': f'Greed index tăng {change:.1f} - tâm lý tham lam cực độ (Z-score: {z_score:.2f}, Xác nhận: {confirmation_score})'
                                })
    
    # === PHÂN TÍCH TỔNG HỢP VÀ TƯƠNG QUAN ===
    if btc_dom is not None and usdt_dom is not None and fear_index is not None:
        # Tính lại stats cho phân tích tổng hợp (sử dụng 3 ngày)
        btc_stats_3d = calculate_stats('btc_dom', history_3d)
        usdt_stats_3d = calculate_stats('usdt_dom', history_3d)
        fear_stats_3d = calculate_stats('fear_index', history_3d)
        
        # Tình huống đặc biệt: BTC dom tăng + USDT dom tăng = rút vốn mạnh
        if (btc_stats_3d and usdt_stats_3d and 
            btc_dom > btc_stats_3d['mean'] + btc_stats_3d['std'] * 1.2 and
            usdt_dom > usdt_stats_3d['mean'] + usdt_stats_3d['std'] * 1.2):
            signal_type = 'CAPITAL_OUTFLOW'
            action = 'SHORT_ALL'
            confidence = 'high'
            combined_value = btc_dom + usdt_dom
            should_emit, reason = utils.should_emit_signal(signal_type, action, confidence, combined_value, now_ts)
            
            if should_emit:
                reason_text = {
                    'new': 'TÍN HIỆU MỚI',
                    'reversal': 'ĐẢO CHIỀU XU HƯỚNG',
                    'value_change': 'THAY ĐỔI GIÁ TRỊ ĐÁNG KỂ',
                    'confidence_upgrade': 'TĂNG ĐỘ TIN CẬY',
                    'expired': 'TÍN HIỆU HẾT HẠN'
                }.get(reason, '')
                
                alerts.append(
                    f"🔴 <b>CẢNH BÁO: RÚT VỐN MẠNH</b> [{reason_text}]\n"
                    f"📊 BTC Dom: {btc_dom:.2f}% | USDT Dom: {usdt_dom:.2f}%\n"
                    f"💡 <b>GỢI Ý:</b> SHORT toàn thị trường, tăng tỷ trọng stablecoin - Thị trường điều chỉnh mạnh!"
                )
                trading_signals.append({
                    'type': signal_type,
                    'action': action,
                    'confidence': confidence,
                    'reason': 'Cả BTC và USDT dominance cùng tăng - dấu hiệu rút vốn'
                })
        
        # Tình huống tích cực: BTC dom giảm + USDT dom giảm + Fear thấp = cơ hội mua
        if (btc_stats_3d and usdt_stats_3d and fear_stats_3d and
            btc_dom < btc_stats_3d['mean'] - btc_stats_3d['std'] * 1.2 and
            usdt_dom < usdt_stats_3d['mean'] - usdt_stats_3d['std'] * 1.2 and
            fear_index < fear_stats_3d['mean'] - fear_stats_3d['std'] * 1.2):
            signal_type = 'BUYING_OPPORTUNITY'
            action = 'LONG_ALL'
            confidence = 'high'
            combined_value = btc_dom + usdt_dom + fear_index
            should_emit, reason = utils.should_emit_signal(signal_type, action, confidence, combined_value, now_ts)
            
            if should_emit:
                reason_text = {
                    'new': 'TÍN HIỆU MỚI',
                    'reversal': 'ĐẢO CHIỀU XU HƯỚNG',
                    'value_change': 'THAY ĐỔI GIÁ TRỊ ĐÁNG KỂ',
                    'confidence_upgrade': 'TĂNG ĐỘ TIN CẬY',
                    'expired': 'TÍN HIỆU HẾT HẠN'
                }.get(reason, '')
                
                alerts.append(
                    f"🟢 <b>CƠ HỘI MUA VÀO</b> [{reason_text}]\n"
                    f"📊 BTC Dom: {btc_dom:.2f}% ↓ | USDT Dom: {usdt_dom:.2f}% ↓ | Fear: {fear_index} ↓\n"
                    f"💡 <b>GỢI Ý:</b> LONG toàn thị trường, ưu tiên BTC và altcoin top - Vốn đang chảy vào!"
                )
                trading_signals.append({
                    'type': signal_type,
                    'action': action,
                    'confidence': confidence,
                    'reason': 'Cả 3 chỉ số đều tích cực - vốn vào thị trường'
                })
    
    return alerts, trading_signals


def analyze_market(btc_dom, usdt_dom, fear_index, fear_label):
    """
    Phân tích thị trường và đưa ra nhận định ngắn hạn, trung hạn, dài hạn.
    
    Args:
        btc_dom (float): BTC Dominance hiện tại
        usdt_dom (float): USDT Dominance hiện tại
        fear_index (int): Fear & Greed Index hiện tại
        fear_label (str): Nhãn của Fear & Greed Index
    
    Returns:
        str: Chuỗi nhận định thị trường
    """
    signals = []
    plans = []
    now = int(time.time())
    history = utils.load_market_history(days=30)
    short_term = [h for h in history if h['timestamp'] >= now - 2*86400]  # 2 ngày
    mid_term = [h for h in history if h['timestamp'] >= now - 14*86400]  # 2 tuần
    long_term = history  # 30 ngày
    
    def avg(key, arr):
        vals = [h[key] for h in arr if h[key] is not None]
        return sum(vals)/len(vals) if vals else None
    
    # Ngắn hạn
    signals.append(f"<b>Ngắn hạn:</b> BTC Dominance hiện tại {btc_dom:.2f}% | USDT Dominance {usdt_dom:.2f}% | Fear & Greed {fear_index} - {fear_label}")
    avg_btc_short = avg('btc_dom', short_term)
    avg_usdt_short = avg('usdt_dom', short_term)
    avg_fear_short = avg('fear_index', short_term)
    
    if btc_dom is not None and avg_btc_short is not None:
        if btc_dom > avg_btc_short + 1:
            plans.append("- Ưu tiên Long BTC, hạn chế altcoin.")
        elif btc_dom < avg_btc_short - 1:
            plans.append("- Có thể giải ngân vào altcoin top.")
    
    if usdt_dom is not None and avg_usdt_short is not None:
        if usdt_dom > avg_usdt_short + 0.5:
            plans.append("- Tăng tỷ trọng stablecoin, giảm coin.")
        elif usdt_dom < avg_usdt_short - 0.5:
            plans.append("- Có thể tăng tỷ trọng coin, giảm stablecoin.")
    
    if fear_index is not None and avg_fear_short is not None:
        if fear_index < avg_fear_short - 5:
            plans.append("- Tâm lý sợ hãi tăng, cân nhắc mua vào từng phần.")
        elif fear_index > avg_fear_short + 5:
            plans.append("- Tâm lý tham lam tăng, nên thận trọng, cân nhắc chốt lời.")
    
    if plans:
        signals.append("<b>Kế hoạch ngắn hạn:</b>\n" + "\n".join(plans))
    
    # Trung hạn
    plans_mid = []
    signals.append("\n<b>Trung hạn (2 tuần):</b>")
    avg_btc_mid = avg('btc_dom', mid_term)
    avg_usdt_mid = avg('usdt_dom', mid_term)
    avg_fear_mid = avg('fear_index', mid_term)
    
    if avg_btc_mid is not None:
        signals.append(f"BTC Dominance TB: {avg_btc_mid:.2f}%")
        if btc_dom > avg_btc_mid + 1:
            plans_mid.append("- Duy trì tỷ trọng BTC cao.")
        elif btc_dom < avg_btc_mid - 1:
            plans_mid.append("- Có thể tăng tỷ trọng altcoin.")
    
    if avg_usdt_mid is not None:
        signals.append(f"USDT Dominance TB: {avg_usdt_mid:.2f}%")
        if usdt_dom > avg_usdt_mid + 0.5:
            plans_mid.append("- Giữ nhiều stablecoin, hạn chế giải ngân mới.")
        elif usdt_dom < avg_usdt_mid - 0.5:
            plans_mid.append("- Có thể giải ngân thêm vào coin.")
    
    if avg_fear_mid is not None:
        signals.append(f"Fear & Greed TB: {avg_fear_mid:.1f}")
        if fear_index < avg_fear_mid - 5:
            plans_mid.append("- Tâm lý thị trường yếu, nên giải ngân từng phần.")
        elif fear_index > avg_fear_mid + 5:
            plans_mid.append("- Thị trường hưng phấn, nên thận trọng với lệnh mới.")
    
    if plans_mid:
        signals.append("<b>Kế hoạch trung hạn:</b>\n" + "\n".join(plans_mid))
    
    # Dài hạn
    plans_long = []
    signals.append("\n<b>Dài hạn (1 tháng):</b>")
    avg_btc_long = avg('btc_dom', long_term)
    avg_usdt_long = avg('usdt_dom', long_term)
    avg_fear_long = avg('fear_index', long_term)
    
    if avg_btc_long is not None:
        signals.append(f"BTC Dominance TB: {avg_btc_long:.2f}%")
        if btc_dom > avg_btc_long + 1:
            plans_long.append("- Duy trì tỷ trọng BTC cao trong danh mục.")
        elif btc_dom < avg_btc_long - 1:
            plans_long.append("- Có thể tích lũy thêm altcoin top.")
    
    if avg_usdt_long is not None:
        signals.append(f"USDT Dominance TB: {avg_usdt_long:.2f}%")
        if usdt_dom > avg_usdt_long + 0.5:
            plans_long.append("- Ưu tiên giữ stablecoin, hạn chế đầu tư mới.")
        elif usdt_dom < avg_usdt_long - 0.5:
            plans_long.append("- Có thể tăng tỷ trọng coin cho đầu tư dài hạn.")
    
    if avg_fear_long is not None:
        signals.append(f"Fear & Greed TB: {avg_fear_long:.1f}")
        if fear_index < avg_fear_long - 5:
            plans_long.append("- Tích lũy dần khi thị trường sợ hãi.")
        elif fear_index > avg_fear_long + 5:
            plans_long.append("- Chốt lời dần khi thị trường quá hưng phấn.")
    
    if plans_long:
        signals.append("<b>Kế hoạch dài hạn:</b>\n" + "\n".join(plans_long))
    
    return "\n".join(signals)

