// Data Structures
export interface OHLCVData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
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

// Strategy Definition
export interface Condition {
  id: string;
  indicator: string;
  operator: string;
  value: number;
}

export interface RiskManagement {
  stopLoss: number;
  takeProfit: number;
  positionSize: number;
}

export interface Strategy {
  name: string;
  asset: string;
  entryConditions: Condition[];
  exitConditions: Condition[];
  riskManagement: RiskManagement;
}

// Backtest Results
export interface BacktestMetrics {
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
}

export interface BacktestResult {
  trades: Trade[];
  metrics: BacktestMetrics;
  equity: number[];
  drawdown: number[];
  benchmark: number[];
}

// Constants
export const AVAILABLE_INDICATORS = ['EMA (20)', 'RSI (14)', 'MACD (12, 26, 9)', 'Bollinger Bands (20, 2)'];
export const AVAILABLE_OPERATORS = ['>', '<', '=', '>=', '<='];
export const AVAILABLE_ASSETS = [
  'AAPL', 'AXP', 'BA', 'CAT', 'CSCO', 'CVX', 'DIS', 'DWDP', 'GE', 'GS',
  'HD', 'IBM', 'INTC', 'JNJ', 'JPM', 'KO', 'MCD', 'MMM', 'MRK', 'MSFT',
  'NKE', 'PFE', 'PG', 'TRV', 'UNH', 'UTX', 'V', 'VZ', 'WMT', 'XOM'
]; 