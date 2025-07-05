from fastapi import WebSocket
from typing import Dict, List, Optional
import asyncio
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.backtest_progress: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, backtest_id: str):
        await websocket.accept()
        if backtest_id not in self.active_connections:
            self.active_connections[backtest_id] = []
        self.active_connections[backtest_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, backtest_id: str):
        if backtest_id in self.active_connections:
            self.active_connections[backtest_id].remove(websocket)
            if not self.active_connections[backtest_id]:
                del self.active_connections[backtest_id]
    
    async def broadcast_progress(self, backtest_id: str, data: dict):
        if backtest_id in self.active_connections:
            self.backtest_progress[backtest_id] = data
            for connection in self.active_connections[backtest_id]:
                try:
                    await connection.send_json(data)
                except:
                    await self.disconnect(connection, backtest_id)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    def get_progress(self, backtest_id: str) -> Optional[Dict]:
        return self.backtest_progress.get(backtest_id)

manager = ConnectionManager() 