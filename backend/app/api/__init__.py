"""
BackDash - API Package
Enhanced API routes with comprehensive functionality
"""

from fastapi import APIRouter
from .routes import strategy, data, analytics

# Create main router
router = APIRouter()

# Include sub-routers
router.include_router(strategy.router, prefix="/strategy", tags=["strategy"])
router.include_router(data.router, prefix="/data", tags=["data"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"]) 