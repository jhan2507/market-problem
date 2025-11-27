"""
Event-driven communication using Redis Streams.
"""

import redis
from redis.connection import ConnectionPool
import json
import logging
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from shared.config_manager import REDIS_HOST, REDIS_PORT, get_config_manager
from shared.logger import get_correlation_id, set_correlation_id
from shared.validation import validate_event
from shared.exceptions import EventPublishError, ServiceError
import redis.exceptions

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None
_redis_pool: Optional[ConnectionPool] = None


def get_redis_client() -> redis.Redis:
    """Get Redis client instance with connection pooling."""
    global _redis_client, _redis_pool
    
    if _redis_client is not None:
        return _redis_client
    
    try:
        config = get_config_manager()
        
        # Connection pool configuration
        max_connections = config.get("redis.max_connections", 50)
        socket_connect_timeout = config.get("redis.socket_connect_timeout", 5)
        socket_timeout = config.get("redis.socket_timeout", 5)
        socket_keepalive = config.get("redis.socket_keepalive", True)
        socket_keepalive_options = config.get("redis.socket_keepalive_options", {})
        
        # Create connection pool
        _redis_pool = ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            max_connections=max_connections,
            decode_responses=True,
            socket_connect_timeout=socket_connect_timeout,
            socket_timeout=socket_timeout,
            socket_keepalive=socket_keepalive,
            socket_keepalive_options=socket_keepalive_options,
            # Health check settings
            health_check_interval=30,  # Check connection health every 30 seconds
            retry_on_timeout=True,
        )
        
        # Create Redis client from pool
        _redis_client = redis.Redis(connection_pool=_redis_pool)
        
        # Test connection
        _redis_client.ping()
        logger.info(
            f"Connected to Redis successfully "
            f"(pool_size: {max_connections}, keepalive: {socket_keepalive})"
        )
        return _redis_client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise


def close_redis_client():
    """Close Redis connection pool."""
    global _redis_client, _redis_pool
    if _redis_client:
        _redis_client.close()
        _redis_client = None
    if _redis_pool:
        _redis_pool.disconnect()
        _redis_pool = None
        logger.info("Redis connection pool closed")


