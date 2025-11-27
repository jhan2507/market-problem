"""
Circuit breaker pattern implementation for external API calls.
"""

import logging
import time
from enum import Enum
from typing import Callable, Optional, Any
from circuitbreaker import circuit

from shared.exceptions import CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for protecting external API calls.
    
    Opens circuit after failure_threshold failures within failure_window seconds.
    Attempts recovery after recovery_timeout seconds.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        failure_window: int = 60
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_window = failure_window
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.next_attempt_time = None
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: If function call fails
        """
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if time.time() < self.next_attempt_time:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Next attempt in {self.next_attempt_time - time.time():.1f} seconds"
                )
            else:
                # Try to recover
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
        
        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit breaker '{self.name}' recovered, closing circuit")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        current_time = time.time()
        
        # Reset failure count if outside failure window
        if self.last_failure_time and (current_time - self.last_failure_time) > self.failure_window:
            self.failure_count = 0
        
        self.failure_count += 1
        self.last_failure_time = current_time
        
        if self.state == CircuitState.HALF_OPEN:
            # Failed in half-open, open circuit again
            self.state = CircuitState.OPEN
            self.next_attempt_time = current_time + self.recovery_timeout
            logger.warning(
                f"Circuit breaker '{self.name}' failed in HALF_OPEN, opening circuit. "
                f"Next attempt in {self.recovery_timeout} seconds"
            )
        elif self.failure_count >= self.failure_threshold:
            # Open circuit
            self.state = CircuitState.OPEN
            self.next_attempt_time = current_time + self.recovery_timeout
            logger.error(
                f"Circuit breaker '{self.name}' opened after {self.failure_count} failures. "
                f"Next attempt in {self.recovery_timeout} seconds"
            )


# Global circuit breakers
_circuit_breakers: dict = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception
) -> CircuitBreaker:
    """Get or create a circuit breaker."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception
        )
    return _circuit_breakers[name]


def circuit_breaker_decorator(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception
):
    """
    Decorator for circuit breaker pattern.
    
    Usage:
        @circuit_breaker_decorator("binance_api", failure_threshold=5, recovery_timeout=60)
        def fetch_price(symbol):
            ...
    """
    cb = get_circuit_breaker(name, failure_threshold, recovery_timeout, expected_exception)
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)
        return wrapper
    return decorator

