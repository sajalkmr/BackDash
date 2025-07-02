"""
API Routes Package - Main router configuration
Strategic integration of all API endpoints
"""

from fastapi import APIRouter
from .routes import data, strategy, backtest, analytics

# Create main API router
router = APIRouter()

# Include all route modules with proper prefixes and tags
router.include_router(
    data.router, 
    prefix="/data", 
    tags=["data"]
)

router.include_router(
    strategy.router, 
    prefix="/strategy", 
    tags=["strategy"]
)

router.include_router(
    backtest.router, 
    prefix="/backtest", 
    tags=["backtest"]
)

router.include_router(
    analytics.router, 
    prefix="/analytics", 
    tags=["analytics"]
) 