import pytest
from app.utils.retry import calculate_retry_delay

def test_fixed_retry_delay():
    # Fixed strategy should return initial delay on every attempt
    delay = calculate_retry_delay("fixed", 1, 1000)
    assert delay == 1000
    
    delay = calculate_retry_delay("fixed", 3, 1000)
    assert delay == 1000

def test_linear_retry_delay():
    # Linear strategy: initial_delay * attempt
    delay = calculate_retry_delay("linear", 1, 1000)
    assert delay == 1000
    
    delay = calculate_retry_delay("linear", 3, 1000)
    assert delay == 3000

def test_exponential_retry_delay():
    # Exponential strategy: initial_delay * (multiplier ** (attempt - 1))
    delay = calculate_retry_delay("exponential", 1, 1000, 2.0)
    assert delay == 1000
    
    delay = calculate_retry_delay("exponential", 2, 1000, 2.0)
    assert delay == 2000
    
    delay = calculate_retry_delay("exponential", 3, 1000, 2.0)
    assert delay == 4000

def test_retry_delay_cap():
    # Delay must not exceed max_delay_ms
    delay = calculate_retry_delay("exponential", 10, 1000, 2.0, 30000)
    assert delay == 30000
