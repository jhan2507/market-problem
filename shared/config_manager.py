"""
Centralized configuration management.
"""

import os
import logging
from typing import Dict, Any, Optional
from shared.secrets import get_secret

logger = logging.getLogger(__name__)


class ConfigManager:
    """Centralized configuration manager."""
    
    def __init__(self, env: str = None):
        """
        Initialize config manager.
        
        Args:
            env: Environment name (development, staging, production)
        """
        self.env = env or os.getenv("ENVIRONMENT", "development")
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment and defaults."""
        # Base config
        self._config = {
            "environment": self.env,
            "mongodb": {
                "uri": os.getenv("MONGODB_URI", "mongodb://admin:password@localhost:27017/market?authSource=admin"),
                "db": os.getenv("MONGODB_DB", "market"),
                "max_pool_size": int(os.getenv("MONGODB_MAX_POOL_SIZE", 100)),
                "min_pool_size": int(os.getenv("MONGODB_MIN_POOL_SIZE", 10)),
                "max_idle_time_ms": int(os.getenv("MONGODB_MAX_IDLE_TIME_MS", 45000)),
                "connect_timeout_ms": int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", 10000)),
                "server_selection_timeout_ms": int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", 5000))
            },
            "redis": {
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": int(os.getenv("REDIS_PORT", 6379)),
                "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", 50)),
                "socket_connect_timeout": int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", 5)),
                "socket_timeout": int(os.getenv("REDIS_SOCKET_TIMEOUT", 5)),
                "socket_keepalive": os.getenv("REDIS_SOCKET_KEEPALIVE", "true").lower() == "true",
                "socket_keepalive_options": {}
            },
            "binance": {
                "api_url": os.getenv("BINANCE_API_URL", "https://api.binance.com")
            },
            "coinmarketcap": {
                "api_key": get_secret("CMC_API_KEY", os.getenv("CMC_API_KEY", ""))
            },
            "telegram": {
                "bot_token": get_secret("TELEGRAM_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN", "")),
                "price_chat_id": os.getenv("TELEGRAM_PRICE_CHAT_ID", ""),
                "signal_chat_id": os.getenv("TELEGRAM_SIGNAL_CHAT_ID", "")
            },
            "coins": [coin.strip() for coin in os.getenv("COINS", "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT").split(",") if coin.strip()],
            "timeframes": ["1m", "15m", "1h", "4h", "8h", "1d", "3d", "1w"],
            "logging": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "format": os.getenv("LOG_FORMAT", "json")  # json or text
            },
            "observability": {
                "metrics_enabled": os.getenv("METRICS_ENABLED", "true").lower() == "true",
                "tracing_enabled": os.getenv("TRACING_ENABLED", "true").lower() == "true",
                "jaeger_endpoint": os.getenv("JAEGER_ENDPOINT", None)
            },
            "resilience": {
                "circuit_breaker": {
                    "failure_threshold": int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", 5)),
                    "recovery_timeout": int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", 60))
                },
                "retry": {
                    "max_attempts": int(os.getenv("RETRY_MAX_ATTEMPTS", 3)),
                    "initial_delay": float(os.getenv("RETRY_INITIAL_DELAY", 1.0))
                },
                "timeout": {
                    "default": float(os.getenv("DEFAULT_TIMEOUT", 10.0))
                }
            },
            # Collections (database collection names)
            "collections": {
                "market_data": "market_data",
                "analysis": "analysis",
                "signals": "signals",
                "price_updates": "price_updates",
                "logs": "logs"
            },
            # Event names
            "events": {
                "market_data_updated": "market_data_updated",
                "market_analysis_completed": "market_analysis_completed",
                "price_update_ready": "price_update_ready",
                "signal_generated": "signal_generated"
            },
            # Signal thresholds
            "signal": {
                "score_high": 75,
                "score_medium": 60,
                "score_min": 60
            },
            # Retry configuration (legacy support)
            "retry_config": {
                "max_retries": 3,
                "retry_delay": 2
            }
        }
        
        # Environment-specific overrides
        if self.env == "production":
            self._config["logging"]["level"] = "INFO"
            self._config["observability"]["metrics_enabled"] = True
        elif self.env == "staging":
            self._config["logging"]["level"] = "DEBUG"
            self._config["observability"]["metrics_enabled"] = True
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get config value using dot notation.
        
        Args:
            key: Config key (e.g., "mongodb.uri")
            default: Default value
        
        Returns:
            Config value
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """
        Set config value using dot notation.
        
        Args:
            key: Config key
            value: Config value
        """
        keys = key.split(".")
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def reload(self):
        """Reload configuration."""
        self._load_config()
        logger.info("Configuration reloaded")


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(env: str = None) -> ConfigManager:
    """Get global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(env)
    return _config_manager


def get_config(key: str, default: Any = None) -> Any:
    """Get config value using global config manager."""
    return get_config_manager().get(key, default)


