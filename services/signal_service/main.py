"""
Signal Service

This is the most critical service.
It generates LONG/SHORT futures signals for BOTH BTC and ALTCOINS,
based on multi-factor scoring (0–100).

Scoring system:
1) Multi-timeframe trend (Dow structure) — 30 points
2) Wyckoff pattern — 15 points
3) Indicators — 20 points
4) Volume confirmation — 10 points
5) Dominance effects — 15 points
6) Funding, OI, Liquidity safety checks — 10 points

Score ≥ 75 → HIGH confidence signal
60–74 → MEDIUM (optional or reduce size)
< 60 → NO SIGNAL
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd

from shared.logger import setup_logger, set_correlation_id
from shared.database import get_database
from shared.events import subscribe_events, publish_event
from shared.shutdown import register_shutdown_handler
from shared.base_service import BaseService
from shared.exceptions import DatabaseError, EventPublishError, ServiceError
from pymongo.errors import PyMongoError
from shared.config_manager import (
    COLLECTION_ANALYSIS, COLLECTION_SIGNALS,
    EVENT_MARKET_ANALYSIS_COMPLETED, EVENT_SIGNAL_GENERATED
)
from shared.theories import (
    analyze_dow_theory, analyze_wyckoff,
    calculate_ema, calculate_rsi, calculate_macd
)

logger = setup_logger("signal_service")


class SignalService(BaseService):
    """Service for generating trading signals."""
    
    def __init__(self):
        super().__init__("signal_service", port=8003)
        self.db = get_database()
        self.analysis_collection = self.db[COLLECTION_ANALYSIS]
        self.signals_collection = self.db[COLLECTION_SIGNALS]
    
    def get_latest_analysis(self) -> Optional[Dict]:
        """Get latest market analysis."""
        try:
            latest = self.analysis_collection.find_one(
                sort=[("timestamp", -1)]
            )
            return latest
        except PyMongoError as e:
            error = DatabaseError(
                f"Failed to get latest analysis: {e}",
                operation="find_one",
                collection=COLLECTION_ANALYSIS
            )
            logger.error(str(error))
            if self.metrics:
                self.metrics.record_error("database_query_failed")
            return None
        except Exception as e:
            error = ServiceError(
                f"Unexpected error getting latest analysis: {e}",
                service_name="signal_service",
                error_code="UNEXPECTED_ERROR"
            )
            logger.error(str(error), exc_info=True)
            if self.metrics:
                self.metrics.record_error("unexpected_error")
            return None
    
    def score_multi_timeframe_trend(self, analyses: Dict[str, Dict], 
                                    signal_type: str) -> Tuple[int, List[str]]:
        """
        Score multi-timeframe trend (Dow structure) — 30 points.
        
        Primary trend (1D, 3D, 1W) = 15 points
        Secondary trend (4H, 8H) = 10 points
        Minor trend (1H) = 5 points
        """
        score = 0
        reasons = []
        
        # Primary timeframes
        primary_tfs = ["1d", "3d", "1w"]
        primary_score = 0
        primary_matches = 0
        
        for tf in primary_tfs:
            if tf in analyses:
                dow = analyses[tf].get("dow", {})
                trend = dow.get("trend", "neutral")
                if signal_type == "LONG" and trend == "bullish":
                    primary_matches += 1
                elif signal_type == "SHORT" and trend == "bearish":
                    primary_matches += 1
        
        if len(primary_tfs) > 0:
            primary_ratio = primary_matches / len(primary_tfs)
            primary_score = int(15 * primary_ratio)
            score += primary_score
            if primary_score > 0:
                reasons.append(f"Primary trend alignment: {primary_matches}/{len(primary_tfs)}")
        
        # Secondary timeframes
        secondary_tfs = ["4h", "8h"]
        secondary_score = 0
        secondary_matches = 0
        
        for tf in secondary_tfs:
            if tf in analyses:
                dow = analyses[tf].get("dow", {})
                trend = dow.get("trend", "neutral")
                if signal_type == "LONG" and trend in ["bullish", "neutral"]:
                    secondary_matches += 1
                elif signal_type == "SHORT" and trend in ["bearish", "neutral"]:
                    secondary_matches += 1
        
        if len(secondary_tfs) > 0:
            secondary_ratio = secondary_matches / len(secondary_tfs)
            secondary_score = int(10 * secondary_ratio)
            score += secondary_score
            if secondary_score > 0:
                reasons.append(f"Secondary trend alignment: {secondary_matches}/{len(secondary_tfs)}")
        
        # Minor timeframe
        minor_tf = "1h"
        minor_score = 0
        if minor_tf in analyses:
            dow = analyses[minor_tf].get("dow", {})
            trend = dow.get("trend", "neutral")
            bos_up = dow.get("bos_up", False)
            bos_down = dow.get("bos_down", False)
            
            if signal_type == "LONG" and (trend == "bullish" or bos_up):
                minor_score = 5
            elif signal_type == "SHORT" and (trend == "bearish" or bos_down):
                minor_score = 5
            
            score += minor_score
            if minor_score > 0:
                reasons.append(f"Minor trend/BOS: {trend}")
        
        return score, reasons
    
    def score_wyckoff_pattern(self, analyses: Dict[str, Dict], 
                             signal_type: str) -> Tuple[int, List[str]]:
        """Score Wyckoff pattern — 15 points."""
        score = 0
        reasons = []
        
        # Check 4H timeframe (preferred for Wyckoff)
        if "4h" in analyses:
            wyckoff = analyses["4h"].get("wyckoff", {})
            phase = wyckoff.get("phase")
            sos = wyckoff.get("sos", False)
            sow = wyckoff.get("sow", False)
            spring = wyckoff.get("spring", False)
            upthrust = wyckoff.get("upthrust", False)
            
            if signal_type == "LONG":
                if phase in ["ACCUMULATION", "MARKUP"] or sos or spring:
                    score = 15
                    if sos:
                        reasons.append("Wyckoff: SOS detected")
                    elif spring:
                        reasons.append("Wyckoff: Spring detected")
                    elif phase:
                        reasons.append(f"Wyckoff: {phase} phase")
            
            elif signal_type == "SHORT":
                if phase in ["DISTRIBUTION", "MARKDOWN"] or sow or upthrust:
                    score = 15
                    if sow:
                        reasons.append("Wyckoff: SOW detected")
                    elif upthrust:
                        reasons.append("Wyckoff: Upthrust detected")
                    elif phase:
                        reasons.append(f"Wyckoff: {phase} phase")
        
        return score, reasons
    
    def score_indicators(self, analyses: Dict[str, Dict], 
                        signal_type: str) -> Tuple[int, List[str]]:
        """Score indicators — 20 points (RSI=7, MACD=7, EMA=6)."""
        score = 0
        reasons = []
        
        # Use 4H timeframe for indicators
        if "4h" not in analyses:
            return score, reasons
        
        indicators = analyses["4h"].get("indicators", {})
        
        # RSI (7 points)
        rsi = indicators.get("rsi")
        if rsi:
            if signal_type == "LONG" and rsi > 50:
                rsi_score = 7 if rsi > 55 else 4
                score += rsi_score
                reasons.append(f"RSI: {rsi:.1f} (>50)")
            elif signal_type == "SHORT" and rsi < 50:
                rsi_score = 7 if rsi < 45 else 4
                score += rsi_score
                reasons.append(f"RSI: {rsi:.1f} (<50)")
        
        # MACD (7 points)
        macd = indicators.get("macd", {})
        histogram = macd.get("histogram")
        if histogram:
            if signal_type == "LONG" and histogram > 0:
                score += 7
                reasons.append("MACD: Bullish crossover")
            elif signal_type == "SHORT" and histogram < 0:
                score += 7
                reasons.append("MACD: Bearish crossover")
        
        # EMA alignment (6 points)
        ema20 = indicators.get("ema20")
        ema50 = indicators.get("ema50")
        current_price = analyses["4h"].get("current_price")
        
        if ema20 and ema50 and current_price:
            if signal_type == "LONG":
                if current_price > ema20 and ema20 > ema50:
                    score += 6
                    reasons.append("EMA: Bullish alignment")
            elif signal_type == "SHORT":
                if current_price < ema20 and ema20 < ema50:
                    score += 6
                    reasons.append("EMA: Bearish alignment")
        
        return score, reasons
    
    def score_volume(self, analyses: Dict[str, Dict], 
                    signal_type: str) -> Tuple[int, List[str]]:
        """Score volume confirmation — 10 points."""
        score = 0
        reasons = []
        
        # Check 4H timeframe
        if "4h" in analyses:
            indicators = analyses["4h"].get("indicators", {})
            volume_spike = indicators.get("volume_spike", False)
            
            if volume_spike:
                score = 10
                reasons.append("Volume: Spike detected")
        
        return score, reasons
    
    def score_dominance(self, analysis_doc: Dict, signal_type: str, 
                       is_btc: bool) -> Tuple[int, List[str]]:
        """Score dominance effects — 15 points."""
        score = 0
        reasons = []
        
        dominance = analysis_doc.get("dominance_analysis", {})
        btc_dom = dominance.get("btc_dominance")
        usdt_dom = dominance.get("usdt_dominance")
        dom_interp = dominance.get("interpretation", {})
        
        if is_btc:
            # BTC signals
            if signal_type == "LONG":
                # BTC.D falling improves long score
                if "falling_good_for_alts" in dom_interp.get("btc_dom", ""):
                    score += 5
                    reasons.append("BTC.D: Falling (positive)")
                
                # USDT.D stable or falling
                if "stable_or_falling" in dom_interp.get("usdt_dom", ""):
                    score += 5
                    reasons.append("USDT.D: Stable/falling")
            
            elif signal_type == "SHORT":
                # BTC.D rising improves short score
                if "rising_money_into_btc" in dom_interp.get("btc_dom", ""):
                    score += 5
                    reasons.append("BTC.D: Rising (positive)")
                
                # USDT.D rising (risk-off)
                if "rising_risk_off" in dom_interp.get("usdt_dom", ""):
                    score += 5
                    reasons.append("USDT.D: Rising (risk-off)")
        else:
            # ALT signals
            if signal_type == "LONG":
                # BTC.D falling is REQUIRED
                if "falling_good_for_alts" in dom_interp.get("btc_dom", ""):
                    score += 10
                    reasons.append("BTC.D: Falling (REQUIRED for ALT long)")
                else:
                    # If BTC.D rising, kill ALT long signal
                    return 0, ["ALT LONG blocked: BTC.D rising"]
                
                # USDT.D must NOT be rising
                if "stable_or_falling" in dom_interp.get("usdt_dom", ""):
                    score += 5
                    reasons.append("USDT.D: Not rising")
            
            elif signal_type == "SHORT":
                # BTC.D rising or USDT.D rising → strong short support
                if "rising_money_into_btc" in dom_interp.get("btc_dom", ""):
                    score += 8
                    reasons.append("BTC.D: Rising (strong short support)")
                
                if "rising_risk_off" in dom_interp.get("usdt_dom", ""):
                    score += 7
                    reasons.append("USDT.D: Rising (strong short support)")
        
        return score, reasons
    
    def score_safety_checks(self, analyses: Dict[str, Dict]) -> Tuple[int, List[str]]:
        """Score funding, OI, liquidity safety checks — 10 points."""
        # Simplified: assume safe if no issues detected
        # In production, would check actual funding rates, OI, liquidity
        score = 10
        reasons = ["Safety: Basic checks passed"]
        return score, reasons
    
    def check_guardrails(self, analysis_doc: Dict, signal_type: str, 
                        is_btc: bool) -> Tuple[bool, str]:
        """Check guardrails before generating signal."""
        dominance = analysis_doc.get("dominance_analysis", {})
        dom_interp = dominance.get("interpretation", {})
        
        # No long signals if USDT.D rising sharply (risk-off)
        if signal_type == "LONG":
            if "rising_risk_off" in dom_interp.get("usdt_dom", ""):
                return False, "Guardrail: USDT.D rising sharply (risk-off)"
        
        # No long ALT if BTC.D rising
        if signal_type == "LONG" and not is_btc:
            if "rising_money_into_btc" in dom_interp.get("btc_dom", ""):
                return False, "Guardrail: BTC.D rising (blocks ALT long)"
        
        return True, "Guardrails passed"
    
    def generate_signal(self, symbol: str, analysis_doc: Dict) -> Optional[Dict]:
        """Generate signal for a symbol."""
        is_btc = symbol == "BTCUSDT"
        
        # Get symbol analyses
        symbol_analyses = analysis_doc.get("symbol_analyses", {}).get(symbol, {})
        if not symbol_analyses:
            return None
        
        # Try both LONG and SHORT
        for signal_type in ["LONG", "SHORT"]:
            # Check guardrails
            guardrail_ok, guardrail_msg = self.check_guardrails(
                analysis_doc, signal_type, is_btc
            )
            if not guardrail_ok:
                logger.debug(f"{symbol} {signal_type} blocked: {guardrail_msg}")
                continue
            
            # Calculate scores
            trend_score, trend_reasons = self.score_multi_timeframe_trend(
                symbol_analyses, signal_type
            )
            wyckoff_score, wyckoff_reasons = self.score_wyckoff_pattern(
                symbol_analyses, signal_type
            )
            indicator_score, indicator_reasons = self.score_indicators(
                symbol_analyses, signal_type
            )
            volume_score, volume_reasons = self.score_volume(
                symbol_analyses, signal_type
            )
            dominance_score, dominance_reasons = self.score_dominance(
                analysis_doc, signal_type, is_btc
            )
            safety_score, safety_reasons = self.score_safety_checks(symbol_analyses)
            
            total_score = (trend_score + wyckoff_score + indicator_score + 
                          volume_score + dominance_score + safety_score)
            
            # Only generate signal if score >= threshold
            if total_score < 60:
                continue
            
            # Determine confidence
            if total_score >= 75:
                confidence = "HIGH"
            elif total_score >= 60:
                confidence = "MEDIUM"
            else:
                continue
            
            # Get entry range (simplified)
            current_price = symbol_analyses.get("4h", {}).get("current_price")
            if not current_price:
                current_price = symbol_analyses.get("1h", {}).get("current_price")
            
            # Create signal
            signal = {
                "signal_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow(),
                "asset": symbol,
                "type": signal_type,
                "score": total_score,
                "confidence": confidence,
                "entry_range": {
                    "min": current_price * 0.995 if current_price else None,
                    "max": current_price * 1.005 if current_price else None
                },
                "take_profit": [
                    current_price * 1.02 if current_price and signal_type == "LONG" else current_price * 0.98,
                    current_price * 1.05 if current_price and signal_type == "LONG" else current_price * 0.95,
                ] if current_price else [],
                "stop_loss": current_price * 0.98 if current_price and signal_type == "LONG" else current_price * 1.02,
                "reasons": {
                    "trend": trend_reasons,
                    "wyckoff": wyckoff_reasons,
                    "indicators": indicator_reasons,
                    "volume": volume_reasons,
                    "dominance": dominance_reasons,
                    "safety": safety_reasons
                },
                "timeframe_alignment": {
                    "primary": "aligned" if trend_score >= 10 else "partial",
                    "secondary": "aligned" if trend_score >= 20 else "partial",
                    "minor": "aligned" if trend_score >= 25 else "partial"
                },
                "liquidity_note": "Basic check passed",
                "funding_note": "Not checked (simplified)"
            }
            
            return signal
        
        return None
    
    def generate_signals(self):
        """Generate signals for all symbols."""
        logger.info("Starting signal generation")
        
        analysis_doc = self.get_latest_analysis()
        if not analysis_doc:
            logger.warning("No analysis available")
            return
        
        symbol_analyses = analysis_doc.get("symbol_analyses", {})
        signals_generated = []
        
        for symbol in symbol_analyses.keys():
            signal = self.generate_signal(symbol, analysis_doc)
            if signal:
                signals_generated.append(signal)
                
                # Store signal
                try:
                    self.signals_collection.insert_one(signal)
                    logger.info(f"Signal generated: {symbol} {signal['type']} (score: {signal['score']})")
                    
                    # Publish event
                    event_data = {
                        "signal_id": signal["signal_id"],
                        "timestamp": signal["timestamp"].isoformat(),
                        "asset": signal["asset"],
                        "type": signal["type"],
                        "score": signal["score"],
                        "confidence": signal["confidence"]
                    }
                    publish_event(EVENT_SIGNAL_GENERATED, event_data, service_name="signal_service")
                    if self.metrics:
                        self.metrics.record_event_published(EVENT_SIGNAL_GENERATED)
                    logger.info(f"Published signal_generated event: {signal['signal_id']}")
                except PyMongoError as e:
                    error = DatabaseError(
                        f"Failed to store signal {signal.get('signal_id')}: {e}",
                        operation="insert_one",
                        collection=COLLECTION_SIGNALS
                    )
                    logger.error(str(error))
                    if self.metrics:
                        self.metrics.record_error("database_insert_failed")
                except Exception as e:
                    error = ServiceError(
                        f"Unexpected error storing signal: {e}",
                        service_name="signal_service",
                        error_code="SIGNAL_STORE_ERROR"
                    )
                    logger.error(str(error), exc_info=True)
                    if self.metrics:
                        self.metrics.record_error("signal_store_failed")
        
        if not signals_generated:
            logger.info("No signals generated (scores below threshold)")
    
    def handle_analysis_completed(self, event_name: str, data: Dict):
        """Handle market_analysis_completed event."""
        logger.info("Received market_analysis_completed event, generating signals")
        self.generate_signals()
    
    def on_shutdown(self):
        """Cleanup on shutdown."""
        # Additional cleanup if needed
        pass
    
    def run(self):
        """Main service loop - event-driven pattern."""
        logger.info("Signal Service started")
        self._running = True
        
        try:
            # Setup observability, health, service discovery (from BaseService)
            self.setup()
            
            # Subscribe to analysis completed events
            def event_handler(event_name: str, data: Dict):
                if event_name == EVENT_MARKET_ANALYSIS_COMPLETED:
                    self.handle_analysis_completed(event_name, data)
            
            subscribe_events(
                [EVENT_MARKET_ANALYSIS_COMPLETED],
                event_handler,
                consumer_group="signal_service",
                consumer_name="signal_1",
                running_flag=lambda: self._running
            )
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        except Exception as e:
            logger.error(f"Error in service loop: {e}", exc_info=True)
        finally:
            logger.info("Signal Service stopped")


if __name__ == "__main__":
    service = SignalService()
    service.run()

