"""
Health check utilities for microservices.
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from shared.database import get_database, get_client
from shared.events import get_redis_client

logger = logging.getLogger(__name__)


class HealthChecker:
    """Health check manager for services."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.start_time = datetime.utcnow()
        self._db_healthy = None
        self._redis_healthy = None
    
    def check_database(self) -> bool:
        """Check MongoDB connection health."""
        try:
            client = get_client()
            if client:
                client.admin.command('ping')
                self._db_healthy = True
                return True
            else:
                # Fallback: try through database object
                db = get_database()
                db.client.admin.command('ping')
                self._db_healthy = True
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            self._db_healthy = False
            return False
    
    def check_redis(self) -> bool:
        """Check Redis connection health."""
        try:
            client = get_redis_client()
            client.ping()
            self._redis_healthy = True
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            self._redis_healthy = False
            return False
    
    def check_service_specific(self) -> Dict[str, bool]:
        """Override this method in service-specific health checkers."""
        return {}
    
    def is_healthy(self) -> bool:
        """Check if service is healthy (all dependencies OK)."""
        db_ok = self.check_database()
        redis_ok = self.check_redis()
        service_ok = all(self.check_service_specific().values())
        return db_ok and redis_ok and service_ok
    
    def is_ready(self) -> bool:
        """Check if service is ready to accept traffic."""
        # Ready if database and redis are connected
        db_ok = self.check_database()
        redis_ok = self.check_redis()
        return db_ok and redis_ok
    
    def get_status(self) -> Dict:
        """Get detailed health status."""
        db_status = self.check_database()
        redis_status = self.check_redis()
        service_status = self.check_service_specific()
        
        overall_healthy = db_status and redis_status and all(service_status.values())
        
        return {
            "service": self.service_name,
            "status": "healthy" if overall_healthy else "unhealthy",
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "checks": {
                "database": {
                    "status": "healthy" if db_status else "unhealthy",
                    "last_check": datetime.utcnow().isoformat()
                },
                "redis": {
                    "status": "healthy" if redis_status else "unhealthy",
                    "last_check": datetime.utcnow().isoformat()
                },
                **{k: {"status": "healthy" if v else "unhealthy"} 
                   for k, v in service_status.items()}
            },
            "timestamp": datetime.utcnow().isoformat()
        }

