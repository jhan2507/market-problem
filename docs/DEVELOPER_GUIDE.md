# Developer Guide

## Table of Contents

1. [Setup Development Environment](#setup-development-environment)
2. [Code Style Guidelines](#code-style-guidelines)
3. [Testing Guidelines](#testing-guidelines)
4. [How to Add New Service](#how-to-add-new-service)
5. [How to Add New Event Type](#how-to-add-new-event-type)
6. [Debugging Tips](#debugging-tips)
7. [Common Issues and Solutions](#common-issues-and-solutions)

## Setup Development Environment

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git

### Initial Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd market-problem
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Setup pre-commit hooks:
```bash
pre-commit install
```

5. Copy environment file:
```bash
cp env.example .env
# Edit .env with your configuration
```

6. Start services with Docker Compose:
```bash
docker-compose up -d
```

### Running Services Locally

To run a service locally (without Docker):

```bash
# Set environment variables
export MONGODB_URI="mongodb://admin:password@localhost:27017/market?authSource=admin"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
# ... other env vars

# Run service
python services/market_data_service/main.py
```

## Code Style Guidelines

### Formatting

We use **Black** for code formatting with line length of 100 characters:

```bash
black --line-length=100 .
```

### Linting

We use **flake8** for linting:

```bash
flake8 .
```

### Type Hints

All new code should include type hints:

```python
def process_data(data: Dict[str, Any], timeout: int = 10) -> Optional[str]:
    """Process data with timeout."""
    ...
```

### Import Sorting

We use **isort** to sort imports:

```bash
isort --profile=black .
```

### Pre-commit Hooks

Pre-commit hooks automatically run:
- Black (formatting)
- isort (import sorting)
- flake8 (linting)
- mypy (type checking)

Run manually:
```bash
pre-commit run --all-files
```

## Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit -m unit

# Run integration tests
pytest tests/integration -m integration

# Run with coverage
pytest --cov=shared --cov=services --cov-report=html
```

### Writing Tests

1. **Unit Tests**: Test individual functions/classes in isolation
2. **Integration Tests**: Test service interactions
3. **Use Fixtures**: Leverage `tests/conftest.py` fixtures

Example:
```python
def test_service_function(mock_mongodb, sample_market_data):
    """Test service function with mocked dependencies."""
    service = MyService(mock_mongodb)
    result = service.process(sample_market_data)
    assert result is not None
```

### Test Coverage

Target coverage: **80%**

Check coverage:
```bash
pytest --cov=shared --cov=services --cov-report=term-missing
```

## How to Add New Service

1. **Create service directory**:
```bash
mkdir -p services/my_service
```

2. **Create service file** (`services/my_service/main.py`):
```python
from shared.base_service import BaseService

class MyService(BaseService):
    def __init__(self):
        super().__init__("my_service", port=8005)
        # Initialize service-specific resources
    
    def run_cycle(self):
        """Execute one cycle of work."""
        # Your service logic here
        pass
    
    def get_cycle_interval(self) -> int:
        """Return interval in seconds."""
        return 60  # Run every 60 seconds
```

3. **Create Dockerfile** (`services/my_service/Dockerfile`):
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY services/my_service/ ./services/my_service/
CMD ["python", "services/my_service/main.py"]
```

4. **Add to docker-compose.yml**:
```yaml
my_service:
  build:
    context: .
    dockerfile: services/my_service/Dockerfile
  ports:
    - "8005:8005"
  environment:
    - MONGODB_URI=${MONGODB_URI}
    - REDIS_HOST=${REDIS_HOST}
  depends_on:
    - mongodb
    - redis
```

5. **Register with API Gateway** (if needed):
Update `services/api_gateway/main.py` to add route.

## How to Add New Event Type

1. **Define event name** in `shared/config_manager.py`:
```python
"events": {
    "my_new_event": "my_new_event"
}
```

2. **Publish event**:
```python
from shared.config_manager import EVENT_MY_NEW_EVENT
from shared.events import publish_event

publish_event(EVENT_MY_NEW_EVENT, {"data": "value"}, service_name="my_service")
```

3. **Subscribe to event**:
```python
from shared.events import subscribe_events
from shared.config_manager import EVENT_MY_NEW_EVENT

def event_handler(event_name: str, data: Dict):
    if event_name == EVENT_MY_NEW_EVENT:
        # Handle event
        pass

subscribe_events([EVENT_MY_NEW_EVENT], event_handler, consumer_group="my_service")
```

4. **Add validation** (optional):
Update `shared/validation.py` to add event schema validation.

## Debugging Tips

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f market_data_service
```

### Check Service Health

```bash
curl http://localhost:8000/health
curl http://localhost:8000/status
curl http://localhost:8000/metrics
```

### Debug with Python Debugger

Add breakpoint:
```python
import pdb; pdb.set_trace()
```

Or use debugger in IDE (VS Code, PyCharm).

### Check Redis Streams

```bash
docker-compose exec redis redis-cli
> XREAD STREAMS events:market_data_updated 0
```

### Check MongoDB

```bash
docker-compose exec mongodb mongosh
> use market
> db.market_data.find().limit(5)
```

## Common Issues and Solutions

### Issue: Service won't start

**Solution**: Check logs and ensure dependencies (MongoDB, Redis) are running:
```bash
docker-compose ps
docker-compose logs service_name
```

### Issue: Import errors

**Solution**: Ensure you're in the project root and virtual environment is activated:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Rate limiting errors

**Solution**: Check API keys and rate limits. For CoinMarketCap, ensure you have valid API key and haven't exceeded rate limits.

### Issue: Circuit breaker open

**Solution**: Check external API status. Circuit breaker opens after multiple failures. Wait for recovery timeout or restart service.

### Issue: Event not received

**Solution**: 
1. Check Redis is running
2. Verify event name matches
3. Check consumer group name
4. View Redis streams: `XREADGROUP GROUP consumer_group consumer_name STREAMS events:event_name >`

### Issue: Type checking errors

**Solution**: Some third-party libraries don't have type stubs. They're ignored in `.mypy.ini`. For new code, ensure type hints are correct.

## Additional Resources

- [Architecture Diagrams](architecture/)
- [API Documentation](api/openapi.yaml)
- [README](../README.md)

