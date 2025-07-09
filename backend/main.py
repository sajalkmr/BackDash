"""
BackDash - Enhanced Main Application
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import asyncio
from datetime import datetime

from app.api.routes import strategy, data, analytics, websocket
from app.api.routes import backtest, admin
from app.config import settings

# Create FastAPI application with configuration-based settings
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
    debug=settings.debug
)

# Configure CORS using configuration settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(strategy.router, prefix="/api/v1/strategy", tags=["strategy"])
app.include_router(data.router, prefix="/api/v1/data", tags=["data"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(backtest.router, prefix="/api/v1/backtest", tags=["backtest"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# Static files serving (for future use)
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "documentation": settings.docs_url,
        "api_version": "v1",
        "environment": "production" if settings.is_production else "development",
        "features": [
            "Visual Strategy Builder",
            "Real-time Backtesting",
            "Advanced Analytics",
            "WebSocket Updates",
            "Professional Risk Management"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.app_version,
        "environment": "production" if settings.is_production else "development",
        "debug_mode": settings.debug,
        "services": {
            "api": "operational",
            "database": "operational" if settings.database_url else "not_configured",
            "websocket": "operational"
        }
    }

# WebSocket endpoint for real-time backtest updates
@app.websocket("/ws/backtest/{backtest_id}")
async def websocket_backtest_updates(websocket: WebSocket, backtest_id: str):
    """WebSocket endpoint for real-time backtest progress and results"""
    await websocket.accept()
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "backtest_id": backtest_id,
            "status": "connected",
            "message": "Real-time updates enabled"
        })
        
        # Keep connection alive and handle messages
        while True:
            # In a real implementation, this would listen for backtest updates
            # For now, we'll wait for client messages
            data = await websocket.receive_text()
            
            # Echo back for testing (replace with actual backtest logic)
            await websocket.send_json({
                "type": "update",
                "backtest_id": backtest_id,
                "status": "processing",
                "message": f"Received: {data}"
            })
            
    except WebSocketDisconnect:
        print(f"Client disconnected from backtest {backtest_id}")
    except Exception as e:
        print(f"WebSocket error for backtest {backtest_id}: {str(e)}")
        await websocket.close(code=1000)

# WebSocket endpoint for strategy validation
@app.websocket("/ws/strategy/{strategy_id}")
async def websocket_strategy_updates(websocket: WebSocket, strategy_id: str):
    """WebSocket endpoint for real-time strategy validation and testing"""
    await websocket.accept()
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "strategy_id": strategy_id,
            "status": "connected",
            "message": "Strategy validation service ready"
        })
        
        # Simulate strategy validation steps
        validation_steps = [
            "Validating indicators configuration",
            "Checking logical conditions",
            "Verifying risk management rules",
            "Strategy validation complete"
        ]
        
        for i, step in enumerate(validation_steps):
            await websocket.send_json({
                "type": "validation_progress",
                "strategy_id": strategy_id,
                "step": i + 1,
                "total_steps": len(validation_steps),
                "message": step,
                "status": "processing" if i < len(validation_steps) - 1 else "complete"
            })
            
            # Add small delay for demonstration
            await asyncio.sleep(0.5)
            
    except WebSocketDisconnect:
        print(f"Client disconnected from strategy {strategy_id}")
    except Exception as e:
        print(f"WebSocket error for strategy {strategy_id}: {str(e)}")
        await websocket.close(code=1000)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload and not settings.is_production,
        log_level=settings.log_level,
        reload_dirs=["app"] if settings.reload else None
    ) 