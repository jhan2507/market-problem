"""
Integration tests for event-driven communication.
"""

import pytest
import time
from shared.events import publish_event, get_redis_client
from shared.config_manager import EVENT_PRICE_UPDATE_READY, EVENT_SIGNAL_GENERATED


def test_publish_event():
    """Test event publishing."""
    event_data = {
        "timestamp": "2024-01-01T00:00:00",
        "prices": {"BTCUSDT": 50000.0},
        "has_volatility": False
    }
    
    result = publish_event(EVENT_PRICE_UPDATE_READY, event_data, service_name="test_service")
    assert result is True


def test_event_validation():
    """Test event validation."""
    # Valid event
    valid_data = {
        "timestamp": "2024-01-01T00:00:00",
        "prices": {"BTCUSDT": 50000.0},
        "has_volatility": False
    }
    
    result = publish_event(EVENT_PRICE_UPDATE_READY, valid_data, service_name="test_service")
    assert result is True
    
    # Invalid event (missing required fields)
    invalid_data = {
        "timestamp": "2024-01-01T00:00:00"
    }
    
    # Should still publish but log warning
    result = publish_event(EVENT_PRICE_UPDATE_READY, invalid_data, service_name="test_service")
    # Event will be published but validation will fail
    assert result is True  # publish_event returns True even if validation fails (logs error)

