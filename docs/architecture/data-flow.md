# Data Flow Diagram

## Data Flow Through System

```mermaid
flowchart TD
    Start([External APIs]) -->|Price Data| MD[Market Data Service]
    Start -->|Market Metrics| MD
    
    MD -->|Store| DB1[(MongoDB<br/>market_data)]
    MD -->|Publish Event| ES[Redis Streams]
    
    ES -->|Event| MA[Market Analyzer]
    MA -->|Analyze| MA
    MA -->|Store| DB2[(MongoDB<br/>analysis)]
    MA -->|Publish Event| ES
    
    ES -->|Event| SS[Signal Service]
    SS -->|Generate Signals| SS
    SS -->|Store| DB3[(MongoDB<br/>signals)]
    SS -->|Publish Event| ES
    
    PS[Price Service] -->|Fetch Prices| Start
    PS -->|Store| DB4[(MongoDB<br/>price_updates)]
    PS -->|Publish Event| ES
    
    ES -->|Events| NS[Notification Service]
    NS -->|Send| TG[Telegram]
    
    style DB1 fill:#e1f5ff
    style DB2 fill:#e1f5ff
    style DB3 fill:#e1f5ff
    style DB4 fill:#e1f5ff
    style ES fill:#fff4e1
    style TG fill:#ffe1f5
```

## Database Collections

- **market_data**: Raw market data (prices, candlesticks, metrics)
- **analysis**: Market analysis results (sentiment, trends, indicators)
- **signals**: Generated trading signals
- **price_updates**: Real-time price updates
- **logs**: System logs (warnings and errors)

