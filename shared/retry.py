"""
Retry utilities with exponential backoff.
"""

import logging
import time
from typing import Callable, Optional, Type, Tuple
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retry_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    before_retry: Optional[Callable] = None
):
    """
    Decorator for retrying with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        retry_exceptions: Tuple of exception types to retry on
        before_retry: Optional callback before retry
    
    Usage:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        def fetch_data():
            ...
    """
    def decorator(func: Callable):
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=initial_delay,
                max=max_delay,
                exp_base=exponential_base
            ),
            retry=retry_if_exception_type(retry_exceptions),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO),
            reraise=True
        )
        def wrapper(*args, **kwargs):
            if before_retry:
                before_retry()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def retry_simple(
    func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Simple retry function (non-decorator version).
    
    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay in seconds
        backoff: Backoff multiplier
        exceptions: Tuple of exception types to retry on
    
    Returns:
        Function result
    
    Raises:
        Last exception if all attempts fail
    """
    attempt = 0
    current_delay = delay
    
    while attempt < max_attempts:
        try:
            return func()
        except exceptions as e:
            attempt += 1
            if attempt >= max_attempts:
                logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
                raise
            
            logger.warning(
                f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                f"Retrying in {current_delay:.1f} seconds..."
            )
            time.sleep(current_delay)
            current_delay *= backoff
    
    raise Exception(f"Failed after {max_attempts} attempts")

