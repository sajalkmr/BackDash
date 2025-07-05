"""
Enhanced Strategy API Routes - Full Phase 2 implementation
Strategic integration of advanced strategy engine and backtesting capabilities
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
import pandas as pd

from ...models.strategy import Strategy
from ...models.backtest import BacktestRequest, BacktestResult
from ...core.strategy_engine import StrategyEngine
from ...core.backtest_engine import BacktestEngine
from ...core.indicators import TechnicalIndicators
from ...services.data_service import DataService

router = APIRouter()

# Initialize engines
strategy_engine = StrategyEngine()
backtest_engine = BacktestEngine()
data_service = DataService()

@router.post("/validate")
async def validate_strategy(strategy: Strategy):
    """Validate strategy configuration with comprehensive checks"""
    try:
        # Use the enhanced strategy engine for validation
        validation_result = strategy_engine.validate_strategy(strategy)
        
        # Add additional API-level checks
        if validation_result["valid"]:
            # Check if symbol is available
            available_symbols = await data_service.get_available_symbols()
            if strategy.asset_selection.symbol not in available_symbols:
                validation_result["errors"].append(
                    f"Symbol '{strategy.asset_selection.symbol}' not available. "
                    f"Available symbols: {available_symbols}"
                )
                validation_result["valid"] = False
                validation_result["checks"]["asset_selection_valid"] = False
        
        return {
            "valid": validation_result["valid"],
            "strategy_name": strategy.name,
            "message": "Strategy validation completed",
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"],
            "checks": validation_result["checks"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Strategy validation failed: {str(e)}")

@router.get("/indicators")
async def get_available_indicators():
    """Get list of available technical indicators with metadata"""
    try:
        indicators_info = TechnicalIndicators.get_available_indicators()
        
        # Format for API response
        formatted_indicators = []
        for indicator_type, info in indicators_info.items():
            formatted_indicators.append({
                "name": indicator_type,
                "display_name": info["name"],
                "description": info["description"],
                "parameters": info["parameters"],
                "category": info["category"],
                "output_count": info["output_count"],
                "outputs": info.get("outputs", [indicator_type]),
                "range": info.get("range", None)
            })
        
        return {
            "indicators": formatted_indicators,
            "categories": {
                "trend": "Trend-following indicators",
                "momentum": "Momentum and oscillator indicators", 
                "volatility": "Volatility indicators",
                "volume": "Volume-based indicators"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching indicators: {str(e)}")

@router.post("/backtest")
async def run_strategy_backtest(
    backtest_request: BacktestRequest,
    background_tasks: BackgroundTasks
):
    """Execute strategy backtest with real-time progress updates"""
    try:
        # Validate the strategy first
        validation_result = strategy_engine.validate_strategy(backtest_request.strategy)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Strategy validation failed: {validation_result['errors']}"
            )
        
        # Get market data
        symbol = backtest_request.strategy.asset_selection.symbol
        market_data = await data_service.get_ohlcv_data(
            symbol=symbol,
            timeframe=backtest_request.timeframe,
            start_date=backtest_request.start_date,
            end_date=backtest_request.end_date
        )
        
        if market_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No market data available for {symbol} in the specified date range"
            )
        
        # For immediate response, run backtest in background if requested
        if backtest_request.enable_real_time_updates:
            # Start background task
            backtest_id = f"bt_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            background_tasks.add_task(
                run_backtest_background,
                backtest_id,
                backtest_request.strategy,
                market_data,
                backtest_request.initial_capital
            )
            
            return {
                "backtest_id": backtest_id,
                "status": "started",
                "message": "Backtest started in background",
                "strategy_name": backtest_request.strategy.name,
                "symbol": symbol,
                "timeframe": backtest_request.timeframe,
                "websocket_url": f"/ws/backtest/{backtest_id}"
            }
        else:
            # Run backtest synchronously
            result = await backtest_engine.run_backtest(
                backtest_request.strategy,
                market_data,
                backtest_request.initial_capital
            )
            
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest execution failed: {str(e)}")

@router.post("/test-signal")
async def test_strategy_signal(
    strategy: Strategy,
    symbol: Optional[str] = None,
    date: Optional[datetime] = None
):
    """Test strategy signal generation on specific data point"""
    try:
        # Use strategy symbol if not provided
        test_symbol = symbol or strategy.asset_selection.symbol
        
        # Get recent data if date not provided
        if not date:
            date = datetime.now() - timedelta(days=1)
        
        # Get market data around the test date
        start_date = date - timedelta(days=60)  # Get 60 days for indicator calculation
        end_date = date + timedelta(days=1)
        
        market_data = await data_service.get_ohlcv_data(
            symbol=test_symbol,
            timeframe="1h",
            start_date=start_date,
            end_date=end_date
        )
        
        if market_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No market data available for {test_symbol}"
            )
        
        # Calculate indicators
        indicators_data = TechnicalIndicators.calculate_multiple_indicators(
            market_data,
            [
                {
                    'type': ind.type,
                    'period': ind.period,
                    'source': ind.source,
                    'fast_period': ind.fast_period,
                    'slow_period': ind.slow_period,
                    'signal_period': ind.signal_period
                }
                for ind in strategy.signal_generation.indicators
            ]
        )
        
        # Get the latest data point
        latest_index = len(market_data) - 1
        current_bar = market_data.iloc[latest_index]
        previous_bar = market_data.iloc[latest_index - 1] if latest_index > 0 else None
        
        # Get current indicator values
        current_indicators = {}
        for name, data in indicators_data.items():
            if isinstance(data, pd.Series) and len(data) > latest_index:
                value = data.iloc[latest_index]
                current_indicators[name] = float(value) if not pd.isna(value) else 0.0
        
        # Get signal summary
        signal_summary = strategy_engine.get_signal_summary(
            strategy, current_indicators, current_bar
        )
        
        return {
            "symbol": test_symbol,
            "test_date": date.isoformat(),
            "current_price": float(current_bar['close']),
            "signal_summary": signal_summary,
            "indicators": current_indicators,
            "market_data_points": len(market_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signal testing failed: {str(e)}")

@router.get("/performance/{strategy_name}")
async def get_strategy_performance(strategy_name: str):
    """Get historical performance data for a strategy (placeholder for Phase 5)"""
    return {
        "strategy_name": strategy_name,
        "message": "Historical performance tracking will be implemented in Phase 5 (Database Integration)",
        "available_in": "Phase 5"
    }

@router.post("/optimize")
async def optimize_strategy_parameters(strategy: Strategy):
    """Optimize strategy parameters (placeholder for Phase 6)"""
    return {
        "strategy_name": strategy.name,
        "message": "Parameter optimization will be implemented in Phase 6 (Advanced Features)",
        "available_in": "Phase 6",
        "planned_methods": [
            "Grid Search",
            "Genetic Algorithm",
            "Bayesian Optimization",
            "Walk-Forward Analysis"
        ]
    }

# Background task function
async def run_backtest_background(
    backtest_id: str,
    strategy: Strategy,
    market_data,
    initial_capital: float
):
    """Run backtest in background with progress updates"""
    try:
        # This would integrate with WebSocket for real-time updates
        # For now, just run the backtest
        result = await backtest_engine.run_backtest(
            strategy,
            market_data,
            initial_capital
        )
        
        # Store result (would be in database in Phase 5)
        print(f"Backtest {backtest_id} completed successfully")
        
    except Exception as e:
        print(f"Background backtest {backtest_id} failed: {str(e)}")

# Health check for strategy service
@router.get("/health")
async def strategy_service_health():
    """Health check for strategy service"""
    return {
        "status": "healthy",
        "engines": {
            "strategy_engine": "operational",
            "backtest_engine": "operational", 
            "indicators_engine": "operational"
        },
        "available_indicators": len(TechnicalIndicators.get_available_indicators()),
        "phase": "Phase 2 - Strategy Engine Enhancement",
        "capabilities": [
            "Advanced strategy validation",
            "Comprehensive backtesting", 
            "Real-time signal testing",
            "Technical indicators library",
            "Risk management integration"
        ]
    } 