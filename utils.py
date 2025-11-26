"""
Các hàm tiện ích hỗ trợ cho bot.

Module này chứa các hàm:
- Gửi tin nhắn Telegram
- Lấy giá từ các API
- Lưu/đọc lịch sử thị trường
- Format thời gian và tin nhắn
"""

import requests
import time
import datetime
import csv
import os
from collections import defaultdict
import config

# Lưu trữ lịch sử giá
price_history = defaultdict(list)  # key: symbol, value: list of (timestamp, price)

# Lưu trữ các tín hiệu đã phát ra gần đây để tránh lặp lại
signal_history = {}  # key: signal_type, value: {'timestamp': ts, 'action': action, 'confidence': conf, 'value': value}


def send_telegram_message(text):
    """
    Gửi tin nhắn đến Telegram channel chính.
    
    Args:
        text (str): Nội dung tin nhắn (có thể dùng HTML)
    
    Returns:
        None
    """
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': config.TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    try:
        r = requests.post(url, data=payload)
        r.raise_for_status()
    except Exception as e:
        print(f"Error sending telegram message: {e}")


def send_signal_message(text):
    """
    Gửi tin nhắn tín hiệu long/short vào channel riêng.
    
    Args:
        text (str): Nội dung tin nhắn tín hiệu (có thể dùng HTML)
    
    Returns:
        None
    """
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': config.TELEGRAM_SIGNAL_CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    try:
        r = requests.post(url, data=payload)
        r.raise_for_status()
    except Exception as e:
        print(f"Error sending signal message: {e}")


def format_trading_signal(signal, btc_dom=None, usdt_dom=None, fear_index=None, technical_details=None):
    """
    Format tín hiệu long/short với thông tin đầy đủ bao gồm phân tích kỹ thuật.
    
    Args:
        signal (dict): Dictionary chứa thông tin tín hiệu với keys:
            - 'action': Hành động (LONG/SHORT)
            - 'confidence': Độ tin cậy ('high' hoặc 'medium')
            - 'reason': Lý do phát tín hiệu
        btc_dom (float, optional): BTC Dominance hiện tại
        usdt_dom (float, optional): USDT Dominance hiện tại
        fear_index (int, optional): Fear & Greed Index hiện tại
        technical_details (dict, optional): Chi tiết phân tích kỹ thuật
    
    Returns:
        str: Tin nhắn đã format với HTML
    """
    now_ts = int(time.time())
    time_str = datetime.datetime.now(config.TZ).strftime('%Y-%m-%d %H:%M:%S')
    
    confidence_emoji = "🟢" if signal['confidence'] == 'high' else "🟡"
    confidence_text = "CAO" if signal['confidence'] == 'high' else "TRUNG BÌNH"
    
    # Xác định emoji và màu sắc dựa trên action
    action_emoji = ""
    if 'LONG' in signal['action']:
        action_emoji = "📈"
    elif 'SHORT' in signal['action']:
        action_emoji = "📉"
    
    # Tạo message
    message = f"{action_emoji} <b>🎯 TÍN HIỆU GIAO DỊCH</b> {action_emoji}\n\n"
    message += f"<b>Hành động:</b> {signal['action']}\n"
    message += f"<b>Độ tin cậy:</b> {confidence_emoji} {confidence_text}\n"
    message += f"<b>Lý do:</b> {signal['reason']}\n\n"
    
    # Thêm thông tin chỉ số hiện tại
    if btc_dom is not None:
        message += f"📊 BTC Dominance: {btc_dom:.2f}%\n"
    if usdt_dom is not None:
        message += f"📊 USDT Dominance: {usdt_dom:.2f}%\n"
    if fear_index is not None:
        message += f"📊 Fear & Greed: {fear_index}\n"
    
    # Thêm thông tin phân tích kỹ thuật
    if technical_details:
        message += f"\n<b>📈 Phân tích kỹ thuật:</b>\n"
        tech_items = []
        
        if 'rsi' in technical_details:
            rsi_val = technical_details['rsi']
            rsi_status = "🟢 Quá bán" if rsi_val > 0.5 else "🔴 Quá mua" if rsi_val < -0.5 else "🟡 Trung tính"
            tech_items.append(f"RSI: {rsi_status}")
        
        if 'macd' in technical_details:
            macd_val = technical_details['macd']
            macd_status = "🟢 Bullish" if macd_val > 0.3 else "🔴 Bearish" if macd_val < -0.3 else "🟡 Neutral"
            tech_items.append(f"MACD: {macd_status}")
        
        if 'wyckoff' in technical_details:
            wyckoff_val = technical_details['wyckoff']
            if wyckoff_val > 0.3:
                tech_items.append(f"Wyckoff: 🟢 Tích lũy")
            elif wyckoff_val < -0.3:
                tech_items.append(f"Wyckoff: 🔴 Phân phối")
        
        if 'dow' in technical_details:
            dow_val = technical_details['dow']
            if dow_val > 0.3:
                tech_items.append(f"Dow Theory: 🟢 Bullish")
            elif dow_val < -0.3:
                tech_items.append(f"Dow Theory: 🔴 Bearish")
        
        if tech_items:
            message += " | ".join(tech_items) + "\n"
    
    message += f"\n⏱ {time_str}"
    
    return message


