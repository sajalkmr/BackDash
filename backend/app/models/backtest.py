"""
Backtest Models - Define request/response structures for backtesting operations
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

from .strategy import Strategy

class BacktestStatus(str, Enum):
    """Backtest execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TradeAction(str, Enum):
    """Trade action types"""
    BUY = "buy"
    SELL = "sell"
    SHORT = "short"
    COVER = "cover"

class BacktestRequest(BaseModel):
    """Backtest execution request"""
    strategy: Strategy = Field(..., description="Strategy configuration")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(default=100000, gt=0, description="Initial capital")
    timeframe: str = Field(default="1h", description="Data timeframe (1m, 5m, 15m, 1h, 4h, 1d)")
    include_weekends: bool = Field(default=True, description="Include weekend data")
    benchmark_symbol: Optional[str] = Field(default=None, description="Benchmark for comparison")
    enable_real_time_updates: bool = Field(default=False, description="Enable WebSocket updates")
    save_trades: bool = Field(default=True, description="Save individual trade records")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        start_date = values.get('start_date')
        if start_date and v <= start_date:
            raise ValueError('End date must be after start date')
        return v

class TradeResult(BaseModel):
    """Individual trade result"""
    trade_id: str = Field(..., description="Unique trade identifier")
    symbol: str = Field(..., description="Trading symbol")
    action: TradeAction = Field(..., description="Trade action")
    entry_time: datetime = Field(..., description="Trade entry timestamp")
    exit_time: Optional[datetime] = Field(default=None, description="Trade exit timestamp")
    entry_price: float = Field(..., gt=0, description="Entry price")
    exit_price: Optional[float] = Field(default=None, description="Exit price")
    quantity: float = Field(..., gt=0, description="Trade quantity")
    gross_pnl: Optional[float] = Field(default=None, description="Gross profit/loss")
    net_pnl: Optional[float] = Field(default=None, description="Net profit/loss after fees")
    commission: float = Field(default=0, description="Commission paid")
    slippage: float = Field(default=0, description="Slippage cost")
    duration_minutes: Optional[int] = Field(default=None, description="Trade duration in minutes")
    return_pct: Optional[float] = Field(default=None, description="Return percentage")
    mae_pct: Optional[float] = Field(default=None, description="Maximum Adverse Excursion %")
    mfe_pct: Optional[float] = Field(default=None, description="Maximum Favorable Excursion %")
    risk_amount: Optional[float] = Field(default=None, description="Risk amount (stop loss)")
    reward_amount: Optional[float] = Field(default=None, description="Reward amount (take profit)")
    r_multiple: Optional[float] = Field(default=None, description="R-multiple (reward/risk ratio)")

class PerformanceMetrics(BaseModel):
    """Core performance metrics"""
    total_return_pct: float = Field(..., description="Total return percentage")
    annual_return_pct: float = Field(..., description="Annualized return percentage")
    monthly_return_pct: float = Field(..., description="Monthly return percentage")
    daily_return_pct: float = Field(..., description="Daily return percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    calmar_ratio: float = Field(..., description="Calmar ratio")
    omega_ratio: Optional[float] = Field(default=None, description="Omega ratio")
    volatility_annual: float = Field(..., description="Annual volatility")
    downside_deviation: float = Field(..., description="Downside deviation")
    alpha: Optional[float] = Field(default=None, description="Alpha vs benchmark")
    beta: Optional[float] = Field(default=None, description="Beta vs benchmark")
    correlation: Optional[float] = Field(default=None, description="Correlation with benchmark")

class DrawdownMetrics(BaseModel):
    """Drawdown analysis metrics"""
    max_drawdown_pct: float = Field(..., description="Maximum drawdown percentage")
    max_drawdown_duration_days: int = Field(..., description="Maximum drawdown duration in days")
    avg_drawdown_pct: float = Field(..., description="Average drawdown percentage")
    avg_drawdown_duration_days: float = Field(..., description="Average drawdown duration in days")
    drawdown_periods: int = Field(..., description="Number of drawdown periods")
    recovery_factor: float = Field(..., description="Recovery factor")
    time_underwater_pct: float = Field(..., description="Percentage of time underwater")
    max_time_to_recovery_days: int = Field(..., description="Maximum time to recovery in days")

class TradingMetrics(BaseModel):
    """Trading-specific metrics"""
    total_trades: int = Field(..., description="Total number of trades")
    winning_trades: int = Field(..., description="Number of winning trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    win_rate_pct: float = Field(..., description="Win rate percentage")
    profit_factor: float = Field(..., description="Profit factor (gross profit / gross loss)")
    avg_trade_return_pct: float = Field(..., description="Average trade return percentage")
    avg_win_return_pct: float = Field(..., description="Average winning trade return percentage")
    avg_loss_return_pct: float = Field(..., description="Average losing trade return percentage")
    avg_trade_duration_hours: float = Field(..., description="Average trade duration in hours")
    avg_win_duration_hours: float = Field(..., description="Average winning trade duration in hours")
    avg_loss_duration_hours: float = Field(..., description="Average losing trade duration in hours")
    best_trade_return_pct: float = Field(..., description="Best trade return percentage")
    worst_trade_return_pct: float = Field(..., description="Worst trade return percentage")
    max_consecutive_wins: int = Field(..., description="Maximum consecutive wins")
    max_consecutive_losses: int = Field(..., description="Maximum consecutive losses")

class BacktestResult(BaseModel):
    """Complete backtest result"""
    backtest_id: str = Field(..., description="Unique backtest identifier")
    strategy_name: str = Field(..., description="Strategy name")
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Data timeframe")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    duration_days: int = Field(..., description="Backtest duration in days")
    initial_capital: float = Field(..., description="Initial capital")
    final_capital: float = Field(..., description="Final capital")
    total_pnl: float = Field(..., description="Total profit/loss")
    performance_metrics: PerformanceMetrics = Field(..., description="Core performance metrics")
    drawdown_metrics: DrawdownMetrics = Field(..., description="Drawdown analysis")
    trading_metrics: TradingMetrics = Field(..., description="Trading-specific metrics")
    trades: List[TradeResult] = Field(default=[], description="Individual trade records")
    status: BacktestStatus = Field(..., description="Backtest status")
    execution_time_seconds: float = Field(..., description="Execution time in seconds")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    equity_curve: List[Dict[str, Any]] = Field(default=[], description="Equity curve data points")
    drawdown_curve: List[Dict[str, Any]] = Field(default=[], description="Drawdown curve data points")
    benchmark_data: Optional[List[Dict[str, Any]]] = Field(default=None, description="Benchmark comparison data")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    warnings: List[str] = Field(default=[], description="Warning messages") 