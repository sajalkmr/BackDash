from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...core.websocket_manager import manager

router = APIRouter()

@router.websocket("/backtest/{backtest_id}")
async def websocket_backtest_endpoint(websocket: WebSocket, backtest_id: str):
    await manager.connect(websocket, backtest_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message text was: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, backtest_id)
        await manager.broadcast_progress(backtest_id, {"status": "client_disconnected"})

@router.websocket("/strategy/{strategy_id}")
async def websocket_strategy_endpoint(websocket: WebSocket, strategy_id: str):
    await manager.connect(websocket, strategy_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Strategy update: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, strategy_id)
        await manager.broadcast_progress(strategy_id, {"status": "client_disconnected"}) 