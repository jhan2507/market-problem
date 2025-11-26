"""
Technical analysis theories: Dow Theory, Wyckoff Method, Gann Theory.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, List, Tuple
from enum import Enum


class Trend(Enum):
    """Trend direction."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class WyckoffPhase(Enum):
    """Wyckoff phases."""
    ACCUMULATION = "ACCUMULATION"
    MARKUP = "MARKUP"
    DISTRIBUTION = "DISTRIBUTION"
    MARKDOWN = "MARKDOWN"
    NONE = None


def analyze_dow_theory(df: pd.DataFrame) -> Optional[Dict]:
    """
    Analyze using Dow Theory.
    
    Primary trend = 1D, 3D, 1W
    Secondary trend = 4H, 8H
    Minor trend = 1H
    
    Identify HH, HL (uptrend) and LH, LL (downtrend)
    Detect BOS (Break of Structure)
    
    Args:
        df: DataFrame with ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    
    Returns:
        Dict with trend analysis
    """
    if df is None or len(df) < 20:
        return None
    
    prices = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    
    # Identify swing highs and lows
    swing_highs = []
    swing_lows = []
    
    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
           highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            swing_highs.append((i, highs[i]))
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
           lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            swing_lows.append((i, lows[i]))
    
    # Determine trend
    trend = Trend.NEUTRAL
    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        # Check for HH, HL (uptrend)
        if swing_highs[-1][1] > swing_highs[-2][1] and \
           swing_lows[-1][1] > swing_lows[-2][1]:
            trend = Trend.BULLISH
        # Check for LH, LL (downtrend)
        elif swing_highs[-1][1] < swing_highs[-2][1] and \
             swing_lows[-1][1] < swing_lows[-2][1]:
            trend = Trend.BEARISH
    
    # Detect BOS (Break of Structure)
    bos_up = False
    bos_down = False
    
    if len(swing_highs) >= 1 and len(swing_lows) >= 1:
        last_swing_high = swing_highs[-1][1]
        last_swing_low = swing_lows[-1][1]
        current_high = highs[-1]
        current_low = lows[-1]
        
        if current_high > last_swing_high:
            bos_up = True
        if current_low < last_swing_low:
            bos_down = True
    
    # Volume confirmation
    volumes = df['volume'].values
    recent_volume = np.mean(volumes[-5:])
    avg_volume = np.mean(volumes[-20:])
    volume_confirmation = recent_volume > avg_volume * 1.2
    
    return {
        "trend": trend.value,
        "bos_up": bos_up,
        "bos_down": bos_down,
        "swing_highs": len(swing_highs),
        "swing_lows": len(swing_lows),
        "volume_confirmation": volume_confirmation,
        "trend_strength": 0.7 if volume_confirmation else 0.5
    }


def analyze_wyckoff(df: pd.DataFrame) -> Optional[Dict]:
    """
    Analyze using Wyckoff Method.
    
    Identify Accumulation / Distribution
    Recognize Spring / Upthrust
    Detect SOS / SOW
    Identify Phases A–E
    
    Args:
        df: DataFrame with ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    
    Returns:
        Dict with Wyckoff analysis
    """
    if df is None or len(df) < 50:
        return None
    
    prices = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    volumes = df['volume'].values
    
    # Calculate price range
    recent_high = np.max(highs[-20:])
    recent_low = np.min(lows[-20:])
    price_range = recent_high - recent_low
    current_price = prices[-1]
    price_position = (current_price - recent_low) / price_range if price_range > 0 else 0.5
    
    # Volume analysis
    recent_volume = np.mean(volumes[-5:])
    avg_volume = np.mean(volumes[-20:])
    volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
    
    # Moving averages
    short_ma = np.mean(prices[-10:])
    long_ma = np.mean(prices[-30:])
    
    # Detect Spring (false breakdown)
    spring = False
    if price_position < 0.3:
        # Price breaks below recent low but recovers quickly
        if len(lows) >= 3:
            if lows[-1] < lows[-2] and prices[-1] > lows[-2]:
                spring = True
    
    # Detect Upthrust (false breakout)
    upthrust = False
    if price_position > 0.7:
        # Price breaks above recent high but fails
        if len(highs) >= 3:
            if highs[-1] > highs[-2] and prices[-1] < highs[-2]:
                upthrust = True
    
    # Detect SOS (Sign of Strength) - strong upward move with volume
    sos = False
    if len(prices) >= 2:
        price_change = (prices[-1] - prices[-2]) / prices[-2]
        if price_change > 0.02 and volume_ratio > 1.3:  # 2% up with 30% more volume
            sos = True
    
    # Detect SOW (Sign of Weakness) - strong downward move with volume
    sow = False
    if len(prices) >= 2:
        price_change = (prices[-1] - prices[-2]) / prices[-2]
        if price_change < -0.02 and volume_ratio > 1.3:  # 2% down with 30% more volume
            sow = True
    
    # Determine phase
    phase = WyckoffPhase.NONE
    if price_position < 0.3 and short_ma < long_ma:
        if spring or (volume_ratio > 1.2 and prices[-1] > prices[-5]):
            phase = WyckoffPhase.ACCUMULATION
    elif price_position > 0.3 and short_ma > long_ma and volume_ratio > 1.1:
        phase = WyckoffPhase.MARKUP
    elif price_position > 0.7 and short_ma > long_ma:
        if upthrust or (volume_ratio < 0.9 and prices[-1] < prices[-5]):
            phase = WyckoffPhase.DISTRIBUTION
    elif price_position < 0.7 and short_ma < long_ma and volume_ratio > 1.1:
        phase = WyckoffPhase.MARKDOWN
    
    return {
        "phase": phase.value if phase != WyckoffPhase.NONE else None,
        "spring": spring,
        "upthrust": upthrust,
        "sos": sos,
        "sow": sow,
        "price_position": float(price_position),
        "volume_ratio": float(volume_ratio),
        "strength": 0.8 if (sos or spring) else (0.6 if phase != WyckoffPhase.NONE else 0.3)
    }


