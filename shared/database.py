"""
MongoDB database client for all microservices.
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from typing import Optional
from shared.config import MONGODB_URI, MONGODB_DB

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None
_db = None


def get_database():
    """Get MongoDB database instance."""
    global _client, _db
    
    if _db is not None:
        return _db
    
    try:
        _client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            retryWrites=True,
            retryReads=True
        )
        # Test connection
        _client.admin.command('ping')
        _db = _client[MONGODB_DB]
        logger.info("Connected to MongoDB successfully")
        return _db
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


def close_database():
    """Close MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")