# Convenience functions for backward compatibility
def get_collection(name: str) -> str:
    """Get collection name."""
    return get_config(f"collections.{name}", name)


def get_event_name(name: str) -> str:
    """Get event name."""
    return get_config(f"events.{name}", name)


# Module-level constants for backward compatibility (using ConfigManager)
def _get_constants():
    """Get all constants from config manager."""
    cm = get_config_manager()
    return {
        # MongoDB
        "MONGODB_URI": cm.get("mongodb.uri"),
        "MONGODB_DB": cm.get("mongodb.db"),
        # Redis
        "REDIS_HOST": cm.get("redis.host"),
        "REDIS_PORT": cm.get("redis.port"),
        # Binance
        "BINANCE_API_URL": cm.get("binance.api_url"),
        # CoinMarketCap
        "CMC_API_KEY": cm.get("coinmarketcap.api_key"),
        # Telegram
        "TELEGRAM_BOT_TOKEN": cm.get("telegram.bot_token"),
        "TELEGRAM_PRICE_CHAT_ID": cm.get("telegram.price_chat_id"),
        "TELEGRAM_SIGNAL_CHAT_ID": cm.get("telegram.signal_chat_id"),
        # Coins and timeframes
        "COINS": cm.get("coins"),
        "TIMEFRAMES": cm.get("timeframes"),
        # Collections
        "COLLECTION_MARKET_DATA": cm.get("collections.market_data"),
        "COLLECTION_ANALYSIS": cm.get("collections.analysis"),
        "COLLECTION_SIGNALS": cm.get("collections.signals"),
        "COLLECTION_PRICE_UPDATES": cm.get("collections.price_updates"),
        "COLLECTION_LOGS": cm.get("collections.logs"),
        # Events
        "EVENT_MARKET_DATA_UPDATED": cm.get("events.market_data_updated"),
        "EVENT_MARKET_ANALYSIS_COMPLETED": cm.get("events.market_analysis_completed"),
        "EVENT_PRICE_UPDATE_READY": cm.get("events.price_update_ready"),
        "EVENT_SIGNAL_GENERATED": cm.get("events.signal_generated"),
        # Signal thresholds
        "SIGNAL_SCORE_HIGH": cm.get("signal.score_high"),
        "SIGNAL_SCORE_MEDIUM": cm.get("signal.score_medium"),
        "SIGNAL_SCORE_MIN": cm.get("signal.score_min"),
        # Retry config
        "MAX_RETRIES": cm.get("retry_config.max_retries"),
        "RETRY_DELAY": cm.get("retry_config.retry_delay"),
    }


# Export constants for backward compatibility
_constants = _get_constants()
MONGODB_URI = _constants["MONGODB_URI"]
MONGODB_DB = _constants["MONGODB_DB"]
REDIS_HOST = _constants["REDIS_HOST"]
REDIS_PORT = _constants["REDIS_PORT"]
BINANCE_API_URL = _constants["BINANCE_API_URL"]
CMC_API_KEY = _constants["CMC_API_KEY"]
TELEGRAM_BOT_TOKEN = _constants["TELEGRAM_BOT_TOKEN"]
TELEGRAM_PRICE_CHAT_ID = _constants["TELEGRAM_PRICE_CHAT_ID"]
TELEGRAM_SIGNAL_CHAT_ID = _constants["TELEGRAM_SIGNAL_CHAT_ID"]
COINS = _constants["COINS"]
TIMEFRAMES = _constants["TIMEFRAMES"]
COLLECTION_MARKET_DATA = _constants["COLLECTION_MARKET_DATA"]
COLLECTION_ANALYSIS = _constants["COLLECTION_ANALYSIS"]
COLLECTION_SIGNALS = _constants["COLLECTION_SIGNALS"]
COLLECTION_PRICE_UPDATES = _constants["COLLECTION_PRICE_UPDATES"]
COLLECTION_LOGS = _constants["COLLECTION_LOGS"]
EVENT_MARKET_DATA_UPDATED = _constants["EVENT_MARKET_DATA_UPDATED"]
EVENT_MARKET_ANALYSIS_COMPLETED = _constants["EVENT_MARKET_ANALYSIS_COMPLETED"]
EVENT_PRICE_UPDATE_READY = _constants["EVENT_PRICE_UPDATE_READY"]
EVENT_SIGNAL_GENERATED = _constants["EVENT_SIGNAL_GENERATED"]
SIGNAL_SCORE_HIGH = _constants["SIGNAL_SCORE_HIGH"]
SIGNAL_SCORE_MEDIUM = _constants["SIGNAL_SCORE_MEDIUM"]
SIGNAL_SCORE_MIN = _constants["SIGNAL_SCORE_MIN"]
MAX_RETRIES = _constants["MAX_RETRIES"]
RETRY_DELAY = _constants["RETRY_DELAY"]

