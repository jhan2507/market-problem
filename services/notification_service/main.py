"""
Notification Service

Responsibilities:
- Receive "price_update_ready" and "signal_generated" events
- Send messages to correct Telegram channels:
  - Price → @ftlssignalzhan
  - Signals → @livingcoinpricechannel
- Handle retry, error logs, and rate limit protection
"""

import time
import threading
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional, List
from collections import deque

from shared.logger import setup_logger
from shared.database import get_database
from shared.events import subscribe_events
from shared.config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_PRICE_CHAT_ID, TELEGRAM_SIGNAL_CHAT_ID,
    EVENT_PRICE_UPDATE_READY, EVENT_SIGNAL_GENERATED,
    MAX_RETRIES, RETRY_DELAY, BINANCE_API_URL, CMC_API_KEY, COINS, TIMEFRAMES
)
from shared.theories import analyze_dow_theory, analyze_wyckoff, analyze_gann, calculate_ema, calculate_rsi, calculate_macd

logger = setup_logger("notification_service")


class NotificationService:
    """Service for sending notifications via Telegram."""
    
    def __init__(self):
        self.db = get_database()
        self.session = requests.Session()
        self.telegram_base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
        
        # Rate limiting: track message timestamps
        self.message_timestamps = deque(maxlen=30)  # Keep last 30 messages
        self.rate_limit_delay = 0.1  # 100ms between messages (Telegram limit: 30 msg/sec)
    
    def check_rate_limit(self):
        """Check and enforce rate limit."""
        now = time.time()
        # Remove timestamps older than 1 second
        while self.message_timestamps and now - self.message_timestamps[0] > 1.0:
            self.message_timestamps.popleft()
        
        # If we've sent 30 messages in the last second, wait
        if len(self.message_timestamps) >= 30:
            sleep_time = 1.0 - (now - self.message_timestamps[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def send_telegram_message(self, chat_id: str, text: str, 
                             retry_count: int = 0) -> bool:
        """
        Send message to Telegram with retry logic.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text (HTML format)
            retry_count: Current retry attempt
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.check_rate_limit()
        
        url = f"{self.telegram_base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            # Track message timestamp
            self.message_timestamps.append(time.time())
            
            return True
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                # Rate limited - wait and retry
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limited, waiting {retry_after} seconds")
                time.sleep(retry_after)
                if retry_count < MAX_RETRIES:
                    return self.send_telegram_message(chat_id, text, retry_count + 1)
            else:
                logger.error(f"HTTP error sending Telegram message: {e}")
                if retry_count < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * (retry_count + 1))
                    return self.send_telegram_message(chat_id, text, retry_count + 1)
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            if retry_count < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (retry_count + 1))
                return self.send_telegram_message(chat_id, text, retry_count + 1)
        
        return False
    
    def format_price_message(self, data: Dict) -> str:
        """Format price update message with header and timestamp."""
        prices = data.get("prices", {})
        timestamp = data.get("timestamp")
        
        # Format prices as BTC:xxx|ETH:xxx|...
        price_parts = []
        for symbol, price in prices.items():
            coin_name = symbol.replace("USDT", "")
            # Format price without $ and commas, keep 2 decimal places
            price_parts.append(f"{coin_name}:{price:.2f}")
        
        price_line = " | ".join(price_parts)
        
        # Format timestamp
        time_str = ""
        if timestamp:
            try:
                from datetime import datetime, timezone, timedelta
                if isinstance(timestamp, str):
                    # Parse ISO format
                    if timestamp.endswith('Z'):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = datetime.fromisoformat(timestamp)
                else:
                    dt = timestamp
                
                # Convert to Vietnam time (UTC+7)
                vn_tz = timezone(timedelta(hours=7))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dt_vn = dt.astimezone(vn_tz)
                
                # Format as Vietnamese time
                time_str = dt_vn.strftime('%H:%M:%S %d/%m/%Y')
            except Exception as e:
                logger.debug(f"Error formatting timestamp: {e}")
                time_str = ""
        
        lines = [
            f"Giá Coin cập nhật: {price_line}"
        ]
        
        if time_str:
            lines.append(f"Giờ cập nhật: {time_str}")
        
        return "\n".join(lines)
    
    def get_market_outlook_summary(self, asset_symbol: str) -> Dict:
        """Get overall market outlook and suggest LONG/SHORT bias."""
        from shared.config import COLLECTION_ANALYSIS
        analysis_collection = self.db[COLLECTION_ANALYSIS]
        
        try:
            # Get latest analysis from DB
            latest_analysis = analysis_collection.find_one(
                sort=[("timestamp", -1)]
            )
            
            # If no data in DB, fetch real-time data
            if not latest_analysis:
                logger.info(f"No analysis data in DB for {asset_symbol}, fetching real-time data...")
                latest_analysis = self.analyze_realtime_market_data()
                if not latest_analysis:
                    return {"outlook": "Không có dữ liệu", "bias": "NEUTRAL"}
            
            # Get symbol analyses
            symbol_analyses = latest_analysis.get("symbol_analyses", {}).get(asset_symbol, {})
            
            if not symbol_analyses:
                # Try to fetch real-time data for this specific symbol
                logger.info(f"No analysis data for {asset_symbol}, fetching real-time data...")
                realtime_analysis = self.analyze_realtime_market_data()
                if realtime_analysis:
                    symbol_analyses = realtime_analysis.get("symbol_analyses", {}).get(asset_symbol, {})
                
                if not symbol_analyses:
                    return {"outlook": "Không có dữ liệu", "bias": "NEUTRAL"}
            
            # Analyze timeframes: 15m, 45m (from 15m), 1h, 4h, 1d, 3d, 1w
            bullish_count = 0
            bearish_count = 0
            neutral_count = 0
            timeframe_trends = {}
            
            # Get 15m analysis
            analysis_15m = symbol_analyses.get("15m", {})
            if analysis_15m:
                dow_15m = analysis_15m.get("dow", {})
                trend_15m = dow_15m.get("trend", "neutral")
                timeframe_trends["15m"] = trend_15m
                if trend_15m == "bullish":
                    bullish_count += 1
                elif trend_15m == "bearish":
                    bearish_count += 1
                else:
                    neutral_count += 1
                
                # Use 15m trend as proxy for 45m (3 candles of 15m = 45m)
                timeframe_trends["45m"] = trend_15m
                if trend_15m == "bullish":
                    bullish_count += 1
                elif trend_15m == "bearish":
                    bearish_count += 1
                else:
                    neutral_count += 1
            
            # Other timeframes
            for tf in ["1h", "4h", "1d", "3d", "1w"]:
                if tf in symbol_analyses:
                    analysis = symbol_analyses[tf]
                    dow = analysis.get("dow", {})
                    trend = dow.get("trend", "neutral")
                    timeframe_trends[tf] = trend
                    
                    if trend == "bullish":
                        bullish_count += 1
                    elif trend == "bearish":
                        bearish_count += 1
                    else:
                        neutral_count += 1
            
            # Determine overall bias
            total_timeframes = len(timeframe_trends)
            if total_timeframes == 0:
                return {"outlook": "Không có dữ liệu", "bias": "NEUTRAL"}
            
            # Calculate trend strength
            bullish_ratio = bullish_count / total_timeframes
            bearish_ratio = bearish_count / total_timeframes
            
            # Generate outlook summary
            if bullish_ratio >= 0.6:
                bias = "LONG"
                outlook = "Xu hướng tăng mạnh"
                emoji = "🟢"
            elif bearish_ratio >= 0.6:
                bias = "SHORT"
                outlook = "Xu hướng giảm mạnh"
                emoji = "🔴"
            elif bullish_ratio > bearish_ratio:
                bias = "LONG"
                outlook = "Xu hướng tăng nhẹ"
                emoji = "🟡"
            elif bearish_ratio > bullish_ratio:
                bias = "SHORT"
                outlook = "Xu hướng giảm nhẹ"
                emoji = "🟡"
            else:
                bias = "NEUTRAL"
                outlook = "Thị trường đi ngang"
                emoji = "⚪"
            
            # Add timeframe summary (order: 15m, 45m, 1h, 4h, 1d, 3d, 1w)
            tf_summary = []
            for tf in ["15m", "45m", "1h", "4h", "1d", "3d", "1w"]:
                if tf in timeframe_trends:
                    trend = timeframe_trends[tf]
                    if trend == "bullish":
                        tf_summary.append(f"{tf}:🟢")
                    elif trend == "bearish":
                        tf_summary.append(f"{tf}:🔴")
                    else:
                        tf_summary.append(f"{tf}:⚪")
            
            outlook_detail = f"{outlook} ({', '.join(tf_summary)})"
            
            return {
                "outlook": outlook_detail,
                "bias": bias,
                "emoji": emoji,
                "bullish_count": bullish_count,
                "bearish_count": bearish_count,
                "total_timeframes": total_timeframes
            }
        except Exception as e:
            logger.error(f"Error getting market outlook: {e}")
            return {"outlook": "Lỗi phân tích", "bias": "NEUTRAL"}
    
    def format_signal_message(self, signal_data: Dict) -> str:
        """Format trading signal message."""
        # Get full signal from database
        from shared.config import COLLECTION_SIGNALS
        signals_collection = self.db[COLLECTION_SIGNALS]
        signal = signals_collection.find_one({"signal_id": signal_data.get("signal_id")})
        
        if not signal:
            return None
        
        asset = signal.get("asset", "").replace("USDT", "")
        signal_type = signal.get("type", "")
        score = signal.get("score", 0)
        confidence = signal.get("confidence", "")
        
        # Emoji based on type
        emoji = "📈" if signal_type == "LONG" else "📉"
        confidence_emoji = "🟢" if confidence == "HIGH" else "🟡"
        
        lines = [
            f"{emoji} <b>🎯 TÍN HIỆU GIAO DỊCH</b> {emoji}\n",
            f"<b>Asset:</b> {asset}",
            f"<b>Type:</b> {signal_type}",
            f"<b>Score:</b> {score}/100",
            f"<b>Confidence:</b> {confidence_emoji} {confidence}\n"
        ]
        
        # Entry range
        entry = signal.get("entry_range", {})
        if entry.get("min") and entry.get("max"):
            lines.append(f"<b>Entry Range:</b> ${entry['min']:,.2f} - ${entry['max']:,.2f}")
        
        # Take profit
        tp = signal.get("take_profit", [])
        if tp:
            lines.append(f"<b>Take Profit:</b> {', '.join([f'${p:,.2f}' for p in tp])}")
        
        # Stop loss
        sl = signal.get("stop_loss")
        if sl:
            lines.append(f"<b>Stop Loss:</b> ${sl:,.2f}\n")
        
        # Market Outlook Summary
        outlook_summary = self.get_market_outlook_summary(signal.get("asset", ""))
        if outlook_summary and outlook_summary.get("outlook"):
            bias = outlook_summary.get("bias", "NEUTRAL")
            bias_emoji = "📈" if bias == "LONG" else "📉" if bias == "SHORT" else "➡️"
            outlook_text = outlook_summary.get("outlook", "")
            outlook_emoji = outlook_summary.get("emoji", "⚪")
            
            lines.append(f"<b>📊 Nhận định thị trường:</b>")
            lines.append(f"{outlook_emoji} {outlook_text}")
            lines.append(f"<b>Gợi ý:</b> {bias_emoji} <b>{bias}</b>\n")
        
        # Reasons
        reasons = signal.get("reasons", {})
        if reasons:
            lines.append("<b>Lý do:</b>")
            for category, reason_list in reasons.items():
                if reason_list:
                    lines.append(f"• {category.upper()}: {', '.join(reason_list)}")
        
        # Timestamp
        timestamp = signal.get("timestamp")
        if timestamp:
            if isinstance(timestamp, str):
                timestamp_str = timestamp
            else:
                timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            lines.append(f"\n⏱ {timestamp_str}")
        
        return "\n".join(lines)
    
    def handle_price_update(self, event_name: str, data: Dict):
        """Handle price_update_ready event."""
        logger.info("Received price_update_ready event")
        
        message = self.format_price_message(data)
        if message:
            success = self.send_telegram_message(TELEGRAM_PRICE_CHAT_ID, message)
            if success:
                logger.info("Price update sent to Telegram")
            else:
                logger.error("Failed to send price update")
    
    def handle_signal_generated(self, event_name: str, data: Dict):
        """Handle signal_generated event."""
        logger.info(f"Received signal_generated event: {data.get('signal_id')}")
        
        message = self.format_signal_message(data)
        if message:
            success = self.send_telegram_message(TELEGRAM_SIGNAL_CHAT_ID, message)
            if success:
                logger.info(f"Signal sent to Telegram: {data.get('signal_id')}")
            else:
                logger.error(f"Failed to send signal: {data.get('signal_id')}")
    
    def fetch_realtime_candlesticks(self, symbol: str, interval: str, limit: int = 500) -> Optional[pd.DataFrame]:
        """Fetch candlestick data from Binance in real-time."""
        try:
            url = f"{BINANCE_API_URL}/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            logger.error(f"Error fetching candlesticks for {symbol} {interval}: {e}")
            return None
    
    def fetch_realtime_btc_dominance(self) -> Optional[float]:
        """Fetch BTC Dominance from CoinMarketCap in real-time."""
        if not CMC_API_KEY:
            logger.warning("CMC_API_KEY not set, skipping BTC dominance")
            return None
        
        try:
            url = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
            headers = {
                'X-CMC_PRO_API_KEY': CMC_API_KEY,
                'Accepts': 'application/json'
            }
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data['data']['btc_dominance'])
        except Exception as e:
            logger.error(f"Error fetching BTC dominance: {e}")
            return None
    
    def fetch_realtime_usdt_dominance(self) -> Optional[float]:
        """Fetch USDT Dominance from CoinMarketCap in real-time."""
        if not CMC_API_KEY:
            logger.warning("CMC_API_KEY not set, skipping USDT dominance")
            return None
        
        try:
            # Get USDT market cap
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            headers = {
                'X-CMC_PRO_API_KEY': CMC_API_KEY,
                'Accepts': 'application/json'
            }
            params = {'symbol': 'USDT'}
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            usdt_market_cap = float(data['data']['USDT']['quote']['USD']['market_cap'])
            
            # Get total market cap
            url_global = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
            response_global = self.session.get(url_global, headers=headers, timeout=10)
            response_global.raise_for_status()
            data_global = response_global.json()
            total_market_cap = float(data_global['data']['quote']['USD']['total_market_cap'])
            
            return (usdt_market_cap / total_market_cap) * 100
        except Exception as e:
            logger.error(f"Error fetching USDT dominance: {e}")
            return None
    
    def analyze_timeframe_realtime(self, df: pd.DataFrame, timeframe: str) -> Dict:
        """Analyze a single timeframe using real-time data."""
        if df is None or len(df) < 20:
            return {}
        
        prices = df['close'].values
        volumes = df['volume'].values
        
        # Dow Theory
        dow_analysis = analyze_dow_theory(df)
        
        # Wyckoff
        wyckoff_analysis = analyze_wyckoff(df)
        
        # Gann
        gann_analysis = analyze_gann(df)
        
        # Indicators
        ema20 = calculate_ema(prices, 20) if len(prices) >= 20 else None
        ema50 = calculate_ema(prices, 50) if len(prices) >= 50 else None
        ema200 = calculate_ema(prices, 200) if len(prices) >= 200 else None
        
        rsi = calculate_rsi(prices, 14)
        macd = calculate_macd(prices)
        
        # Volume analysis
        current_volume = volumes[-1] if len(volumes) > 0 else None
        avg_volume = float(pd.Series(volumes).mean()) if len(volumes) > 0 else None
        volume_spike = (current_volume / avg_volume) > 1.5 if (current_volume and avg_volume) else False
        
        return {
            "timeframe": timeframe,
            "dow": dow_analysis,
            "wyckoff": wyckoff_analysis,
            "gann": gann_analysis,
            "indicators": {
                "ema20": float(ema20) if ema20 else None,
                "ema50": float(ema50) if ema50 else None,
                "ema200": float(ema200) if ema200 else None,
                "rsi": rsi,
                "macd": macd,
                "volume_spike": volume_spike
            },
            "current_price": float(prices[-1]) if len(prices) > 0 else None
        }
    
    def analyze_realtime_market_data(self) -> Optional[Dict]:
        """Fetch and analyze real-time market data from Binance."""
        logger.info("Fetching real-time market data for analysis...")
        
        try:
            # Fetch candlesticks for all coins and timeframes
            symbol_analyses = {}
            
            # Timeframes needed for analysis (skip 1m, 8h)
            analysis_timeframes = [tf for tf in TIMEFRAMES if tf not in ["1m", "8h"]]
            
            for symbol in COINS:
                symbol_analyses[symbol] = {}
                
                for timeframe in analysis_timeframes:
                    # Map timeframe to Binance interval
                    interval_map = {
                        "15m": "15m",
                        "1h": "1h",
                        "4h": "4h",
                        "1d": "1d",
                        "3d": "3d",
                        "1w": "1w"
                    }
                    
                    binance_interval = interval_map.get(timeframe)
                    if not binance_interval:
                        continue
                    
                    # Fetch candlesticks
                    df = self.fetch_realtime_candlesticks(symbol, binance_interval, limit=500)
                    if df is not None and len(df) >= 20:
                        # Analyze timeframe
                        analysis = self.analyze_timeframe_realtime(df, timeframe)
                        if analysis:
                            symbol_analyses[symbol][timeframe] = analysis
                            logger.debug(f"Analyzed {symbol} {timeframe}")
            
            # Fetch dominance data
            btc_dom = self.fetch_realtime_btc_dominance()
            usdt_dom = self.fetch_realtime_usdt_dominance()
            
            # Analyze dominance
            dominance_analysis = {}
            if btc_dom is not None:
                dominance_analysis["btc_dominance"] = btc_dom
                # Simple interpretation
                if btc_dom > 55:
                    dominance_analysis["interpretation"] = {
                        "btc_dom": "rising_money_into_btc_alts_weaken"
                    }
                elif btc_dom < 45:
                    dominance_analysis["interpretation"] = {
                        "btc_dom": "falling_good_for_alts"
                    }
                else:
                    dominance_analysis["interpretation"] = {
                        "btc_dom": "stable"
                    }
            
            if usdt_dom is not None:
                dominance_analysis["usdt_dominance"] = usdt_dom
                if "interpretation" not in dominance_analysis:
                    dominance_analysis["interpretation"] = {}
                
                if usdt_dom > 8:
                    dominance_analysis["interpretation"]["usdt_dom"] = "rising_risk_off_shorts_favored"
                else:
                    dominance_analysis["interpretation"]["usdt_dom"] = "stable_or_falling"
            
            return {
                "symbol_analyses": symbol_analyses,
                "dominance_analysis": dominance_analysis,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Error analyzing real-time market data: {e}")
            return None
    
    def get_overall_market_outlook(self) -> Dict:
        """Get overall market outlook based on BTC.D, USDT.D and money flow trends."""
        from shared.config import COLLECTION_ANALYSIS
        analysis_collection = self.db[COLLECTION_ANALYSIS]
        
        try:
            # Get latest analysis from DB
            latest_analysis = analysis_collection.find_one(
                sort=[("timestamp", -1)]
            )
            
            # If no data in DB, fetch real-time data
            if not latest_analysis:
                logger.info("No analysis data in DB, fetching real-time data...")
                latest_analysis = self.analyze_realtime_market_data()
                if not latest_analysis:
                    return {"outlook": "Không có dữ liệu", "bias": "NEUTRAL", "reasons": [], "btc_dom": None, "usdt_dom": None}
            
            symbol_analyses = latest_analysis.get("symbol_analyses", {})
            dominance_analysis = latest_analysis.get("dominance_analysis", {})
            
            # Get dominance values
            btc_dom = dominance_analysis.get("btc_dominance")
            usdt_dom = dominance_analysis.get("usdt_dominance")
            dom_interp = dominance_analysis.get("interpretation", {})
            btc_dom_interp = dom_interp.get("btc_dom", "")
            usdt_dom_interp = dom_interp.get("usdt_dom", "")
            
            if btc_dom is None and usdt_dom is None:
                return {"outlook": "Không có dữ liệu dominance", "bias": "NEUTRAL", "reasons": [], "btc_dom": None, "usdt_dom": None}
            
            # Collect reasons from theories and dominance
            reasons = []
            money_flow_signals = []
            
            # BTC Dominance analysis
            if btc_dom is not None:
                if "rising_money_into_btc" in btc_dom_interp or "rising_money_into_btc_alts_weaken" in btc_dom_interp:
                    money_flow_signals.append("SHORT_ALTS")
                    reasons.append(f"BTC.D (Tỷ lệ thống trị BTC): {btc_dom:.2f}% - Tăng → Vốn vào BTC, altcoin yếu")
                elif "falling_good_for_alts" in btc_dom_interp:
                    money_flow_signals.append("LONG_ALTS")
                    reasons.append(f"BTC.D (Tỷ lệ thống trị BTC): {btc_dom:.2f}% - Giảm → Tốt cho altcoin")
                elif "stable" in btc_dom_interp:
                    reasons.append(f"BTC.D (Tỷ lệ thống trị BTC): {btc_dom:.2f}% - Ổn định")
            
            # USDT Dominance analysis
            if usdt_dom is not None:
                if "rising_risk_off" in usdt_dom_interp or "rising_risk_off_shorts_favored" in usdt_dom_interp:
                    money_flow_signals.append("SHORT_MARKET")
                    reasons.append(f"USDT.D (Tỷ lệ thống trị USDT): {usdt_dom:.2f}% - Tăng → Rút vốn khỏi thị trường (risk-off)")
                elif "stable_or_falling" in usdt_dom_interp:
                    money_flow_signals.append("LONG_MARKET")
                    reasons.append(f"USDT.D (Tỷ lệ thống trị USDT): {usdt_dom:.2f}% - Ổn định/giảm → Vốn vào thị trường")
            
            # Get BTC analysis for primary trend analysis (theories)
            btc_analyses = symbol_analyses.get("BTCUSDT", {})
            
            # Dow Theory reasons (from primary timeframes: 1d, 3d, 1w)
            dow_trends = []
            for tf in ["1d", "3d", "1w"]:
                if tf in btc_analyses:
                    dow = btc_analyses[tf].get("dow", {})
                    trend = dow.get("trend", "neutral")
                    if trend != "neutral":
                        trend_vn = "Tăng giá" if trend == "bullish" else "Giảm giá"
                        dow_trends.append(f"{tf}:{trend_vn}")
            
            if dow_trends:
                bullish_count = len([t for t in dow_trends if "Tăng giá" in t])
                bearish_count = len([t for t in dow_trends if "Giảm giá" in t])
                if bullish_count > bearish_count:
                    primary_trend = "Tăng giá"
                    reasons.append(f"Dow Theory (Lý thuyết Dow): Xu hướng chính tăng ({', '.join(dow_trends)})")
                elif bearish_count > bullish_count:
                    primary_trend = "Giảm giá"
                    reasons.append(f"Dow Theory (Lý thuyết Dow): Xu hướng chính giảm ({', '.join(dow_trends)})")
            
            # Wyckoff reasons (from 4h timeframe)
            if "4h" in btc_analyses:
                wyckoff = btc_analyses["4h"].get("wyckoff", {})
                phase = wyckoff.get("phase", "")
                if phase:
                    phase_vn = {
                        "ACCUMULATION": "Tích lũy",
                        "MARKUP": "Tăng giá",
                        "DISTRIBUTION": "Phân phối",
                        "MARKDOWN": "Giảm giá"
                    }.get(phase, phase)
                    reasons.append(f"Wyckoff (Phương pháp Wyckoff): Giai đoạn {phase_vn}")
                if wyckoff.get("sos", False):
                    reasons.append("Wyckoff: SOS (Sign of Strength - Dấu hiệu sức mạnh)")
                if wyckoff.get("sow", False):
                    reasons.append("Wyckoff: SOW (Sign of Weakness - Dấu hiệu yếu)")
            
            # Indicators reasons (from 4h)
            if "4h" in btc_analyses:
                indicators = btc_analyses["4h"].get("indicators", {})
                rsi = indicators.get("rsi")
                macd = indicators.get("macd", {})
                
                if rsi:
                    if rsi > 70:
                        reasons.append(f"RSI (Chỉ số sức mạnh tương đối): {rsi:.1f} - Quá mua")
                    elif rsi > 50:
                        reasons.append(f"RSI (Chỉ số sức mạnh tương đối): {rsi:.1f} - Tăng giá")
                    elif rsi < 30:
                        reasons.append(f"RSI (Chỉ số sức mạnh tương đối): {rsi:.1f} - Quá bán")
                    elif rsi < 50:
                        reasons.append(f"RSI (Chỉ số sức mạnh tương đối): {rsi:.1f} - Giảm giá")
                
                if macd.get("histogram"):
                    if macd["histogram"] > 0:
                        reasons.append("MACD (Phân kỳ hội tụ trung bình động): Tín hiệu tăng giá")
                    else:
                        reasons.append("MACD (Phân kỳ hội tụ trung bình động): Tín hiệu giảm giá")
            
            # Determine overall market bias based on dominance and money flow
            bias = "NEUTRAL"
            outlook = "Thị trường đi ngang"
            emoji = "⚪"
            
            # Priority: USDT.D > BTC.D
            if "SHORT_MARKET" in money_flow_signals:
                bias = "SHORT"
                outlook = "Rút vốn khỏi thị trường"
                emoji = "🔴"
            elif "LONG_MARKET" in money_flow_signals:
                if "SHORT_ALTS" in money_flow_signals:
                    bias = "NEUTRAL"
                    outlook = "Vốn vào thị trường nhưng tập trung vào BTC"
                    emoji = "🟡"
                elif "LONG_ALTS" in money_flow_signals:
                    bias = "LONG"
                    outlook = "Vốn vào thị trường, altcoin mạnh"
                    emoji = "🟢"
                else:
                    bias = "LONG"
                    outlook = "Vốn vào thị trường"
                    emoji = "🟢"
            elif "SHORT_ALTS" in money_flow_signals:
                bias = "NEUTRAL"
                outlook = "Vốn tập trung vào BTC, altcoin yếu"
                emoji = "🟡"
            elif "LONG_ALTS" in money_flow_signals:
                bias = "LONG"
                outlook = "Vốn chảy vào altcoin"
                emoji = "🟢"
            
            # Create outlook detail with dominance info
            outlook_parts = [outlook]
            if btc_dom is not None:
                outlook_parts.append(f"BTC.D: {btc_dom:.2f}%")
            if usdt_dom is not None:
                outlook_parts.append(f"USDT.D: {usdt_dom:.2f}%")
            
            outlook_detail = " | ".join(outlook_parts)
            
            return {
                "outlook": outlook_detail,
                "bias": bias,
                "emoji": emoji,
                "reasons": reasons,
                "btc_dom": btc_dom,
                "usdt_dom": usdt_dom,
                "money_flow_signals": money_flow_signals
            }
        except Exception as e:
            logger.error(f"Error getting overall market outlook: {e}")
            return {"outlook": "Lỗi phân tích", "bias": "NEUTRAL", "reasons": [], "btc_dom": None, "usdt_dom": None}
    
    def format_market_outlook_message(self) -> Optional[str]:
        """Format overall market outlook message for periodic sending."""
        outlook_summary = self.get_overall_market_outlook()
        
        if not outlook_summary or not outlook_summary.get("outlook"):
            return None
        
        bias = outlook_summary.get("bias", "NEUTRAL")
        outlook_text = outlook_summary.get("outlook", "")
        outlook_emoji = outlook_summary.get("emoji", "⚪")
        reasons = outlook_summary.get("reasons", [])
        
        # Map bias to market trend description
        if bias == "LONG":
            trend_desc = "Xu hướng tăng"
            trend_emoji = "📈"
        elif bias == "SHORT":
            trend_desc = "Xu hướng giảm"
            trend_emoji = "📉"
        else:
            trend_desc = "Xu hướng đi ngang"
            trend_emoji = "➡️"
        
        lines = [
            f"<b>📊 Nhận định thị trường</b>\n",
            f"{outlook_emoji} {outlook_text}",
            f"<b>Xu hướng hiện tại:</b> {trend_emoji} <b>{trend_desc}</b>"
        ]
        
        # Add reasons if available
        if reasons:
            lines.append("")
            lines.append("<b>Lý do:</b>")
            for reason in reasons[:5]:  # Limit to 5 most important reasons
                lines.append(f"• {reason}")
        
        return "\n".join(lines)
    
    def send_periodic_market_outlook(self):
        """Send market outlook message periodically (every 5 minutes)."""
        try:
            # Get overall market outlook (all coins)
            message = self.format_market_outlook_message()
            if message:
                success = self.send_telegram_message(TELEGRAM_SIGNAL_CHAT_ID, message)
                if success:
                    logger.info("Periodic market outlook sent to Telegram")
                else:
                    logger.error("Failed to send periodic market outlook")
            else:
                logger.warning("No market outlook data available")
        except Exception as e:
            logger.error(f"Error sending periodic market outlook: {e}")
    
    def run(self):
        """Main service loop."""
        logger.info("Notification Service started")
        
        # Send initial market outlook on startup
        logger.info("Sending initial market outlook...")
        self.send_periodic_market_outlook()
        
        # Subscribe to events
        def event_handler(event_name: str, data: Dict):
            if event_name == EVENT_PRICE_UPDATE_READY:
                self.handle_price_update(event_name, data)
            elif event_name == EVENT_SIGNAL_GENERATED:
                self.handle_signal_generated(event_name, data)
        
        # Start periodic market outlook thread
        def periodic_outlook_loop():
            """Run periodic outlook in separate thread."""
            while True:
                time.sleep(300)  # 5 minutes = 300 seconds
                self.send_periodic_market_outlook()
        
        outlook_thread = threading.Thread(target=periodic_outlook_loop, daemon=True)
        outlook_thread.start()
        logger.info("Periodic market outlook thread started (5 minutes interval)")
        
        try:
            subscribe_events(
                [EVENT_PRICE_UPDATE_READY, EVENT_SIGNAL_GENERATED],
                event_handler,
                consumer_group="notification_service",
                consumer_name="notifier_1"
            )
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        except Exception as e:
            logger.error(f"Error in service loop: {e}")


if __name__ == "__main__":
    service = NotificationService()
    service.run()

