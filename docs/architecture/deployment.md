# Deployment Architecture

## Docker Compose Deployment

```mermaid
graph TB
    subgraph "Docker Network: market_network"
        subgraph "Services"
            MD[market_data_service<br/>:8000]
            MA[market_analyzer_service<br/>:8001]
            PS[price_service<br/>:8002]
            SS[signal_service<br/>:8003]
            NS[notification_service<br/>:8004]
            AG[api_gateway<br/>:8080]
        end
        
        subgraph "Data Stores"
            MongoDB[(mongodb<br/>:27017)]
            Redis[(redis<br/>:6379)]
        end
    end
    
    MD --> MongoDB
    MA --> MongoDB
    PS --> MongoDB
    SS --> MongoDB
    NS --> MongoDB
    
    MD --> Redis
    MA --> Redis
    PS --> Redis
    SS --> Redis
    NS --> Redis
    AG --> Redis
    
    AG --> MD
    AG --> MA
    AG --> PS
    AG --> SS
    AG --> NS
```

## Health Checks

All services expose health check endpoints:
- `/health` - Basic health check
- `/ready` - Readiness check
- `/status` - Detailed status
- `/metrics` - Prometheus metrics

## Service Ports

- Market Data Service: 8000
- Market Analyzer Service: 8001
- Price Service: 8002
- Signal Service: 8003
- Notification Service: 8004
- API Gateway: 8080

