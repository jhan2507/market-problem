"""
API Gateway Service

Routes requests to appropriate microservices.
Provides load balancing, rate limiting, and authentication.
"""

import os
import logging
import requests
import time
from flask import Flask, request, jsonify, Response
from typing import Dict, Optional
from datetime import datetime, timedelta

from shared.logger import setup_logger, set_correlation_id, get_correlation_id
from shared.health import HealthChecker
from shared.http_server import ServiceHTTPServer
from shared.shutdown import get_shutdown_manager, register_shutdown_handler
from shared.metrics import MetricsCollector
from shared.tracing import setup_tracing, get_tracer
from shared.service_discovery import ServiceRegistry, get_service_registry
from shared.events import get_redis_client
from shared.api_validation import validate_request_body, ProxyRequestSchema

logger = setup_logger("api_gateway")

app = Flask(__name__)

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
RATE_LIMIT_KEY_PREFIX = "rate_limit:api_gateway:"

# Authentication configuration
API_KEY_ENABLED = os.getenv("API_KEY_ENABLED", "false").lower() == "true"
API_KEYS = os.getenv("API_KEYS", "").split(",")  # Comma-separated list of valid API keys
AUTH_EXEMPT_PATHS = ["/health", "/metrics"]  # Paths that don't require authentication

# Service routing
SERVICE_ROUTES = {
    "market_data": "market_data_service",
    "market_analyzer": "market_analyzer_service",
    "price": "price_service",
    "signal": "signal_service",
    "notification": "notification_service"
}


def check_rate_limit(client_id: str) -> bool:
    """
    Check if client has exceeded rate limit using Redis sliding window.
    
    Uses Redis sorted sets to implement a sliding window rate limiter.
    This is scalable across multiple API Gateway instances.
    
    Args:
        client_id: Client identifier (IP address or API key)
    
    Returns:
        bool: True if within limit, False if exceeded
    """
    try:
        redis_client = get_redis_client()
        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW
        
        # Redis key for this client
        key = f"{RATE_LIMIT_KEY_PREFIX}{client_id}"
        
        # Remove entries outside the window
        redis_client.zremrangebyscore(key, 0, window_start)
        
        # Count current requests in window
        current_count = redis_client.zcard(key)
        
        if current_count >= RATE_LIMIT_REQUESTS:
            # Rate limit exceeded
            logger.warning(f"Rate limit exceeded for client {client_id}: {current_count}/{RATE_LIMIT_REQUESTS}")
            return False
        
        # Add current request timestamp
        redis_client.zadd(key, {str(now): now})
        
        # Set expiry on the key (cleanup after window + buffer)
        redis_client.expire(key, RATE_LIMIT_WINDOW + 10)
        
        return True
    
    except Exception as e:
        # If Redis fails, log error but allow request (fail-open)
        logger.error(f"Rate limit check failed for client {client_id}: {e}")
        # In production, you might want to fail-closed instead
        return True


def get_service_url(service_name: str) -> Optional[str]:
    """Get service URL from service discovery."""
    registry = get_service_registry()
    service = registry.get_service(service_name)
    
    if service and service["healthy"]:
        return f"http://{service['host']}:{service['port']}"
    
    # Fallback to default (for development)
    default_ports = {
        "market_data_service": 8000,
        "market_analyzer_service": 8001,
        "price_service": 8002,
        "signal_service": 8003,
        "notification_service": 8004
    }
    
    port = default_ports.get(service_name, 8000)
    return f"http://localhost:{port}"


def check_authentication() -> tuple[bool, Optional[str]]:
    """
    Check API key authentication.
    
    Returns:
        Tuple of (is_authenticated, error_message)
    """
    # Skip authentication for exempt paths
    if request.path in AUTH_EXEMPT_PATHS:
        return True, None
    
    # Skip if authentication is disabled
    if not API_KEY_ENABLED:
        return True, None
    
    # Check for API key in headers
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
    
    # Extract API key from Authorization header if present
    if api_key and api_key.startswith("Bearer "):
        api_key = api_key[7:]  # Remove "Bearer " prefix
    
    if not api_key:
        return False, "API key required. Provide X-API-Key header or Authorization: Bearer <key>"
    
    # Validate API key
    if api_key not in API_KEYS:
        logger.warning(f"Invalid API key attempted from {request.remote_addr}")
        return False, "Invalid API key"
    
    return True, None


