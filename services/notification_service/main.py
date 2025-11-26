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
import requests
from datetime import datetime
from typing import Dict, Optional
from collections import deque

from shared.logger import setup_logger
from shared.database import get_database
from shared.events import subscribe_events
from shared.config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_PRICE_CHAT_ID, TELEGRAM_SIGNAL_CHAT_ID,
    EVENT_PRICE_UPDATE_READY, EVENT_SIGNAL_GENERATED,
    MAX_RETRIES, RETRY_DELAY
)

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
        """Format price update message."""
        prices = data.get("prices", {})
        volatilities = data.get("volatilities", [])
        
        lines = ["💰 <b>Giá coin cập nhật:</b>\n"]
        
        for symbol, price in prices.items():
            coin_name = symbol.replace("USDT", "")
            lines.append(f"{coin_name}: ${price:,.2f}")
        
        # Add volatility alerts
        if volatilities:
            lines.append("\n🚨 <b>Cảnh báo biến động:</b>")
            for vol in volatilities:
                vol_type = vol.get("type", "")
                change = vol.get("change_5m") or vol.get("change_15m", 0)
                symbol = vol.get("symbol", "").replace("USDT", "")
                
                if vol_type == "pump":
                    lines.append(f"🚀 {symbol}: +{change:.2f}% ({vol.get('timeframe', '')})")
                elif vol_type == "dump":
                    lines.append(f"⚠️ {symbol}: {change:.2f}% ({vol.get('timeframe', '')})")
                elif vol_type == "btc_movement":
                    lines.append(f"📊 BTC: {change:+.2f}% (15m)")
        
        return "\n".join(lines)
    
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
    
    def run(self):
        """Main service loop."""
        logger.info("Notification Service started")
        
        # Subscribe to events
        def event_handler(event_name: str, data: Dict):
            if event_name == EVENT_PRICE_UPDATE_READY:
                self.handle_price_update(event_name, data)
            elif event_name == EVENT_SIGNAL_GENERATED:
                self.handle_signal_generated(event_name, data)
        
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

