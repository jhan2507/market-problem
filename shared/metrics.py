"""
Prometheus metrics for microservices.
"""

import logging
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from flask import Response

logger = logging.getLogger(__name__)

# Common metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

service_events_published = Counter(
    'service_events_published_total',
    'Total events published',
    ['service', 'event_type']
)

service_events_consumed = Counter(
    'service_events_consumed_total',
    'Total events consumed',
    ['service', 'event_type']
)

service_errors_total = Counter(
    'service_errors_total',
    'Total errors',
    ['service', 'error_type']
)

service_processing_duration_seconds = Histogram(
    'service_processing_duration_seconds',
    'Service processing duration in seconds',
    ['service', 'operation']
)

# Service-specific metrics
database_operations_total = Counter(
    'database_operations_total',
    'Total database operations',
    ['service', 'operation', 'status']
)

database_operation_duration_seconds = Histogram(
    'database_operation_duration_seconds',
    'Database operation duration in seconds',
    ['service', 'operation']
)

redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['service', 'operation', 'status']
)

external_api_requests_total = Counter(
    'external_api_requests_total',
    'Total external API requests',
    ['service', 'api', 'status']
)

external_api_request_duration_seconds = Histogram(
    'external_api_request_duration_seconds',
    'External API request duration in seconds',
    ['service', 'api']
)


class MetricsCollector:
    """Metrics collector for services."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
    
    def record_event_published(self, event_type: str):
        """Record an event published."""
        service_events_published.labels(
            service=self.service_name,
            event_type=event_type
        ).inc()
    
    def record_event_consumed(self, event_type: str):
        """Record an event consumed."""
        service_events_consumed.labels(
            service=self.service_name,
            event_type=event_type
        ).inc()
    
    def record_error(self, error_type: str):
        """Record an error."""
        service_errors_total.labels(
            service=self.service_name,
            error_type=error_type
        ).inc()
    
    def record_processing_time(self, operation: str, duration: float):
        """Record processing time."""
        service_processing_duration_seconds.labels(
            service=self.service_name,
            operation=operation
        ).observe(duration)
    
    def record_db_operation(self, operation: str, status: str, duration: float = None):
        """Record database operation."""
        database_operations_total.labels(
            service=self.service_name,
            operation=operation,
            status=status
        ).inc()
        if duration is not None:
            database_operation_duration_seconds.labels(
                service=self.service_name,
                operation=operation
            ).observe(duration)
    
    def record_redis_operation(self, operation: str, status: str):
        """Record Redis operation."""
        redis_operations_total.labels(
            service=self.service_name,
            operation=operation,
            status=status
        ).inc()
    
    def record_external_api_call(self, api: str, status: str, duration: float = None):
        """Record external API call."""
        external_api_requests_total.labels(
            service=self.service_name,
            api=api,
            status=status
        ).inc()
        if duration is not None:
            external_api_request_duration_seconds.labels(
                service=self.service_name,
                api=api
            ).observe(duration)


def get_metrics_response():
    """Get Prometheus metrics response."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

