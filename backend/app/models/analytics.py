"""
Analytics Models - Advanced performance analysis and metrics
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class AnalyticsPeriod(str, Enum):
    """Analytics calculation periods"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ALL_TIME = "all_time"

class RiskMetrics(BaseModel):
    """Advanced risk analysis metrics"""
    # Value at Risk (VaR)
    var_95_daily: float = Field(..., description="95% Daily Value at Risk")
    var_99_daily: float = Field(..., description="99% Daily Value at Risk")
    cvar_95_daily: float = Field(..., description="95% Conditional Value at Risk")
    
    # Risk ratios
    information_ratio: float = Field(..., description="Information ratio")
    treynor_ratio: Optional[float] = Field(default=None, description="Treynor ratio")
    jensen_alpha: Optional[float] = Field(default=None, description="Jensen's alpha")
    
    # Volatility metrics
    realized_volatility: float = Field(..., description="Realized volatility")
    volatility_of_volatility: float = Field(..., description="Volatility of volatility")
    
    # Tail risk metrics
    skewness: float = Field(..., description="Return distribution skewness")
    kurtosis: float = Field(..., description="Return distribution kurtosis")
    tail_ratio: float = Field(..., description="Tail ratio (95th/5th percentile)")
    
    # Tracking metrics
    tracking_error: Optional[float] = Field(default=None, description="Tracking error vs benchmark")
    active_return: Optional[float] = Field(default=None, description="Active return vs benchmark")

class PerformanceAttribution(BaseModel):
    """Performance attribution analysis"""
    # Time-based attribution
    monthly_returns: List[Dict[str, float]] = Field(default=[], description="Monthly return breakdown")
    quarterly_returns: List[Dict[str, float]] = Field(default=[], description="Quarterly return breakdown")
    yearly_returns: List[Dict[str, float]] = Field(default=[], description="Yearly return breakdown")
    
    # Factor attribution (for future implementation)
    market_timing_effect: Optional[float] = Field(default=None, description="Market timing attribution")
    security_selection_effect: Optional[float] = Field(default=None, description="Security selection attribution")
    
    # Rolling metrics
    rolling_sharpe_30d: List[Dict[str, Any]] = Field(default=[], description="30-day rolling Sharpe ratio")
    rolling_volatility_30d: List[Dict[str, Any]] = Field(default=[], description="30-day rolling volatility")
    rolling_drawdown: List[Dict[str, Any]] = Field(default=[], description="Rolling drawdown analysis")

class TradeAnalysis(BaseModel):
    """Detailed trade analysis"""
    # Trade distribution
    trade_size_distribution: Dict[str, int] = Field(default={}, description="Trade size distribution")
    trade_duration_distribution: Dict[str, int] = Field(default={}, description="Trade duration distribution")
    hourly_trade_distribution: Dict[str, int] = Field(default={}, description="Hourly trade distribution")
    daily_trade_distribution: Dict[str, int] = Field(default={}, description="Daily trade distribution")
    
    # Performance by characteristics
    performance_by_hour: Dict[str, float] = Field(default={}, description="Performance by hour of day")
    performance_by_day: Dict[str, float] = Field(default={}, description="Performance by day of week")
    performance_by_month: Dict[str, float] = Field(default={}, description="Performance by month")
    
    # Trade streaks
    win_streak_analysis: Dict[str, Any] = Field(default={}, description="Winning streak analysis")
    loss_streak_analysis: Dict[str, Any] = Field(default={}, description="Losing streak analysis")
    
    # Risk per trade
    avg_risk_per_trade: float = Field(default=0, description="Average risk per trade")
    max_risk_per_trade: float = Field(default=0, description="Maximum risk per trade")
    risk_adjusted_returns: float = Field(default=0, description="Risk-adjusted returns")

