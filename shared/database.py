"""
MongoDB database client for all microservices.
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, PyMongoError
import logging
from typing import Optional
from shared.config_manager import MONGODB_URI, MONGODB_DB, get_config_manager
from shared.exceptions import DatabaseError

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None
_db = None


def get_database():
    """Get MongoDB database instance with connection pooling."""
    global _client, _db
    
    if _db is not None:
        return _db
    
    try:
        config = get_config_manager()
        
        # Connection pool configuration
        max_pool_size = config.get("mongodb.max_pool_size", 100)
        min_pool_size = config.get("mongodb.min_pool_size", 10)
        max_idle_time_ms = config.get("mongodb.max_idle_time_ms", 45000)  # 45 seconds
        connect_timeout_ms = config.get("mongodb.connect_timeout_ms", 10000)  # 10 seconds
        server_selection_timeout_ms = config.get("mongodb.server_selection_timeout_ms", 5000)  # 5 seconds
        
        _client = MongoClient(
            MONGODB_URI,
            maxPoolSize=max_pool_size,
            minPoolSize=min_pool_size,
            maxIdleTimeMS=max_idle_time_ms,
            connectTimeoutMS=connect_timeout_ms,
            serverSelectionTimeoutMS=server_selection_timeout_ms,
            retryWrites=True,
            retryReads=True,
            # Heartbeat settings for better connection health
            heartbeatFrequencyMS=10000,  # 10 seconds
        )
        # Test connection
        _client.admin.command('ping')
        _db = _client[MONGODB_DB]
        logger.info(
            f"Connected to MongoDB successfully "
            f"(pool_size: {min_pool_size}-{max_pool_size}, max_idle: {max_idle_time_ms}ms)"
        )
        return _db
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error = DatabaseError(
            f"Failed to connect to MongoDB: {e}",
            operation="connect",
            collection=None
        )
        logger.error(str(error))
        raise error
    except PyMongoError as e:
        error = DatabaseError(
            f"MongoDB error: {e}",
            operation="connect",
            collection=None
        )
        logger.error(str(error))
        raise error


def get_client():
    """Get MongoDB client instance."""
    global _client
    # Ensure database is initialized (which also initializes client)
    if _client is None:
        get_database()  # This will initialize both _client and _db
    return _client


def close_database():
    """Close MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")

