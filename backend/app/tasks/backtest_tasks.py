"""
Celery tasks for backtest execution
Enhanced background processing with progress tracking
"""

from celery import current_task
from typing import Dict, Any
import asyncio
import json
from datetime import datetime

from ..celery_app import celery_app
from ..core.backtest_engine import BacktestEngine
from ..services.data_service import DataService
from ..models.strategy import Strategy
from ..models.backtest import BacktestResult
from ..core.websocket_manager import manager
from ..core.redis_manager import redis_manager

@celery_app.task(bind=True, name="run_backtest_task")
def run_backtest_task(
    self,
    backtest_db_id: str,
    user_id: str,
    strategy_data: Dict[str, Any],
    timeframe: str,
    start_date: str,
    end_date: str,
    initial_capital: float
) -> Dict[str, Any]:
    """
    Execute backtest in background with progress tracking
    
    Args:
        strategy_data: Strategy configuration dictionary
        timeframe: Timeframe for backtesting
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        initial_capital: Initial capital amount
        
    Returns:
        Backtest result dictionary
    """
    task_id = self.request.id
    
    try:
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={
                'stage': 'initialization',
                'progress': 0,
                'message': 'Initializing backtest...',
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Store task info in Redis
        redis_manager.store_task_info(task_id, {
            'type': 'backtest',
            'status': 'running',
            'progress': 0,
            'message': 'Initializing backtest...',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })
        
        # Broadcast initial status via WebSocket
        asyncio.create_task(manager.broadcast_progress(task_id, {
            'task_id': task_id,
            'status': 'running',
            'progress': 0,
            'message': 'Initializing backtest...'
        }))
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Create strategy object
        strategy = Strategy.parse_obj(strategy_data)
        
        # Progress callback for backtest engine
        def progress_callback(progress: float, message: str):
            # Update Celery task state
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'stage': 'backtesting',
                    'progress': int(progress),
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Update Redis
            redis_manager.update_task_progress(task_id, int(progress), message)
            
            # Broadcast via WebSocket (async)
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(manager.broadcast_progress(task_id, {
                    'task_id': task_id,
                    'status': 'running',
                    'progress': int(progress),
                    'message': message
                }))
            except RuntimeError:
                # No event loop running, skip WebSocket broadcast
                pass
        
        # Initialize services
        backtest_engine = BacktestEngine()
        data_service = DataService()
        
        # Update progress
        progress_callback(10, "Loading market data...")
        
        # Get market data (synchronous call)
        market_data = asyncio.run(data_service.get_ohlcv_data(
            symbol=strategy.asset_selection.symbol,
            timeframe=timeframe,
            start_date=start_dt,
            end_date=end_dt
        ))
        
        if market_data.empty:
            raise ValueError(f"No market data available for {strategy.asset_selection.symbol}")
        
        progress_callback(20, "Starting backtest execution...")
        
        # Run backtest (synchronous call)
        result = asyncio.run(backtest_engine.run_backtest(
            strategy,
            market_data,
            initial_capital,
            progress_callback
        ))
        
        # Convert result to dictionary for JSON serialization
        result_dict = result.dict() if hasattr(result, 'dict') else result

        # Persist to database
        from app.db.database import SessionLocal  # local import to avoid Celery serialization issues
        from app.db.models import Backtest as BacktestORM, Analytics as AnalyticsORM
        db_sess = SessionLocal()
        try:
            bt_row = db_sess.query(BacktestORM).filter(BacktestORM.id == backtest_db_id).first()
            if bt_row:
                setattr(bt_row, "status", "completed")
                setattr(bt_row, "completed_at", datetime.utcnow())
                setattr(bt_row, "result", result_dict)
                db_sess.commit()

                # Save analytics metrics if present
                metrics = result_dict.get("performance_metrics") if isinstance(result_dict, dict) else None
                if metrics:
                    analytics = AnalyticsORM(
                        backtest_id=bt_row.id,
                        metrics=metrics,
                    )
                    db_sess.add(analytics)
                    db_sess.commit()
        finally:
            db_sess.close()
        
        # Update final status
        current_task.update_state(
            state='SUCCESS',
            meta={
                'stage': 'completed',
                'progress': 100,
                'message': 'Backtest completed successfully',
                'timestamp': datetime.now().isoformat(),
                'result': result_dict
            }
        )
        
        # Final WebSocket broadcast
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(manager.broadcast_progress(task_id, {
                'task_id': task_id,
                'status': 'completed',
                'progress': 100,
                'message': 'Backtest completed successfully',
                'result': result_dict
            }))
        except RuntimeError:
            pass
        
        return result_dict  # type: ignore[return-value]
        
    except Exception as e:
        error_message = f"Backtest failed: {str(e)}"
        
        # Update error status and persist
        current_task.update_state(
            state='FAILURE',
            meta={
                'stage': 'failed',
                'progress': 0,
                'message': error_message,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
        )
        
        # Store error in Redis

        from app.db.database import SessionLocal as _SessionLocal
        from app.db.models import Backtest as BacktestORM
        db_err = _SessionLocal()
        try:
            bt_row = db_err.query(BacktestORM).filter(BacktestORM.id == backtest_db_id).first()
            if bt_row:
                setattr(bt_row, "status", "failed")
                setattr(bt_row, "completed_at", datetime.utcnow())
                setattr(bt_row, "result", {"error": str(e)})
        finally:
            db_err.close()
        
        # Broadcast error via WebSocket
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(manager.broadcast_progress(task_id, {
                'task_id': task_id,
                'status': 'failed',
                'progress': 0,
                'message': error_message,
                'error': str(e)
            }))
        except RuntimeError:
            pass
        
        raise

@celery_app.task(name="get_backtest_status")
def get_backtest_status(task_id: str) -> Dict[str, Any]:
    """Get backtest task status"""
    
    # Get from Redis first
    task_info = redis_manager.get_task_info(task_id)
    if task_info:
        return task_info
    
    # Fallback to Celery result backend
    result = celery_app.AsyncResult(task_id)
    
    if result.state == 'PENDING':
        return {
            'task_id': task_id,
            'status': 'pending',
            'progress': 0,
            'message': 'Task is waiting to be processed'
        }
    elif result.state == 'PROGRESS':
        return {
            'task_id': task_id,
            'status': 'running',
            'progress': result.info.get('progress', 0),
            'message': result.info.get('message', 'Processing...'),
            'stage': result.info.get('stage', 'unknown')
        }
    elif result.state == 'SUCCESS':
        return {
            'task_id': task_id,
            'status': 'completed',
            'progress': 100,
            'message': 'Task completed successfully',
            'result': result.result
        }
    else:  # FAILURE
        return {
            'task_id': task_id,
            'status': 'failed',
            'progress': 0,
            'message': f'Task failed: {str(result.info)}',
            'error': str(result.info)
        }

@celery_app.task(name="cancel_backtest")
def cancel_backtest(task_id: str) -> Dict[str, Any]:
    """Cancel a running backtest task"""
    
    # Revoke the task
    celery_app.control.revoke(task_id, terminate=True)
    
    # Update status in Redis
    redis_manager.update_task_status(task_id, 'cancelled', 'Task was cancelled by user')
    
    # Broadcast cancellation via WebSocket
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(manager.broadcast_progress(task_id, {
            'task_id': task_id,
            'status': 'cancelled',
            'progress': 0,
            'message': 'Task was cancelled by user'
        }))
    except RuntimeError:
        pass
    
    return {
        'task_id': task_id,
        'status': 'cancelled',
        'message': 'Task cancellation requested'
    } 