def get_price_binance(symbol):
    """
    Lấy giá hiện tại của coin từ Binance API.
    
    Args:
        symbol (str): Symbol coin trên Binance (ví dụ: 'BTCUSDT')
    
    Returns:
        float: Giá hiện tại hoặc None nếu có lỗi
    """
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        return float(data['price'])
    except Exception as e:
        print(f"Error getting price for {symbol}: {e}")
        return None


def get_klines_binance(symbol, interval='1h', limit=200):
    """
    Lấy dữ liệu kline (OHLCV) từ Binance để phân tích kỹ thuật.
    
    Args:
        symbol (str): Symbol coin trên Binance (ví dụ: 'BTCUSDT')
        interval (str): Khung thời gian ('1h', '4h', '1d', etc.)
        limit (int): Số lượng nến cần lấy
    
    Returns:
        pandas.DataFrame: DataFrame chứa ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                         hoặc None nếu có lỗi
    """
    import pandas as pd
    url = f"https://api.binance.com/api/v3/klines"
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        # Chuyển đổi sang DataFrame: [timestamp, open, high, low, close, volume]
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                         'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                                         'taker_buy_quote', 'ignore'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    except Exception as e:
        print(f"Error getting klines for {symbol}: {e}")
        return None


def get_xauusd_price():
    """
    Lấy giá vàng (XAU/USD) từ Yahoo Finance.
    
    Returns:
        float: Giá vàng hiện tại hoặc None nếu có lỗi
    """
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        price = data['chart']['result'][0]['meta']['regularMarketPrice']
        return float(price)
    except Exception as e:
        print(f"Error getting XAUUSD price from Yahoo: {e}")
        return None


def get_fear_and_greed():
    """
    Lấy Fear & Greed Index từ Alternative.me API.
    
    Returns:
        tuple: (value, classification, timestamp) hoặc (None, None, None) nếu có lỗi
    """
    try:
        r = requests.get(config.URL_FNG, timeout=10)
        r.raise_for_status()
        data = r.json()
        if 'data' in data and len(data['data']) > 0:
            fng = data['data'][0]
            return int(fng['value']), fng['value_classification'], fng['timestamp']
        else:
            return None, None, None
    except Exception as e:
        print(f"Error getting Fear & Greed Index: {e}")
        return None, None, None


