"""
Shared configuration for all microservices.
"""

import os
from typing import List

# MongoDB
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://admin:password@localhost:27017/market?authSource=admin")
MONGODB_DB = os.getenv("MONGODB_DB", "market")

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Binance API
BINANCE_API_URL = os.getenv("BINANCE_API_URL", "https://api.binance.com")

# CoinMarketCap API
CMC_API_KEY = os.getenv("CMC_API_KEY", "")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_PRICE_CHAT_ID = os.getenv("TELEGRAM_PRICE_CHAT_ID", "@ftlssignalzhan")
TELEGRAM_SIGNAL_CHAT_ID = os.getenv("TELEGRAM_SIGNAL_CHAT_ID", "@livingcoinpricechannel")

# Coins to monitor
COINS_ENV = os.getenv("COINS", "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT")
COINS: List[str] = [coin.strip() for coin in COINS_ENV.split(",") if coin.strip()]

# Timeframes for candlesticks
TIMEFRAMES = ["1m", "15m", "1h", "4h", "8h", "1d", "3d", "1w"]

# Collections
COLLECTION_MARKET_DATA = "market_data"
COLLECTION_ANALYSIS = "analysis"
COLLECTION_SIGNALS = "signals"
COLLECTION_PRICE_UPDATES = "price_updates"
COLLECTION_LOGS = "logs"

# Event names
EVENT_MARKET_DATA_UPDATED = "market_data_updated"
EVENT_MARKET_ANALYSIS_COMPLETED = "market_analysis_completed"
EVENT_PRICE_UPDATE_READY = "price_update_ready"
EVENT_SIGNAL_GENERATED = "signal_generated"

# Signal thresholds
SIGNAL_SCORE_HIGH = 75
SIGNAL_SCORE_MEDIUM = 60
SIGNAL_SCORE_MIN = 60

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2

