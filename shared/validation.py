"""
Input validation for events and API requests.
"""

import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, ValidationError, Field
from datetime import datetime

logger = logging.getLogger(__name__)


class EventSchema(BaseModel):
    """Base schema for events."""
    timestamp: str
    correlation_id: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow additional fields


class PriceUpdateEventSchema(EventSchema):
    """Schema for price_update_ready event."""
    prices: Dict[str, float]
    volatilities: List[Dict[str, Any]] = []
    has_volatility: bool = False


class SignalGeneratedEventSchema(EventSchema):
    """Schema for signal_generated event."""
    signal_id: str
    asset: str
    type: str = Field(..., pattern="^(LONG|SHORT)$")
    score: int = Field(..., ge=0, le=100)
    confidence: str = Field(..., pattern="^(HIGH|MEDIUM|LOW)$")


class MarketDataUpdatedEventSchema(EventSchema):
    """Schema for market_data_updated event."""
    coins: List[str]
    has_candlesticks: bool
    has_metrics: bool


class MarketAnalysisCompletedEventSchema(EventSchema):
    """Schema for market_analysis_completed event."""
    sentiment: str = Field(..., pattern="^(bullish|bearish|neutral)$")
    trend_strength: int = Field(..., ge=0, le=100)
    symbols_analyzed: List[str]


# Event schema mapping
EVENT_SCHEMAS = {
    "price_update_ready": PriceUpdateEventSchema,
    "signal_generated": SignalGeneratedEventSchema,
    "market_data_updated": MarketDataUpdatedEventSchema,
    "market_analysis_completed": MarketAnalysisCompletedEventSchema
}


def validate_event(event_name: str, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate event data against schema.
    
    Args:
        event_name: Name of the event
        data: Event data dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if event_name not in EVENT_SCHEMAS:
        logger.warning(f"No schema defined for event: {event_name}")
        return True, None  # Allow unknown events
    
    schema_class = EVENT_SCHEMAS[event_name]
    
    try:
        schema_class(**data)
        return True, None
    except ValidationError as e:
        error_msg = f"Validation error for event {event_name}: {e}"
        logger.error(error_msg)
        return False, error_msg


def validate_and_clean_event(event_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean event data.
    
    Args:
        event_name: Name of the event
        data: Event data dictionary
    
    Returns:
        Cleaned and validated data
    
    Raises:
        ValidationError: If validation fails
    """
    is_valid, error_msg = validate_event(event_name, data)
    if not is_valid:
        raise ValidationError(error_msg)
    
    # Return validated data
    if event_name in EVENT_SCHEMAS:
        schema_class = EVENT_SCHEMAS[event_name]
        validated = schema_class(**data)
        return validated.dict()
    
    return data

