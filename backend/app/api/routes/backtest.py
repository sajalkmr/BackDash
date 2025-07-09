"""
Backtest API Routes
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime

from ...models.backtest import BacktestRequest, BacktestResult
from ...tasks.backtest_tasks import run_backtest_task, get_backtest_status, cancel_backtest
from ...core.redis_manager import redis_manager

router = APIRouter()

@router.post("/run")
async def run_backtest(backtest_request: BacktestRequest):
    """Run backtest with Celery and real-time progress updates"""
    try:
        # Start Celery task
        task = run_backtest_task.delay(
            strategy_data=backtest_request.strategy.dict(),
            timeframe=backtest_request.timeframe,
            start_date=backtest_request.start_date.isoformat(),
            end_date=backtest_request.end_date.isoformat(),
            initial_capital=backtest_request.initial_capital
        )
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "Backtest started with Celery",
            "websocket_url": f"/ws/backtest/{task.id}",
            "celery_task_id": task.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest execution failed: {str(e)}")

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get backtest task status from Redis/Celery"""
    try:
        # Try Redis first for faster response
        task_info = redis_manager.get_task_info(task_id)
        if task_info:
            return {
                "task_id": task_id,
                "status": task_info.get("status", "unknown"),
                "progress": task_info.get("progress", 0),
                "message": task_info.get("message", ""),
                "result": task_info.get("result") if task_info.get("status") == "completed" else None,
                "error": task_info.get("error") if task_info.get("status") == "failed" else None,
                "source": "redis"
            }
        
        # Fallback to Celery task status
        status_result = get_backtest_status.delay(task_id)
        status_data = status_result.get(timeout=5)
        
        return {
            **status_data,
            "source": "celery"
        }
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found: {str(e)}")

@router.get("/result/{task_id}")
async def get_task_result(task_id: str):
    """Get backtest result from Redis"""
    try:
        # Get from Redis first
        result = redis_manager.get_task_result(task_id)
        if result:
            return result
        
        # Check task status
        task_info = redis_manager.get_task_info(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        if task_info.get("status") != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Task {task_id} is not completed (status: {task_info.get('status', 'unknown')})"
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Task {task_id} is completed but result not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving result: {str(e)}")

@router.post("/cancel/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a running backtest task"""
    try:
        # Cancel via Celery
        cancel_result = cancel_backtest.delay(task_id)
        result = cancel_result.get(timeout=5)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling task: {str(e)}")

@router.get("/active")
async def get_active_tasks():
    """Get list of active backtest tasks"""
    try:
        active_tasks = redis_manager.get_active_tasks()
        
        # Get detailed info for each task
        tasks_info = []
        for task_id in active_tasks:
            task_info = redis_manager.get_task_info(task_id)
            if task_info and task_info.get('type') == 'backtest':
                tasks_info.append({
                    'task_id': task_id,
                    'status': task_info.get('status'),
                    'progress': task_info.get('progress'),
                    'message': task_info.get('message'),
                    'created_at': task_info.get('created_at'),
                    'updated_at': task_info.get('updated_at')
                })
        
        return {
            'active_tasks': tasks_info,
            'total_count': len(tasks_info)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving active tasks: {str(e)}")

@router.get("/statistics")
async def get_task_statistics():
    """Get task processing statistics"""
    try:
        stats = redis_manager.get_task_statistics()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}") 