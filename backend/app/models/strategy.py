"""
Strategy Models - Define the structure for trading strategies
Enhanced with comprehensive validation and examples
"""

from typing import Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime

class AssetSelection(BaseModel):
    """Asset and market selection configuration"""
    symbol: str = Field(..., description="Trading symbol (e.g., BTC-USDT)")
    exchange: str = Field(..., description="Exchange name")
    market_type: Literal["spot", "perp", "futures", "options"] = Field(..., description="Market type")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Symbol must be at least 3 characters')
        return v.upper()

class IndicatorConfig(BaseModel):
    """Technical indicator configuration"""
    type: Literal["ema", "sma", "rsi", "macd", "bb", "atr", "stoch", "obv", "vwap"] = Field(..., description="Indicator type")
    period: int = Field(..., gt=0, le=500, description="Indicator period")
    source: Literal["open", "high", "low", "close", "volume", "hl2", "hlc3", "ohlc4"] = Field(default="close", description="Price source")
    
    # MACD specific parameters
    fast_period: Optional[int] = Field(default=12, description="MACD fast period")
    slow_period: Optional[int] = Field(default=26, description="MACD slow period")
    signal_period: Optional[int] = Field(default=9, description="MACD signal period")
    
    # Bollinger Bands specific parameters
    std_dev: Optional[float] = Field(default=2.0, description="Bollinger Bands standard deviation")
    
    # Stochastic specific parameters
    k_period: Optional[int] = Field(default=14, description="Stochastic %K period")
    d_period: Optional[int] = Field(default=3, description="Stochastic %D period")
    
    @validator('period')
    def validate_period(cls, v):
        if v <= 0:
            raise ValueError('Period must be positive')
        return v

class LogicalCondition(BaseModel):
    """Individual logical condition"""
    left_operand: str = Field(..., description="Left operand (indicator name or value)")
    operator: Literal[">", "<", ">=", "<=", "=", "!=", "crosses_above", "crosses_below"] = Field(..., description="Comparison operator")
    right_operand: Union[str, float] = Field(..., description="Right operand (indicator name or value)")
    
    @validator('left_operand', 'right_operand')
    def validate_operands(cls, v):
        if isinstance(v, str) and not v.strip():
            raise ValueError('String operands cannot be empty')
        return v

class LogicalExpression(BaseModel):
    """Complex logical expression with operators"""
    conditions: List[LogicalCondition] = Field(..., min_items=1, description="List of conditions")
    operators: List[Literal["AND", "OR", "NOT"]] = Field(default=[], description="Logical operators between conditions")
    
    @validator('operators')
    def validate_operators(cls, v, values):
        conditions = values.get('conditions', [])
        if len(conditions) > 1 and len(v) != len(conditions) - 1:
            raise ValueError('Number of operators must be one less than number of conditions')
        return v

class SignalGeneration(BaseModel):
    """Signal generation configuration"""
    indicators: List[IndicatorConfig] = Field(..., min_items=1, description="Technical indicators to calculate")
    entry_conditions: LogicalExpression = Field(..., description="Entry signal conditions")
    exit_conditions: LogicalExpression = Field(..., description="Exit signal conditions")
    
    # Optional signal confirmation settings
    confirmation_bars: int = Field(default=1, ge=1, le=10, description="Number of bars to confirm signal")
    allow_multiple_entries: bool = Field(default=False, description="Allow multiple entries in same direction")

class ExecutionParameters(BaseModel):
    """Order execution parameters"""
    order_type: Literal["market", "limit", "stop_market", "stop_limit"] = Field(default="market", description="Order type")
    quantity_type: Literal["fixed", "percentage", "risk_based"] = Field(default="percentage", description="Quantity calculation type")
    quantity_value: float = Field(..., gt=0, description="Quantity value (fixed amount or percentage)")
    
    # Advanced execution settings
    fees_bps: float = Field(default=10, ge=0, le=1000, description="Trading fees in basis points")
    slippage_bps: float = Field(default=5, ge=0, le=1000, description="Slippage in basis points")
    max_spread_bps: Optional[float] = Field(default=None, ge=0, description="Maximum allowed spread in basis points")
    
    # Limit order specific
    limit_offset_bps: Optional[float] = Field(default=None, description="Limit order offset in basis points")
    order_timeout_minutes: int = Field(default=60, gt=0, description="Order timeout in minutes")