def publish_event(event_name: str, data: Dict[str, Any], service_name: str = None) -> bool:
    """
    Publish an event to Redis Stream.
    
    Args:
        event_name: Name of the event
        data: Event data dictionary
        service_name: Name of the service publishing the event (for metrics)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        client = get_redis_client()
        
        # Validate event data
        is_valid, error_msg = validate_event(event_name, data)
        if not is_valid:
            logger.error(f"Event validation failed: {error_msg}")
            if service_name:
                try:
                    from shared.metrics import MetricsCollector
                    metrics = MetricsCollector(service_name)
                    metrics.record_error("event_validation_failed")
                except Exception:
                    pass
            return False
        
        # Add correlation ID if not present
        if "correlation_id" not in data:
            data["correlation_id"] = get_correlation_id()
        
        # Add timestamp if not present
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow().isoformat()
        
        start_time = time.time()
        event_data = {
            "event": event_name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": json.dumps(data)
        }
        stream_name = f"events:{event_name}"
        client.xadd(stream_name, event_data)
        
        duration = time.time() - start_time
        
        # Record metrics if service_name provided
        if service_name:
            try:
                from shared.metrics import MetricsCollector
                metrics = MetricsCollector(service_name)
                metrics.record_event_published(event_name)
                metrics.record_redis_operation("publish_event", "success")
            except Exception:
                pass  # Don't fail if metrics not available
        
        logger.info(f"Published event: {event_name} [correlation_id: {data.get('correlation_id')}]")
        return True
    except redis.exceptions.RedisError as e:
        error = EventPublishError(
            f"Redis error publishing event {event_name}: {e}",
            event_name=event_name
        )
        logger.error(str(error))
        if service_name:
            try:
                from shared.metrics import MetricsCollector
                metrics = MetricsCollector(service_name)
                metrics.record_error("publish_event_redis_failed")
                metrics.record_redis_operation("publish_event", "failed")
            except Exception:
                pass
        return False
    except Exception as e:
        error = EventPublishError(
            f"Failed to publish event {event_name}: {e}",
            event_name=event_name
        )
        logger.error(str(error), exc_info=True)
        if service_name:
            try:
                from shared.metrics import MetricsCollector
                metrics = MetricsCollector(service_name)
                metrics.record_error("publish_event_failed")
                metrics.record_redis_operation("publish_event", "failed")
            except Exception:
                pass
        return False


def subscribe_events(event_names: list, handler: Callable[[str, Dict[str, Any]], None], 
                     consumer_group: str = "default", consumer_name: str = "consumer",
                     running_flag: Optional[Callable[[], bool]] = None):
    """
    Subscribe to events from Redis Streams.
    
    Args:
        event_names: List of event names to subscribe to
        handler: Callback function(event_name, data)
        consumer_group: Consumer group name
        consumer_name: Consumer name
        running_flag: Optional callable that returns False when service should stop
    """
    try:
        client = get_redis_client()
        
        # Create consumer groups for each stream
        for event_name in event_names:
            stream_name = f"events:{event_name}"
            try:
                client.xgroup_create(stream_name, consumer_group, id="0", mkstream=True)
            except redis.exceptions.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise
        
        # Read from streams
        while True:
            # Check running flag if provided
            if running_flag and not running_flag():
                logger.info("Event subscription stopped (running flag is False)")
                break
            
            streams = {f"events:{name}": ">" for name in event_names}
            messages = client.xreadgroup(
                consumer_group,
                consumer_name,
                streams,
                count=1,
                block=1000
            )
            
            if messages:
                for stream, msgs in messages:
                    for msg_id, msg_data in msgs:
                        event_name = stream.split(":")[1]
                        try:
                            data = json.loads(msg_data["data"])
                            
                            # Set correlation ID from event data
                            if "correlation_id" in data:
                                set_correlation_id(data["correlation_id"])
                            
                            # Record metrics
                            try:
                                from shared.metrics import MetricsCollector
                                # Try to get service name from consumer_group
                                metrics = MetricsCollector(consumer_group)
                                metrics.record_event_consumed(event_name)
                            except Exception:
                                pass
                            
                            handler(event_name, data)
                            # Acknowledge message
                            client.xack(stream, consumer_group, msg_id)
                        except ServiceError as e:
                            # Custom service errors - log but don't fail the subscription
                            logger.error(f"Service error processing event {event_name}: {e}")
                            try:
                                from shared.metrics import MetricsCollector
                                metrics = MetricsCollector(consumer_group)
                                metrics.record_error(f"event_processing_error_{e.error_code}")
                            except Exception:
                                pass
                        except Exception as e:
                            error = ServiceError(
                                f"Unexpected error processing event {event_name}: {e}",
                                service_name=consumer_group,
                                error_code="EVENT_PROCESSING_ERROR"
                            )
                            logger.error(str(error), exc_info=True)
                            try:
                                from shared.metrics import MetricsCollector
                                metrics = MetricsCollector(consumer_group)
                                metrics.record_error("event_processing_failed")
                            except Exception:
                                pass
    except KeyboardInterrupt:
        logger.info("Event subscription interrupted")
        raise
    except redis.exceptions.RedisError as e:
        error = ServiceError(
            f"Redis error in event subscription: {e}",
            service_name=consumer_group,
            error_code="REDIS_SUBSCRIPTION_ERROR"
        )
        logger.error(str(error))
        raise
    except Exception as e:
        error = ServiceError(
            f"Unexpected error in event subscription: {e}",
            service_name=consumer_group,
            error_code="SUBSCRIPTION_ERROR"
        )
        logger.error(str(error), exc_info=True)
        raise

