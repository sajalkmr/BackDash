export interface OHLCVData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TechnicalIndicator {
  id: string;
  type: 'EMA' | 'RSI' | 'MACD';
  params: Record<string, number>;
}

export interface Condition {
  id: string;
  indicator: string;
  operator: '>' | '<' | '>=' | '<=' | '=' | '!=';
  value: number;
}

export interface Strategy {
  id: string;
  name: string;
  asset: string;
  entryConditions: Condition[];
  exitConditions: Condition[];
  riskManagement: {
    stopLoss: number;
    takeProfit: number;
    positionSize: number;
  };
  indicators: TechnicalIndicator[];
}

export interface Trade {
  id: string;
  entryPrice: number;
  exitPrice: number;
  entryTime: number;
  exitTime: number;
  quantity: number;
  pnl: number;
  pnlPercent: number;
  type: 'long' | 'short';
}

export interface StrategyBuilderProps {
  onStrategyStart: (strategyId: string) => void;
  onBacktestStart: (backtestId: string) => void;
}

export interface EquityChartProps {
  data?: Array<{
    timestamp: string;
    portfolio_value: number;
    total_return_pct: number;
  }>;
}

export interface PerformanceMetricsProps {
  data?: {
    total_return_pct: number;
    annual_return_pct: number;
    sharpe_ratio: number;
    sortino_ratio: number;
    calmar_ratio: number;
    volatility_annual: number;
    downside_deviation: number;
  };
}

export interface BenchmarkComparisonProps {
  data?: {
    strategy_return_pct: number;
    benchmark_return_pct: number;
    alpha: number;
    beta: number;
    correlation: number;
  };
}

export interface RiskVisualsProps {
  data?: {
    max_drawdown_pct: number;
    var95: number;
    cvar95: number;
    recovery_factor: number;
    time_underwater_pct: number;
  };
}

export interface TradesListProps {
  trades?: Array<{
    timestamp: string;
    type: 'buy' | 'sell';
    price: number;
    quantity: number;
    pnl?: number;
    return_pct?: number;
    duration_minutes?: number;
  }>;
}

export interface BacktestResult {
  trades: TradesListProps['trades'];
  metrics: {
    performance: PerformanceMetricsProps['data'];
    risk: RiskVisualsProps['data'];
    benchmark: BenchmarkComparisonProps['data'];
  };
  equity_curve: EquityChartProps['data'];
}