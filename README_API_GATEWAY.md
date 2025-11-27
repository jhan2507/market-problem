# API Gateway & Service Discovery

## Overview

The system now includes an API Gateway and Service Discovery mechanism to improve service communication and provide a single entry point for external clients.

## API Gateway

The API Gateway runs on port **8080** and provides:

- **Request Routing**: Routes requests to appropriate microservices
- **Service Discovery**: Automatically discovers healthy services
- **Rate Limiting**: Protects services from excessive requests (100 req/60s default)
- **Correlation ID**: Propagates correlation IDs across service calls
- **Health-based Routing**: Only routes to healthy services

### Usage

Access services through the API Gateway:

```bash
# Health check through API Gateway
curl http://localhost:8080/api/market_data/health
curl http://localhost:8080/api/price/health
curl http://localhost:8080/api/signal/health

# List all registered services
curl http://localhost:8080/services

# Direct service access (still available)
curl http://localhost:8000/health
```

### Service Routes

| Route | Service | Port |
|-------|---------|------|
| `/api/market_data/*` | market_data_service | 8000 |
| `/api/market_analyzer/*` | market_analyzer_service | 8001 |
| `/api/price/*` | price_service | 8002 |
| `/api/signal/*` | signal_service | 8003 |
| `/api/notification/*` | notification_service | 8004 |

### Configuration

Environment variables for API Gateway:

```bash
RATE_LIMIT_REQUESTS=100    # Max requests per window
RATE_LIMIT_WINDOW=60       # Time window in seconds
```

## Service Discovery

Service Discovery uses Redis to maintain a registry of all services.

### Features

- **Automatic Registration**: Services register on startup
- **Health Checking**: Periodic health checks for registered services
- **Heartbeat**: Services send heartbeats to stay registered
- **Automatic Cleanup**: Unhealthy services are removed from registry

### Service Registration

Each service automatically registers with:
- Service name
- Host and port
- Health check URL
- Metadata

### Service Discovery API

```python
from shared.service_discovery import get_service_registry

registry = get_service_registry()

# Get service information
service = registry.get_service("market_data_service")
# Returns: {"name": "market_data_service", "host": "localhost", "port": 8000, ...}

# Discover service URL
url = registry.discover_service("market_data_service")
# Returns: "http://localhost:8000"

# List all services
services = registry.list_services()
```

## Architecture

```
External Client
      |
      v
  API Gateway (8080)
      |
      +---> Service Discovery (Redis)
      |
      +---> market_data_service (8000)
      +---> market_analyzer_service (8001)
      +---> price_service (8002)
      +---> signal_service (8003)
      +---> notification_service (8004)
```

## Benefits

1. **Single Entry Point**: All external requests go through API Gateway
2. **Service Abstraction**: Clients don't need to know service locations
3. **Load Balancing Ready**: Easy to add multiple service instances
4. **Rate Limiting**: Protects backend services
5. **Monitoring**: Centralized request logging and metrics
6. **Resilience**: Automatic failover to healthy services

## Deployment

The API Gateway is included in `docker-compose.yml` and starts automatically:

```bash
docker-compose up -d api_gateway
```

Or start all services:

```bash
docker-compose up -d
```

## Monitoring

API Gateway exposes the same endpoints as other services:

- `/health` - Health check
- `/ready` - Readiness check
- `/status` - Detailed status
- `/metrics` - Prometheus metrics

## Next Steps

- Add authentication/authorization
- Implement load balancing for multiple instances
- Add request/response transformation
- Implement API versioning
- Add request caching