@app.before_request
def before_request():
    """Setup request context."""
    # Set correlation ID
    corr_id = request.headers.get("X-Correlation-ID") or set_correlation_id()
    set_correlation_id(corr_id)
    
    # Check authentication
    is_authenticated, auth_error = check_authentication()
    if not is_authenticated:
        return jsonify({
            "error": "Unauthorized",
            "message": auth_error
        }), 401
    
    # Check rate limit
    client_id = request.headers.get("X-Client-ID") or request.headers.get("X-API-Key") or request.remote_addr
    if not check_rate_limit(client_id):
        return jsonify({
            "error": "Rate limit exceeded",
            "message": f"Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds"
        }), 429


@app.route("/api/<service>/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def proxy_request(service: str, path: str):
    """Proxy request to appropriate service."""
    tracer = get_tracer("api_gateway")
    
    with tracer.start_as_current_span("proxy_request") as span:
        span.set_attribute("service", service)
        span.set_attribute("path", path)
        span.set_attribute("method", request.method)
        
        # Validate request
        request_data = {
            "method": request.method,
            "path": f"/{path}",
            "headers": dict(request.headers),
            "params": dict(request.args)
        }
        
        # Add body for POST/PUT/PATCH requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            json_body = request.get_json(silent=True)
            if json_body:
                request_data["body"] = json_body
                # Validate body if present
                is_valid, validated, error_msg = validate_request_body(
                    ProxyRequestSchema, request_data
                )
                if not is_valid:
                    logger.warning(f"Request validation failed: {error_msg}")
                    return jsonify({
                        "error": "Invalid request",
                        "message": error_msg
                    }), 400
        
        # Get service name
        service_name = SERVICE_ROUTES.get(service)
        if not service_name:
            return jsonify({"error": f"Unknown service: {service}"}), 404
        
        # Get service URL
        service_url = get_service_url(service_name)
        if not service_url:
            return jsonify({"error": f"Service {service_name} not available"}), 503
        
        # Forward request
        target_url = f"{service_url}/{path}"
        
        try:
            # Prepare headers
            headers = dict(request.headers)
            headers["X-Correlation-ID"] = get_correlation_id()
            headers.pop("Host", None)
            headers.pop("Content-Length", None)
            
            # Forward request
            response = requests.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.args,
                json=request.get_json(silent=True),
                data=request.get_data(),
                timeout=30,
                allow_redirects=False
            )
            
            # Return response
            return Response(
                response.content,
                status=response.status_code,
                headers=dict(response.headers)
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Error proxying request to {service_name}: {e}")
            return jsonify({
                "error": "Service unavailable",
                "message": str(e)
            }), 503


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "api_gateway"}), 200


@app.route("/services", methods=["GET"])
def list_services():
    """List all registered services."""
    registry = get_service_registry()
    services = registry.list_services()
    return jsonify({"services": services}), 200


def run():
    """Main service loop."""
    logger.info("API Gateway Service started")
    
    # Setup tracing
    setup_tracing("api_gateway")
    
    # Setup metrics
    metrics = MetricsCollector("api_gateway")
    
    # Setup health checker
    health_checker = HealthChecker("api_gateway")
    http_server = ServiceHTTPServer("api_gateway", port=8080, health_checker=health_checker, metrics_collector=metrics)
    http_server.start()
    
    # Register with service discovery
    registry = get_service_registry()
    registry.register_service(
        "api_gateway",
        host="localhost",
        port=8080,
        health_check_url="http://localhost:8080/health"
    )
    
    # Register shutdown handler
    def shutdown_handler():
        logger.info("Shutting down API Gateway...")
        registry.unregister_service("api_gateway")
    
    register_shutdown_handler(shutdown_handler)
    
    # Run Flask app
    app.run(host="0.0.0.0", port=8080, debug=False)


if __name__ == "__main__":
    run()

