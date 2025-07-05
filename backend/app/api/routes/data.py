"""
Data API Routes - Market data endpoints
Enhanced integration with professional data service
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Query
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd

from ...services.data_service import DataService

router = APIRouter()

# Initialize data service
data_service = DataService()

@router.get("/symbols", response_model=List[str])
async def get_available_symbols():
    """Get list of all available trading symbols"""
    try:
        return await data_service.get_available_symbols()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching symbols: {str(e)}")

@router.get("/exchanges", response_model=List[str])
async def get_available_exchanges():
    """Get list of all supported exchanges"""
    try:
        return await data_service.get_available_exchanges()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching exchanges: {str(e)}")

@router.get("/timeframes", response_model=List[str])
async def get_supported_timeframes():
    """Get list of all supported timeframes"""
    try:
        return await data_service.get_supported_timeframes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching timeframes: {str(e)}")

@router.get("/datasets", response_model=List[Dict])
async def get_available_datasets():
    """Get list of available CSV datasets with metadata"""
    try:
        return await data_service.get_available_datasets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching datasets: {str(e)}")

@router.get("/symbol/{symbol}/info")
async def get_symbol_info(
    symbol: str,
    exchange: str = Query(default="binance", description="Exchange name")
):
    """Get detailed information about a specific symbol"""
    try:
        return await data_service.get_symbol_info(symbol, exchange)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching symbol info: {str(e)}")

@router.get("/ohlcv/{symbol}", response_model=Dict)
async def get_ohlcv_data(
    symbol: str,
    timeframe: str = "1h",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: Optional[int] = None
):
    """Get OHLCV market data for a symbol"""
    try:
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
            
        data = await data_service.get_ohlcv_data(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "data_points": len(data),
            "data": data.to_dict(orient="records")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching OHLCV data: {str(e)}")

@router.post("/upload")
async def upload_data_file(file: UploadFile = File(...)):
    """Upload market data file"""
    try:
        content = await file.read()
        df = pd.read_csv(content)
        
        if not all(col in df.columns for col in ["timestamp", "open", "high", "low", "close", "volume"]):
            raise ValueError("File must contain OHLCV columns")
        
        await data_service.save_data(df, file.filename)
        
        return {
            "message": "Data file uploaded successfully",
            "filename": file.filename,
            "rows": len(df)
        }
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.get("/validate/{symbol}/{timeframe}")
async def validate_dataset(
    symbol: str,
    timeframe: str,
    exchange: str = Query(default="binance", description="Exchange name")
):
    """Validate data integrity for a specific dataset"""
    try:
        df = await data_service.get_ohlcv_data(
            symbol=symbol,
            timeframe=timeframe,
            exchange=exchange
        )
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for the specified parameters")
        
        # Perform validation checks
        validation_results = {
            "symbol": symbol,
            "timeframe": timeframe,
            "total_records": len(df),
            "date_range": {
                "start": df.index.min().isoformat(),
                "end": df.index.max().isoformat()
            },
            "checks": {
                "no_missing_values": not df.isnull().any().any(),
                "valid_ohlc_relationships": (
                    (df['high'] >= df['low']).all() and
                    (df['high'] >= df['open']).all() and
                    (df['high'] >= df['close']).all() and
                    (df['low'] <= df['open']).all() and
                    (df['low'] <= df['close']).all()
                ),
                "positive_prices": (df[['open', 'high', 'low', 'close']] > 0).all().all(),
                "non_negative_volume": (df['volume'] >= 0).all(),
                "no_duplicates": not df.index.duplicated().any(),
                "chronological_order": df.index.is_monotonic_increasing
            }
        }
        
        # Calculate data quality score
        checks = validation_results["checks"]
        quality_score = sum(checks.values()) / len(checks) * 100
        validation_results["quality_score"] = round(quality_score, 2)
        
        # Add warnings if any
        warnings = []
        if not checks["no_missing_values"]:
            warnings.append("Dataset contains missing values")
        if not checks["valid_ohlc_relationships"]:
            warnings.append("Invalid OHLC price relationships detected")
        if not checks["positive_prices"]:
            warnings.append("Non-positive prices detected")
        if not checks["non_negative_volume"]:
            warnings.append("Negative volume values detected")
        if not checks["no_duplicates"]:
            warnings.append("Duplicate timestamps detected")
        if not checks["chronological_order"]:
            warnings.append("Data is not in chronological order")
        
        validation_results["warnings"] = warnings
        validation_results["is_valid"] = len(warnings) == 0
        
        return validation_results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating dataset: {str(e)}")

@router.get("/health")
async def data_service_health():
    """Health check for data service"""
    return {
        "status": "healthy",
        "service": "data_service",
        "features": [
            "OHLCV data retrieval",
            "Multiple timeframes",
            "Data validation",
            "File upload support"
        ]
    }

@router.get("/stats/{symbol}/{timeframe}")
async def get_data_statistics(
    symbol: str,
    timeframe: str,
    exchange: str = Query(default="binance", description="Exchange name")
):
    """Get statistical summary of the dataset"""
    try:
        df = await data_service.get_ohlcv_data(
            symbol=symbol,
            timeframe=timeframe,
            exchange=exchange
        )
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Calculate statistics
        price_stats = df[['open', 'high', 'low', 'close']].describe()
        volume_stats = df['volume'].describe()
        
        # Calculate additional metrics
        returns = df['close'].pct_change().dropna()
        
        statistics = {
            "symbol": symbol,
            "timeframe": timeframe,
            "total_records": len(df),
            "date_range": {
                "start": df.index.min().isoformat(),
                "end": df.index.max().isoformat(),
                "duration_days": (df.index.max() - df.index.min()).days
            },
            "price_statistics": {
                "mean": round(df['close'].mean(), 6),
                "min": round(df['close'].min(), 6),
                "max": round(df['close'].max(), 6),
                "std": round(df['close'].std(), 6),
                "median": round(df['close'].median(), 6)
            },
            "volume_statistics": {
                "mean": round(volume_stats['mean'], 2),
                "min": round(volume_stats['min'], 2),
                "max": round(volume_stats['max'], 2),
                "std": round(volume_stats['std'], 2),
                "median": round(volume_stats['50%'], 2)
            },
            "return_statistics": {
                "mean_daily_return": round(returns.mean(), 6),
                "volatility": round(returns.std(), 6),
                "min_return": round(returns.min(), 6),
                "max_return": round(returns.max(), 6),
                "skewness": round(returns.skew(), 4),
                "kurtosis": round(returns.kurtosis(), 4)
            },
            "gaps_and_missing": {
                "missing_records": int(df.isnull().sum().sum()),
                "zero_volume_periods": int((df['volume'] == 0).sum())
            }
        }
        
        return statistics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating statistics: {str(e)}") 