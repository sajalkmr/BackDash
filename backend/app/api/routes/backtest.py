"""
Backtest API Routes - Backtesting execution endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
from datetime import datetime

from ...models.backtest import BacktestRequest, BacktestResult
from ...core.backtest_engine import BacktestEngine
from ...core.task_manager import task_manager
from ...services.data_service import DataService

router = APIRouter()
backtest_engine = BacktestEngine()
data_service = DataService()

@router.post("/run")
async def run_backtest(backtest_request: BacktestRequest):
    """Run backtest with real-time progress updates"""
    try:
        # Create task
        task_id = task_manager.create_task(
            "backtest",
            {
                "strategy": backtest_request.strategy.dict(),
                "timeframe": backtest_request.timeframe,
                "start_date": backtest_request.start_date.isoformat(),
                "end_date": backtest_request.end_date.isoformat(),
                "initial_capital": backtest_request.initial_capital
            }
        )
        
        # Get market data
        market_data = await data_service.get_ohlcv_data(
            symbol=backtest_request.strategy.asset_selection.symbol,
            timeframe=backtest_request.timeframe,
            start_date=backtest_request.start_date,
            end_date=backtest_request.end_date
        )
        
        if market_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No market data available for {backtest_request.strategy.asset_selection.symbol}"
            )
        
        # Run backtest in background
        async def run_with_progress():
            return await backtest_engine.run_backtest(
                backtest_request.strategy,
                market_data,
                backtest_request.initial_capital,
                lambda progress, message: task_manager.update_task(
                    task_id,
                    progress=progress,
                    message=message
                )
            )
        
        # Start background task
        await task_manager.run_task(task_id, run_with_progress)
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Backtest started",
            "websocket_url": f"/ws/backtest/{task_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest execution failed: {str(e)}")

@router.get("/status/{task_id}")
async def get_backtest_status(task_id: str):
    """Get backtest task status"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return {
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "message": task["message"],
        "result": task["result"] if task["status"] == "completed" else None,
        "error": task["error"] if task["status"] == "failed" else None
    }

@router.get("/result/{task_id}")
async def get_backtest_result(task_id: str):
    """Get backtest result"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    if task["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Task {task_id} is not completed (status: {task['status']})"
        )
    
    return task["result"] 