def get_btc_dominance_and_total_marketcap(api_key, max_retries=3):
    """
    Lấy BTC Dominance và Total Market Cap từ CoinMarketCap API.
    
    Args:
        api_key (str): API key của CoinMarketCap
        max_retries (int): Số lần retry tối đa khi gặp lỗi 429
    
    Returns:
        tuple: (btc_dominance, total_market_cap) hoặc (None, None) nếu có lỗi
    """
    url = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
    headers = {'X-CMC_PRO_API_KEY': api_key, 'Accepts': 'application/json'}
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 429:
                wait_time = 2 ** attempt
                print(f"429 Too Many Requests. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            r.raise_for_status()
            data = r.json()
            btc_dom = float(data['data']['btc_dominance'])
            total_market_cap = float(data['data']['quote']['USD']['total_market_cap'])
            return btc_dom, total_market_cap
        except Exception as e:
            print(f"Error getting BTC dominance and total market cap: {e}")
            if attempt == max_retries - 1:
                return None, None
            time.sleep(2 ** attempt)
    return None, None


def get_usdt_market_cap(api_key, max_retries=3):
    """
    Lấy USDT Market Cap từ CoinMarketCap API.
    
    Args:
        api_key (str): API key của CoinMarketCap
        max_retries (int): Số lần retry tối đa khi gặp lỗi 429
    
    Returns:
        float: USDT Market Cap hoặc None nếu có lỗi
    """
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    parameters = {'symbol': 'USDT'}
    headers = {'X-CMC_PRO_API_KEY': api_key, 'Accepts': 'application/json'}
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=headers, params=parameters, timeout=10)
            if r.status_code == 429:
                wait_time = 2 ** attempt
                print(f"429 Too Many Requests (USDT market cap). Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            r.raise_for_status()
            data = r.json()
            return data['data']['USDT']['quote']['USD']['market_cap']
        except Exception as e:
            print(f"Error getting USDT market cap: {e}")
            if attempt == max_retries - 1:
                return None
            time.sleep(2 ** attempt)
    return None


def get_usdt_dominance(usdt_market_cap, total_market_cap):
    """
    Tính USDT Dominance từ USDT Market Cap và Total Market Cap.
    
    Args:
        usdt_market_cap (float): USDT Market Cap
        total_market_cap (float): Total Market Cap
    
    Returns:
        float: USDT Dominance (%) hoặc None nếu thiếu dữ liệu
    """
    if usdt_market_cap is not None and total_market_cap is not None:
        return (usdt_market_cap / total_market_cap) * 100
    else:
        return None


def format_time(ts):
    """
    Format timestamp thành chuỗi thời gian.
    
    Args:
        ts (int): Unix timestamp
    
    Returns:
        str: Chuỗi thời gian đã format hoặc "Unknown time" nếu có lỗi
    """
    try:
        dt = datetime.datetime.fromtimestamp(int(ts), config.TZ)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "Unknown time"


def save_market_history(ts, btc_dom, usdt_dom, fear_index):
    """
    Lưu lịch sử thị trường vào file CSV.
    
    Args:
        ts (int): Unix timestamp
        btc_dom (float): BTC Dominance
        usdt_dom (float): USDT Dominance
        fear_index (int): Fear & Greed Index
    
    Returns:
        None
    """
    file_exists = os.path.isfile(config.HISTORY_FILE)
    with open(config.HISTORY_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'btc_dom', 'usdt_dom', 'fear_index'])
        writer.writerow([ts, btc_dom, usdt_dom, fear_index])


