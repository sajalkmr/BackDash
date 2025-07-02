"""
Data API Routes - Market data endpoints
Enhanced integration with professional data service
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Query
from typing import List, Dict, Optional
from datetime import datetime
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

@router.get("/ohlcv/{symbol}/{timeframe}")
async def get_ohlcv_data(
    symbol: str,
    timeframe: str,
    exchange: str = Query(default="binance", description="Exchange name"),
    start_date: Optional[datetime] = Query(default=None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(default=None, description="End date (ISO format)"),
    limit: Optional[int] = Query(default=None, description="Maximum number of records", ge=1, le=10000)
):
    """Get OHLCV data for a symbol and timeframe"""
    try:
        # Validate symbol and timeframe
        available_symbols = await data_service.get_available_symbols()
        if symbol not in available_symbols:
            raise HTTPException(
                status_code=400, 
                detail=f"Symbol '{symbol}' not supported. Available symbols: {available_symbols}"
            )
        
        available_timeframes = await data_service.get_supported_timeframes()
        if timeframe not in available_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Timeframe '{timeframe}' not supported. Available timeframes: {available_timeframes}"
            )
        
        # Get data
        df = await data_service.get_ohlcv_data(
            symbol=symbol,
            exchange=exchange,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        # Convert to response format
        data = df.reset_index().to_dict(orient="records")
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "exchange": exchange,
            "count": len(data),
            "start_date": df.index.min().isoformat() if not df.empty else None,
            "end_date": df.index.max().isoformat() if not df.empty else None,
            "data": data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching OHLCV data: {str(e)}")

@router.post("/upload")
async def upload_csv_data(
    file: UploadFile = File(...),
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query(..., description="Data timeframe"),
    validate: bool = Query(default=True, description="Validate data integrity")
):
    """Upload CSV data file for a specific symbol and timeframe"""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Validate symbol and timeframe format
        if not symbol or len(symbol) < 3:
            raise HTTPException(status_code=400, detail="Invalid symbol format")
        
        available_timeframes = await data_service.get_supported_timeframes()
        if timeframe not in available_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Timeframe '{timeframe}' not supported. Available: {available_timeframes}"
            )
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Upload and validate
        result = await data_service.upload_csv_data(
            file_content=file_content,
            symbol=symbol,
            timeframe=timeframe,
            validate=validate
        )
        
        if result["success"]:
            return {
                "message": "File uploaded successfully",
                "filename": file.filename,
                **result
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
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
    """Health check endpoint for data service"""
    try:
        return await data_service.health_check()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data service health check failed: {str(e)}")

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