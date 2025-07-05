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

export interface BacktestResult {
  trades: Trade[];
  metrics: {
    totalPnL: number;
    totalPnLPercent: number;
    cagr: number;
    sharpe: number;
    sortino: number;
    calmar: number;
    maxDrawdown: number;
    maxDrawdownPercent: number;
    volatility: number;
    tradeCount: number;
    winRate: number;
    avgTradeDuration: number;
    largestWin: number;
    largestLoss: number;
    turnover: number;
    var95: number;
    leverage: number;
    beta: number;
  };
  equity: number[];
  drawdown: number[];
  benchmark: number[];
}