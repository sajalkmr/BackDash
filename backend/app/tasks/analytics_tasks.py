"""
Celery tasks for analytics and maintenance operations
"""

from celery import current_task
from typing import Dict, Any
from datetime import datetime

from ..celery_app import celery_app
from ..core.redis_manager import redis_manager

@celery_app.task(name="cleanup_expired_tasks")
def cleanup_expired_tasks() -> Dict[str, Any]:
    """
    Periodic task to clean up expired tasks
    """
    try:
        cleaned_count = redis_manager.cleanup_expired_tasks()
        
        return {
            'cleaned_tasks': cleaned_count,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'status': 'failed'
        }

@celery_app.task(name="get_system_statistics")
def get_system_statistics() -> Dict[str, Any]:
    """
    Get system statistics for monitoring
    """
    try:
        # Get Redis statistics
        redis_stats = redis_manager.get_task_statistics()
        
        # Get Celery statistics
        celery_stats = {
            'active_tasks': len(celery_app.control.inspect().active() or {}),
            'scheduled_tasks': len(celery_app.control.inspect().scheduled() or {}),
            'reserved_tasks': len(celery_app.control.inspect().reserved() or {})
        }
        
        return {
            'redis': redis_stats,
            'celery': celery_stats,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'status': 'failed'
        }

@celery_app.task(name="health_check_task")
def health_check_task() -> Dict[str, Any]:
    """
    System health check task
    """
    try:
        redis_healthy = redis_manager.health_check()
        
        return {
            'redis_healthy': redis_healthy,
            'celery_healthy': True,  # If this task runs, Celery is working
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy' if redis_healthy else 'degraded'
        }
    except Exception as e:
        return {
            'redis_healthy': False,
            'celery_healthy': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'status': 'unhealthy'
        } 