"""
Redis Manager for Task Persistence
Enhanced task storage and result management
"""

import redis
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pickle

from ..config import settings

class RedisManager:
    """Redis-based task and result management"""
    
    def __init__(self):
        # Parse Redis URL
        if settings.redis_url.startswith('redis://'):
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_timeout=30,
                socket_connect_timeout=30,
                retry_on_timeout=True,
                health_check_interval=30
            )
        else:
            # Fallback for local Redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_timeout=30,
                socket_connect_timeout=30,
                retry_on_timeout=True
            )
        
        # Key prefixes for organization
        self.TASK_PREFIX = "backdash:task:"
        self.RESULT_PREFIX = "backdash:result:"
        self.PROGRESS_PREFIX = "backdash:progress:"
        self.STATUS_PREFIX = "backdash:status:"
        
        # Default TTL (Time To Live) in seconds
        self.DEFAULT_TTL = 3600  # 1 hour
        self.RESULT_TTL = 86400   # 24 hours
        
    def _get_task_key(self, task_id: str) -> str:
        """Get Redis key for task info"""
        return f"{self.TASK_PREFIX}{task_id}"
    
    def _get_result_key(self, task_id: str) -> str:
        """Get Redis key for task result"""
        return f"{self.RESULT_PREFIX}{task_id}"
    
    def _get_progress_key(self, task_id: str) -> str:
        """Get Redis key for task progress"""
        return f"{self.PROGRESS_PREFIX}{task_id}"
    
    def _get_status_key(self, task_id: str) -> str:
        """Get Redis key for task status"""
        return f"{self.STATUS_PREFIX}{task_id}"
    
    def store_task_info(self, task_id: str, task_info: Dict[str, Any]) -> bool:
        """Store task information in Redis"""
        try:
            key = self._get_task_key(task_id)
            task_info['updated_at'] = datetime.now().isoformat()
            
            # Store as JSON
            self.redis_client.setex(
                key,
                self.DEFAULT_TTL,
                json.dumps(task_info, default=str)
            )
            
            # Also store in a set for task listing
            self.redis_client.sadd("backdash:active_tasks", task_id)
            self.redis_client.expire("backdash:active_tasks", self.DEFAULT_TTL)
            
            return True
        except Exception as e:
            print(f"Error storing task info for {task_id}: {e}")
            return False
    
    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task information from Redis"""
        try:
            key = self._get_task_key(task_id)
            data = self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Error getting task info for {task_id}: {e}")
            return None
    
    def update_task_progress(self, task_id: str, progress: int, message: str) -> bool:
        """Update task progress"""
        try:
            # Update progress specifically
            progress_key = self._get_progress_key(task_id)
            progress_data = {
                'progress': progress,
                'message': message,
                'updated_at': datetime.now().isoformat()
            }
            
            self.redis_client.setex(
                progress_key,
                self.DEFAULT_TTL,
                json.dumps(progress_data)
            )
            
            # Update main task info
            task_info = self.get_task_info(task_id)
            if task_info:
                task_info.update({
                    'progress': progress,
                    'message': message,
                    'updated_at': datetime.now().isoformat()
                })
                self.store_task_info(task_id, task_info)
            
            return True
        except Exception as e:
            print(f"Error updating task progress for {task_id}: {e}")
            return False
    
    def update_task_status(self, task_id: str, status: str, message: str) -> bool:
        """Update task status"""
        try:
            # Update status specifically
            status_key = self._get_status_key(task_id)
            status_data = {
                'status': status,
                'message': message,
                'updated_at': datetime.now().isoformat()
            }
            
            self.redis_client.setex(
                status_key,
                self.DEFAULT_TTL,
                json.dumps(status_data)
            )
            
            # Update main task info
            task_info = self.get_task_info(task_id)
            if task_info:
                task_info.update({
                    'status': status,
                    'message': message,
                    'updated_at': datetime.now().isoformat()
                })
                self.store_task_info(task_id, task_info)
            
            # Remove from active tasks if completed/failed/cancelled
            if status in ['completed', 'failed', 'cancelled']:
                self.redis_client.srem("backdash:active_tasks", task_id)
            
            return True
        except Exception as e:
            print(f"Error updating task status for {task_id}: {e}")
            return False
    
    def store_task_result(self, task_id: str, result: Any) -> bool:
        """Store task result in Redis"""
        try:
            key = self._get_result_key(task_id)
            
            # Store result with longer TTL
            if isinstance(result, dict):
                self.redis_client.setex(
                    key,
                    self.RESULT_TTL,
                    json.dumps(result, default=str)
                )
            else:
                # Use pickle for complex objects
                self.redis_client.setex(
                    key,
                    self.RESULT_TTL,
                    pickle.dumps(result)
                )
            
            # Update task info with completion
            self.update_task_status(task_id, 'completed', 'Task completed successfully')
            
            return True
        except Exception as e:
            print(f"Error storing task result for {task_id}: {e}")
            return False
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get task result from Redis"""
        try:
            key = self._get_result_key(task_id)
            data = self.redis_client.get(key)
            
            if data:
                try:
                    # Try JSON first
                    return json.loads(data)
                except json.JSONDecodeError:
                    # Fall back to pickle
                    return pickle.loads(data)
            return None
        except Exception as e:
            print(f"Error getting task result for {task_id}: {e}")
            return None
    
    def store_task_error(self, task_id: str, error: str) -> bool:
        """Store task error information"""
        try:
            # Update task info with error
            task_info = self.get_task_info(task_id)
            if task_info:
                task_info.update({
                    'status': 'failed',
                    'error': error,
                    'message': f'Task failed: {error}',
                    'updated_at': datetime.now().isoformat()
                })
                self.store_task_info(task_id, task_info)
            
            # Remove from active tasks
            self.redis_client.srem("backdash:active_tasks", task_id)
            
            return True
        except Exception as e:
            print(f"Error storing task error for {task_id}: {e}")
            return False
    
    def get_active_tasks(self) -> List[str]:
        """Get list of active task IDs"""
        try:
            return list(self.redis_client.smembers("backdash:active_tasks"))
        except Exception as e:
            print(f"Error getting active tasks: {e}")
            return []
    
    def cleanup_expired_tasks(self) -> int:
        """Clean up expired tasks and return count of cleaned tasks"""
        try:
            cleaned_count = 0
            active_tasks = self.get_active_tasks()
            
            for task_id in active_tasks:
                task_info = self.get_task_info(task_id)
                if not task_info:
                    # Task info doesn't exist, remove from active list
                    self.redis_client.srem("backdash:active_tasks", task_id)
                    cleaned_count += 1
                    continue
                
                # Check if task is old (more than 2 hours)
                created_at = task_info.get('created_at')
                if created_at:
                    created_time = datetime.fromisoformat(created_at)
                    if datetime.now() - created_time > timedelta(hours=2):
                        # Clean up old task
                        self.delete_task(task_id)
                        cleaned_count += 1
            
            return cleaned_count
        except Exception as e:
            print(f"Error cleaning up expired tasks: {e}")
            return 0
    
    def delete_task(self, task_id: str) -> bool:
        """Delete all task-related data"""
        try:
            # Delete all keys related to this task
            keys_to_delete = [
                self._get_task_key(task_id),
                self._get_result_key(task_id),
                self._get_progress_key(task_id),
                self._get_status_key(task_id)
            ]
            
            # Delete keys
            for key in keys_to_delete:
                self.redis_client.delete(key)
            
            # Remove from active tasks
            self.redis_client.srem("backdash:active_tasks", task_id)
            
            return True
        except Exception as e:
            print(f"Error deleting task {task_id}: {e}")
            return False
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get task processing statistics"""
        try:
            active_tasks = self.get_active_tasks()
            stats = {
                'active_tasks_count': len(active_tasks),
                'redis_memory_usage': self.redis_client.info()['used_memory_human'],
                'redis_connected_clients': self.redis_client.info()['connected_clients'],
                'total_keys': self.redis_client.dbsize()
            }
            
            # Count by status
            status_counts = {}
            for task_id in active_tasks:
                task_info = self.get_task_info(task_id)
                if task_info:
                    status = task_info.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
            
            stats['status_breakdown'] = status_counts
            return stats
        except Exception as e:
            print(f"Error getting task statistics: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            return self.redis_client.ping()
        except:
            return False

# Global Redis manager instance
redis_manager = RedisManager() 