"""
Timeout management utilities.
"""

import signal
import logging
import threading
from typing import Callable, Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Exception raised when operation times out."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Operation timed out")


def with_timeout(seconds: float):
    """
    Decorator to add timeout to function calls.
    
    Note: This uses signal which only works on main thread on Unix systems.
    For cross-platform, use threading-based timeout.
    
    Args:
        seconds: Timeout in seconds
    
    Usage:
        @with_timeout(5.0)
        def slow_operation():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Set signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(seconds))
            
            try:
                result = func(*args, **kwargs)
            finally:
                # Restore old handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            return result
        return wrapper
    return decorator


def timeout_thread(target: Callable, timeout: float, *args, **kwargs) -> Any:
    """
    Execute function with timeout using threading (cross-platform).
    
    Args:
        target: Function to execute
        timeout: Timeout in seconds
        *args: Function arguments
        **kwargs: Function keyword arguments
    
    Returns:
        Function result
    
    Raises:
        TimeoutError: If function exceeds timeout
    """
    result = [None]
    exception = [None]
    
    def target_wrapper():
        try:
            result[0] = target(*args, **kwargs)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target_wrapper)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        logger.warning(f"Function {target.__name__} timed out after {timeout} seconds")
        raise TimeoutError(f"Operation timed out after {timeout} seconds")
    
    if exception[0]:
        raise exception[0]
    
    return result[0]


class TimeoutContext:
    """Context manager for timeout operations."""
    
    def __init__(self, timeout: float):
        self.timeout = timeout
        self.timer: Optional[threading.Timer] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer:
            self.timer.cancel()
        return False
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with timeout."""
        return timeout_thread(func, self.timeout, *args, **kwargs)

