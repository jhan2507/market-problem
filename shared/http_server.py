"""
HTTP server wrapper for microservices with health check endpoints.
"""

import os
import threading
import logging
import time
from flask import Flask, jsonify, request, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from typing import Optional, Callable

from shared.health import HealthChecker
from shared.shutdown import get_shutdown_manager
from shared.metrics import MetricsCollector, http_requests_total, http_request_duration_seconds, get_metrics_response

logger = logging.getLogger(__name__)


class ServiceHTTPServer:
    """HTTP server for service health checks and metrics."""
    
    def __init__(self, service_name: str, port: int = 8000, health_checker: Optional[HealthChecker] = None, metrics_collector: Optional[MetricsCollector] = None):
        self.service_name = service_name
        self.port = port
        self.app = Flask(service_name)
        self.health_checker = health_checker or HealthChecker(service_name)
        self.metrics_collector = metrics_collector
        self.server_thread: Optional[threading.Thread] = None
        
        # API key authentication (optional)
        self.api_key_enabled = os.getenv("API_KEY_ENABLED", "false").lower() == "true"
        self.api_key = os.getenv("API_KEY", "")
        
        # Rate limiting (optional)
        self.rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        
        # Initialize Flask-Limiter
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=[f"{self.rate_limit_per_minute}/minute"] if self.rate_limit_enabled else [],
            storage_uri=os.getenv("REDIS_URL", None)  # Use Redis if available, otherwise in-memory
        )
        
        self._setup_routes()
        self._setup_middleware()
    
    def _check_api_key(self) -> bool:
        """Check if API key is valid (if authentication is enabled)."""
        if not self.api_key_enabled:
            return True  # Authentication disabled
        
        if not self.api_key:
            logger.warning("API_KEY_ENABLED is true but API_KEY is not set")
            return False
        
        # Check API key from header or query parameter
        provided_key = request.headers.get("X-API-Key") or request.args.get("api_key")
        
        if not provided_key:
            return False
        
        return provided_key == self.api_key
    
    def _setup_middleware(self):
        """Setup middleware for metrics and tracing."""
        @self.app.before_request
        def before_request():
            request.start_time = time.time()
            
            # Check API key for /metrics endpoint if enabled
            if request.path == "/metrics" and self.api_key_enabled:
                if not self._check_api_key():
                    abort(401, description="Invalid or missing API key")
        
        @self.app.after_request
        def after_request(response):
            # Record metrics
            if self.metrics_collector:
                duration = time.time() - request.start_time
                http_request_duration_seconds.labels(
                    method=request.method,
                    endpoint=request.endpoint or request.path
                ).observe(duration)
                http_requests_total.labels(
                    method=request.method,
                    endpoint=request.endpoint or request.path,
                    status=response.status_code
                ).inc()
            return response
    
    def _setup_routes(self):
        """Setup HTTP routes."""
        
        # Health endpoints - no rate limiting (for monitoring systems)
        @self.app.route('/health', methods=['GET'])
        @self.limiter.exempt
        def health():
            """Health check endpoint."""
            if self.health_checker.is_healthy():
                return jsonify({
                    "status": "healthy",
                    "service": self.service_name
                }), 200
            else:
                return jsonify({
                    "status": "unhealthy",
                    "service": self.service_name
                }), 503
        
        @self.app.route('/ready', methods=['GET'])
        @self.limiter.exempt
        def ready():
            """Readiness check endpoint."""
            if self.health_checker.is_ready():
                return jsonify({
                    "status": "ready",
                    "service": self.service_name
                }), 200
            else:
                return jsonify({
                    "status": "not_ready",
                    "service": self.service_name
                }), 503
        
        @self.app.route('/status', methods=['GET'])
        @self.limiter.exempt
        def status():
            """Detailed status endpoint."""
            status_data = self.health_checker.get_status()
            status_code = 200 if status_data["status"] == "healthy" else 503
            return jsonify(status_data), status_code
        
        # Metrics endpoint - rate limited and optionally protected by API key
        @self.app.route('/metrics', methods=['GET'])
        @self.limiter.limit(f"{self.rate_limit_per_minute}/minute" if self.rate_limit_enabled else None)
        def metrics():
            """Prometheus metrics endpoint (protected by API key if enabled)."""
            # API key check is done in middleware
            return get_metrics_response()
        
        @self.app.errorhandler(401)
        def unauthorized(error):
            """Handle 401 Unauthorized errors."""
            return jsonify({
                "error": "Unauthorized",
                "message": str(error.description)
            }), 401
        
        @self.app.errorhandler(429)
        def ratelimit_handler(error):
            """Handle 429 Rate Limit errors."""
            return jsonify({
                "error": "Rate Limit Exceeded",
                "message": "Too many requests. Please try again later."
            }), 429
    
    def start(self, daemon: bool = True):
        """Start HTTP server in background thread."""
        def run_server():
            logger.info(f"Starting HTTP server for {self.service_name} on port {self.port}")
            self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run_server, daemon=daemon)
        self.server_thread.start()
        
        # Register shutdown handler
        def stop_server():
            logger.info(f"Stopping HTTP server for {self.service_name}")
            # Flask doesn't have a clean shutdown, but thread will stop when main process exits
        
        get_shutdown_manager().register_handler(stop_server)
    
    def stop(self):
        """Stop HTTP server."""
        # Flask doesn't support graceful shutdown easily
        # The thread will be terminated when main process exits
        logger.info(f"HTTP server for {self.service_name} will stop with main process")

