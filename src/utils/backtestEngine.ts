import { Strategy, BacktestResult, Trade, OHLCVData } from '../types';
import { calculateIndicator } from './technicalIndicators';

export function runBacktest(data: OHLCVData[], strategy: Strategy): BacktestResult {
  const trades: Trade[] = [];
  let inPosition = false;
  let entryPrice = 0;
  let entryTime = '';
  let cash = 100000;
  let equity = cash;
  let maxDrawdown = 0;
  let maxEquity = cash;
  let equityCurve: number[] = [cash];
  let drawdownCurve: number[] = [0];
  
  for (let i = 50; i < data.length; i++) {
    const currentBar = data[i];
    const previousBar = data[i - 1];
    
    const indicators = calculateIndicators(data.slice(0, i + 1), strategy);
    const entrySignal = evaluateConditions(strategy.entryConditions, indicators, currentBar);
    const exitSignal = evaluateConditions(strategy.exitConditions, indicators, currentBar);
    
    if (!inPosition && entrySignal) {
      inPosition = true;
      entryPrice = currentBar.close;
      entryTime = currentBar.timestamp;
      
      trades.push({
        type: 'buy',
        timestamp: currentBar.timestamp,
        price: currentBar.close,
        quantity: calculatePositionSize(cash, currentBar.close, strategy)
      });
      
      cash -= trades[trades.length - 1].quantity * currentBar.close;
    }
    else if (inPosition && exitSignal) {
      inPosition = false;
      const lastTrade = trades[trades.length - 1];
      
      trades.push({
        type: 'sell',
        timestamp: currentBar.timestamp,
        price: currentBar.close,
        quantity: lastTrade.quantity,
        pnl: (currentBar.close - entryPrice) * lastTrade.quantity,
        duration: calculateDuration(entryTime, currentBar.timestamp)
      });
      
      cash += lastTrade.quantity * currentBar.close;
    }
    
    equity = cash + (inPosition ? trades[trades.length - 1].quantity * currentBar.close : 0);
    equityCurve.push(equity);
    
    if (equity > maxEquity) {
      maxEquity = equity;
    }
    
    const drawdown = ((maxEquity - equity) / maxEquity) * 100;
    drawdownCurve.push(drawdown);
    
    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown;
    }
  }
  
  const metrics = calculateMetrics(trades, equityCurve, drawdownCurve);
  
  return {
    trades,
    metrics,
    equityCurve,
    drawdownCurve
  };
}

function calculateIndicators(data: OHLCVData[], strategy: Strategy) {
  const indicators: { [key: string]: number } = {};
  
  for (const indicator of strategy.indicators) {
    const result = calculateIndicator(data, indicator.type, indicator.period);
    indicators[`${indicator.type}_${indicator.period}`] = result[result.length - 1];
  }
  
  return indicators;
}

function evaluateConditions(conditions: any[], indicators: any, currentBar: OHLCVData): boolean {
  return conditions.every(condition => {
    const leftValue = resolveValue(condition.left, indicators, currentBar);
    const rightValue = resolveValue(condition.right, indicators, currentBar);
    
    switch (condition.operator) {
      case '>': return leftValue > rightValue;
      case '<': return leftValue < rightValue;
      case '>=': return leftValue >= rightValue;
      case '<=': return leftValue <= rightValue;
      case '=': return Math.abs(leftValue - rightValue) < 0.0001;
      default: return false;
    }
  });
}

function resolveValue(operand: any, indicators: any, currentBar: OHLCVData): number {
  if (typeof operand === 'number') return operand;
  if (typeof operand === 'string') {
    if (operand in indicators) return indicators[operand];
    if (operand in currentBar) return currentBar[operand];
    return parseFloat(operand);
  }
  return 0;
}

function calculatePositionSize(cash: number, price: number, strategy: Strategy): number {
  const riskAmount = cash * (strategy.riskManagement.positionSize / 100);
  return riskAmount / price;
}

function calculateDuration(entryTime: string, exitTime: string): number {
  return Math.round((new Date(exitTime).getTime() - new Date(entryTime).getTime()) / (1000 * 60));
}

function calculateMetrics(trades: Trade[], equityCurve: number[], drawdownCurve: number[]) {
  const winningTrades = trades.filter(t => t.type === 'sell' && t.pnl && t.pnl > 0);
  const losingTrades = trades.filter(t => t.type === 'sell' && t.pnl && t.pnl <= 0);
  
  const totalReturn = ((equityCurve[equityCurve.length - 1] - equityCurve[0]) / equityCurve[0]) * 100;
  const maxDrawdown = Math.max(...drawdownCurve);
  const winRate = (winningTrades.length / (winningTrades.length + losingTrades.length)) * 100;
  
  const avgWinPnl = winningTrades.reduce((sum, t) => sum + (t.pnl || 0), 0) / winningTrades.length;
  const avgLossPnl = losingTrades.reduce((sum, t) => sum + (t.pnl || 0), 0) / losingTrades.length;
  
  return {
    totalReturn,
    maxDrawdown,
    winRate,
    totalTrades: winningTrades.length + losingTrades.length,
    winningTrades: winningTrades.length,
    losingTrades: losingTrades.length,
    avgWinPnl,
    avgLossPnl,
    profitFactor: Math.abs(avgWinPnl / avgLossPnl)
  };
}