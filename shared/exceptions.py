"""
Custom exception classes for the microservices system.
"""


class ServiceError(Exception):
    """Base exception for all service errors."""
    
    def __init__(self, message: str, service_name: str = None, error_code: str = None):
        """
        Initialize service error.
        
        Args:
            message: Error message
            service_name: Name of the service that raised the error
            error_code: Optional error code for categorization
        """
        super().__init__(message)
        self.message = message
        self.service_name = service_name
        self.error_code = error_code
    
    def __str__(self) -> str:
        if self.service_name:
            return f"[{self.service_name}] {self.message}"
        return self.message


class ConfigurationError(ServiceError):
    """Raised when there's a configuration error."""
    
    def __init__(self, message: str, config_key: str = None):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_key: Configuration key that caused the error
        """
        super().__init__(message, error_code="CONFIG_ERROR")
        self.config_key = config_key


class DatabaseError(ServiceError):
    """Raised when there's a database operation error."""
    
    def __init__(self, message: str, operation: str = None, collection: str = None):
        """
        Initialize database error.
        
        Args:
            message: Error message
            operation: Database operation that failed
            collection: Collection name involved in the error
        """
        super().__init__(message, error_code="DATABASE_ERROR")
        self.operation = operation
        self.collection = collection


class ExternalAPIError(ServiceError):
    """Raised when there's an error calling an external API."""
    
    def __init__(self, message: str, api_name: str = None, status_code: int = None):
        """
        Initialize external API error.
        
        Args:
            message: Error message
            api_name: Name of the external API
            status_code: HTTP status code if applicable
        """
        super().__init__(message, error_code="EXTERNAL_API_ERROR")
        self.api_name = api_name
        self.status_code = status_code


class EventPublishError(ServiceError):
    """Raised when there's an error publishing an event."""
    
    def __init__(self, message: str, event_name: str = None):
        """
        Initialize event publish error.
        
        Args:
            message: Error message
            event_name: Name of the event that failed to publish
        """
        super().__init__(message, error_code="EVENT_PUBLISH_ERROR")
        self.event_name = event_name


class ValidationError(ServiceError):
    """Raised when there's a validation error."""
    
    def __init__(self, message: str, field: str = None, value: any = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field name that failed validation
            value: Value that failed validation
        """
        super().__init__(message, error_code="VALIDATION_ERROR")
        self.field = field
        self.value = value


class CircuitBreakerOpenError(ServiceError):
    """Raised when circuit breaker is open."""
    
    def __init__(self, message: str, service_name: str = None):
        """
        Initialize circuit breaker error.
        
        Args:
            message: Error message
            service_name: Name of the service with open circuit breaker
        """
        super().__init__(message, service_name=service_name, error_code="CIRCUIT_BREAKER_OPEN")

