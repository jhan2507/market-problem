"""
Integration tests for health check endpoints.
"""

import pytest
import requests
import time


SERVICES = {
    "market_data_service": "http://localhost:8000",
    "market_analyzer_service": "http://localhost:8001",
    "price_service": "http://localhost:8002",
    "signal_service": "http://localhost:8003",
    "notification_service": "http://localhost:8004"
}


@pytest.mark.parametrize("service_name,base_url", SERVICES.items())
def test_health_endpoint(service_name, base_url):
    """Test health endpoint for each service."""
    url = f"{base_url}/health"
    response = requests.get(url, timeout=5)
    
    assert response.status_code in [200, 503], f"Unexpected status code: {response.status_code}"
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert data["service"] == service_name


@pytest.mark.parametrize("service_name,base_url", SERVICES.items())
def test_ready_endpoint(service_name, base_url):
    """Test readiness endpoint for each service."""
    url = f"{base_url}/ready"
    response = requests.get(url, timeout=5)
    
    assert response.status_code in [200, 503], f"Unexpected status code: {response.status_code}"
    data = response.json()
    assert "status" in data
    assert "service" in data


@pytest.mark.parametrize("service_name,base_url", SERVICES.items())
def test_status_endpoint(service_name, base_url):
    """Test status endpoint for each service."""
    url = f"{base_url}/status"
    response = requests.get(url, timeout=5)
    
    assert response.status_code in [200, 503], f"Unexpected status code: {response.status_code}"
    data = response.json()
    assert "service" in data
    assert "status" in data
    assert "checks" in data


@pytest.mark.parametrize("service_name,base_url", SERVICES.items())
def test_metrics_endpoint(service_name, base_url):
    """Test metrics endpoint for each service."""
    url = f"{base_url}/metrics"
    response = requests.get(url, timeout=5)
    
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    assert response.headers["Content-Type"] == "text/plain; version=0.0.4; charset=utf-8"
    assert "http_requests_total" in response.text

