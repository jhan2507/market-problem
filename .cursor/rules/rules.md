---
alwaysApply: true
---
You are an expert software architect and senior backend engineer.  
Your responsibility is to help me build, refactor, extend, and maintain a COMPLETE
microservice-based crypto market monitoring & futures signal system using:

- Python (FastAPI or pure services)
- MongoDB
- Telegram Bot API
- Event-driven architecture (Redis Streams / RabbitMQ / Kafka)
- Docker + Docker Compose

Your output MUST ALWAYS follow the business logic below with absolute correctness.

==================================================
              SYSTEM ARCHITECTURE
==================================================

The system consists of 5 independent microservices:

1. Market Data Service  
2. Crypto Market Analyzer  
3. Price Service  
4. Signal Service  
5. Notification Service  

All services must:
- run independently  
- communicate by events  
- store data in MongoDB  
- use clean, modular Python  
- include logging, retry, error handling  
- be containerized with Docker  

==================================================
        SERVICE 1 — MARKET DATA SERVICE
==================================================

Responsibilities:
- Fetch price data for all coins listed in .env.
- Fetch candlesticks for: 1m (optional), 1h, 4h, 8h, 1d, 3d, 1w.
- Fetch market-wide metrics:
  - BTC Dominance (BTC.D)
  - USDT Dominance (USDT.D)
  - TOTAL, TOTAL2, TOTAL3 market cap
  - BTC volatility
- Normalize and store all data into MongoDB.
- Publish `market_data_updated` events.

==================================================
     SERVICE 2 — CRYPTO MARKET ANALYZER
==================================================

The Analyzer must interpret price structure using:

1) **Dow Theory**
- Primary trend = 1D, 3D, 1W
- Secondary trend = 4H, 8H
- Minor trend = 1H
- Identify HH, HL (uptrend) and LH, LL (downtrend)
- Detect BOS (Break of Structure)
- Use volume to confirm trend continuation or weakness

2) **Wyckoff Method**
- Identify Accumulation / Distribution
- Recognize Spring / Upthrust
- Detect SOS / SOW
- Identify Phases A–E

3) **Gann Theory**
- Time/Price cycles
- Gann Angles (1x1, 2x1, 4x1)
- Detect reversal windows

4) **Dominance Analysis**
- BTC.D rising → money into BTC → ALTs weaken
- BTC.D falling → good for ALTs
- USDT.D rising → risk-off market → shorts favored
- TOTAL2 rising → alt season strengthening

5) **Indicators**
- EMA20/EMA50/EMA200 alignment
- RSI (50-line bias)
- MACD histogram + cross
- Volume spikes
- Funding rate
- Open interest

The Analyzer must:
- Evaluate all timeframes and generate a final market sentiment:
  - bullish / bearish / neutral
  - trend strength score (0–100)  
- Publish `market_analysis_completed`.

==================================================
         SERVICE 3 — PRICE SERVICE
==================================================

Responsibilities:
- Fetch live prices every 60 seconds.
- Create readable price message.
- Detect short-term volatility:
  - Coins pumping/dumping in 5–15 minutes
  - BTC >0.5% movement in 15m
- Publish `price_update_ready`.

==================================================
        SERVICE 4 — SIGNAL SERVICE
==================================================

This is the most critical service.  
It must generate **LONG/SHORT futures signals** for BOTH BTC and ALTCOINS,  
based on **multi-factor scoring (0–100)**.

==================================================
          SIGNAL RULES (UPDATED)
==================================================

### GENERAL PRINCIPLES
- Must use multi-timeframe alignment (Dow Theory).
- BTC and ALT follow different dominance behaviors.
- Volume, liquidity, funding, OI must be validated.
- Signal must be generated only when total score >= required threshold.

==================================================
            BTC SIGNAL RULES
==================================================

### LONG (BTC)
- Primary trend (1D–3D–1W): Uptrend OR neutral + strong BOS upward on 4H/1H
- Secondary trend (4H–8H): Uptrend or Neutral
- Minor trend (1H): Uptrend or BOS upward
- RSI > 50 (prefer RSI 4H > 50)
- MACD cross up (preferably on 4H or 1D)
- EMA: price > EMA20 and EMA20 > EMA50
- Wyckoff: SOS or Spring/Shakeout on BTC
- BTC.D falling improves long score
- USDT.D stable or falling
- Volume increases when price rises

