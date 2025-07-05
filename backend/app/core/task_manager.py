from typing import Dict, Any, Optional, Callable
import asyncio
from datetime import datetime
import uuid

from .websocket_manager import manager

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.progress_callbacks: Dict[str, Callable] = {}
    
    def create_task(self, task_type: str, params: Dict[str, Any]) -> str:
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            "id": task_id,
            "type": task_type,
            "params": params,
            "status": "pending",
            "progress": 0,
            "message": "Task created",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "result": None,
            "error": None
        }
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.tasks.get(task_id)
    
    async def update_task(
        self, 
        task_id: str, 
        status: Optional[str] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ):
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if status:
                task["status"] = status
            if progress is not None:
                task["progress"] = progress
            if message:
                task["message"] = message
            if result is not None:
                task["result"] = result
            if error:
                task["error"] = error
            
            task["updated_at"] = datetime.now().isoformat()
            
            # Broadcast progress via WebSocket
            await manager.broadcast_progress(task_id, {
                "task_id": task_id,
                "status": task["status"],
                "progress": task["progress"],
                "message": task["message"]
            })
            
            # Call progress callback if registered
            if task_id in self.progress_callbacks:
                await self.progress_callbacks[task_id](
                    task["progress"],
                    task["message"]
                )
    
    def register_progress_callback(
        self, 
        task_id: str, 
        callback: Callable[[int, str], None]
    ):
        self.progress_callbacks[task_id] = callback
    
    def unregister_progress_callback(self, task_id: str):
        if task_id in self.progress_callbacks:
            del self.progress_callbacks[task_id]
    
    async def run_task(
        self,
        task_id: str,
        func: Callable,
        *args,
        **kwargs
    ):
        try:
            await self.update_task(
                task_id,
                status="running",
                progress=0,
                message="Task started"
            )
            
            result = await func(*args, **kwargs)
            
            await self.update_task(
                task_id,
                status="completed",
                progress=100,
                message="Task completed successfully",
                result=result
            )
            
        except Exception as e:
            await self.update_task(
                task_id,
                status="failed",
                message=f"Task failed: {str(e)}",
                error=str(e)
            )
            raise
        finally:
            self.unregister_progress_callback(task_id)

task_manager = TaskManager() 