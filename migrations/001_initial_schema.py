"""
Initial database schema migration.
Creates indexes for better query performance.
"""

import logging
from shared.database import get_database

logger = logging.getLogger(__name__)


def up():
    """Apply migration."""
    db = get_database()
    
    # Create indexes for market_data collection
    market_data = db["market_data"]
    market_data.create_index("timestamp", background=True)
    market_data.create_index([("timestamp", -1)], background=True)
    
    # Create indexes for analysis collection
    analysis = db["analysis"]
    analysis.create_index("timestamp", background=True)
    analysis.create_index([("timestamp", -1)], background=True)
    analysis.create_index("sentiment", background=True)
    
    # Create indexes for signals collection
    signals = db["signals"]
    signals.create_index("timestamp", background=True)
    signals.create_index([("timestamp", -1)], background=True)
    signals.create_index("asset", background=True)
    signals.create_index("type", background=True)
    signals.create_index("score", background=True)
    signals.create_index("signal_id", unique=True, background=True)
    
    # Create indexes for price_updates collection
    price_updates = db["price_updates"]
    price_updates.create_index("timestamp", background=True)
    price_updates.create_index([("timestamp", -1)], background=True)
    
    logger.info("Initial schema migration applied")


def down():
    """Rollback migration."""
    db = get_database()
    
    # Drop indexes (MongoDB will handle this automatically when collections are dropped)
    # For safety, we'll just log
    logger.info("Initial schema migration rolled back (indexes remain)")

