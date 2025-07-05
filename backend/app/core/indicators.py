"""
Technical Indicators Library - Comprehensive indicator calculations
Strategic integration from multiple projects with enhanced functionality
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional, Union

class TechnicalIndicators:
    """Comprehensive technical indicators calculation engine"""
    
    @staticmethod
    def calculate_indicator(
        data: pd.DataFrame,
        indicator_type: str,
        source: str = "close",
        period: int = 14,
        **kwargs
    ) -> Union[pd.Series, Tuple[pd.Series, ...]]:
        """Calculate technical indicator with unified interface"""
        if data.empty:
            raise ValueError("Input data cannot be empty")
        
        if source in data.columns:
            source_data = data[source]
        else:
            if source == "hl2":
                source_data = (data['high'] + data['low']) / 2
            elif source == "hlc3":
                source_data = (data['high'] + data['low'] + data['close']) / 3
            elif source == "ohlc4":
                source_data = (data['open'] + data['high'] + data['low'] + data['close']) / 4
            else:
                raise ValueError(f"Unknown source: {source}")
        
        indicator_type = indicator_type.lower()
        
        if indicator_type == "sma":
            return TechnicalIndicators._calculate_sma(source_data, period)
        elif indicator_type == "ema":
            return TechnicalIndicators._calculate_ema(source_data, period)
        elif indicator_type == "rsi":
            return TechnicalIndicators._calculate_rsi(source_data, period)
        elif indicator_type == "macd":
            return TechnicalIndicators._calculate_macd(
                source_data, 
                kwargs.get('fast_period', 12),
                kwargs.get('slow_period', 26),
                kwargs.get('signal_period', 9)
            )
        elif indicator_type == "bb":
            return TechnicalIndicators._calculate_bollinger_bands(
                source_data, period, kwargs.get('std_dev', 2.0)
            )
        elif indicator_type == "atr":
            return TechnicalIndicators._calculate_atr(data, period)
        elif indicator_type == "stoch":
            return TechnicalIndicators._calculate_stochastic(
                data, 
                kwargs.get('k_period', 14),
                kwargs.get('d_period', 3)
            )
        elif indicator_type == "obv":
            return TechnicalIndicators._calculate_obv(data)
        elif indicator_type == "vwap":
            return TechnicalIndicators._calculate_vwap(data)
        else:
            raise ValueError(f"Unsupported indicator type: {indicator_type}")
    
    @staticmethod
    def _calculate_sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=period, min_periods=1).mean()
    
    @staticmethod
    def _calculate_ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def _calculate_rsi(data: pd.Series, period: int) -> pd.Series:
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)
    
    @staticmethod
    def _calculate_macd(
        data: pd.Series, 
        fast_period: int = 12, 
        slow_period: int = 26, 
        signal_period: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = TechnicalIndicators._calculate_ema(data, fast_period)
        ema_slow = TechnicalIndicators._calculate_ema(data, slow_period)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators._calculate_ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def _calculate_bollinger_bands(
        data: pd.Series, 
        period: int, 
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands"""
        sma = TechnicalIndicators._calculate_sma(data, period)
        std = data.rolling(window=period, min_periods=1).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return upper_band, sma, lower_band
    
    @staticmethod
    def _calculate_atr(data: pd.DataFrame, period: int) -> pd.Series:
        """Average True Range"""
        high_low = data['high'] - data['low']
        high_close_prev = np.abs(data['high'] - data['close'].shift(1))
        low_close_prev = np.abs(data['low'] - data['close'].shift(1))
        
        true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        atr = true_range.rolling(window=period, min_periods=1).mean()
        
        return atr
    
    @staticmethod
    def _calculate_stochastic(
        data: pd.DataFrame, 
        k_period: int = 14, 
        d_period: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """Stochastic Oscillator"""
        lowest_low = data['low'].rolling(window=k_period, min_periods=1).min()
        highest_high = data['high'].rolling(window=k_period, min_periods=1).max()
        
        k_percent = 100 * ((data['close'] - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period, min_periods=1).mean()
        
        return k_percent.fillna(50), d_percent.fillna(50)
    
    @staticmethod
    def _calculate_obv(data: pd.DataFrame) -> pd.Series:
        """On-Balance Volume"""
        obv = pd.Series(index=data.index, dtype='float64')
        obv.iloc[0] = data['volume'].iloc[0]
        
        for i in range(1, len(data)):
            if data['close'].iloc[i] > data['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + data['volume'].iloc[i]
            elif data['close'].iloc[i] < data['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - data['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    @staticmethod
    def _calculate_vwap(data: pd.DataFrame) -> pd.Series:
        """Volume Weighted Average Price"""
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        vwap = (typical_price * data['volume']).cumsum() / data['volume'].cumsum()
        
        return vwap
    
    @staticmethod
    def get_available_indicators() -> Dict[str, Dict[str, Any]]:
        """Get comprehensive list of available indicators with metadata"""
        return {
            "sma": {
                "name": "Simple Moving Average",
                "description": "Average price over a specified period",
                "parameters": ["period", "source"],
                "category": "trend",
                "output_count": 1
            },
            "ema": {
                "name": "Exponential Moving Average", 
                "description": "Weighted moving average giving more weight to recent prices",
                "parameters": ["period", "source"],
                "category": "trend",
                "output_count": 1
            },
            "rsi": {
                "name": "Relative Strength Index",
                "description": "Momentum oscillator measuring speed and magnitude of price changes",
                "parameters": ["period", "source"],
                "category": "momentum",
                "output_count": 1,
                "range": [0, 100]
            },
            "macd": {
                "name": "MACD",
                "description": "Moving Average Convergence Divergence indicator",
                "parameters": ["fast_period", "slow_period", "signal_period", "source"],
                "category": "momentum",
                "output_count": 3,
                "outputs": ["macd_line", "signal_line", "histogram"]
            },
            "bb": {
                "name": "Bollinger Bands",
                "description": "Volatility bands around a moving average",
                "parameters": ["period", "std_dev", "source"],
                "category": "volatility",
                "output_count": 3,
                "outputs": ["upper_band", "middle_band", "lower_band"]
            },
            "atr": {
                "name": "Average True Range",
                "description": "Volatility indicator measuring true range over a period",
                "parameters": ["period"],
                "category": "volatility",
                "output_count": 1
            },
            "stoch": {
                "name": "Stochastic Oscillator",
                "description": "Momentum indicator comparing closing price to price range",
                "parameters": ["k_period", "d_period"],
                "category": "momentum",
                "output_count": 2,
                "outputs": ["percent_k", "percent_d"],
                "range": [0, 100]
            },
            "obv": {
                "name": "On-Balance Volume",
                "description": "Volume indicator relating volume to price change",
                "parameters": [],
                "category": "volume",
                "output_count": 1
            },
            "vwap": {
                "name": "Volume Weighted Average Price",
                "description": "Average price weighted by volume",
                "parameters": [],
                "category": "volume",
                "output_count": 1
            }
        }
    
    @staticmethod
    def calculate_multiple_indicators(
        data: pd.DataFrame, 
        indicator_configs: list
    ) -> Dict[str, pd.Series]:
        """Calculate multiple indicators efficiently"""
        results = {}
        
        for config in indicator_configs:
            indicator_type = config.get('type')
            period = config.get('period', 14)
            source = config.get('source', 'close')
            
            if indicator_type == "macd":
                fast = config.get('fast_period', 12)
                slow = config.get('slow_period', 26)
                signal = config.get('signal_period', 9)
                indicator_name = f"{indicator_type}_{fast}_{slow}_{signal}"
                
                macd_line, signal_line, histogram = TechnicalIndicators.calculate_indicator(
                    data, indicator_type, source, period,
                    fast_period=fast, slow_period=slow, signal_period=signal
                )
                
                results[f"{indicator_name}_line"] = macd_line
                results[f"{indicator_name}_signal"] = signal_line
                results[f"{indicator_name}_histogram"] = histogram
                
            elif indicator_type == "bb":
                std_dev = config.get('std_dev', 2.0)
                indicator_name = f"{indicator_type}_{period}"
                
                upper, middle, lower = TechnicalIndicators.calculate_indicator(
                    data, indicator_type, source, period, std_dev=std_dev
                )
                
                results[f"{indicator_name}_upper"] = upper
                results[f"{indicator_name}_middle"] = middle
                results[f"{indicator_name}_lower"] = lower
                
            elif indicator_type == "stoch":
                k_period = config.get('k_period', 14)
                d_period = config.get('d_period', 3)
                indicator_name = f"{indicator_type}_{k_period}_{d_period}"
                
                k_percent, d_percent = TechnicalIndicators.calculate_indicator(
                    data, indicator_type, source, period,
                    k_period=k_period, d_period=d_period
                )
                
                results[f"{indicator_name}_k"] = k_percent
                results[f"{indicator_name}_d"] = d_percent
                
            else:
                indicator_name = f"{indicator_type}_{period}"
                result = TechnicalIndicators.calculate_indicator(
                    data, indicator_type, source, period
                )
                results[indicator_name] = result
        
        return results


# Legacy function for backward compatibility
def calculate_indicator(
    market_data: pd.DataFrame,
    indicator_type: str,
    source: str,
    period: int = 14,
    **kwargs
) -> Union[pd.Series, Tuple[pd.Series, ...]]:
    """Legacy function for backward compatibility"""
    return TechnicalIndicators.calculate_indicator(
        market_data, indicator_type, source, period, **kwargs
    ) 