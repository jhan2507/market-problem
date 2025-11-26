"""
Market Data Service

Responsibilities:
- Fetch price data for all coins listed in .env
- Fetch candlesticks for: 1m (optional), 1h, 4h, 8h, 1d, 3d, 1w
- Fetch market-wide metrics:
  - BTC Dominance (BTC.D)
  - USDT Dominance (USDT.D)
  - TOTAL, TOTAL2, TOTAL3 market cap
  - BTC volatility
- Normalize and store all data into MongoDB
- Publish market_data_updated events
"""

import time
import asyncio
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

from shared.logger import setup_logger
from shared.database import get_database
from shared.events import publish_event
from shared.config import (
    BINANCE_API_URL, CMC_API_KEY, COINS, TIMEFRAMES,
    COLLECTION_MARKET_DATA, EVENT_MARKET_DATA_UPDATED
)

logger = setup_logger("market_data_service")


class MarketDataService:
    """Service for fetching and storing market data."""
    
    def __init__(self):
        self.db = get_database()
        self.collection = self.db[COLLECTION_MARKET_DATA]
        self.session = requests.Session()
    
    def fetch_price(self, symbol: str) -> Optional[float]:
        """Fetch current price from Binance."""
        try:
            url = f"{BINANCE_API_URL}/api/v3/ticker/price"
            params = {"symbol": symbol}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data["price"])
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def fetch_candlesticks(self, symbol: str, interval: str, limit: int = 500) -> Optional[pd.DataFrame]:
        """Fetch candlestick data from Binance."""
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
    
    def fetch_btc_dominance(self) -> Optional[float]:
        """Fetch BTC Dominance from CoinMarketCap."""
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
    
    def fetch_usdt_dominance(self) -> Optional[float]:
        """Fetch USDT Dominance from CoinMarketCap."""
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
    
    def fetch_market_caps(self) -> Dict[str, Optional[float]]:
        """Fetch TOTAL, TOTAL2, TOTAL3 market caps."""
        if not CMC_API_KEY:
            logger.warning("CMC_API_KEY not set, skipping market caps")
            return {"TOTAL": None, "TOTAL2": None, "TOTAL3": None}
        
        try:
            url = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
            headers = {
                'X-CMC_PRO_API_KEY': CMC_API_KEY,
                'Accepts': 'application/json'
            }
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            total = float(data['data']['quote']['USD']['total_market_cap'])
            # TOTAL2 = Total market cap excluding BTC
            # TOTAL3 = Total market cap excluding BTC and ETH
            # These require additional calculations
            total2 = None
            total3 = None
            
            return {
                "TOTAL": total,
                "TOTAL2": total2,
                "TOTAL3": total3
            }
        except Exception as e:
            logger.error(f"Error fetching market caps: {e}")
            return {"TOTAL": None, "TOTAL2": None, "TOTAL3": None}
    
    def calculate_btc_volatility(self, btc_df: Optional[pd.DataFrame]) -> Optional[float]:
        """Calculate BTC volatility (standard deviation of returns)."""
        if btc_df is None or len(btc_df) < 20:
            return None
        
        try:
            returns = btc_df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            return float(volatility * 100)  # As percentage
        except Exception as e:
            logger.error(f"Error calculating BTC volatility: {e}")
            return None
    
    def store_market_data(self, data: Dict[str, Any]) -> bool:
        """Store market data to MongoDB."""
        try:
            data['timestamp'] = datetime.utcnow()
            data['_id'] = f"{data.get('symbol', 'market')}_{int(time.time())}"
            self.collection.insert_one(data)
            return True
        except Exception as e:
            logger.error(f"Error storing market data: {e}")
            return False
    
    def fetch_and_store_all(self):
        """Fetch all market data and store to MongoDB."""
        logger.info("Starting market data fetch cycle")
        
        timestamp = datetime.utcnow()
        all_data = {
            "timestamp": timestamp,
            "prices": {},
            "candlesticks": {},
            "market_metrics": {}
        }
        
        # Fetch prices for all coins
        for symbol in COINS:
            price = self.fetch_price(symbol)
            if price:
                all_data["prices"][symbol] = price
                logger.info(f"Fetched price for {symbol}: {price}")
        
        # Fetch candlesticks for all coins and timeframes
        for symbol in COINS:
            all_data["candlesticks"][symbol] = {}
            for timeframe in TIMEFRAMES:
                if timeframe == "1m":  # Optional - skip for now
                    continue
                df = self.fetch_candlesticks(symbol, timeframe, limit=500)
                if df is not None and len(df) > 0:
                    # Store as list of dicts for MongoDB
                    # Convert timestamp to string for JSON serialization
                    df_copy = df.copy()
                    df_copy['timestamp'] = df_copy['timestamp'].astype(str)
                    all_data["candlesticks"][symbol][timeframe] = df_copy.to_dict('records')
                    logger.info(f"Fetched {timeframe} candlesticks for {symbol}: {len(df)} candles")
        
        # Fetch market metrics
        btc_dom = self.fetch_btc_dominance()
        usdt_dom = self.fetch_usdt_dominance()
        market_caps = self.fetch_market_caps()
        
        # Calculate BTC volatility
        btc_df = self.fetch_candlesticks("BTCUSDT", "1d", limit=30)
        btc_volatility = self.calculate_btc_volatility(btc_df)
        
        all_data["market_metrics"] = {
            "btc_dominance": btc_dom,
            "usdt_dominance": usdt_dom,
            "total_market_cap": market_caps.get("TOTAL"),
            "total2_market_cap": market_caps.get("TOTAL2"),
            "total3_market_cap": market_caps.get("TOTAL3"),
            "btc_volatility": btc_volatility
        }
        
        # Store to MongoDB
        if self.store_market_data(all_data):
            logger.info("Market data stored successfully")
            
            # Publish event
            event_data = {
                "timestamp": timestamp.isoformat(),
                "coins": list(all_data["prices"].keys()),
                "has_candlesticks": bool(all_data["candlesticks"]),
                "has_metrics": bool(all_data["market_metrics"])
            }
            publish_event(EVENT_MARKET_DATA_UPDATED, event_data)
            logger.info("Published market_data_updated event")
        else:
            logger.error("Failed to store market data")
    
    def run(self):
        """Main service loop."""
        logger.info("Market Data Service started")
        
        while True:
            try:
                self.fetch_and_store_all()
                # Run every 5 minutes
                time.sleep(300)
            except KeyboardInterrupt:
                logger.info("Service stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in service loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry


if __name__ == "__main__":
    service = MarketDataService()
    service.run()

