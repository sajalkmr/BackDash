"""
Advanced Analytics Models - Enhanced performance metrics and analytics
Phase 4: Advanced Analytics Implementation
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ComparisonType(str, Enum):
    """Types of comparison analysis"""
    BENCHMARK = "benchmark"
    MULTI_STRATEGY = "multi_strategy"
    PEER_GROUP = "peer_group"

class CoreMetrics(BaseModel):
    """Core performance metrics"""
    pnl_percent: float = Field(..., description="Total P&L percentage")
    pnl_dollars: float = Field(..., description="Total P&L in dollars")
    cagr_percent: float = Field(..., description="Compound Annual Growth Rate")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    calmar_ratio: float = Field(..., description="Calmar ratio")
    max_drawdown_percent: float = Field(..., description="Maximum drawdown percentage")
    max_drawdown_dollars: float = Field(..., description="Maximum drawdown in dollars")
    volatility_percent: float = Field(..., description="Annualized volatility percentage")

class TradingMetrics(BaseModel):
    """Trading-specific metrics"""
    total_trades: int = Field(..., description="Total number of trades")
    win_rate_percent: float = Field(..., description="Win rate percentage")
    avg_trade_duration_hours: float = Field(..., description="Average trade duration in hours")
    largest_win_percent: float = Field(..., description="Largest winning trade percentage")
    largest_loss_percent: float = Field(..., description="Largest losing trade percentage")
    turnover_percent: float = Field(..., description="Portfolio turnover percentage")
    profit_factor: float = Field(..., description="Profit factor (gross profit / gross loss)")
    avg_win_percent: float = Field(..., description="Average winning trade percentage")
    avg_loss_percent: float = Field(..., description="Average losing trade percentage")
    
    # Enhanced trading metrics
    expectancy: float = Field(default=0, description="Mathematical expectancy per trade")
    ulcer_index: float = Field(default=0, description="Ulcer Index for risk measurement")
    recovery_factor: float = Field(default=0, description="Net profit / Max drawdown")
    max_consecutive_wins: int = Field(default=0, description="Maximum consecutive winning trades")
    max_consecutive_losses: int = Field(default=0, description="Maximum consecutive losing trades")

class RiskMetrics(BaseModel):
    """Risk-related metrics"""
    value_at_risk_95: float = Field(..., description="Value at Risk at 95% confidence")
    value_at_risk_99: float = Field(..., description="Value at Risk at 99% confidence")
    leverage_percent: float = Field(..., description="Average leverage percentage")
    beta_to_benchmark: Optional[float] = Field(default=None, description="Beta relative to benchmark")
    max_consecutive_losses: int = Field(..., description="Maximum consecutive losing trades")
    downside_deviation: float = Field(..., description="Downside deviation")
    
    # Enhanced risk metrics
    conditional_var_95: float = Field(default=0, description="Conditional VaR at 95%")
    conditional_var_99: float = Field(default=0, description="Conditional VaR at 99%")
    omega_ratio: float = Field(default=0, description="Omega ratio")
    kappa_3: float = Field(default=0, description="Kappa 3 (skewness preference)")
    gain_pain_ratio: float = Field(default=0, description="Gain to Pain ratio")
    sterling_ratio: float = Field(default=0, description="Sterling ratio")

class DrawdownPeriod(BaseModel):
    """Individual drawdown period"""
    start_date: datetime = Field(..., description="Drawdown start date")
    end_date: Optional[datetime] = Field(default=None, description="Drawdown end date")
    peak_value: float = Field(..., description="Portfolio value at peak")
    trough_value: float = Field(..., description="Portfolio value at trough")
    drawdown_percent: float = Field(..., description="Drawdown percentage")
    duration_days: Optional[int] = Field(default=None, description="Drawdown duration in days")
    recovery_days: Optional[int] = Field(default=None, description="Recovery duration in days")
    underwater_days: int = Field(default=0, description="Total days underwater")

class MonthlyReturns(BaseModel):
    """Monthly returns breakdown"""
    year: int = Field(..., description="Year")
    month: int = Field(..., description="Month (1-12)")
    return_percent: float = Field(..., description="Monthly return percentage")
    trades_count: int = Field(..., description="Number of trades in the month")
    drawdown_percent: float = Field(default=0, description="Max drawdown in the month")
    volatility_percent: float = Field(default=0, description="Monthly volatility")

class PerformanceAnalytics(BaseModel):
    """Complete performance analytics"""
    backtest_id: str = Field(..., description="Associated backtest ID")
    generated_at: datetime = Field(..., description="Analytics generation timestamp")
    
    # Core performance metrics
    core_metrics: CoreMetrics = Field(..., description="Core performance metrics")
    
    # Trading metrics
    trading_metrics: TradingMetrics = Field(..., description="Trading-specific metrics")
    
    # Risk metrics
    risk_metrics: RiskMetrics = Field(..., description="Risk-related metrics")
    
    # Detailed breakdowns
    monthly_returns: List[MonthlyReturns] = Field(default=[], description="Monthly returns breakdown")
    drawdown_periods: List[DrawdownPeriod] = Field(default=[], description="All drawdown periods")
    
    # Return distributions
    daily_returns: List[float] = Field(default=[], description="Daily return percentages")
    trade_returns: List[float] = Field(default=[], description="Individual trade return percentages")
    
    # Rolling metrics (30-day windows)
    rolling_sharpe: List[float] = Field(default=[], description="30-day rolling Sharpe ratio")
    rolling_volatility: List[float] = Field(default=[], description="30-day rolling volatility")
    rolling_returns: List[float] = Field(default=[], description="30-day rolling returns")

class BenchmarkComparison(BaseModel):
    """Comparison with benchmark"""
    benchmark_symbol: str = Field(..., description="Benchmark symbol")
    benchmark_name: str = Field(default="", description="Human-readable benchmark name")
    
    # Return comparison
    strategy_return: float = Field(..., description="Strategy total return")
    benchmark_return: float = Field(..., description="Benchmark total return")
    excess_return: float = Field(..., description="Excess return over benchmark")
    
    # Risk-adjusted comparison
    tracking_error: float = Field(..., description="Tracking error")
    information_ratio: float = Field(..., description="Information ratio")
    correlation: float = Field(..., description="Correlation with benchmark")
    beta: float = Field(default=1.0, description="Beta coefficient")
    alpha: float = Field(default=0, description="Jensen's alpha")
    
    # Drawdown comparison
    strategy_max_drawdown: float = Field(..., description="Strategy max drawdown")
    benchmark_max_drawdown: float = Field(..., description="Benchmark max drawdown")
    
    # Timeline data for charts
    benchmark_equity_curve: List[Dict[str, Any]] = Field(default=[], description="Benchmark equity curve")
    relative_performance: List[Dict[str, Any]] = Field(default=[], description="Relative performance over time")

class StrategyComparison(BaseModel):
    """Multi-strategy comparison"""
    strategy_id: str = Field(..., description="Strategy identifier")
    strategy_name: str = Field(..., description="Strategy name")
    
    # Performance summary
    total_return: float = Field(..., description="Total return")
    cagr: float = Field(..., description="CAGR")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    volatility: float = Field(..., description="Volatility")
    
    # Rank among compared strategies
    rank_return: int = Field(default=0, description="Rank by return")
    rank_sharpe: int = Field(default=0, description="Rank by Sharpe ratio")
    rank_drawdown: int = Field(default=0, description="Rank by drawdown (lower is better)")
    
    # Risk-adjusted metrics
    sortino_ratio: float = Field(default=0, description="Sortino ratio")
    calmar_ratio: float = Field(default=0, description="Calmar ratio")
    
    # Additional context
    total_trades: int = Field(default=0, description="Total number of trades")
    win_rate: float = Field(default=0, description="Win rate percentage")

class MultiStrategyAnalysis(BaseModel):
    """Multi-strategy comparison analysis"""
    comparison_id: str = Field(..., description="Comparison analysis ID")
    generated_at: datetime = Field(..., description="Analysis generation timestamp")
    
    # Strategy comparisons
    strategies: List[StrategyComparison] = Field(..., description="Individual strategy comparisons")
    
    # Summary statistics
    best_return_strategy: str = Field(..., description="Strategy with best return")
    best_sharpe_strategy: str = Field(..., description="Strategy with best Sharpe ratio")
    lowest_drawdown_strategy: str = Field(..., description="Strategy with lowest drawdown")
    
    # Portfolio statistics if combined
    correlation_matrix: Dict[str, Dict[str, float]] = Field(default={}, description="Strategy correlation matrix")
    
    # Efficient frontier data
    efficient_frontier: List[Dict[str, float]] = Field(default=[], description="Risk-return efficient frontier")

class ExportData(BaseModel):
    """Data export package"""
    export_id: str = Field(..., description="Export identifier")
    export_type: str = Field(..., description="Type of export (CSV, Excel, PDF)")
    generated_at: datetime = Field(..., description="Export generation timestamp")
    
    # Data packages
    performance_data: Dict[str, Any] = Field(default={}, description="Performance data")
    trade_data: List[Dict[str, Any]] = Field(default=[], description="Individual trade data")
    daily_data: List[Dict[str, Any]] = Field(default=[], description="Daily portfolio data")
    
    # Chart data
    chart_configs: List[Dict[str, Any]] = Field(default=[], description="Chart configuration data")
    
    # Metadata
    strategy_config: Dict[str, Any] = Field(default={}, description="Strategy configuration")
    backtest_params: Dict[str, Any] = Field(default={}, description="Backtest parameters")

class CompleteAnalytics(BaseModel):
    """Complete analytics package"""
    performance: PerformanceAnalytics = Field(..., description="Performance analytics")
    benchmark_comparison: Optional[BenchmarkComparison] = Field(default=None, description="Benchmark comparison")
    multi_strategy_analysis: Optional[MultiStrategyAnalysis] = Field(default=None, description="Multi-strategy analysis")
    
    # Chart data for frontend
    equity_curve: List[Dict[str, Any]] = Field(default=[], description="Equity curve data points")
    drawdown_chart: List[Dict[str, Any]] = Field(default=[], description="Drawdown chart data points")
    monthly_heatmap: List[List[float]] = Field(default=[], description="Monthly returns heatmap data")
    returns_distribution: List[Dict[str, Any]] = Field(default=[], description="Returns distribution histogram")
    rolling_metrics_chart: List[Dict[str, Any]] = Field(default=[], description="Rolling metrics over time")
    
    # Export capabilities
    export_data: Optional[ExportData] = Field(default=None, description="Export data package")

# Additional utility models
class AnalyticsRequest(BaseModel):
    """Request for analytics calculation"""
    backtest_ids: List[str] = Field(..., description="List of backtest IDs to analyze")
    benchmark_symbol: Optional[str] = Field(default="BTC-USDT", description="Benchmark for comparison")
    comparison_type: ComparisonType = Field(default=ComparisonType.BENCHMARK, description="Type of analysis")
    include_rolling_metrics: bool = Field(default=True, description="Include rolling metrics")
    rolling_window_days: int = Field(default=30, description="Rolling window size in days")

class AnalyticsConfiguration(BaseModel):
    """Configuration for analytics calculation"""
    risk_free_rate: float = Field(default=0.02, description="Risk-free rate for calculations")
    confidence_levels: List[float] = Field(default=[0.95, 0.99], description="VaR confidence levels")
    benchmark_symbols: List[str] = Field(default=["BTC-USDT", "ETH-USDT"], description="Available benchmarks")
    export_formats: List[str] = Field(default=["CSV", "Excel", "PDF"], description="Supported export formats") 