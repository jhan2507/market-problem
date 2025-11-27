"""
Shared pytest fixtures and configuration.
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Generator
import os

# Set test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["MONGODB_URI"] = "mongodb://test:test@localhost:27017/test"
os.environ["MONGODB_DB"] = "test"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB client."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__ = Mock(return_value=mock_collection)
    return mock_db


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    mock_redis.xadd.return_value = "test-id"
    mock_redis.xreadgroup.return_value = []
    mock_redis.xack.return_value = 1
    return mock_redis


@pytest.fixture
def mock_requests_session():
    """Mock requests session."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response
    mock_session.post.return_value = mock_response
    return mock_session


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        "timestamp": "2024-01-01T00:00:00Z",
        "prices": {
            "BTCUSDT": 50000.0,
            "ETHUSDT": 3000.0
        },
        "candlesticks": {
            "BTCUSDT": {
                "1h": [
                    {
                        "timestamp": "2024-01-01T00:00:00Z",
                        "open": 50000.0,
                        "high": 50100.0,
                        "low": 49900.0,
                        "close": 50050.0,
                        "volume": 1000.0
                    }
                ]
            }
        },
        "market_metrics": {
            "btc_dominance": 50.0,
            "usdt_dominance": 5.0,
            "total_market_cap": 1000000000000
        }
    }


@pytest.fixture
def sample_analysis():
    """Sample analysis data for testing."""
    return {
        "timestamp": "2024-01-01T00:00:00Z",
        "symbol_analyses": {
            "BTCUSDT": {
                "1h": {
                    "dow": {"trend": "bullish"},
                    "wyckoff": {"phase": "MARKUP"},
                    "indicators": {
                        "rsi": 55.0,
                        "macd": {"histogram": 10.0},
                        "ema20": 50000.0,
                        "ema50": 49000.0
                    }
                }
            }
        },
        "dominance_analysis": {
            "btc_dominance": 50.0,
            "usdt_dominance": 5.0
        },
        "sentiment": "bullish",
        "trend_strength": 75
    }


@pytest.fixture
def sample_signal():
    """Sample signal data for testing."""
    return {
        "signal_id": "test-signal-id",
        "timestamp": "2024-01-01T00:00:00Z",
        "asset": "BTCUSDT",
        "type": "LONG",
        "score": 80,
        "confidence": "HIGH",
        "entry_range": {
            "min": 50000.0,
            "max": 50100.0
        },
        "take_profit": [51000.0, 52000.0],
        "stop_loss": 49000.0,
        "reasons": {
            "trend": ["Primary trend alignment"],
            "wyckoff": ["SOS detected"],
            "indicators": ["RSI > 50", "MACD bullish"]
        }
    }

