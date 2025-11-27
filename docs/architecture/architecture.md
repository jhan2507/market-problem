# System Architecture

## High-Level Architecture

```mermaid
graph TB
    subgraph "External Services"
        Binance[Binance API]
        CMC[CoinMarketCap API]
        Telegram[Telegram Bot API]
    end
    
    subgraph "API Gateway"
        Gateway[API Gateway<br/>Port 8080]
    end
    
    subgraph "Microservices"
        MarketData[Market Data Service<br/>Port 8000]
        Analyzer[Market Analyzer Service<br/>Port 8001]
        Price[Price Service<br/>Port 8002]
        Signal[Signal Service<br/>Port 8003]
        Notification[Notification Service<br/>Port 8004]
    end
    
    subgraph "Data Layer"
        MongoDB[(MongoDB)]
        Redis[(Redis Streams)]
    end
    
    Binance --> MarketData
    CMC --> MarketData
    MarketData --> MongoDB
    MarketData --> Redis
    Redis --> Analyzer
    Analyzer --> MongoDB
    Analyzer --> Redis
    Redis --> Price
    Price --> MongoDB
    Price --> Redis
    Redis --> Signal
    Signal --> MongoDB
    Signal --> Redis
    Redis --> Notification
    Notification --> Telegram
    
    Gateway --> MarketData
    Gateway --> Analyzer
    Gateway --> Price
    Gateway --> Signal
    Gateway --> Notification
```

## Service Responsibilities

1. **Market Data Service**: Fetches price data, candlesticks, and market metrics from external APIs
2. **Market Analyzer Service**: Analyzes market data using technical analysis theories
3. **Price Service**: Monitors live prices and detects volatility
4. **Signal Service**: Generates trading signals based on analysis
5. **Notification Service**: Sends notifications via Telegram

