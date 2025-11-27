"""
Unit tests for retry mechanism.
"""

import pytest
from unittest.mock import Mock, patch
from shared.retry import retry_with_backoff


def test_retry_success():
    """Test retry with successful call."""
    call_count = [0]
    
    @retry_with_backoff(max_attempts=3, initial_delay=0.1)
    def success_func():
        call_count[0] += 1
        return "success"
    
    result = success_func()
    assert result == "success"
    assert call_count[0] == 1


def test_retry_with_failures():
    """Test retry with failures then success."""
    call_count = [0]
    
    @retry_with_backoff(max_attempts=3, initial_delay=0.1)
    def fail_then_success():
        call_count[0] += 1
        if call_count[0] < 2:
            raise Exception("Test error")
        return "success"
    
    result = fail_then_success()
    assert result == "success"
    assert call_count[0] == 2


def test_retry_max_attempts():
    """Test retry exhausts max attempts."""
    call_count = [0]
    
    @retry_with_backoff(max_attempts=3, initial_delay=0.1)
    def always_fail():
        call_count[0] += 1
        raise Exception("Test error")
    
    with pytest.raises(Exception, match="Test error"):
        always_fail()
    
    assert call_count[0] == 3

