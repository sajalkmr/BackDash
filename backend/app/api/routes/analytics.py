"""
Enhanced Analytics API Routes - Phase 4 Implementation
Advanced analytics, benchmark comparison, and multi-strategy analysis
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...models.analytics import (
    CompleteAnalytics, AnalyticsRequest, ComparisonType, 
    BenchmarkComparison, MultiStrategyAnalysis, ExportData
)
from ...models.backtest import BacktestResult
from ...core.analytics_engine import EnhancedAnalyticsEngine
from ...core.redis_manager import redis_manager
from ...services.export_service import EnhancedExportService
from ...services.database_service import database_service

router = APIRouter()
analytics_engine = EnhancedAnalyticsEngine()
export_service = EnhancedExportService()

@router.get("/health")
async def analytics_health():
    """Health check for enhanced analytics service"""
    return {
        "status": "healthy",
        "service": "enhanced_analytics",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "features": [
            "Advanced Performance Metrics",
            "Benchmark Comparison",
            "Multi-Strategy Analysis", 
            "Rolling Metrics",
            "Risk Analytics",
            "Export Capabilities"
        ]
    }

@router.post("/generate/{backtest_id}")
async def generate_comprehensive_analytics(
    backtest_id: str,
    benchmark_symbol: Optional[str] = "BTC-USDT",
    include_benchmark: bool = True,
    include_rolling_metrics: bool = True
) -> Dict[str, Any]:
    """Generate comprehensive analytics for a backtest"""
    try:
        # Get backtest result from Redis
        backtest_result = redis_manager.get_task_result(backtest_id)
        if not backtest_result:
            raise HTTPException(status_code=404, detail=f"Backtest {backtest_id} not found")
        
        # Convert to BacktestResult object if needed
        if isinstance(backtest_result, dict):
            try:
                backtest_result = BacktestResult(**backtest_result)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid backtest result format: {str(e)}")
        
        # Generate analytics
        analytics = await analytics_engine.calculate_complete_analytics(
            backtest_result,
            benchmark_symbol,
            include_benchmark,
            include_rolling_metrics
        )
        
        # Store in Redis for fast access
        analytics_key = f"analytics:{backtest_id}"
        redis_manager.redis_client.setex(
            analytics_key,
            86400,  # 24 hours
            analytics.json()
        )
        
        # Store in database for persistence (Phase 5 enhancement)
        try:
            database_service.save_analytics(backtest_id, analytics)
        except Exception as db_error:
            # Log error but don't fail the request
            print(f"Warning: Failed to save analytics to database: {db_error}")
        
        return {
            "analytics": analytics.dict(),
            "generated_at": datetime.now().isoformat(),
            "status": "completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics generation failed: {str(e)}")

@router.get("/get/{backtest_id}")
async def get_analytics(backtest_id: str) -> Dict[str, Any]:
    """Get stored analytics for a backtest"""
    try:
        # Try Redis first for fast access
        analytics_key = f"analytics:{backtest_id}"
        analytics_data = redis_manager.redis_client.get(analytics_key)
        
        if analytics_data:
            analytics = CompleteAnalytics.parse_raw(analytics_data)
            return analytics.dict()
        
        # Fallback to database (Phase 5 enhancement)
        try:
            db_analytics = database_service.get_analytics(backtest_id)
            if db_analytics and db_analytics.metrics:
                # Restore to Redis for future fast access
                redis_manager.redis_client.setex(
                    analytics_key,
                    86400,  # 24 hours
                    CompleteAnalytics(**db_analytics.metrics).json()
                )
                return db_analytics.metrics
        except Exception as db_error:
            print(f"Warning: Failed to retrieve analytics from database: {db_error}")
        
        raise HTTPException(status_code=404, detail=f"Analytics for backtest {backtest_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analytics: {str(e)}")

@router.post("/benchmark-compare/{backtest_id}")
async def compare_with_benchmark(
    backtest_id: str,
    benchmark_symbol: str = "BTC-USDT"
) -> Dict[str, Any]:
    """Compare strategy performance with benchmark"""
    try:
        # Get backtest result
        backtest_result = redis_manager.get_task_result(backtest_id)
        if not backtest_result:
            raise HTTPException(status_code=404, detail=f"Backtest {backtest_id} not found")
        
        if isinstance(backtest_result, dict):
            backtest_result = BacktestResult(**backtest_result)
        
        # Calculate benchmark comparison
        benchmark_comparison = await analytics_engine.calculate_benchmark_comparison(
            backtest_result, benchmark_symbol
        )
        
        return benchmark_comparison.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark comparison failed: {str(e)}")

@router.post("/multi-strategy-compare")
async def compare_multiple_strategies(
    analytics_request: AnalyticsRequest
) -> Dict[str, Any]:
    """Compare multiple strategies"""
    try:
        if len(analytics_request.backtest_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 strategies required for comparison")
        
        # Get backtest results
        backtest_results = []
        for backtest_id in analytics_request.backtest_ids:
            result_data = redis_manager.get_task_result(backtest_id)
            if result_data:
                if isinstance(result_data, dict):
                    result_data = BacktestResult(**result_data)
                backtest_results.append(result_data)
        
        if len(backtest_results) < 2:
            raise HTTPException(status_code=400, detail="Could not find enough valid backtest results")
        
        # Calculate multi-strategy analysis
        multi_strategy_analysis = await analytics_engine.calculate_multi_strategy_analysis(
            backtest_results
        )
        
        return multi_strategy_analysis.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-strategy comparison failed: {str(e)}")

@router.get("/rolling-metrics/{backtest_id}")
async def get_rolling_metrics(
    backtest_id: str,
    window_days: int = 30,
    metrics: List[str] = ["sharpe", "volatility", "returns"]
) -> Dict[str, List[float]]:
    """Get rolling metrics for a backtest"""
    try:
        # Get analytics
        analytics_key = f"analytics:{backtest_id}"
        analytics_data = redis_manager.redis_client.get(analytics_key)
        
        if not analytics_data:
            raise HTTPException(status_code=404, detail=f"Analytics for backtest {backtest_id} not found")
        
        analytics = CompleteAnalytics.parse_raw(analytics_data)
        
        rolling_data = {}
        if "sharpe" in metrics:
            rolling_data["sharpe"] = analytics.performance.rolling_sharpe
        if "volatility" in metrics:
            rolling_data["volatility"] = analytics.performance.rolling_volatility
        if "returns" in metrics:
            rolling_data["returns"] = analytics.performance.rolling_returns
        
        return rolling_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving rolling metrics: {str(e)}")

@router.get("/risk-metrics/{backtest_id}")
async def get_detailed_risk_metrics(backtest_id: str) -> Dict[str, Any]:
    """Get detailed risk metrics for a backtest"""
    try:
        # Get analytics
        analytics_key = f"analytics:{backtest_id}"
        analytics_data = redis_manager.redis_client.get(analytics_key)
        
        if not analytics_data:
            raise HTTPException(status_code=404, detail=f"Analytics for backtest {backtest_id} not found")
        
        analytics = CompleteAnalytics.parse_raw(analytics_data)
        
        return {
            "basic_risk": analytics.performance.risk_metrics.dict(),
            "drawdown_periods": [dp.dict() for dp in analytics.performance.drawdown_periods],
            "var_analysis": {
                "var_95": analytics.performance.risk_metrics.value_at_risk_95,
                "var_99": analytics.performance.risk_metrics.value_at_risk_99,
                "cvar_95": analytics.performance.risk_metrics.conditional_var_95,
                "cvar_99": analytics.performance.risk_metrics.conditional_var_99
            },
            "distribution_metrics": {
                "omega_ratio": analytics.performance.risk_metrics.omega_ratio,
                "kappa_3": analytics.performance.risk_metrics.kappa_3,
                "gain_pain_ratio": analytics.performance.risk_metrics.gain_pain_ratio
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving risk metrics: {str(e)}")

@router.get("/performance-summary/{backtest_id}")
async def get_performance_summary(backtest_id: str) -> Dict[str, Any]:
    """Get performance summary for quick overview"""
    try:
        # Get analytics
        analytics_key = f"analytics:{backtest_id}"
        analytics_data = redis_manager.redis_client.get(analytics_key)
        
        if not analytics_data:
            raise HTTPException(status_code=404, detail=f"Analytics for backtest {backtest_id} not found")
        
        analytics = CompleteAnalytics.parse_raw(analytics_data)
        
        return {
            "core_metrics": {
                "total_return": analytics.performance.core_metrics.pnl_percent,
                "cagr": analytics.performance.core_metrics.cagr_percent,
                "sharpe_ratio": analytics.performance.core_metrics.sharpe_ratio,
                "max_drawdown": analytics.performance.core_metrics.max_drawdown_percent,
                "volatility": analytics.performance.core_metrics.volatility_percent
            },
            "trading_summary": {
                "total_trades": analytics.performance.trading_metrics.total_trades,
                "win_rate": analytics.performance.trading_metrics.win_rate_percent,
                "profit_factor": analytics.performance.trading_metrics.profit_factor,
                "expectancy": analytics.performance.trading_metrics.expectancy
            },
            "benchmark_performance": analytics.benchmark_comparison.dict() if analytics.benchmark_comparison else None,
            "generated_at": analytics.performance.generated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving performance summary: {str(e)}")

@router.post("/export/{backtest_id}")
async def export_analytics(
    backtest_id: str,
    export_format: str = "JSON",
    include_charts: bool = True,
    include_trade_details: bool = True,
    include_daily_data: bool = True,
    include_rolling_metrics: bool = True,
    include_benchmark_comparison: bool = True
) -> Dict[str, Any]:
    """Export analytics data in various formats"""
    try:
        # Validate export format
        supported_formats = export_service.get_supported_formats()
        if export_format not in supported_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported export format. Supported formats: {', '.join(supported_formats)}"
            )
        
        # Get analytics and backtest result
        analytics_key = f"analytics:{backtest_id}"
        analytics_data = redis_manager.redis_client.get(analytics_key)
        
        if not analytics_data:
            raise HTTPException(status_code=404, detail=f"Analytics for backtest {backtest_id} not found")
        
        analytics = CompleteAnalytics.parse_raw(analytics_data)
        
        # Get backtest result
        backtest_result = redis_manager.get_task_result(backtest_id)
        if not backtest_result:
            raise HTTPException(status_code=404, detail=f"Backtest {backtest_id} not found")
        
        if isinstance(backtest_result, dict):
            backtest_result = BacktestResult(**backtest_result)
        
        # Validate export request
        if not await export_service.validate_export_request(export_format, analytics):
            raise HTTPException(status_code=400, detail="Invalid export request")
        
        # Generate export using enhanced export service
        export_data = await export_service.export_analytics(
            analytics=analytics,
            backtest_result=backtest_result,
            export_format=export_format,
            include_charts=include_charts,
            include_trade_details=include_trade_details,
            include_daily_data=include_daily_data,
            include_rolling_metrics=include_rolling_metrics,
            include_benchmark_comparison=include_benchmark_comparison
        )
        
        return {
            "export_data": export_data.dict(),
            "status": "completed",
            "format": export_format,
            "supported_formats": supported_formats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/list")
async def list_available_analytics(
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """List available analytics reports"""
    try:
        # Get analytics keys from Redis
        pattern = "analytics:*"
        keys = redis_manager.redis_client.keys(pattern)
        
        analytics_list = []
        for key in keys[offset:offset+limit]:
            try:
                data = redis_manager.redis_client.get(key)
                if data:
                    analytics = CompleteAnalytics.parse_raw(data)
                    analytics_list.append({
                        "backtest_id": analytics.performance.backtest_id,
                        "generated_at": analytics.performance.generated_at.isoformat(),
                        "has_benchmark": analytics.benchmark_comparison is not None,
                        "total_return": analytics.performance.core_metrics.pnl_percent,
                        "sharpe_ratio": analytics.performance.core_metrics.sharpe_ratio,
                        "max_drawdown": analytics.performance.core_metrics.max_drawdown_percent
                    })
            except:
                continue  # Skip invalid entries
        
        return {
            "analytics": analytics_list,
            "total": len(keys),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing analytics: {str(e)}")

@router.delete("/delete/{backtest_id}")
async def delete_analytics(backtest_id: str):
    """Delete analytics for a backtest"""
    try:
        # Delete from Redis
        analytics_key = f"analytics:{backtest_id}"
        redis_deleted = redis_manager.redis_client.delete(analytics_key)
        
        # Delete from database (Phase 5 enhancement)
        db_deleted = False
        try:
            db_deleted = database_service.delete_analytics(backtest_id)
        except Exception as db_error:
            print(f"Warning: Failed to delete analytics from database: {db_error}")
        
        if redis_deleted or db_deleted:
            return {
                "message": f"Analytics for backtest {backtest_id} deleted successfully",
                "deleted_from_redis": bool(redis_deleted),
                "deleted_from_database": db_deleted,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Analytics for backtest {backtest_id} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting analytics: {str(e)}")

# ==================== PHASE 5 DATABASE INTEGRATION ENDPOINTS ====================

@router.get("/database/list")
async def list_database_analytics(
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """List analytics stored in database (Phase 5 feature)"""
    try:
        # This would require a new method in database_service
        # For now, return a placeholder response
        return {
            "message": "Database analytics listing",
            "note": "This endpoint lists analytics stored persistently in the database",
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing database analytics: {str(e)}")

@router.post("/database/migrate")
async def migrate_analytics_to_database():
    """Migrate analytics from Redis to database for persistence"""
    try:
        # Get all analytics keys from Redis
        pattern = "analytics:*"
        keys = redis_manager.redis_client.keys(pattern)
        
        migrated_count = 0
        failed_count = 0
        
        for key in keys:
            try:
                # Get analytics data from Redis
                analytics_data = redis_manager.redis_client.get(key)
                if analytics_data:
                    analytics = CompleteAnalytics.parse_raw(analytics_data)
                    backtest_id = key.decode('utf-8').replace('analytics:', '')
                    
                    # Save to database
                    database_service.save_analytics(backtest_id, analytics)
                    migrated_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Failed to migrate analytics for key {key}: {e}")
        
        return {
            "message": "Analytics migration completed",
            "migrated_count": migrated_count,
            "failed_count": failed_count,
            "total_processed": len(keys),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during analytics migration: {str(e)}")