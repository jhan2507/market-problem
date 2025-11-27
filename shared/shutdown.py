"""
Graceful shutdown handler for microservices.
"""

import signal
import sys
import logging
import threading
from typing import List, Callable, Optional

logger = logging.getLogger(__name__)


class GracefulShutdown:
    """Handle graceful shutdown of services."""
    
    def __init__(self):
        self.shutdown_handlers: List[Callable] = []
        self.is_shutting_down = False
        self._lock = threading.Lock()
    
    def register_handler(self, handler: Callable):
        """Register a shutdown handler."""
        self.shutdown_handlers.append(handler)
    
    def shutdown(self, signum=None, frame=None):
        """Execute all shutdown handlers."""
        with self._lock:
            if self.is_shutting_down:
                logger.warning("Shutdown already in progress")
                return
            
            self.is_shutting_down = True
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        
        # Execute all handlers
        for handler in self.shutdown_handlers:
            try:
                logger.info(f"Executing shutdown handler: {handler.__name__}")
                handler()
            except Exception as e:
                logger.error(f"Error in shutdown handler {handler.__name__}: {e}")
        
        logger.info("Graceful shutdown completed")
        sys.exit(0)
    
    def setup_signal_handlers(self):
        """Setup signal handlers for SIGTERM and SIGINT."""
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        logger.info("Signal handlers registered for SIGTERM and SIGINT")


# Global shutdown manager instance
_shutdown_manager: Optional[GracefulShutdown] = None


def get_shutdown_manager() -> GracefulShutdown:
    """Get global shutdown manager instance."""
    global _shutdown_manager
    if _shutdown_manager is None:
        _shutdown_manager = GracefulShutdown()
        _shutdown_manager.setup_signal_handlers()
    return _shutdown_manager


def register_shutdown_handler(handler: Callable):
    """Register a shutdown handler."""
    get_shutdown_manager().register_handler(handler)

