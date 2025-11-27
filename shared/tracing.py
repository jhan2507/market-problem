"""
OpenTelemetry tracing setup for microservices.
"""

import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

logger = logging.getLogger(__name__)

_tracer_provider: TracerProvider = None


def setup_tracing(service_name: str, jaeger_endpoint: str = None):
    """
    Setup OpenTelemetry tracing.
    
    Args:
        service_name: Name of the service
        jaeger_endpoint: Optional Jaeger endpoint (e.g., http://jaeger:14268/api/traces)
    """
    global _tracer_provider
    
    if _tracer_provider is not None:
        logger.warning("Tracing already initialized")
        return
    
    try:
        # Create resource
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0"
        })
        
        # Create tracer provider
        _tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(_tracer_provider)
        
        # Add console exporter (for development)
        console_exporter = ConsoleSpanExporter()
        span_processor = BatchSpanProcessor(console_exporter)
        _tracer_provider.add_span_processor(span_processor)
        
        # Add Jaeger exporter if endpoint provided
        if jaeger_endpoint:
            try:
                from opentelemetry.exporter.jaeger.thrift import JaegerExporter
                jaeger_exporter = JaegerExporter(
                    agent_host_name=jaeger_endpoint.split("://")[1].split(":")[0] if "://" in jaeger_endpoint else jaeger_endpoint.split(":")[0],
                    agent_port=int(jaeger_endpoint.split(":")[-1]) if ":" in jaeger_endpoint else 14268
                )
                jaeger_processor = BatchSpanProcessor(jaeger_exporter)
                _tracer_provider.add_span_processor(jaeger_processor)
                logger.info(f"Jaeger exporter configured: {jaeger_endpoint}")
            except ImportError:
                logger.warning("Jaeger exporter not available, install opentelemetry-exporter-jaeger-thrift")
            except Exception as e:
                logger.warning(f"Failed to setup Jaeger exporter: {e}")
        
        # Instrument Flask and Requests
        try:
            FlaskInstrumentor().instrument()
            RequestsInstrumentor().instrument()
            logger.info("Flask and Requests instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument Flask/Requests: {e}")
        
        logger.info(f"Tracing initialized for service: {service_name}")
    except Exception as e:
        logger.error(f"Failed to setup tracing: {e}")


def get_tracer(name: str = None):
    """Get tracer instance."""
    return trace.get_tracer(name or "default")