### SHORT (BTC)
- Primary: Downtrend
- Secondary: Downtrend or Neutral
- Minor: Downtrend or BOS downward
- RSI < 50 (prefer 4H < 50)
- MACD cross down (4H or 1D)
- EMA20 < EMA50
- Wyckoff: SOW or Upthrust
- BTC.D rising improves short score
- USDT.D rising (risk-off)
- Volume increases on sell candles

==================================================
            ALTCOIN SIGNAL RULES
==================================================

ALTCOINS MUST consider **correlation + dominance**.

### Pre-Filters for ALTs
- Liquidity must pass threshold (orderbook depth OK).
- Correlation with BTC > 0.85 means ALT must follow BTC bias.
- Small-cap volatility filter enabled.
- TOTAL2 and BTC.D must not contradict direction.

### LONG (ALT)
- Primary: Uptrend OR Primary neutral + TOTAL2 rising + BTC.D falling
- Secondary: Uptrend or Neutral
- Minor: Uptrend or BOS upward
- RSI 4H > 50 (prefer 55+)
- MACD cross up (4H preferred)
- EMA alignment bullish
- Wyckoff: SOS or Spring on the ALT chart
- BTC.D falling is REQUIRED; rising kills ALT long signal
- USDT.D must NOT be rising (risk-off)
- TOTAL2 rising → strong alt support

### SHORT (ALT)
- Primary: Downtrend OR neutral + BTC.D rising + TOTAL2 falling
- Secondary: Downtrend or Neutral
- Minor: Downtrend or BOS downward
- RSI 4H < 50
- MACD cross down (4H)
- EMA bearish
- Wyckoff: SOW or Upthrust
- BTC.D rising or USDT.D rising → strong short support

==================================================
      MULTI-FACTOR SCORING SYSTEM (0–100)
==================================================

Each signal must score points from these weighted factors:

### 1) Multi-timeframe trend (Dow structure) — 30 points
- Primary trend match = 15
- Secondary trend match = 10
- Minor trend match/BOS = 5

### 2) Wyckoff pattern — 15 points
- SOS/Spring/SOW/Upthrust

### 3) Indicators — 20 points
- RSI = 7
- MACD = 7
- EMA alignment = 6

### 4) Volume confirmation — 10 points

### 5) Dominance effects (BTC.D / USDT.D / TOTAL2) — 15 points

### 6) Funding, OI, Liquidity safety checks — 10 points

### SCORING DECISIONS
- **Score ≥ 75 → HIGH confidence signal**  
- **60–74 → MEDIUM (optional or reduce size)**  
- **< 60 → NO SIGNAL**

==================================================
               GUARDRAILS
==================================================

- No long signals if USDT.D rising sharply (risk-off).
- No long ALT if BTC.D rising.
- No signals if liquidity below threshold.
- No signals during BTC crash (>X% in 15m).
- No conflicting signals (BTC strong short + ALT strong long).
- Limit max 1 active signal per asset per time window.

==================================================
               SIGNAL FORMAT
==================================================

A signal MUST include:

- asset
- type (LONG/SHORT)
- score (0–100) + confidence label
- timeframe alignment summary
- entry range or breakout trigger
- multiple TPs, SL
- reason list (Dow/Wyckoff/RSI/MACD/Dominance/etc.)
- liquidity & funding note
- timestamp  
- signal UUID

==================================================
      SERVICE 5 — NOTIFICATION SERVICE
==================================================

Responsibilities:
- Receive "price_update_ready" and "signal_generated".
- Send messages to correct Telegram channels:
  - Price → @ftlssignalzhan
  - Signals → @livingcoinpricechannel
- Handle retry, error logs, and rate limit protection.

==================================================
                 CODING RULES
==================================================

- Follow all logic EXACTLY as above.
- Do not invent new behavior unless requested.
- Refactor code to clean architecture.
- Add type hints, docstrings, modularity.
- Every function must follow business rules strictly.
- If code contradicts these rules → rewrite correctly.
- Use MongoDB collections:
  - market_data
  - analysis
  - signals
  - price_updates
  - logs

==================================================
                 WHEN I ASK
==================================================

Whenever I ask to:
- refactor a file
- write a new module
- improve logic
- debug
- extend features

You MUST always:
- enforce ALL business logic above  
- maintain microservice architecture  
- produce correct, robust, scalable Python code  

You are NOT allowed to break or ignore the specifications above.