class RiskManagement(BaseModel):
    """Risk management configuration"""
    # Position-level risk
    stop_loss_pct: Optional[float] = Field(default=None, ge=0, le=100, description="Stop loss percentage")
    take_profit_pct: Optional[float] = Field(default=None, ge=0, description="Take profit percentage")
    trailing_stop_pct: Optional[float] = Field(default=None, ge=0, le=100, description="Trailing stop percentage")
    
    # Portfolio-level risk
    max_position_size_pct: float = Field(default=100, gt=0, le=100, description="Maximum position size as % of portfolio")
    max_daily_loss_pct: Optional[float] = Field(default=None, ge=0, le=100, description="Maximum daily loss percentage")
    max_drawdown_pct: Optional[float] = Field(default=None, ge=0, le=100, description="Maximum drawdown percentage")
    
    # Advanced risk controls
    correlation_limit: Optional[float] = Field(default=None, ge=0, le=1, description="Maximum correlation with existing positions")
    volatility_filter: Optional[float] = Field(default=None, ge=0, description="Minimum volatility threshold")
    
    @validator('stop_loss_pct', 'take_profit_pct', 'trailing_stop_pct')
    def validate_percentages(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Percentage values must be between 0 and 100')
        return v

class BacktestSettings(BaseModel):
    """Backtesting specific settings"""
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(default=100000, gt=0, description="Initial capital for backtest")
    benchmark_symbol: Optional[str] = Field(default=None, description="Benchmark symbol for comparison")
    commission_type: Literal["fixed", "percentage"] = Field(default="percentage", description="Commission calculation type")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        start_date = values.get('start_date')
        if start_date and v <= start_date:
            raise ValueError('End date must be after start date')
        return v

class Strategy(BaseModel):
    """Complete strategy definition"""
    # Basic information
    name: str = Field(..., min_length=1, max_length=100, description="Strategy name")
    description: Optional[str] = Field(default="", max_length=1000, description="Strategy description")
    version: str = Field(default="1.0.0", description="Strategy version")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    # Strategy components
    asset_selection: AssetSelection = Field(..., description="Asset and market selection")
    signal_generation: SignalGeneration = Field(..., description="Signal generation rules")
    execution_parameters: ExecutionParameters = Field(..., description="Execution parameters")
    risk_management: RiskManagement = Field(..., description="Risk management rules")
    backtest_settings: Optional[BacktestSettings] = Field(default=None, description="Backtesting settings")
    
    # Metadata
    tags: List[str] = Field(default=[], description="Strategy tags for categorization")
    is_active: bool = Field(default=True, description="Whether strategy is active")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Enhanced EMA Crossover Strategy",
                "description": "EMA crossover with RSI filter and advanced risk management",
                "version": "1.0.0",
                "asset_selection": {
                    "symbol": "BTC-USDT",
                    "exchange": "binance",
                    "market_type": "spot"
                },
                "signal_generation": {
                    "indicators": [
                        {"type": "ema", "period": 20, "source": "close"},
                        {"type": "ema", "period": 50, "source": "close"},
                        {"type": "rsi", "period": 14, "source": "close"}
                    ],
                    "entry_conditions": {
                        "conditions": [
                            {"left_operand": "ema_20", "operator": "crosses_above", "right_operand": "ema_50"},
                            {"left_operand": "rsi_14", "operator": ">", "right_operand": 30},
                            {"left_operand": "rsi_14", "operator": "<", "right_operand": 70}
                        ],
                        "operators": ["AND", "AND"]
                    },
                    "exit_conditions": {
                        "conditions": [
                            {"left_operand": "ema_20", "operator": "crosses_below", "right_operand": "ema_50"}
                        ],
                        "operators": []
                    },
                    "confirmation_bars": 2,
                    "allow_multiple_entries": False
                },
                "execution_parameters": {
                    "order_type": "market",
                    "quantity_type": "percentage",
                    "quantity_value": 10,
                    "fees_bps": 10,
                    "slippage_bps": 5,
                    "order_timeout_minutes": 30
                },
                "risk_management": {
                    "stop_loss_pct": 3,
                    "take_profit_pct": 9,
                    "trailing_stop_pct": 2,
                    "max_position_size_pct": 25,
                    "max_daily_loss_pct": 5,
                    "volatility_filter": 0.5
                },
                "tags": ["momentum", "trend_following", "crypto"],
                "is_active": True
            }
        } 