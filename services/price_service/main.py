"""
Price Service

Responsibilities:
- Fetch live prices every 60 seconds
- Create readable price message
- Detect short-term volatility:
  - Coins pumping/dumping in 5–15 minutes
  - BTC >0.5% movement in 15m
- Publish price_update_ready events
"""

import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from shared.logger import setup_logger, set_correlation_id
from shared.database import get_database
from shared.events import publish_event
from shared.health import HealthChecker
from shared.http_server import ServiceHTTPServer
from shared.shutdown import get_shutdown_manager, register_shutdown_handler
from shared.metrics import MetricsCollector
from shared.tracing import setup_tracing, get_tracer
from shared.service_discovery import get_service_registry
from shared.config_manager import (
    BINANCE_API_URL, COINS,
    COLLECTION_PRICE_UPDATES, EVENT_PRICE_UPDATE_READY
)

logger = setup_logger("price_service")


class PriceService:
    """Service for monitoring live prices and detecting volatility."""
    
    def __init__(self):
        self.db = get_database()
        self.collection = self.db[COLLECTION_PRICE_UPDATES]
        self.session = requests.Session()
        self._running = True
        self.metrics = None
        
        # Store price history for volatility detection
        self.price_history = defaultdict(list)  # symbol -> [(timestamp, price), ...]
    
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
    
    def detect_volatility(self, symbol: str, current_price: float, 
                         current_time: datetime) -> Optional[Dict]:
        """
        Detect short-term volatility.
        
        Returns volatility alert if detected, None otherwise.
        """
        history = self.price_history[symbol]
        
        # Keep only last 15 minutes
        cutoff_time = current_time - timedelta(minutes=15)
        history = [(ts, price) for ts, price in history if ts >= cutoff_time]
        self.price_history[symbol] = history
        
        if len(history) < 2:
            return None
        
        # Check 5-minute change
        five_min_ago = current_time - timedelta(minutes=5)
        prices_5m = [price for ts, price in history if ts >= five_min_ago]
        
        if len(prices_5m) >= 2:
            change_5m = ((current_price - prices_5m[0]) / prices_5m[0]) * 100
            if abs(change_5m) >= 3.0:  # 3% change in 5 minutes
                return {
                    "type": "pump" if change_5m > 0 else "dump",
                    "symbol": symbol,
                    "change_5m": change_5m,
                    "timeframe": "5m"
                }
        
        # Check 15-minute change
        prices_15m = history
        if len(prices_15m) >= 2:
            change_15m = ((current_price - prices_15m[0][1]) / prices_15m[0][1]) * 100
            
            # Special check for BTC: >0.5% in 15m
            if symbol == "BTCUSDT" and abs(change_15m) >= 0.5:
                return {
                    "type": "btc_movement",
                    "symbol": symbol,
                    "change_15m": change_15m,
                    "timeframe": "15m"
                }
            
            # Other coins: >5% in 15m
            if symbol != "BTCUSDT" and abs(change_15m) >= 5.0:
                return {
                    "type": "pump" if change_15m > 0 else "dump",
                    "symbol": symbol,
                    "change_15m": change_15m,
                    "timeframe": "15m"
                }
        
        return None
    
    def create_price_message(self, prices: Dict[str, float]) -> str:
        """Create price message in format BTC:xxx|ETH:xxx|..."""
        price_parts = []
        for symbol, price in prices.items():
            # Format symbol (remove USDT)
            coin_name = symbol.replace("USDT", "")
            # Format as COIN:price (no $, no commas)
            price_parts.append(f"{coin_name}:{price:.2f}")
        
        return "|".join(price_parts)
    
    def fetch_and_process_prices(self):
        """Fetch all prices and process."""
        logger.info("Fetching live prices")
        
        current_time = datetime.utcnow()
        prices = {}
        volatilities = []
        
        # Fetch prices for all coins
        for symbol in COINS:
            price = self.fetch_price(symbol)
            if price:
                prices[symbol] = price
                
                # Update history
                self.price_history[symbol].append((current_time, price))
                
                # Detect volatility
                volatility = self.detect_volatility(symbol, price, current_time)
                if volatility:
                    volatilities.append(volatility)
                    logger.info(f"Volatility detected for {symbol}: {volatility}")
        
        if not prices:
            logger.warning("No prices fetched")
            return
        
        # Create price message
        price_message = self.create_price_message(prices)
        
        # Store price update
        price_update = {
            "timestamp": current_time,
            "prices": prices,
            "volatilities": volatilities,
            "message": price_message
        }
        
        try:
            self.collection.insert_one(price_update)
            logger.info("Price update stored")
            
            # Publish event
            event_data = {
                "timestamp": current_time.isoformat(),
                "prices": prices,
                "volatilities": volatilities,
                "has_volatility": len(volatilities) > 0
            }
            publish_event(EVENT_PRICE_UPDATE_READY, event_data, service_name="price_service")
            if self.metrics:
                self.metrics.record_event_published(EVENT_PRICE_UPDATE_READY)
            logger.info("Published price_update_ready event")
        except Exception as e:
            logger.error(f"Error storing price update: {e}")
    
    def run(self):
        """Main service loop."""
        logger.info("Price Service started")
        
        # Setup tracing
        setup_tracing("price_service")
        
        # Setup metrics
        metrics = MetricsCollector("price_service")
        self.metrics = metrics
        
        # Setup health checker and HTTP server
        health_checker = HealthChecker("price_service")
        http_server = ServiceHTTPServer("price_service", port=8002, health_checker=health_checker, metrics_collector=metrics)
        http_server.start()
        
        # Register with service discovery
        registry = get_service_registry()
        registry.register_service(
            "price_service",
            host="localhost",
            port=8002,
            health_check_url="http://localhost:8002/health"
        )
        
        # Register shutdown handler
        def shutdown_handler():
            logger.info("Shutting down Price Service...")
            self._running = False
            registry.unregister_service("price_service")
            if self.session:
                self.session.close()
        
        register_shutdown_handler(shutdown_handler)
        
        while self._running:
            try:
                self.fetch_and_process_prices()
                # Run every 60 seconds
                for _ in range(60):  # Check _running every second
                    if not self._running:
                        break
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Service stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in service loop: {e}")
                if self._running:
                    time.sleep(60)
        
        logger.info("Price Service stopped")


if __name__ == "__main__":
    service = PriceService()
    service.run()

