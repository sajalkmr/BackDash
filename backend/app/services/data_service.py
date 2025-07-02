"""
Data Service - Enhanced market data loading and management
Strategic integration from 'mine' project with additional features
"""

import pandas as pd
import numpy as np
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import aiofiles

class DataService:
    """Enhanced service for managing market data"""
    
    def __init__(self, data_directory: str = "data"):
        self.data_directory = data_directory
        self._available_symbols = [
            "BTC-USDT", "ETH-USDT", "BNB-USDT", "ADA-USDT", "SOL-USDT",
            "DOGE-USDT", "MATIC-USDT", "AVAX-USDT", "DOT-USDT", "ATOM-USDT"
        ]
        self._available_exchanges = ["binance", "coinbase", "kraken", "bitfinex"]
        self._supported_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        
        # Initialize data directory
        os.makedirs(data_directory, exist_ok=True)
    
    async def get_available_symbols(self) -> List[str]:
        """Get list of available trading symbols"""
        return self._available_symbols
    
    async def get_available_exchanges(self) -> List[str]:
        """Get list of available exchanges"""
        return self._available_exchanges
    
    async def get_supported_timeframes(self) -> List[str]:
        """Get list of supported timeframes"""
        return self._supported_timeframes
    
    async def get_symbol_info(self, symbol: str, exchange: str = "binance") -> Dict:
        """Get detailed information about a trading symbol"""
        base_asset, quote_asset = symbol.split('-') if '-' in symbol else (symbol[:3], symbol[3:])
        
        return {
            "symbol": symbol,
            "exchange": exchange,
            "market_type": "spot",
            "base_asset": base_asset,
            "quote_asset": quote_asset,
            "min_quantity": 0.001,
            "max_quantity": 10000,
            "tick_size": 0.01,
            "status": "active",
            "price_precision": 2,
            "quantity_precision": 6,
            "supported_timeframes": self._supported_timeframes
        }
    
    async def load_csv_data(
        self, 
        file_path: str,
        symbol: str = None,
        validate: bool = True
    ) -> pd.DataFrame:
        """Load OHLCV data from CSV file with validation"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        # Read CSV asynchronously
        df = pd.read_csv(file_path)
        
        # Normalize column names
        df.columns = [col.lower().strip() for col in df.columns]
        
        # Handle different timestamp column names
        timestamp_cols = ['timestamp', 'datetime', 'date', 'time']
        timestamp_col = None
        for col in timestamp_cols:
            if col in df.columns:
                timestamp_col = col
                break
        
        if not timestamp_col:
            raise ValueError("No timestamp column found. Expected one of: " + ", ".join(timestamp_cols))
        
        # Convert timestamp to datetime
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        df.set_index(timestamp_col, inplace=True)
        
        # Validate required OHLCV columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        if validate:
            df = self._validate_ohlcv_data(df, symbol)
        
        return df
    
    def _validate_ohlcv_data(self, df: pd.DataFrame, symbol: str = None) -> pd.DataFrame:
        """Validate OHLCV data integrity"""
        original_len = len(df)
        
        # Remove rows with invalid prices (negative or zero)
        df = df[(df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
        
        # Remove rows where high < low (invalid)
        df = df[df['high'] >= df['low']]
        
        # Remove rows where OHLC relationships are invalid
        df = df[
            (df['high'] >= df['open']) & 
            (df['high'] >= df['close']) & 
            (df['low'] <= df['open']) & 
            (df['low'] <= df['close'])
        ]
        
        # Remove rows with negative volume
        df = df[df['volume'] >= 0]
        
        # Sort by timestamp
        df = df.sort_index()
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        cleaned_len = len(df)
        if cleaned_len < original_len:
            print(f"Data cleaning removed {original_len - cleaned_len} invalid rows from {symbol or 'data'}")
        
        return df
    
    async def get_ohlcv_data(
        self,
        symbol: str,
        exchange: str = "binance",
        timeframe: str = "1h",
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = None
    ) -> pd.DataFrame:
        """
        Get OHLCV data for a symbol and date range
        First tries to load from CSV, then generates mock data if not found
        """
        # Try to load from CSV first
        csv_filename = f"{symbol}_{timeframe}.csv"
        csv_path = os.path.join(self.data_directory, csv_filename)
        
        if os.path.exists(csv_path):
            try:
                df = await self.load_csv_data(csv_path, symbol)
                
                # Filter by date range if specified
                if start_date:
                    df = df[df.index >= start_date]
                if end_date:
                    df = df[df.index <= end_date]
                
                if limit:
                    df = df.head(limit)
                
                return df
            except Exception as e:
                print(f"Error loading CSV data for {symbol}: {e}. Generating mock data.")
        
        # Generate mock data if CSV not available
        return await self._generate_mock_data(
            symbol, exchange, timeframe, start_date, end_date, limit
        )
    
    async def _generate_mock_data(
        self,
        symbol: str,
        exchange: str,
        timeframe: str,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = None
    ) -> pd.DataFrame:
        """Generate realistic mock OHLCV data"""
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=365)
        
        # Generate date range based on timeframe
        freq_map = {
            '1m': '1T', '5m': '5T', '15m': '15T', '30m': '30T',
            '1h': '1H', '4h': '4H', '1d': '1D', '1w': '1W'
        }
        freq = freq_map.get(timeframe, '1H')
        dates = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        if limit:
            dates = dates[:limit]
        
        # Generate realistic price movement
        np.random.seed(hash(symbol) % 2**32)  # Consistent seed per symbol
        
        # Starting price based on symbol
        base_prices = {
            "BTC-USDT": 45000, "ETH-USDT": 3000, "BNB-USDT": 300,
            "ADA-USDT": 0.5, "SOL-USDT": 100, "DOGE-USDT": 0.08,
            "MATIC-USDT": 0.8, "AVAX-USDT": 25, "DOT-USDT": 6, "ATOM-USDT": 10
        }
        base_price = base_prices.get(symbol, 100)
        
        # Volatility based on timeframe
        volatility_map = {
            '1m': 0.001, '5m': 0.003, '15m': 0.005, '30m': 0.008,
            '1h': 0.01, '4h': 0.02, '1d': 0.03, '1w': 0.05
        }
        volatility = volatility_map.get(timeframe, 0.01)
        
        # Generate price series with random walk and mean reversion
        price_changes = np.random.normal(0, volatility, len(dates))
        
        # Add trend and cycles
        trend = np.linspace(0, 0.2, len(dates))  # 20% upward trend over period
        cycle = 0.1 * np.sin(np.linspace(0, 4*np.pi, len(dates)))  # Cyclical pattern
        
        prices = [base_price]
        for i, change in enumerate(price_changes[1:]):
            trend_component = trend[i+1] - trend[i]
            cycle_component = cycle[i+1] - cycle[i]
            total_change = change + trend_component + cycle_component
            
            new_price = prices[-1] * (1 + total_change)
            prices.append(max(new_price, 0.001))  # Prevent very low prices
        
        # Generate OHLCV data
        data = []
        for i, (date, close_price) in enumerate(zip(dates, prices)):
            # Generate realistic intrabar volatility
            intrabar_vol = np.random.uniform(0.002, volatility)
            
            open_price = prices[i-1] if i > 0 else close_price
            
            # Generate high and low with realistic distribution
            high_move = np.random.exponential(intrabar_vol)
            low_move = np.random.exponential(intrabar_vol)
            
            high = max(open_price, close_price) * (1 + high_move)
            low = min(open_price, close_price) * (1 - low_move)
            
            # Ensure OHLC relationships are valid
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            # Generate volume with some correlation to price movement
            price_move = abs(close_price - open_price) / open_price
            base_volume = np.random.lognormal(8, 1)  # Log-normal distribution
            volume_multiplier = 1 + (price_move * 5)  # Higher volume on bigger moves
            volume = base_volume * volume_multiplier
            
            data.append({
                'open': round(open_price, 6),
                'high': round(high, 6),
                'low': round(low, 6),
                'close': round(close_price, 6),
                'volume': round(volume, 2)
            })
        
        df = pd.DataFrame(data, index=dates)
        return df
    
    async def get_available_datasets(self) -> List[Dict[str, str]]:
        """Get list of available datasets from CSV files"""
        datasets = []
        
        if not os.path.exists(self.data_directory):
            return datasets
        
        for filename in os.listdir(self.data_directory):
            if filename.endswith('.csv') and '_' in filename:
                name = filename.replace('.csv', '')
                parts = name.split('_')
                if len(parts) >= 2:
                    symbol = parts[0]
                    timeframe = parts[1] if len(parts) == 2 else '_'.join(parts[1:])
                    
                    # Get file size and modification time
                    file_path = os.path.join(self.data_directory, filename)
                    file_stat = os.stat(file_path)
                    
                    datasets.append({
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "filename": filename,
                        "size_bytes": file_stat.st_size,
                        "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    })
        
        return sorted(datasets, key=lambda x: x['symbol'])
    
    async def health_check(self) -> Dict:
        """Comprehensive health check of data services"""
        available_datasets = await self.get_available_datasets()
        
        return {
            "status": "healthy",
            "data_directory": self.data_directory,
            "available_symbols": len(self._available_symbols),
            "available_exchanges": len(self._available_exchanges),
            "supported_timeframes": len(self._supported_timeframes),
            "csv_datasets": len(available_datasets),
            "last_updated": datetime.now().isoformat()
        }
    
    async def upload_csv_data(
        self, 
        file_content: bytes, 
        symbol: str, 
        timeframe: str,
        validate: bool = True
    ) -> Dict:
        """Upload and save CSV data file"""
        filename = f"{symbol}_{timeframe}.csv"
        file_path = os.path.join(self.data_directory, filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        # Validate the uploaded data
        try:
            df = await self.load_csv_data(file_path, symbol, validate)
            
            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "filename": filename,
                "rows": len(df),
                "date_range": {
                    "start": df.index.min().isoformat(),
                    "end": df.index.max().isoformat()
                },
                "columns": list(df.columns)
            }
        except Exception as e:
            # Remove invalid file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "timeframe": timeframe
            } 