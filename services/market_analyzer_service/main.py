"""
Crypto Market Analyzer Service

The Analyzer interprets price structure using:
1) Dow Theory
2) Wyckoff Method
3) Gann Theory
4) Dominance Analysis
5) Indicators (EMA, RSI, MACD, Volume, Funding, OI)

Evaluates all timeframes and generates final market sentiment:
- bullish / bearish / neutral
- trend strength score (0–100)
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd

from shared.logger import setup_logger
from shared.database import get_database
from shared.events import subscribe_events, publish_event
from shared.config import (
    COLLECTION_MARKET_DATA, COLLECTION_ANALYSIS,
    EVENT_MARKET_DATA_UPDATED, EVENT_MARKET_ANALYSIS_COMPLETED
)
from shared.theories import (
    analyze_dow_theory, analyze_wyckoff, analyze_gann,
    calculate_ema, calculate_rsi, calculate_macd
)

logger = setup_logger("market_analyzer_service")


class MarketAnalyzer:
    """Service for analyzing market using multiple theories and indicators."""
    
    def __init__(self):
        self.db = get_database()
        self.market_data_collection = self.db[COLLECTION_MARKET_DATA]
        self.analysis_collection = self.db[COLLECTION_ANALYSIS]
    
    def get_latest_market_data(self) -> Optional[Dict]:
        """Get latest market data from MongoDB."""
        try:
            latest = self.market_data_collection.find_one(
                sort=[("timestamp", -1)]
            )
            return latest
        except Exception as e:
            logger.error(f"Error getting latest market data: {e}")
            return None
    
    def analyze_timeframe(self, df: pd.DataFrame, timeframe: str) -> Dict:
        """Analyze a single timeframe."""
        if df is None or len(df) < 20:
            return {}
        
        prices = df['close'].values
        volumes = df['volume'].values
        
        # Dow Theory
        dow_analysis = analyze_dow_theory(df)
        
        # Wyckoff
        wyckoff_analysis = analyze_wyckoff(df)
        
        # Gann
        gann_analysis = analyze_gann(df)
        
        # Indicators
        ema20 = calculate_ema(prices, 20) if len(prices) >= 20 else None
        ema50 = calculate_ema(prices, 50) if len(prices) >= 50 else None
        ema200 = calculate_ema(prices, 200) if len(prices) >= 200 else None
        
        rsi = calculate_rsi(prices, 14)
        macd = calculate_macd(prices)
        
        # Volume analysis
        current_volume = volumes[-1] if len(volumes) > 0 else None
        avg_volume = float(pd.Series(volumes).mean()) if len(volumes) > 0 else None
        volume_spike = (current_volume / avg_volume) > 1.5 if (current_volume and avg_volume) else False
        
        return {
            "timeframe": timeframe,
            "dow": dow_analysis,
            "wyckoff": wyckoff_analysis,
            "gann": gann_analysis,
            "indicators": {
                "ema20": float(ema20) if ema20 else None,
                "ema50": float(ema50) if ema50 else None,
                "ema200": float(ema200) if ema200 else None,
                "rsi": rsi,
                "macd": macd,
                "volume_spike": volume_spike
            },
            "current_price": float(prices[-1]) if len(prices) > 0 else None
        }
    
    def analyze_dominance(self, market_data: Dict) -> Dict:
        """Analyze dominance metrics."""
        metrics = market_data.get("market_metrics", {})
        
        btc_dom = metrics.get("btc_dominance")
        usdt_dom = metrics.get("usdt_dominance")
        total_mcap = metrics.get("total_market_cap")
        
        analysis = {
            "btc_dominance": btc_dom,
            "usdt_dominance": usdt_dom,
            "total_market_cap": total_mcap,
            "interpretation": {}
        }
        
        # BTC.D analysis
        if btc_dom:
            if btc_dom > 55:
                analysis["interpretation"]["btc_dom"] = "rising_money_into_btc_alts_weaken"
            elif btc_dom < 45:
                analysis["interpretation"]["btc_dom"] = "falling_good_for_alts"
            else:
                analysis["interpretation"]["btc_dom"] = "neutral"
        
        # USDT.D analysis
        if usdt_dom:
            if usdt_dom > 5.0:  # Threshold may need adjustment
                analysis["interpretation"]["usdt_dom"] = "rising_risk_off_shorts_favored"
            else:
                analysis["interpretation"]["usdt_dom"] = "stable_or_falling"
        
        # TOTAL2 analysis (would need additional data)
        if total_mcap:
            analysis["interpretation"]["total_mcap"] = "available"
        
        return analysis
    
    def calculate_sentiment_score(self, timeframe_analyses: Dict[str, Dict], 
                                  dominance_analysis: Dict) -> Dict:
        """Calculate overall market sentiment and trend strength (0-100)."""
        bullish_signals = 0
        bearish_signals = 0
        total_signals = 0
        
        # Analyze each timeframe
        for timeframe, analysis in timeframe_analyses.items():
            # Dow Theory
            dow = analysis.get("dow", {})
            if dow:
                trend = dow.get("trend", "neutral")
                if trend == "bullish":
                    bullish_signals += 1
                elif trend == "bearish":
                    bearish_signals += 1
                total_signals += 1
            
            # Wyckoff
            wyckoff = analysis.get("wyckoff", {})
            if wyckoff:
                phase = wyckoff.get("phase")
                if phase in ["ACCUMULATION", "MARKUP"]:
                    bullish_signals += 1
                elif phase in ["DISTRIBUTION", "MARKDOWN"]:
                    bearish_signals += 1
                total_signals += 1
            
            # Indicators
            indicators = analysis.get("indicators", {})
            rsi = indicators.get("rsi")
            if rsi:
                if rsi > 50:
                    bullish_signals += 0.5
                else:
                    bearish_signals += 0.5
                total_signals += 0.5
            
            macd = indicators.get("macd", {})
            if macd.get("histogram"):
                if macd["histogram"] > 0:
                    bullish_signals += 0.5
                else:
                    bearish_signals += 0.5
                total_signals += 0.5
        
        # Dominance effects
        dom_interp = dominance_analysis.get("interpretation", {})
        btc_dom_interp = dom_interp.get("btc_dom", "")
        if "falling_good_for_alts" in btc_dom_interp:
            bullish_signals += 1
        elif "rising_money_into_btc" in btc_dom_interp:
            bearish_signals += 1
        total_signals += 1
        
        # Calculate sentiment
        if total_signals == 0:
            sentiment = "neutral"
            trend_strength = 0
        else:
            bullish_ratio = bullish_signals / total_signals
            if bullish_ratio > 0.6:
                sentiment = "bullish"
            elif bullish_ratio < 0.4:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
            
            # Trend strength (0-100)
            trend_strength = int(abs(bullish_ratio - 0.5) * 200)
        
        return {
            "sentiment": sentiment,
            "trend_strength": trend_strength,
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals,
            "total_signals": total_signals
        }
    
    def analyze_market(self):
        """Perform complete market analysis."""
        logger.info("Starting market analysis")
        
        # Get latest market data
        market_data = self.get_latest_market_data()
        if not market_data:
            logger.warning("No market data available")
            return
        
        # Analyze each coin and timeframe
        all_analyses = {}
        candlesticks = market_data.get("candlesticks", {})
        
        for symbol, timeframes_data in candlesticks.items():
            all_analyses[symbol] = {}
            
            for timeframe, candles_list in timeframes_data.items():
                if not candles_list:
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame(candles_list)
                if 'timestamp' in df.columns:
                    # Handle both string and datetime timestamps
                    if df['timestamp'].dtype == 'object':
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Ensure required columns exist
                required_cols = ['open', 'high', 'low', 'close', 'volume']
                if not all(col in df.columns for col in required_cols):
                    logger.warning(f"Missing required columns for {symbol} {timeframe}")
                    continue
                
                # Analyze this timeframe
                analysis = self.analyze_timeframe(df, timeframe)
                all_analyses[symbol][timeframe] = analysis
        
        # Analyze dominance
        dominance_analysis = self.analyze_dominance(market_data)
        
        # Calculate overall sentiment (focus on BTC for main sentiment)
        btc_analyses = all_analyses.get("BTCUSDT", {})
        if btc_analyses:
            sentiment_score = self.calculate_sentiment_score(btc_analyses, dominance_analysis)
        else:
            sentiment_score = {"sentiment": "neutral", "trend_strength": 0}
        
        # Create analysis document
        analysis_doc = {
            "timestamp": datetime.utcnow(),
            "market_data_timestamp": market_data.get("timestamp"),
            "symbol_analyses": all_analyses,
            "dominance_analysis": dominance_analysis,
            "sentiment": sentiment_score["sentiment"],
            "trend_strength": sentiment_score["trend_strength"],
            "sentiment_details": sentiment_score
        }
        
        # Store analysis
        try:
            self.analysis_collection.insert_one(analysis_doc)
            logger.info(f"Analysis stored: sentiment={sentiment_score['sentiment']}, strength={sentiment_score['trend_strength']}")
            
            # Publish event
            event_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "sentiment": sentiment_score["sentiment"],
                "trend_strength": sentiment_score["trend_strength"],
                "symbols_analyzed": list(all_analyses.keys())
            }
            publish_event(EVENT_MARKET_ANALYSIS_COMPLETED, event_data)
            logger.info("Published market_analysis_completed event")
        except Exception as e:
            logger.error(f"Error storing analysis: {e}")
    
    def handle_market_data_updated(self, event_name: str, data: Dict):
        """Handle market_data_updated event."""
        logger.info("Received market_data_updated event, starting analysis")
        self.analyze_market()
    
    def run(self):
        """Main service loop."""
        logger.info("Market Analyzer Service started")
        
        # Subscribe to market_data_updated events
        def event_handler(event_name: str, data: Dict):
            if event_name == EVENT_MARKET_DATA_UPDATED:
                self.handle_market_data_updated(event_name, data)
        
        try:
            subscribe_events(
                [EVENT_MARKET_DATA_UPDATED],
                event_handler,
                consumer_group="market_analyzer",
                consumer_name="analyzer_1"
            )
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        except Exception as e:
            logger.error(f"Error in service loop: {e}")


if __name__ == "__main__":
    analyzer = MarketAnalyzer()
    analyzer.run()

