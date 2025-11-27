"""
Input validation schemas for API Gateway requests.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ValidationError, validator
import logging

logger = logging.getLogger(__name__)


class ProxyRequestSchema(BaseModel):
    """Schema for proxied requests through API Gateway."""
    method: str = Field(..., description="HTTP method")
    path: str = Field(..., description="Request path")
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None
    
    @validator('method')
    def validate_method(cls, v):
        allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        if v.upper() not in allowed_methods:
            raise ValueError(f"Method must be one of {allowed_methods}")
        return v.upper()
    
    @validator('path')
    def validate_path(cls, v):
        if not v or not v.startswith('/'):
            raise ValueError("Path must start with /")
        if '..' in v:  # Security: prevent path traversal
            raise ValueError("Path cannot contain '..'")
        return v


class HealthCheckRequestSchema(BaseModel):
    """Schema for health check requests."""
    service: Optional[str] = Field(None, description="Optional service name to check")


class ServiceListRequestSchema(BaseModel):
    """Schema for service list requests."""
    include_unhealthy: Optional[bool] = Field(False, description="Include unhealthy services")


def validate_request_body(schema_class: type[BaseModel], data: Any) -> tuple[bool, Optional[BaseModel], Optional[str]]:
    """
    Validate request body against a Pydantic schema.
    
    Args:
        schema_class: Pydantic schema class
        data: Request data to validate
    
    Returns:
        Tuple of (is_valid, validated_data, error_message)
    """
    try:
        if isinstance(data, dict):
            validated = schema_class(**data)
        else:
            validated = schema_class.parse_obj(data)
        return True, validated, None
    except ValidationError as e:
        error_msg = f"Validation error: {e}"
        logger.warning(error_msg)
        return False, None, error_msg
    except Exception as e:
        error_msg = f"Unexpected validation error: {e}"
        logger.error(error_msg, exc_info=True)
        return False, None, error_msg

