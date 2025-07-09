"""
Backtest API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional, List, cast
from datetime import datetime
from sqlalchemy.orm import Session
from app.api.routes.auth import get_current_user
from app.db.database import get_db
from app.db.models import Backtest as BacktestORM, User as UserORM

from ...models.backtest import BacktestRequest, BacktestResult
from ...tasks.backtest_tasks import run_backtest_task, get_backtest_status, cancel_backtest
from ...core.redis_manager import redis_manager

router = APIRouter()

@router.post("/run")
async def run_backtest(backtest_request: BacktestRequest, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    """Run backtest with Celery and real-time progress updates"""
    try:
        # Create DB row with status pending
        bt_row = BacktestORM(
            user_id=current_user.id,
            status="pending",
            initial_capital=backtest_request.initial_capital,
        )
        db.add(bt_row)
        db.commit()
        db.refresh(bt_row)

        # Start Celery task, pass identifiers
        task = run_backtest_task.delay(
            backtest_db_id=str(bt_row.id),
            user_id=str(current_user.id),
            strategy_data=backtest_request.strategy.dict(),
            timeframe=backtest_request.timeframe,
            start_date=backtest_request.start_date.isoformat(),
            end_date=backtest_request.end_date.isoformat(),
            initial_capital=backtest_request.initial_capital,
        )

        db.commit()

        return {
            "task_id": task.id,
            "backtest_id": str(bt_row.id),
            "status": "started",
            "message": "Backtest started with Celery",
            "websocket_url": f"/ws/backtest/{task.id}",
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

# ------------------ Phase 5 – Backtest Persistence Endpoints ------------------

@router.get("/history", response_model=List[Dict[str, Any]])
async def list_backtests(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    """Return a summary of the current user's backtests."""
    rows = (
        db.query(BacktestORM)
        .filter(BacktestORM.user_id == current_user.id)
        .order_by(BacktestORM.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(r.id),
            "status": str(r.status),  # type: ignore[arg-type]
            "initial_capital": r.initial_capital,
            "created_at": (
                str(cast(Any, r.created_at)) if cast(Any, r.created_at) is not None else None
            ),
            "completed_at": (
                str(cast(Any, r.completed_at)) if cast(Any, r.completed_at) is not None else None
            ),
            "result_available": bool(getattr(r, "result", None) is not None),  # type: ignore[call-arg]
        }
        for r in rows
    ]  # type: ignore[return-value]


@router.get("/history/{backtest_id}", response_model=Dict[str, Any])
async def get_backtest_detail(
    backtest_id: str,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    """Return stored backtest result JSON (if available)."""
    row = db.query(BacktestORM).filter(BacktestORM.id == backtest_id).first()
    if not row or row.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return {
        "id": str(row.id),
        "status": row.status,
        "result": row.result,
    } 