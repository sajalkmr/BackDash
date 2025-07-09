"""
Celery Application Configuration
Enhanced task processing with Redis backend
"""

from celery import Celery
from app.config import settings
import os

# Create Celery instance
celery_app = Celery(
    "backdash",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.backtest_tasks",
        "app.tasks.strategy_tasks",
        "app.tasks.analytics_tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.backtest_tasks.*": {"queue": "backtest"},
        "app.tasks.strategy_tasks.*": {"queue": "strategy"},
        "app.tasks.analytics_tasks.*": {"queue": "analytics"},
    },
    
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task timeouts and retries
    task_soft_time_limit=settings.task_timeout_seconds,
    task_time_limit=settings.task_timeout_seconds + 60,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Worker settings
    worker_max_tasks_per_child=50,
    worker_disable_rate_limits=False,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Task result ignore
    task_ignore_result=False,
    
    # Beat schedule (for periodic tasks)
    beat_schedule={
        'cleanup-expired-tasks': {
            'task': 'app.tasks.analytics_tasks.cleanup_expired_tasks',
            'schedule': 300.0,  # Every 5 minutes
        },
    },
)

# Configuration based on environment
if settings.is_production:
    # Production settings
    celery_app.conf.update(
        worker_concurrency=4,
        task_always_eager=False,
        task_eager_propagates=True,
        broker_connection_retry_on_startup=True,
    )
else:
    # Development settings
    celery_app.conf.update(
        worker_concurrency=2,
        task_always_eager=False,  # Set to True for synchronous testing
        task_eager_propagates=True,
        broker_connection_retry_on_startup=True,
    )

# Task discovery
celery_app.autodiscover_tasks([
    "app.tasks"
])

if __name__ == "__main__":
    celery_app.start() 