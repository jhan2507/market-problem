"""
Base service class for all microservices.
Provides common initialization, health checks, metrics, and lifecycle management.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Callable

from shared.logger import setup_logger
from shared.metrics import MetricsCollector
from shared.tracing import setup_tracing
from shared.health import HealthChecker
from shared.http_server import ServiceHTTPServer
from shared.shutdown import register_shutdown_handler
from shared.service_discovery import get_service_registry

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Abstract base class for all microservices."""
    
    def __init__(self, service_name: str, port: int):
        """
        Initialize base service.
        
        Args:
            service_name: Name of the service
            port: HTTP port for the service
        """
        self.service_name = service_name
        self.port = port
        self.logger = setup_logger(service_name)
        self._running = False
        
        # Will be initialized in run()
        self.metrics: Optional[MetricsCollector] = None
        self.health_checker: Optional[HealthChecker] = None
        self.http_server: Optional[ServiceHTTPServer] = None
        self.registry = get_service_registry()
    
    def _setup_observability(self):
        """Setup observability (tracing and metrics)."""
        # Setup tracing
        setup_tracing(self.service_name)
        
        # Setup metrics
        self.metrics = MetricsCollector(self.service_name)
    
    def _setup_health_and_http(self):
        """Setup health checker and HTTP server."""
        self.health_checker = HealthChecker(self.service_name)
        self.http_server = ServiceHTTPServer(
            self.service_name,
            port=self.port,
            health_checker=self.health_checker,
            metrics_collector=self.metrics
        )
        self.http_server.start()
    
    def _register_service_discovery(self):
        """Register service with service discovery."""
        self.registry.register_service(
            self.service_name,
            host="localhost",
            port=self.port,
            health_check_url=f"http://localhost:{self.port}/health"
        )
    
    def _register_shutdown_handler(self):
        """Register shutdown handler."""
        def shutdown_handler():
            self.logger.info(f"Shutting down {self.service_name}...")
            self._running = False
            self.registry.unregister_service(self.service_name)
            self.on_shutdown()
        
        register_shutdown_handler(shutdown_handler)
    
    def on_shutdown(self):
        """
        Called during shutdown. Override in subclasses for custom cleanup.
        """
        pass
    
    def setup(self):
        """
        Setup service (observability, health, service discovery).
        Call this in custom run() implementations for event-driven services.
        """
        # Setup observability
        self._setup_observability()
        
        # Setup health and HTTP server
        self._setup_health_and_http()
        
        # Register with service discovery
        self._register_service_discovery()
        
        # Register shutdown handler
        self._register_shutdown_handler()
    
    def run_cycle(self):
        """
        Execute one cycle of the service's main work.
        Override this for polling-based services.
        """
        raise NotImplementedError("Service must implement run_cycle() or override run()")
    
    def get_cycle_interval(self) -> int:
        """
        Get the interval between cycles in seconds.
        Override this for polling-based services.
        
        Returns:
            Interval in seconds
        """
        return 60  # Default: 1 minute
    
    def run(self):
        """
        Main service loop.
        Override this for event-driven services, or use default polling pattern.
        """
        self.logger.info(f"{self.service_name} started")
        self._running = True
        
        try:
            # Setup service
            self.setup()
            
            # Main service loop (polling pattern)
            while self._running:
                try:
                    self.run_cycle()
                    
                    # Wait for next cycle, checking _running periodically
                    interval = self.get_cycle_interval()
                    for _ in range(interval):
                        if not self._running:
                            break
                        time.sleep(1)
                        
                except KeyboardInterrupt:
                    self.logger.info("Service stopped by user")
                    break
                except Exception as e:
                    self.logger.error(f"Error in service loop: {e}", exc_info=True)
                    if self._running:
                        # Wait before retrying
                        time.sleep(60)
        
        finally:
            self.logger.info(f"{self.service_name} stopped")
    
    def stop(self):
        """Stop the service."""
        self._running = False

