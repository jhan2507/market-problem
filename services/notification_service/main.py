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

from shared.logger import setup_logger, set_correlation_id
from shared.database import get_database
from shared.events import subscribe_events
from shared.health import HealthChecker
from shared.http_server import ServiceHTTPServer
from shared.shutdown import get_shutdown_manager, register_shutdown_handler
from shared.metrics import MetricsCollector
from shared.tracing import setup_tracing, get_tracer
from shared.circuit_breaker import get_circuit_breaker, CircuitBreakerOpenError
from shared.retry import retry_with_backoff
from shared.timeout import timeout_thread
from shared.service_discovery import get_service_registry
from shared.config_manager import (
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
        self._running = True
        self.metrics = None
        
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
    
    @retry_with_backoff(max_attempts=3, initial_delay=1.0, retry_exceptions=(requests.exceptions.RequestException,))
    def send_telegram_message(self, chat_id: str, text: str, 
                             retry_count: int = 0) -> bool:
        """
        Send message to Telegram with retry logic and circuit breaker.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text (HTML format)
            retry_count: Current retry attempt (kept for backward compatibility)
        
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
            cb = get_circuit_breaker("telegram_api", failure_threshold=5, recovery_timeout=60)
            
            def _send():
                response = self.session.post(url, json=payload, timeout=10)
                response.raise_for_status()
                return response
            
            try:
                response = cb.call(_send)
                # Track message timestamp
                self.message_timestamps.append(time.time())
                
                if self.metrics:
                    self.metrics.record_external_api_call("telegram", "success")
                return True
            except CircuitBreakerOpenError as e:
                logger.error(f"Circuit breaker open for Telegram API: {e}")
                if self.metrics:
                    self.metrics.record_external_api_call("telegram", "circuit_open")
                return False
        except requests.exceptions.HTTPError as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                # Rate limited - wait and retry
                retry_after = int(e.response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limited, waiting {retry_after} seconds")
                time.sleep(retry_after)
                if self.metrics:
                    self.metrics.record_external_api_call("telegram", "rate_limited")
            else:
                logger.error(f"HTTP error sending Telegram message: {e}")
                if self.metrics:
                    self.metrics.record_external_api_call("telegram", "error")
            return False
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            if self.metrics:
                self.metrics.record_external_api_call("telegram", "error")
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
        from shared.config_manager import COLLECTION_ANALYSIS
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
        from shared.config_manager import COLLECTION_SIGNALS
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
    
    def fetch_realtime_btc_dominance(self, max_retries: int = 3) -> Optional[float]:
        """Fetch BTC Dominance from CoinMarketCap in real-time with retry logic."""
        if not CMC_API_KEY:
            logger.warning("CMC_API_KEY not set, skipping BTC dominance")
            return None
        
        import time
        url = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
        headers = {
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
            'Accepts': 'application/json'
        }
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, headers=headers, timeout=10)
                
                # Handle rate limit (429)
                if response.status_code == 429:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Rate limit hit (429), retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Max retries reached for BTC dominance (rate limit)")
                        return None
                
                response.raise_for_status()
                data = response.json()
                return float(data['data']['btc_dominance'])
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Error fetching BTC dominance after {max_retries} attempts: {e}")
                else:
                    wait_time = 2 ** attempt
                    logger.warning(f"Error fetching BTC dominance, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(wait_time)
        
        return None
    
    def fetch_realtime_usdt_dominance(self, max_retries: int = 3) -> Optional[float]:
        """Fetch USDT Dominance from CoinMarketCap in real-time with retry logic."""
        if not CMC_API_KEY:
            logger.warning("CMC_API_KEY not set, skipping USDT dominance")
            return None
        
        import time
        headers = {
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
            'Accepts': 'application/json'
        }
        
        for attempt in range(max_retries):
            try:
                # Get USDT market cap
                url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
                params = {'symbol': 'USDT'}
                response = self.session.get(url, headers=headers, params=params, timeout=10)
                
                # Handle rate limit (429)
                if response.status_code == 429:
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limit hit (429) for USDT, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Max retries reached for USDT market cap (rate limit)")
                        return None
                
                response.raise_for_status()
                data = response.json()
                usdt_market_cap = float(data['data']['USDT']['quote']['USD']['market_cap'])
                
                # Get total market cap
                url_global = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
                response_global = self.session.get(url_global, headers=headers, timeout=10)
                
                # Handle rate limit for global metrics
                if response_global.status_code == 429:
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limit hit (429) for global metrics, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Max retries reached for global metrics (rate limit)")
                        return None
                
                response_global.raise_for_status()
                data_global = response_global.json()
                total_market_cap = float(data_global['data']['quote']['USD']['total_market_cap'])
                
                return (usdt_market_cap / total_market_cap) * 100
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Error fetching USDT dominance after {max_retries} attempts: {e}")
                else:
                    wait_time = 2 ** attempt
                    logger.warning(f"Error fetching USDT dominance, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(wait_time)
        
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
        from shared.config_manager import COLLECTION_ANALYSIS, COLLECTION_MARKET_DATA
        analysis_collection = self.db[COLLECTION_ANALYSIS]
        market_data_collection = self.db[COLLECTION_MARKET_DATA]
        
        try:
            # Initialize variables
            symbol_analyses = {}
            dominance_analysis = {}
            btc_dom = None
            usdt_dom = None
            
            # Step 1: Try to get from analysis collection
            latest_analysis = analysis_collection.find_one(
                sort=[("timestamp", -1)]
            )
            
            if latest_analysis:
                symbol_analyses = latest_analysis.get("symbol_analyses", {})
                dominance_analysis = latest_analysis.get("dominance_analysis", {})
                btc_dom = dominance_analysis.get("btc_dominance")
                usdt_dom = dominance_analysis.get("usdt_dominance")
            
            # Step 2: If no dominance in analysis, try market_data collection
            if btc_dom is None or usdt_dom is None:
                logger.info("Dominance not in analysis, checking market_data collection...")
                latest_market_data = market_data_collection.find_one(
                    sort=[("timestamp", -1)]
                )
                
                if latest_market_data:
                    market_metrics = latest_market_data.get("market_metrics", {})
                    if btc_dom is None:
                        btc_dom = market_metrics.get("btc_dominance")
                    if usdt_dom is None:
                        usdt_dom = market_metrics.get("usdt_dominance")
            
            # Step 3: Only fetch real-time if we REALLY don't have data in DB
            # Priority: Use DB data first, only fetch realtime as last resort
            need_realtime_dominance = (btc_dom is None or usdt_dom is None)
            need_realtime_analysis = (not symbol_analyses)
            
            # Check data freshness if we have some data
            data_is_fresh = False
            should_fetch_realtime = False
            
            if latest_analysis or latest_market_data:
                from datetime import datetime, timedelta
                latest_timestamp = None
                
                if latest_analysis:
                    latest_timestamp = latest_analysis.get("timestamp")
                if latest_market_data:
                    market_timestamp = latest_market_data.get("timestamp")
                    if market_timestamp:
                        # Handle both datetime and string timestamps
                        if isinstance(market_timestamp, str):
                            try:
                                market_timestamp = datetime.fromisoformat(market_timestamp.replace('Z', '+00:00'))
                            except:
                                pass
                        if not latest_timestamp or (isinstance(market_timestamp, datetime) and 
                            (not isinstance(latest_timestamp, datetime) or market_timestamp > latest_timestamp)):
                            latest_timestamp = market_timestamp
                
                if latest_timestamp:
                    if isinstance(latest_timestamp, datetime):
                        time_diff = datetime.utcnow() - latest_timestamp
                    elif isinstance(latest_timestamp, str):
                        try:
                            latest_timestamp = datetime.fromisoformat(latest_timestamp.replace('Z', '+00:00'))
                            time_diff = datetime.utcnow() - latest_timestamp
                        except:
                            time_diff = timedelta(hours=1)  # Assume stale if can't parse
                    else:
                        time_diff = timedelta(hours=1)  # Assume stale if unknown type
                    
                    # Consider data fresh if less than 10 minutes old
                    data_is_fresh = time_diff < timedelta(minutes=10)
                    logger.info(f"Latest data is {time_diff.total_seconds()/60:.1f} minutes old (fresh: {data_is_fresh})")
            
            # Only fetch realtime if:
            # 1. We don't have dominance AND (no data in DB OR data is stale)
            # 2. OR we don't have any analysis data at all
            if need_realtime_dominance:
                if not latest_analysis and not latest_market_data:
                    logger.info("No data in DB, will fetch real-time dominance...")
                    should_fetch_realtime = True
                elif not data_is_fresh:
                    logger.info("Dominance missing and data is stale, will fetch real-time...")
                    should_fetch_realtime = True
                else:
                    logger.info("Dominance missing but data is fresh, skipping realtime fetch to avoid rate limit")
            
            if need_realtime_analysis and not symbol_analyses:
                logger.info("Analysis data missing, will fetch real-time...")
                should_fetch_realtime = True
            
            if should_fetch_realtime:
                logger.info("Fetching real-time market data...")
                realtime_analysis = self.analyze_realtime_market_data()
                
                if realtime_analysis:
                    # Update dominance from realtime if we don't have it
                    realtime_dom = realtime_analysis.get("dominance_analysis", {})
                    if btc_dom is None:
                        btc_dom = realtime_dom.get("btc_dominance")
                    if usdt_dom is None:
                        usdt_dom = realtime_dom.get("usdt_dominance")
                    
                    # Update dominance_analysis from realtime
                    if realtime_dom:
                        dominance_analysis = realtime_dom
                    
                    # Update symbol_analyses if we don't have it
                    if not symbol_analyses:
                        symbol_analyses = realtime_analysis.get("symbol_analyses", {})
                else:
                    # If analyze_realtime_market_data failed, try direct fetch for dominance
                    logger.warning("analyze_realtime_market_data failed, trying direct dominance fetch...")
                    if btc_dom is None:
                        btc_dom = self.fetch_realtime_btc_dominance()
                    if usdt_dom is None:
                        usdt_dom = self.fetch_realtime_usdt_dominance()
            
            # Step 4: Build dominance_analysis if we have values but no structure
            if (btc_dom is not None or usdt_dom is not None):
                if not dominance_analysis:
                    dominance_analysis = {}
                if btc_dom is not None and "btc_dominance" not in dominance_analysis:
                    dominance_analysis["btc_dominance"] = btc_dom
                if usdt_dom is not None and "usdt_dominance" not in dominance_analysis:
                    dominance_analysis["usdt_dominance"] = usdt_dom
                if "interpretation" not in dominance_analysis:
                    dominance_analysis["interpretation"] = {}
            
            # Step 5: Interpret dominance if we have values
            dom_interp = dominance_analysis.get("interpretation", {})
            if btc_dom is not None and "btc_dom" not in dom_interp:
                if btc_dom > 55:
                    dom_interp["btc_dom"] = "rising_money_into_btc_alts_weaken"
                elif btc_dom < 45:
                    dom_interp["btc_dom"] = "falling_good_for_alts"
                else:
                    dom_interp["btc_dom"] = "stable"
            
            if usdt_dom is not None and "usdt_dom" not in dom_interp:
                if usdt_dom > 8:
                    dom_interp["usdt_dom"] = "rising_risk_off_shorts_favored"
                else:
                    dom_interp["usdt_dom"] = "stable_or_falling"
            
            dominance_analysis["interpretation"] = dom_interp
            
            btc_dom_interp = dom_interp.get("btc_dom", "")
            usdt_dom_interp = dom_interp.get("usdt_dom", "")
            
            # Final check: if still no dominance after all attempts
            if btc_dom is None and usdt_dom is None:
                # Determine the reason for missing data
                has_db_data = (latest_analysis is not None) or (latest_market_data is not None)
                
                if should_fetch_realtime:
                    # We tried to fetch but failed
                    logger.error("Failed to fetch dominance from all sources (DB and realtime) - likely rate limited")
                    return {
                        "outlook": "Không thể lấy dữ liệu dominance",
                        "bias": "NEUTRAL", 
                        "reasons": [
                            "⚠️ Không tìm thấy dữ liệu BTC.D và USDT.D trong database" if not has_db_data else "⚠️ Dữ liệu trong database không có dominance",
                            "⚠️ Không thể lấy dữ liệu từ CoinMarketCap (có thể bị rate limit)",
                            "💡 Hệ thống sẽ tự động thử lại sau",
                            "📊 Vui lòng đợi vài phút để dữ liệu được cập nhật"
                        ], 
                        "btc_dom": None, 
                        "usdt_dom": None,
                        "error": "no_dominance_data"
                    }
                elif has_db_data and not data_is_fresh:
                    # Data exists in DB but is stale, and we didn't fetch (to avoid rate limit)
                    logger.warning("Dominance data is stale but not fetching to avoid rate limit")
                    return {
                        "outlook": "Dữ liệu dominance đã cũ",
                        "bias": "NEUTRAL", 
                        "reasons": [
                            "⚠️ Dữ liệu BTC.D và USDT.D trong database đã cũ (hơn 10 phút)",
                            "💡 Hệ thống sẽ tự động cập nhật khi có thể",
                            "📊 Vui lòng đợi để tránh rate limit"
                        ], 
                        "btc_dom": None, 
                        "usdt_dom": None,
                        "error": "stale_data"
                    }
                else:
                    # No data in DB at all
                    logger.warning("No dominance data in database")
                    return {
                        "outlook": "Chưa có dữ liệu dominance",
                        "bias": "NEUTRAL", 
                        "reasons": [
                            "⚠️ Chưa có dữ liệu BTC.D và USDT.D trong database",
                            "💡 Hệ thống đang chờ dữ liệu từ market_data_service",
                            "📊 Dữ liệu sẽ được cập nhật tự động"
                        ], 
                        "btc_dom": None, 
                        "usdt_dom": None,
                        "error": "no_db_data"
                    }
            
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
            
            # Dow Theory analysis (from primary timeframes: 1d, 3d, 1w)
            dow_trends = []
            dow_bullish_count = 0
            dow_bearish_count = 0
            primary_trend = None
            
            for tf in ["1d", "3d", "1w"]:
                if tf in btc_analyses:
                    dow = btc_analyses[tf].get("dow", {})
                    trend = dow.get("trend", "neutral")
                    if trend != "neutral":
                        trend_vn = "Tăng giá" if trend == "bullish" else "Giảm giá"
                        dow_trends.append(f"{tf}:{trend_vn}")
                        if trend == "bullish":
                            dow_bullish_count += 1
                        else:
                            dow_bearish_count += 1
            
            if dow_trends:
                if dow_bullish_count > dow_bearish_count:
                    primary_trend = "BULLISH"
                    reasons.append(f"Dow Theory (Lý thuyết Dow): Xu hướng chính tăng ({', '.join(dow_trends)})")
                elif dow_bearish_count > dow_bullish_count:
                    primary_trend = "BEARISH"
                    reasons.append(f"Dow Theory (Lý thuyết Dow): Xu hướng chính giảm ({', '.join(dow_trends)})")
                else:
                    primary_trend = "NEUTRAL"
            
            # Wyckoff analysis (from 4h timeframe)
            wyckoff_phase = None
            wyckoff_bullish = False
            wyckoff_sos = False
            wyckoff_sow = False
            
            if "4h" in btc_analyses:
                wyckoff = btc_analyses["4h"].get("wyckoff", {})
                phase = wyckoff.get("phase", "")
                if phase:
                    wyckoff_phase = phase
                    phase_vn = {
                        "ACCUMULATION": "Tích lũy",         
                        "MARKUP": "Tăng giá",
                        "DISTRIBUTION": "Phân phối",
                        "MARKDOWN": "Giảm giá"
                    }.get(phase, phase)
                    reasons.append(f"Wyckoff (Phương pháp Wyckoff): Giai đoạn {phase_vn}")
                    wyckoff_bullish = phase in ["ACCUMULATION", "MARKUP"]
                
                wyckoff_sos = wyckoff.get("sos", False)
                wyckoff_sow = wyckoff.get("sow", False)
                
                if wyckoff_sos:
                    reasons.append("Wyckoff: SOS (Sign of Strength - Dấu hiệu sức mạnh)")
                if wyckoff_sow:
                    reasons.append("Wyckoff: SOW (Sign of Weakness - Dấu hiệu yếu)")
            
            # Indicators analysis (from 4h)
            rsi_value = None
            rsi_signal = None
            macd_signal = None
            rsi_overbought = False
            rsi_oversold = False
            
            if "4h" in btc_analyses:
                indicators = btc_analyses["4h"].get("indicators", {})
                rsi_value = indicators.get("rsi")
                macd = indicators.get("macd", {})
                
                if rsi_value:
                    if rsi_value > 70:
                        rsi_signal = "OVERBOUGHT"
                        rsi_overbought = True
                        reasons.append(f"RSI (Chỉ số sức mạnh tương đối): {rsi_value:.1f} - Quá mua")
                    elif rsi_value > 50:
                        rsi_signal = "BULLISH"
                        reasons.append(f"RSI (Chỉ số sức mạnh tương đối): {rsi_value:.1f} - Tăng giá")
                    elif rsi_value < 30:
                        rsi_signal = "OVERSOLD"
                        rsi_oversold = True
                        reasons.append(f"RSI (Chỉ số sức mạnh tương đối): {rsi_value:.1f} - Quá bán")
                    elif rsi_value < 50:
                        rsi_signal = "BEARISH"
                        reasons.append(f"RSI (Chỉ số sức mạnh tương đối): {rsi_value:.1f} - Giảm giá")
                
                if macd.get("histogram"):
                    if macd["histogram"] > 0:
                        macd_signal = "BULLISH"
                        reasons.append("MACD (Phân kỳ hội tụ trung bình động): Tín hiệu tăng giá")
                    else:
                        macd_signal = "BEARISH"
                        reasons.append("MACD (Phân kỳ hội tụ trung bình động): Tín hiệu giảm giá")
            
            # Detect conflicts between indicators
            conflicts = []
            
            # Conflict: Dow Theory vs Wyckoff
            if primary_trend == "BEARISH" and wyckoff_bullish:
                conflicts.append("⚠️ Mâu thuẫn: Dow Theory (dài hạn giảm) vs Wyckoff (ngắn hạn tăng) - Có thể là điều chỉnh tăng trong xu hướng giảm")
            elif primary_trend == "BULLISH" and not wyckoff_bullish and wyckoff_phase in ["DISTRIBUTION", "MARKDOWN"]:
                conflicts.append("⚠️ Mâu thuẫn: Dow Theory (dài hạn tăng) vs Wyckoff (ngắn hạn giảm) - Có thể là điều chỉnh giảm trong xu hướng tăng")
            
            # Conflict: RSI overbought in bullish phase
            if rsi_overbought and wyckoff_bullish:
                conflicts.append("⚠️ Cảnh báo: RSI quá mua trong giai đoạn tăng - Cần thận trọng")
            
            # Conflict: RSI oversold in bearish phase
            if rsi_oversold and not wyckoff_bullish:
                conflicts.append("⚠️ Cảnh báo: RSI quá bán trong giai đoạn giảm - Có thể phục hồi")
            
            # Conflict: Dominance vs Dow Theory
            if "LONG_MARKET" in money_flow_signals and primary_trend == "BEARISH":
                conflicts.append("⚠️ Mâu thuẫn: Vốn vào thị trường nhưng xu hướng dài hạn giảm - Cần theo dõi")
            elif "SHORT_MARKET" in money_flow_signals and primary_trend == "BULLISH":
                conflicts.append("⚠️ Mâu thuẫn: Rút vốn nhưng xu hướng dài hạn tăng - Có thể là điều chỉnh")
            
            # Weighted scoring system
            # Weights: Dominance (40%), Dow Theory (30%), Wyckoff (20%), RSI/MACD (10%)
            bullish_score = 0.0
            bearish_score = 0.0
            
            # Dominance weight: 40%
            if "LONG_MARKET" in money_flow_signals:
                bullish_score += 0.4
            elif "SHORT_MARKET" in money_flow_signals:
                bearish_score += 0.4
            
            if "LONG_ALTS" in money_flow_signals:
                bullish_score += 0.2
            elif "SHORT_ALTS" in money_flow_signals:
                bearish_score += 0.2
            
            # Dow Theory weight: 30%
            if primary_trend == "BULLISH":
                bullish_score += 0.3
            elif primary_trend == "BEARISH":
                bearish_score += 0.3
            
            # Wyckoff weight: 20%
            if wyckoff_bullish:
                bullish_score += 0.2
            elif wyckoff_phase in ["DISTRIBUTION", "MARKDOWN"]:
                bearish_score += 0.2
            
            # RSI/MACD weight: 10%
            if rsi_signal == "BULLISH" or macd_signal == "BULLISH":
                bullish_score += 0.05
            elif rsi_signal == "BEARISH" or macd_signal == "BEARISH":
                bearish_score += 0.05
            
            # Determine overall market bias with confidence level
            bias = "NEUTRAL"
            outlook = "Thị trường đi ngang"
            emoji = "⚪"
            confidence = "MEDIUM"
            
            score_diff = bullish_score - bearish_score
            
            # High confidence threshold: > 0.3 difference
            # Medium confidence: 0.1 - 0.3 difference
            # Low confidence: < 0.1 difference or conflicts
            
            if score_diff > 0.3:
                bias = "LONG"
                confidence = "HIGH" if len(conflicts) == 0 else "MEDIUM"
                if "LONG_ALTS" in money_flow_signals:
                    outlook = "Vốn vào thị trường, altcoin mạnh"
                    emoji = "🟢"
                elif "SHORT_ALTS" in money_flow_signals:
                    outlook = "Vốn vào thị trường nhưng tập trung vào BTC"
                    emoji = "🟡"
                else:
                    outlook = "Vốn vào thị trường"
                    emoji = "🟢"
            elif score_diff < -0.3:
                bias = "SHORT"
                confidence = "HIGH" if len(conflicts) == 0 else "MEDIUM"
                if "SHORT_MARKET" in money_flow_signals:
                    outlook = "Rút vốn khỏi thị trường"
                    emoji = "🔴"
                else:
                    outlook = "Xu hướng giảm"
                    emoji = "🔴"
            elif score_diff > 0.1:
                bias = "LONG"
                confidence = "MEDIUM" if len(conflicts) == 0 else "LOW"
                if "SHORT_ALTS" in money_flow_signals:
                    outlook = "Vốn vào thị trường nhưng tập trung vào BTC"
                    emoji = "🟡"
                else:
                    outlook = "Xu hướng tăng nhẹ"
                    emoji = "🟡"
            elif score_diff < -0.1:
                bias = "SHORT"
                confidence = "MEDIUM" if len(conflicts) == 0 else "LOW"
                outlook = "Xu hướng giảm nhẹ"
                emoji = "🟡"
            else:
                bias = "NEUTRAL"
                confidence = "LOW" if len(conflicts) > 0 else "MEDIUM"
                if "SHORT_ALTS" in money_flow_signals:
                    outlook = "Vốn tập trung vào BTC, altcoin yếu"
                    emoji = "🟡"
                else:
                    outlook = "Thị trường đi ngang"
                    emoji = "⚪"
            
            # Add conflicts to reasons
            if conflicts:
                reasons.extend(conflicts)
            
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
                "money_flow_signals": money_flow_signals,
                "confidence": confidence,
                "conflicts": conflicts,
                "bullish_score": bullish_score,
                "bearish_score": bearish_score
            }
        except Exception as e:
            logger.error(f"Error getting overall market outlook: {e}")
            return {"outlook": "Lỗi phân tích", "bias": "NEUTRAL", "reasons": [], "btc_dom": None, "usdt_dom": None}
    
    def format_market_outlook_message(self) -> Optional[str]:
        """Format overall market outlook message for periodic sending."""
        outlook_summary = self.get_overall_market_outlook()
        
        if not outlook_summary:
            logger.warning("get_overall_market_outlook returned None")
            return None
        
        bias = outlook_summary.get("bias", "NEUTRAL")
        outlook_text = outlook_summary.get("outlook", "")
        outlook_emoji = outlook_summary.get("emoji", "⚪")
        reasons = outlook_summary.get("reasons", [])
        btc_dom = outlook_summary.get("btc_dom")
        usdt_dom = outlook_summary.get("usdt_dom")
        confidence = outlook_summary.get("confidence", "MEDIUM")
        conflicts = outlook_summary.get("conflicts", [])
        bullish_score = outlook_summary.get("bullish_score", 0.0)
        bearish_score = outlook_summary.get("bearish_score", 0.0)
        
        # Check if we have valid dominance data
        has_dominance = btc_dom is not None or usdt_dom is not None
        
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
            f"{outlook_emoji} {outlook_text}"
        ]
        
        # Only show trend if we have dominance data
        if has_dominance:
            lines.append(f"<b>Xu hướng hiện tại:</b> {trend_emoji} <b>{trend_desc}</b>")
        
        # Show confidence level
        if confidence == "HIGH":
            lines.append(f"<b>Độ tin cậy:</b> 🟢 <b>Cao</b>")
        elif confidence == "MEDIUM":
            lines.append(f"<b>Độ tin cậy:</b> 🟡 <b>Trung bình</b>")
        else:
            lines.append(f"<b>Độ tin cậy:</b> 🔴 <b>Thấp</b>")
        
        # Show conflicts/warnings if any
        if conflicts:
            lines.append("")
            lines.append("<b>⚠️ Cảnh báo:</b>")
            for conflict in conflicts:
                lines.append(f"• {conflict}")
        
        # Show dominance values if available
        if btc_dom is not None or usdt_dom is not None:
            lines.append("")
            lines.append("<b>Chỉ số dominance:</b>")
            if btc_dom is not None:
                lines.append(f"• BTC.D (Tỷ lệ thống trị BTC): {btc_dom:.2f}%")
            if usdt_dom is not None:
                lines.append(f"• USDT.D (Tỷ lệ thống trị USDT): {usdt_dom:.2f}%")
        
        # Add reasons if available
        if reasons:
            lines.append("")
            if has_dominance:
                lines.append("<b>Phân tích:</b>")
            else:
                lines.append("<b>Thông tin:</b>")
            # Separate conflicts from regular reasons
            regular_reasons = [r for r in reasons if not r.startswith("⚠️")]
            conflict_reasons = [r for r in reasons if r.startswith("⚠️")]
            
            # Show regular reasons first (limit to 5)
            for reason in regular_reasons[:5]:
                lines.append(f"• {reason}")
            
            # Conflicts already shown above, so skip them here
    
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
        
        # Setup tracing
        setup_tracing("notification_service")
        
        # Setup metrics
        metrics = MetricsCollector("notification_service")
        self.metrics = metrics
        
        # Setup health checker and HTTP server
        health_checker = HealthChecker("notification_service")
        http_server = ServiceHTTPServer("notification_service", port=8004, health_checker=health_checker, metrics_collector=metrics)
        http_server.start()
        
        # Register with service discovery
        registry = get_service_registry()
        registry.register_service(
            "notification_service",
            host="localhost",
            port=8004,
            health_check_url="http://localhost:8004/health"
        )
        
        # Register shutdown handler
        def shutdown_handler():
            logger.info("Shutting down Notification Service...")
            self._running = False
            
            # Wait for outlook thread to finish (with timeout)
            if hasattr(self, 'outlook_thread') and self.outlook_thread.is_alive():
                logger.info("Waiting for outlook thread to finish...")
                self.outlook_thread.join(timeout=5.0)
                if self.outlook_thread.is_alive():
                    logger.warning("Outlook thread did not finish within timeout")
            
            registry.unregister_service("notification_service")
            if self.session:
                self.session.close()
        
        register_shutdown_handler(shutdown_handler)
        
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
            while self._running:
                for _ in range(300):  # Check _running every second
                    if not self._running:
                        break
                    time.sleep(1)
                if self._running:
                    self.send_periodic_market_outlook()
        
        outlook_thread = threading.Thread(target=periodic_outlook_loop, daemon=True, name="outlook-thread")
        outlook_thread.start()
        self.outlook_thread = outlook_thread  # Keep reference for cleanup
        logger.info("Periodic market outlook thread started (5 minutes interval)")
        
        try:
            subscribe_events(
                [EVENT_PRICE_UPDATE_READY, EVENT_SIGNAL_GENERATED],
                event_handler,
                consumer_group="notification_service",
                consumer_name="notifier_1",
                running_flag=lambda: self._running
            )
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        except Exception as e:
            logger.error(f"Error in service loop: {e}")
        finally:
            logger.info("Notification Service stopped")


if __name__ == "__main__":
    service = NotificationService()
    service.run()

