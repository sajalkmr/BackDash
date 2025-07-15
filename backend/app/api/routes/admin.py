"""
Admin API Routes - System monitoring and management
Enhanced Phase 5 implementation with user management and database operations
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ...core.redis_manager import redis_manager
from ...tasks.analytics_tasks import health_check_task, get_system_statistics
from ...celery_app import celery_app
from ...services.database_service import database_service
from ...db.database import get_db
from ...db.models import User as UserORM, UserRole
from ...api.routes.auth import get_current_user
from ...models.user import UserCreate, UserRead

router = APIRouter()

# Admin authentication dependency
async def get_admin_user(current_user: UserORM = Depends(get_current_user)) -> UserORM:
    """Ensure current user is an admin"""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

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

# ==================== USER MANAGEMENT ENDPOINTS ====================

@router.get("/users", response_model=List[UserRead])
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    active_only: bool = True,
    admin_user: UserORM = Depends(get_admin_user)
):
    """List all users (admin only)"""
    try:
        users = database_service.list_users(
            skip=skip,
            limit=limit,
            role=role,
            active_only=active_only
        )
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")

@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    user_data: UserCreate,
    role: UserRole = UserRole.user,
    admin_user: UserORM = Depends(get_admin_user)
):
    """Create a new user (admin only)"""
    try:
        user = database_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            role=role
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.get("/users/{user_id}", response_model=UserRead)
async def get_user_admin(
    user_id: str,
    admin_user: UserORM = Depends(get_admin_user)
):
    """Get user details (admin only)"""
    try:
        user = database_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")

@router.put("/users/{user_id}", response_model=UserRead)
async def update_user_admin(
    user_id: str,
    updates: Dict[str, Any],
    admin_user: UserORM = Depends(get_admin_user)
):
    """Update user information (admin only)"""
    try:
        user = database_service.update_user(user_id, updates)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

@router.post("/users/{user_id}/deactivate")
async def deactivate_user_admin(
    user_id: str,
    admin_user: UserORM = Depends(get_admin_user)
):
    """Deactivate a user account (admin only)"""
    try:
        success = database_service.deactivate_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": user_id,
            "status": "deactivated",
            "message": "User account has been deactivated",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deactivating user: {str(e)}")

@router.post("/users/{user_id}/promote")
async def promote_user_to_admin(
    user_id: str,
    admin_user: UserORM = Depends(get_admin_user)
):
    """Promote user to admin role (admin only)"""
    try:
        user = database_service.update_user(user_id, {"role": UserRole.admin})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": user_id,
            "status": "promoted",
            "message": "User has been promoted to admin",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error promoting user: {str(e)}")

# ==================== DATABASE MANAGEMENT ENDPOINTS ====================

@router.get("/database/statistics")
async def get_database_statistics(
    admin_user: UserORM = Depends(get_admin_user)
):
    """Get comprehensive database statistics (admin only)"""
    try:
        stats = database_service.get_system_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving database statistics: {str(e)}")

@router.post("/database/cleanup")
async def cleanup_old_database_data(
    days_old: int = 90,
    admin_user: UserORM = Depends(get_admin_user)
):
    """Clean up old database data (admin only)"""
    try:
        cleanup_result = database_service.cleanup_old_data(days_old)
        return {
            "cleanup_result": cleanup_result,
            "message": f"Database cleanup completed for data older than {days_old} days",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during database cleanup: {str(e)}")

@router.get("/database/export/{user_id}")
async def export_user_data_admin(
    user_id: str,
    admin_user: UserORM = Depends(get_admin_user)
):
    """Export all data for a specific user (admin only)"""
    try:
        user_data = database_service.export_user_data(user_id)
        return user_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting user data: {str(e)}")

# ==================== SYSTEM MAINTENANCE ENDPOINTS ====================

@router.post("/maintenance/analytics/rebuild")
async def rebuild_analytics_cache(
    admin_user: UserORM = Depends(get_admin_user)
):
    """Rebuild analytics cache from database (admin only)"""
    try:
        # This would trigger a background task to rebuild analytics cache
        # For now, return a placeholder response
        return {
            "status": "initiated",
            "message": "Analytics cache rebuild initiated",
            "timestamp": datetime.now().isoformat(),
            "note": "This is a placeholder - actual implementation would trigger background task"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initiating analytics rebuild: {str(e)}")

@router.post("/maintenance/data/validate")
async def validate_data_integrity(
    admin_user: UserORM = Depends(get_admin_user)
):
    """Validate data integrity across the system (admin only)"""
    try:
        # Placeholder for data integrity validation
        return {
            "status": "completed",
            "message": "Data integrity validation completed",
            "issues_found": 0,
            "timestamp": datetime.now().isoformat(),
            "note": "This is a placeholder - actual implementation would perform comprehensive validation"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during data validation: {str(e)}")

@router.get("/maintenance/status")
async def get_maintenance_status(
    admin_user: UserORM = Depends(get_admin_user)
):
    """Get current maintenance status (admin only)"""
    try:
        return {
            "maintenance_mode": False,
            "scheduled_maintenance": None,
            "last_cleanup": None,
            "system_health": "operational",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving maintenance status: {str(e)}")