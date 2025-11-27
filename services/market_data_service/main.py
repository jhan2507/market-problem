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
import threading
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

from shared.logger import setup_logger, set_correlation_id
from shared.database import get_database
from shared.events import publish_event
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
        self._running = True
        self.metrics = None  # Will be set in run()
    
    @retry_with_backoff(max_attempts=3, initial_delay=1.0, retry_exceptions=(Exception,))
    def fetch_price(self, symbol: str) -> Optional[float]:
        """Fetch current price from Binance."""
        try:
            cb = get_circuit_breaker("binance_api", failure_threshold=5, recovery_timeout=60)
            
            def _fetch():
                url = f"{BINANCE_API_URL}/api/v3/ticker/price"
                params = {"symbol": symbol}
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                return float(data["price"])
            
            try:
                result = cb.call(_fetch)
                if self.metrics:
                    self.metrics.record_external_api_call("binance", "success")
                return result
            except CircuitBreakerOpenError as e:
                logger.error(f"Circuit breaker open for Binance API: {e}")
                if self.metrics:
                    self.metrics.record_external_api_call("binance", "circuit_open")
                return None
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            if self.metrics:
                self.metrics.record_external_api_call("binance", "error")
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
    
    @retry_with_backoff(max_attempts=3, initial_delay=2.0, retry_exceptions=(Exception,))
    def fetch_btc_dominance(self) -> Optional[float]:
        """Fetch BTC Dominance from CoinMarketCap."""
        if not CMC_API_KEY:
            logger.warning("CMC_API_KEY not set, skipping BTC dominance")
            return None
        
        try:
            cb = get_circuit_breaker("coinmarketcap_api", failure_threshold=3, recovery_timeout=120)
            
            def _fetch():
                url = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
                headers = {
                    'X-CMC_PRO_API_KEY': CMC_API_KEY,
                    'Accepts': 'application/json'
                }
                response = self.session.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                return float(data['data']['btc_dominance'])
            
            try:
                result = cb.call(_fetch)
                if self.metrics:
                    self.metrics.record_external_api_call("coinmarketcap", "success")
                return result
            except CircuitBreakerOpenError as e:
                logger.error(f"Circuit breaker open for CoinMarketCap API: {e}")
                if self.metrics:
                    self.metrics.record_external_api_call("coinmarketcap", "circuit_open")
                return None
        except Exception as e:
            logger.error(f"Error fetching BTC dominance: {e}")
            if self.metrics:
                self.metrics.record_external_api_call("coinmarketcap", "error")
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
        corr_id = set_correlation_id()
        logger.info(f"Starting market data fetch cycle [correlation_id: {corr_id}]")
        
        tracer = get_tracer("market_data_service")
        with tracer.start_as_current_span("fetch_and_store_all") as span:
            span.set_attribute("correlation_id", corr_id)
            
            import time
            start_time = time.time()
            
            timestamp = datetime.utcnow()
            all_data = {
                "timestamp": timestamp,
                "prices": {},
                "candlesticks": {},
                "market_metrics": {}
            }
            
            # Fetch prices for all coins
            for symbol in COINS:
                with tracer.start_as_current_span(f"fetch_price_{symbol}"):
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
                    with tracer.start_as_current_span(f"fetch_candlesticks_{symbol}_{timeframe}"):
                        df = self.fetch_candlesticks(symbol, timeframe, limit=500)
                        if df is not None and len(df) > 0:
                            # Store as list of dicts for MongoDB
                            # Convert timestamp to string for JSON serialization
                            df_copy = df.copy()
                            df_copy['timestamp'] = df_copy['timestamp'].astype(str)
                            all_data["candlesticks"][symbol][timeframe] = df_copy.to_dict('records')
                            logger.info(f"Fetched {timeframe} candlesticks for {symbol}: {len(df)} candles")
            
            # Fetch market metrics
            with tracer.start_as_current_span("fetch_market_metrics"):
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
            with tracer.start_as_current_span("store_market_data"):
                if self.store_market_data(all_data):
                    logger.info("Market data stored successfully")
                    
                    # Publish event
                    event_data = {
                        "timestamp": timestamp.isoformat(),
                        "coins": list(all_data["prices"].keys()),
                        "has_candlesticks": bool(all_data["candlesticks"]),
                        "has_metrics": bool(all_data["market_metrics"]),
                        "correlation_id": corr_id
                    }
                    publish_event(EVENT_MARKET_DATA_UPDATED, event_data, service_name="market_data_service")
                    logger.info("Published market_data_updated event")
                    
                    # Record metrics
                    if hasattr(self, 'metrics'):
                        duration = time.time() - start_time
                        self.metrics.record_processing_time("fetch_and_store_all", duration)
                        self.metrics.record_event_published(EVENT_MARKET_DATA_UPDATED)
                else:
                    logger.error("Failed to store market data")
                    if hasattr(self, 'metrics'):
                        self.metrics.record_error("store_failed")
    
    def run(self):
        """Main service loop."""
        logger.info("Market Data Service started")
        
        # Setup tracing
        setup_tracing("market_data_service")
        tracer = get_tracer("market_data_service")
        
        # Setup metrics
        metrics = MetricsCollector("market_data_service")
        
        # Setup health checker and HTTP server
        health_checker = HealthChecker("market_data_service")
        http_server = ServiceHTTPServer("market_data_service", port=8000, health_checker=health_checker, metrics_collector=metrics)
        http_server.start()
        
        # Register with service discovery
        registry = get_service_registry()
        registry.register_service(
            "market_data_service",
            host="localhost",
            port=8000,
            health_check_url="http://localhost:8000/health"
        )
        
        # Set metrics for use in methods
        self.metrics = metrics
        
        # Start heartbeat thread
        def heartbeat_loop():
            while self._running:
                try:
                    registry.heartbeat("market_data_service")
                except Exception as e:
                    logger.error(f"Error sending heartbeat: {e}")
                for _ in range(30):  # Heartbeat every 30 seconds
                    if not self._running:
                        break
                    time.sleep(1)
        
        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True, name="heartbeat-thread")
        heartbeat_thread.start()
        self.heartbeat_thread = heartbeat_thread  # Keep reference for cleanup
        
        # Register shutdown handler
        def shutdown_handler():
            logger.info("Shutting down Market Data Service...")
            self._running = False
            
            # Wait for heartbeat thread to finish (with timeout)
            if hasattr(self, 'heartbeat_thread') and self.heartbeat_thread.is_alive():
                logger.info("Waiting for heartbeat thread to finish...")
                self.heartbeat_thread.join(timeout=2.0)
                if self.heartbeat_thread.is_alive():
                    logger.warning("Heartbeat thread did not finish within timeout")
            
            registry.unregister_service("market_data_service")
            if self.session:
                self.session.close()
        
        register_shutdown_handler(shutdown_handler)
        
        while self._running:
            try:
                self.fetch_and_store_all()
                # Run every 5 minutes
                for _ in range(300):  # Check _running every second
                    if not self._running:
                        break
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Service stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in service loop: {e}")
                if self._running:
                    time.sleep(60)  # Wait 1 minute before retry
        
        logger.info("Market Data Service stopped")


if __name__ == "__main__":
    service = MarketDataService()
    service.run()

