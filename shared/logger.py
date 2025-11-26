"""
Logging configuration for all microservices.
"""

import logging
import sys
from datetime import datetime
from shared.database import get_database
from shared.config import COLLECTION_LOGS


def setup_logger(service_name: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    Setup logger for a microservice.
    
    Args:
        service_name: Name of the service
        log_level: Logging level
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    formatter = logging.Formatter(
        f'%(asctime)s - {service_name} - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # MongoDB handler (optional, for persistent logging)
    try:
        db = get_database()
        mongo_handler = MongoDBHandler(db[COLLECTION_LOGS], service_name)
        mongo_handler.setLevel(logging.WARNING)  # Only log warnings and errors to DB
        logger.addHandler(mongo_handler)
    except Exception as e:
        logger.warning(f"Could not setup MongoDB logging: {e}")
    
    return logger


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
                "line": record.lineno
            }
            if record.exc_info:
                log_entry["exception"] = self.format(record)
            self.collection.insert_one(log_entry)
        except Exception:
            pass  # Don't fail if logging fails