class BenchmarkComparison(BaseModel):
    """Benchmark comparison analysis"""
    benchmark_symbol: str = Field(..., description="Benchmark symbol")
    benchmark_return: float = Field(..., description="Benchmark total return")
    strategy_return: float = Field(..., description="Strategy total return")
    excess_return: float = Field(..., description="Excess return vs benchmark")
    
    # Regression analysis
    alpha: float = Field(..., description="Alpha (intercept)")
    beta: float = Field(..., description="Beta (slope)")
    r_squared: float = Field(..., description="R-squared")
    correlation: float = Field(..., description="Correlation coefficient")
    
    # Up/Down capture ratios
    up_capture_ratio: float = Field(..., description="Up market capture ratio")
    down_capture_ratio: float = Field(..., description="Down market capture ratio")
    
    # Performance periods
    outperformance_periods: int = Field(..., description="Number of periods outperforming")
    underperformance_periods: int = Field(..., description="Number of periods underperforming")
    outperformance_percentage: float = Field(..., description="Percentage of periods outperforming")

class MonteCarloAnalysis(BaseModel):
    """Monte Carlo simulation results"""
    simulations_count: int = Field(..., description="Number of simulations run")
    confidence_intervals: Dict[str, Dict[str, float]] = Field(..., description="Confidence intervals for key metrics")
    
    # Probability distributions
    prob_positive_return: float = Field(..., description="Probability of positive return")
    prob_target_return: Optional[float] = Field(default=None, description="Probability of achieving target return")
    prob_max_drawdown: Dict[str, float] = Field(default={}, description="Probability of various drawdown levels")
    
    # Percentile analysis
    return_percentiles: Dict[str, float] = Field(..., description="Return percentiles (5th, 25th, 50th, 75th, 95th)")
    drawdown_percentiles: Dict[str, float] = Field(..., description="Drawdown percentiles")
    
    # Scenario analysis
    best_case_scenario: Dict[str, float] = Field(..., description="Best case scenario metrics")
    worst_case_scenario: Dict[str, float] = Field(..., description="Worst case scenario metrics")
    median_scenario: Dict[str, float] = Field(..., description="Median scenario metrics")

class AnalyticsReport(BaseModel):
    """Comprehensive analytics report"""
    # Report metadata
    report_id: str = Field(..., description="Unique report identifier")
    backtest_id: str = Field(..., description="Associated backtest ID")
    generated_at: datetime = Field(default_factory=datetime.now, description="Report generation timestamp")
    period: AnalyticsPeriod = Field(..., description="Analysis period")
    
    # Core analytics
    risk_metrics: RiskMetrics = Field(..., description="Advanced risk metrics")
    performance_attribution: PerformanceAttribution = Field(..., description="Performance attribution analysis")
    trade_analysis: TradeAnalysis = Field(..., description="Detailed trade analysis")
    
    # Optional advanced analysis
    benchmark_comparison: Optional[BenchmarkComparison] = Field(default=None, description="Benchmark comparison")
    monte_carlo_analysis: Optional[MonteCarloAnalysis] = Field(default=None, description="Monte Carlo simulation results")
    
    # Custom metrics
    custom_metrics: Dict[str, Any] = Field(default={}, description="Custom user-defined metrics")
    
    # Export settings
    include_charts: bool = Field(default=True, description="Include chart data")
    chart_data: Optional[Dict[str, Any]] = Field(default=None, description="Chart data for visualization")
    
    class Config:
        schema_extra = {
            "example": {
                "report_id": "rpt_001",
                "backtest_id": "bt_001",
                "period": "quarterly",
                "risk_metrics": {
                    "var_95_daily": -0.025,
                    "var_99_daily": -0.045,
                    "information_ratio": 1.2,
                    "realized_volatility": 0.35,
                    "skewness": -0.15,
                    "kurtosis": 3.2
                },
                "trade_analysis": {
                    "avg_risk_per_trade": 1500,
                    "max_risk_per_trade": 5000,
                    "risk_adjusted_returns": 0.85
                },
                "include_charts": True
            }
        } 