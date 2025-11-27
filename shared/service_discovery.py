"""
Service Discovery implementation using Redis.
"""

import logging
import json
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from shared.events import get_redis_client
from shared.health import HealthChecker

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Service registry for service discovery."""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.registry_key = "service_registry"
        self.health_check_interval = 30  # seconds
        self.service_ttl = 60  # seconds
    
    def register_service(
        self,
        service_name: str,
        host: str,
        port: int,
        health_check_url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Register a service with the registry.
        
        Args:
            service_name: Name of the service
            host: Service host
            port: Service port
            health_check_url: Optional health check URL
            metadata: Optional service metadata
        """
        service_data = {
            "name": service_name,
            "host": host,
            "port": port,
            "health_check_url": health_check_url,
            "registered_at": datetime.utcnow().isoformat(),
            "last_heartbeat": datetime.utcnow().isoformat(),
            "healthy": True,
            "metadata": metadata or {}
        }
        
        try:
            key = f"{self.registry_key}:{service_name}"
            self.redis.setex(
                key,
                self.service_ttl,
                json.dumps(service_data)
            )
            logger.info(f"Registered service: {service_name} at {host}:{port}")
        except Exception as e:
            logger.error(f"Error registering service {service_name}: {e}")
    
    def unregister_service(self, service_name: str):
        """Unregister a service."""
        try:
            key = f"{self.registry_key}:{service_name}"
            self.redis.delete(key)
            logger.info(f"Unregistered service: {service_name}")
        except Exception as e:
            logger.error(f"Error unregistering service {service_name}: {e}")
    
    def heartbeat(self, service_name: str):
        """Update service heartbeat."""
        try:
            key = f"{self.registry_key}:{service_name}"
            service_data = self.get_service(service_name)
            
            if service_data:
                service_data["last_heartbeat"] = datetime.utcnow().isoformat()
                self.redis.setex(
                    key,
                    self.service_ttl,
                    json.dumps(service_data)
                )
        except Exception as e:
            logger.error(f"Error updating heartbeat for {service_name}: {e}")
    
    def get_service(self, service_name: str) -> Optional[Dict]:
        """
        Get service information.
        
        Args:
            service_name: Name of the service
        
        Returns:
            Service data or None
        """
        try:
            key = f"{self.registry_key}:{service_name}"
            data = self.redis.get(key)
            
            if data:
                service_data = json.loads(data)
                
                # Check if service is still healthy
                if service_data.get("health_check_url"):
                    service_data["healthy"] = self._check_health(service_data["health_check_url"])
                
                return service_data
            return None
        except Exception as e:
            logger.error(f"Error getting service {service_name}: {e}")
            return None
    
    def list_services(self) -> List[Dict]:
        """List all registered services."""
        try:
            pattern = f"{self.registry_key}:*"
            keys = self.redis.keys(pattern)
            
            services = []
            for key in keys:
                data = self.redis.get(key)
                if data:
                    service_data = json.loads(data)
                    
                    # Check health
                    if service_data.get("health_check_url"):
                        service_data["healthy"] = self._check_health(service_data["health_check_url"])
                    
                    services.append(service_data)
            
            return services
        except Exception as e:
            logger.error(f"Error listing services: {e}")
            return []
    
    def _check_health(self, health_check_url: str) -> bool:
        """Check service health."""
        try:
            import requests
            response = requests.get(health_check_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def discover_service(self, service_name: str) -> Optional[str]:
        """
        Discover service URL.
        
        Args:
            service_name: Name of the service
        
        Returns:
            Service URL or None
        """
        service = self.get_service(service_name)
        if service and service.get("healthy"):
            return f"http://{service['host']}:{service['port']}"
        return None


# Global service registry instance
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get global service registry instance."""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry

