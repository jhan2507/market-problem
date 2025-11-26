"""
Event-driven communication using Redis Streams.
"""

import redis
import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from shared.config import REDIS_HOST, REDIS_PORT

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    try:
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        _redis_client.ping()
        logger.info("Connected to Redis successfully")
        return _redis_client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise


def publish_event(event_name: str, data: Dict[str, Any]) -> bool:
    """
    Publish an event to Redis Stream.
    
    Args:
        event_name: Name of the event
        data: Event data dictionary
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        client = get_redis_client()
        event_data = {
            "event": event_name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": json.dumps(data)
        }
        stream_name = f"events:{event_name}"
        client.xadd(stream_name, event_data)
        logger.info(f"Published event: {event_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish event {event_name}: {e}")
        return False


def subscribe_events(event_names: list, handler: Callable[[str, Dict[str, Any]], None], 
                     consumer_group: str = "default", consumer_name: str = "consumer"):
    """
    Subscribe to events from Redis Streams.
    
    Args:
        event_names: List of event names to subscribe to
        handler: Callback function(event_name, data)
        consumer_group: Consumer group name
        consumer_name: Consumer name
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
                            handler(event_name, data)
                            # Acknowledge message
                            client.xack(stream, consumer_group, msg_id)
                        except Exception as e:
                            logger.error(f"Error processing event {event_name}: {e}")
    except KeyboardInterrupt:
        logger.info("Event subscription interrupted")
        raise
    except Exception as e:
        logger.error(f"Error in event subscription: {e}")
        raise