def analyze_gann(df: pd.DataFrame) -> Optional[Dict]:
    """
    Analyze using Gann Theory.
    
    Time/Price cycles
    Gann Angles (1x1, 2x1, 4x1)
    Detect reversal windows
    
    Args:
        df: DataFrame with ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    
    Returns:
        Dict with Gann analysis
    """
    if df is None or len(df) < 50:
        return None
    
    prices = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    
    # Find significant high and low
    significant_high_idx = np.argmax(highs[-50:])
    significant_low_idx = np.argmin(lows[-50:])
    significant_high = highs[-50:][significant_high_idx]
    significant_low = lows[-50:][significant_low_idx]
    
    # Calculate price range
    price_range = significant_high - significant_low
    if price_range == 0:
        return None
    
    # Calculate time range
    time_range = len(df) - 50
    
    # Gann Angles (1x1 = 45 degrees)
    # Simplified: check if price is following 1x1 angle
    current_price = prices[-1]
    price_from_low = current_price - significant_low
    time_from_low = len(df) - (50 + significant_low_idx)
    
    if time_from_low > 0:
        gann_1x1_slope = price_range / time_range
        expected_price_1x1 = significant_low + (time_from_low * gann_1x1_slope)
        
        # Check if price is near 1x1 line
        price_deviation = abs(current_price - expected_price_1x1) / price_range
        
        # Reversal window detection (simplified)
        reversal_window = False
        if price_deviation > 0.1:  # Price deviated significantly
            # Check if price is reversing
            if len(prices) >= 3:
                recent_trend = (prices[-1] - prices[-3]) / prices[-3]
                if abs(recent_trend) < 0.01:  # Price stabilizing
                    reversal_window = True
        
        return {
            "gann_1x1_slope": float(gann_1x1_slope),
            "price_deviation": float(price_deviation),
            "reversal_window": reversal_window,
            "significant_high": float(significant_high),
            "significant_low": float(significant_low)
        }
    
    return None


def calculate_ema(prices: np.ndarray, period: int) -> float:
    """Calculate Exponential Moving Average."""
    if len(prices) < period:
        return np.mean(prices)
    return pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1]


def calculate_rsi(prices: np.ndarray, period: int = 14) -> Optional[float]:
    """Calculate RSI."""
    if len(prices) < period + 1:
        return None
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi)


def calculate_macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
    """Calculate MACD."""
    if len(prices) < slow:
        return {"macd": None, "signal": None, "histogram": None}
    
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd_line = ema_fast - ema_slow
    
    # Calculate signal line (EMA of MACD)
    if len(prices) >= slow + signal:
        macd_series = []
        for i in range(slow, len(prices)):
            ema_f = calculate_ema(prices[:i+1], fast)
            ema_s = calculate_ema(prices[:i+1], slow)
            macd_series.append(ema_f - ema_s)
        
        if len(macd_series) >= signal:
            signal_line = calculate_ema(np.array(macd_series), signal)
            histogram = macd_line - signal_line
            return {
                "macd": float(macd_line),
                "signal": float(signal_line),
                "histogram": float(histogram)
            }
    
    return {"macd": float(macd_line), "signal": None, "histogram": None}

