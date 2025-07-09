"""
Admin API Routes - System monitoring and management
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime

from ...core.redis_manager import redis_manager
from ...tasks.analytics_tasks import health_check_task, get_system_statistics
from ...celery_app import celery_app

router = APIRouter()

@router.get("/health")
async def health_check():
    """Comprehensive system health check"""
    try:
        # Run health check task
        health_task = health_check_task.delay()
        health_result = health_task.get(timeout=10)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": health_result.get("status", "unknown"),
            "components": {
                "api": "healthy",  # If this endpoint responds, API is working
                "redis": "healthy" if health_result.get("redis_healthy") else "unhealthy",
                "celery": "healthy" if health_result.get("celery_healthy") else "unhealthy"
            },
            "details": health_result
        }
        
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unhealthy",
            "components": {
                "api": "healthy",
                "redis": "unknown",
                "celery": "unhealthy"
            },
            "error": str(e)
        }

@router.get("/statistics")
async def system_statistics():
    """Get comprehensive system statistics"""
    try:
        # Get statistics from background task
        stats_task = get_system_statistics.delay()
        stats_result = stats_task.get(timeout=10)
        
        # Add additional FastAPI statistics
        stats_result.update({
            "api": {
                "status": "operational",
                "endpoints_count": len(router.routes),
                "timestamp": datetime.now().isoformat()
            }
        })
        
        return stats_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")

@router.get("/tasks/active")
async def get_all_active_tasks():
    """Get all active tasks across all queues"""
    try:
        active_tasks = redis_manager.get_active_tasks()
        
        # Get detailed info for each task
        tasks_detail = []
        for task_id in active_tasks:
            task_info = redis_manager.get_task_info(task_id)
            if task_info:
                tasks_detail.append({
                    'task_id': task_id,
                    'type': task_info.get('type'),
                    'status': task_info.get('status'),
                    'progress': task_info.get('progress'),
                    'message': task_info.get('message'),
                    'created_at': task_info.get('created_at'),
                    'updated_at': task_info.get('updated_at')
                })
        
        return {
            'active_tasks': tasks_detail,
            'total_count': len(tasks_detail),
            'by_type': {},
            'by_status': {}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving active tasks: {str(e)}")

@router.post("/tasks/{task_id}/cancel")
async def cancel_any_task(task_id: str):
    """Cancel any task by ID"""
    try:
        # Revoke the task
        celery_app.control.revoke(task_id, terminate=True)
        
        # Update status in Redis
        redis_manager.update_task_status(task_id, 'cancelled', 'Task cancelled by admin')
        
        return {
            'task_id': task_id,
            'status': 'cancelled',
            'message': 'Task cancellation requested',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling task: {str(e)}")

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task and all its data"""
    try:
        success = redis_manager.delete_task(task_id)
        
        if success:
            return {
                'task_id': task_id,
                'status': 'deleted',
                'message': 'Task and all related data deleted',
                'timestamp': datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")

@router.post("/cleanup")
async def cleanup_expired_tasks():
    """Clean up expired tasks"""
    try:
        cleaned_count = redis_manager.cleanup_expired_tasks()
        
        return {
            'cleaned_tasks': cleaned_count,
            'message': f'Cleaned up {cleaned_count} expired tasks',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")

@router.get("/celery/workers")
async def get_celery_workers():
    """Get information about active Celery workers"""
    try:
        inspect = celery_app.control.inspect()
        
        # Get worker information
        stats = inspect.stats()
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        reserved_tasks = inspect.reserved()
        
        return {
            'workers': {
                'stats': stats or {},
                'active_tasks': active_tasks or {},
                'scheduled_tasks': scheduled_tasks or {},
                'reserved_tasks': reserved_tasks or {}
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving worker info: {str(e)}")

@router.get("/redis/info")
async def get_redis_info():
    """Get Redis server information"""
    try:
        if redis_manager.health_check():
            redis_info = redis_manager.redis_client.info()
            
            # Filter important information
            important_info = {
                'redis_version': redis_info.get('redis_version'),
                'used_memory_human': redis_info.get('used_memory_human'),
                'connected_clients': redis_info.get('connected_clients'),
                'total_commands_processed': redis_info.get('total_commands_processed'),
                'keyspace_hits': redis_info.get('keyspace_hits'),
                'keyspace_misses': redis_info.get('keyspace_misses'),
                'uptime_in_seconds': redis_info.get('uptime_in_seconds')
            }
            
            return {
                'status': 'healthy',
                'info': important_info,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'status': 'unhealthy',
                'error': 'Redis connection failed',
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving Redis info: {str(e)}") 