def load_market_history(days=30):
    """
    Đọc lịch sử thị trường từ file CSV.
    
    Args:
        days (int): Số ngày lịch sử cần đọc (mặc định 30)
    
    Returns:
        list: Danh sách dictionary chứa lịch sử với keys:
              ['timestamp', 'btc_dom', 'usdt_dom', 'fear_index']
    """
    history = []
    if not os.path.isfile(config.HISTORY_FILE):
        return history
    now = int(time.time())
    cutoff = now - days * 86400
    with open(config.HISTORY_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = int(row['timestamp'])
            if ts >= cutoff:
                history.append({
                    'timestamp': ts,
                    'btc_dom': float(row['btc_dom']) if row['btc_dom'] else None,
                    'usdt_dom': float(row['usdt_dom']) if row['usdt_dom'] else None,
                    'fear_index': int(row['fear_index']) if row['fear_index'] else None
                })
    return history


def should_emit_signal(signal_type, action, confidence, current_value, now_ts):
    """
    Kiểm tra xem có nên phát tín hiệu hay không dựa trên:
    - Phát tín hiệu mới nếu chưa từng phát
    - Phát lại nếu tín hiệu đã hết hạn (sau SIGNAL_COOLDOWN)
    - Phát lại nếu tín hiệu đảo chiều (action khác)
    - Phát lại nếu giá trị thay đổi đáng kể (>SIGNAL_VALUE_THRESHOLD)
    - Phát lại nếu confidence tăng từ medium lên high
    
    Args:
        signal_type (str): Loại tín hiệu (ví dụ: 'BTC_DOM_SPIKE_UP')
        action (str): Hành động (ví dụ: 'LONG_BTC_SHORT_ALT')
        confidence (str): Độ tin cậy ('high' hoặc 'medium')
        current_value (float): Giá trị hiện tại của chỉ số
        now_ts (int): Unix timestamp hiện tại
    
    Returns:
        tuple: (should_emit (bool), reason (str))
               reason có thể là: 'new', 'reversal', 'value_change', 
                                 'confidence_upgrade', 'expired', 'cooldown'
    """
    global signal_history
    
    # Kiểm tra tín hiệu trước đó
    if signal_type in signal_history:
        last_signal = signal_history[signal_type]
        time_since_last = now_ts - last_signal['timestamp']
        
        # Nếu tín hiệu đảo chiều (action khác) -> phát ngay
        if last_signal['action'] != action:
            signal_history[signal_type] = {
                'timestamp': now_ts,
                'action': action,
                'confidence': confidence,
                'value': current_value
            }
            return True, 'reversal'
        
        # Nếu tín hiệu chưa hết hạn và cùng action -> kiểm tra thay đổi giá trị
        if time_since_last < config.SIGNAL_COOLDOWN:
            # Kiểm tra thay đổi giá trị đáng kể
            if last_signal['value'] is not None and current_value is not None:
                value_change = abs(current_value - last_signal['value']) / abs(last_signal['value']) if last_signal['value'] != 0 else 0
                # Nếu giá trị thay đổi > threshold -> phát lại
                if value_change > config.SIGNAL_VALUE_THRESHOLD:
                    signal_history[signal_type] = {
                        'timestamp': now_ts,
                        'action': action,
                        'confidence': confidence,
                        'value': current_value
                    }
                    return True, 'value_change'
            
            # Nếu confidence tăng từ medium lên high -> phát lại
            if last_signal['confidence'] == 'medium' and confidence == 'high':
                signal_history[signal_type] = {
                    'timestamp': now_ts,
                    'action': action,
                    'confidence': confidence,
                    'value': current_value
                }
                return True, 'confidence_upgrade'
            
            # Không phát lại nếu tín hiệu vẫn còn hiệu lực và không có thay đổi đáng kể
            return False, 'cooldown'
        
        # Tín hiệu đã hết hạn -> phát lại
        signal_history[signal_type] = {
            'timestamp': now_ts,
            'action': action,
            'confidence': confidence,
            'value': current_value
        }
        return True, 'expired'
    
    # Tín hiệu mới -> phát ngay
    signal_history[signal_type] = {
        'timestamp': now_ts,
        'action': action,
        'confidence': confidence,
        'value': current_value
    }
    return True, 'new'


def get_24h_change_binance(symbol):
    """
    Lấy thay đổi giá 24h của coin từ Binance API.
    
    Args:
        symbol (str): Symbol coin trên Binance (ví dụ: 'BTCUSDT')
    
    Returns:
        float: Thay đổi giá 24h (%) hoặc None nếu có lỗi
    """
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        return float(data['priceChangePercent'])
    except Exception as e:
        print(f"Error getting 24h change for {symbol}: {e}")
        return None


def detect_price_spike(symbol):
    """
    Phát hiện biến động giá mạnh trong 5 phút gần nhất.
    
    Args:
        symbol (str): Symbol coin trên Binance (ví dụ: 'BTCUSDT')
    
    Returns:
        str: Tin nhắn cảnh báo hoặc None nếu không có biến động lớn
    """
    history = price_history[symbol][-6:]
    if len(history) < 6:
        return None
    prices = [p[1] for p in history]
    change = (prices[-1] - prices[0]) / prices[0] * 100
    if abs(change) >= 3:
        if change > 0:
            return f"🚀 <b>{config.COINS[symbol]} GIÁ TĂNG MẠNH:</b> +{change:.3f}% trong 5 phút! Hãy chú ý cơ hội."
        else:
            return f"⚠️ <b>{config.COINS[symbol]} GIÁ GIẢM MẠNH:</b> {change:.3f}% trong 5 phút! Cẩn trọng biến động."
    return None

