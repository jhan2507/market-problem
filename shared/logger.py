"""
Logging configuration for all microservices.
"""

import logging
import sys
import uuid
from datetime import datetime
from contextvars import ContextVar
from shared.database import get_database
from shared.config_manager import COLLECTION_LOGS

# Context variable for correlation ID
correlation_id: ContextVar[str] = ContextVar('correlation_id', default=None)


class CorrelationIDFilter(logging.Filter):
    """Filter to add correlation ID to log records."""
    
    def filter(self, record):
        corr_id = correlation_id.get()
        if corr_id:
            record.correlation_id = corr_id
        else:
            record.correlation_id = "N/A"
        return True


def setup_logger(service_name: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    Setup logger for a microservice with structured logging.
    
    Args:
        service_name: Name of the service
        log_level: Logging level
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(log_level)
    
    # Console handler with structured format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Add correlation ID filter
    correlation_filter = CorrelationIDFilter()
    console_handler.addFilter(correlation_filter)
    
    formatter = logging.Formatter(
        f'%(asctime)s - {service_name} - [%(correlation_id)s] - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # MongoDB handler (optional, for persistent logging)
    try:
        db = get_database()
        mongo_handler = MongoDBHandler(db[COLLECTION_LOGS], service_name)
        mongo_handler.setLevel(logging.WARNING)  # Only log warnings and errors to DB
        mongo_handler.addFilter(correlation_filter)
        logger.addHandler(mongo_handler)
    except Exception as e:
        logger.warning(f"Could not setup MongoDB logging: {e}")
    
    return logger


def set_correlation_id(corr_id: str = None):
    """Set correlation ID for current context."""
    if corr_id is None:
        corr_id = str(uuid.uuid4())
    correlation_id.set(corr_id)
    return corr_id


def get_correlation_id() -> str:
    """Get current correlation ID."""
    return correlation_id.get() or str(uuid.uuid4())


class MongoDBHandler(logging.Handler):
    """Custom logging handler that writes to MongoDB."""
    
    def __init__(self, collection, service_name: str):
        super().__init__()
        self.collection = collection
        self.service_name = service_name
    
    def emit(self, record):
        try:
            log_entry = {
                "timestamp": datetime.utcnow(),
                "service": self.service_name,
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "correlation_id": getattr(record, 'correlation_id', 'N/A')
            }
            if record.exc_info:
                log_entry["exception"] = self.format(record)
            self.collection.insert_one(log_entry)
        except Exception:
            pass  # Don't fail if logging fails

