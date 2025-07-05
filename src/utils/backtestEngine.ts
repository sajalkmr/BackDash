import { OHLCVData, Strategy, Trade, BacktestResult, Condition } from '../types';
import { getIndicatorValue } from './technicalIndicators';

export function runBacktest(data: OHLCVData[], strategy: Strategy): BacktestResult {
  const trades: Trade[] = [];
  let currentPosition: 'none' | 'long' | 'short' = 'none';
  let entryPrice = 0;
  let entryTime = 0;
  let positionSize = strategy.riskManagement.positionSize;
  let portfolioValue = 10000;
  const equity: number[] = [portfolioValue];
  const returns: number[] = [];
  
  const stopLossMultiplier = 1 - (strategy.riskManagement.stopLoss / 100);
  const takeProfitMultiplier = 1 + (strategy.riskManagement.takeProfit / 100);
  
  const startIndex = Math.max(50, Math.floor(data.length * 0.1));
  
  const maxEquitySize = data.length - startIndex + 1;
  equity.length = maxEquitySize;
  let equityIndex = 1;
  
  for (let i = startIndex; i < data.length; i++) {
    const currentData = data[i];
    const currentPrice = currentData?.close;
    
    if (!currentPrice) continue;
    
    if (currentPosition !== 'none') {
      const shouldExit = checkConditions(data, strategy.exitConditions, i);
      
      let exitTriggered = shouldExit;
      
      if (currentPosition === 'long') {
        if (currentPrice <= entryPrice * stopLossMultiplier || 
            currentPrice >= entryPrice * takeProfitMultiplier) {
          exitTriggered = true;
        }
      }
      
      if (exitTriggered) {
        const pnl = currentPosition === 'long' 
          ? (currentPrice - entryPrice) * positionSize
          : (entryPrice - currentPrice) * positionSize;
        
        const pnlPercent = (pnl / (entryPrice * positionSize)) * 100;
        
        trades.push({
          id: `trade_${trades.length + 1}`,
          entryPrice,
          exitPrice: currentPrice,
          entryTime,
          exitTime: currentData!.timestamp,
          quantity: positionSize,
          pnl,
          pnlPercent,
          type: currentPosition
        });
        
        portfolioValue += pnl;
        returns.push(pnlPercent);
        currentPosition = 'none';
      }
    }
    
    if (currentPosition === 'none') {
      const shouldEnter = checkConditions(data, strategy.entryConditions, i);
      
      if (shouldEnter) {
        currentPosition = 'long';
        entryPrice = currentPrice;
        entryTime = currentData!.timestamp;
        positionSize = Math.floor(portfolioValue * 0.95 / currentPrice);
      }
    }
    
    equity[equityIndex++] = portfolioValue;
  }
  
  equity.length = equityIndex;
  
  const metrics = calculateMetrics(trades, returns, equity);
  const drawdown = calculateDrawdown(equity);
  
  const benchmark = data.length > startIndex ? 
    data.slice(startIndex).map(d => (d.close / data[startIndex]!.close) * portfolioValue) :
    [];

  return {
    trades,
    metrics: metrics as BacktestResult['metrics'],
    equity,
    drawdown,
    benchmark
  };
}

function checkConditions(data: OHLCVData[], conditions: Condition[], index: number): boolean {
  return conditions.every(condition => {
    const indicatorValue = getIndicatorValue(data, condition.indicator, index);
    
    switch (condition.operator) {
      case '>':
        return indicatorValue > condition.value;
      case '<':
        return indicatorValue < condition.value;
      case '>=':
        return indicatorValue >= condition.value;
      case '<=':
        return indicatorValue <= condition.value;
      case '=':
        return Math.abs(indicatorValue - condition.value) < 0.01;
      case '!=':
        return Math.abs(indicatorValue - condition.value) >= 0.01;
      default:
        return false;
    }
  });
}

function calculateMetrics(trades: Trade[], returns: number[], equity: number[]) {
  const totalTrades = trades.length;
  
  if (totalTrades === 0) {
    return {
      totalPnL: 0,
      totalPnLPercent: 0,
      cagr: 0,
      sharpe: 0,
      sortino: 0,
      calmar: 0,
      maxDrawdown: 0,
      maxDrawdownPercent: 0,
      volatility: 0,
      tradeCount: 0,
      winRate: 0,
      avgTradeDuration: 0,
      largestWin: 0,
      largestLoss: 0,
      turnover: 0,
      var95: 0,
      leverage: 0,
      beta: 1.0
    };
  }
  
  const winningTrades = trades.filter(t => t.pnl > 0);
  const losingTrades = trades.filter(t => t.pnl < 0);
  
  const totalPnL = trades.reduce((sum, t) => sum + t.pnl, 0);
  const totalPnLPercent = (totalPnL / 10000) * 100;
  
  const avgReturn = returns.length > 0 ? returns.reduce((sum, r) => sum + r, 0) / returns.length : 0;
  const returnVariance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length;
  const returnStd = Math.sqrt(returnVariance);
  
  const sharpe = returnStd > 0 ? (avgReturn / returnStd) * Math.sqrt(252) : 0;
  
  const downside = returns.filter(r => r < 0);
  const downsideVariance = downside.length > 0 ? 
    downside.reduce((sum, r) => sum + Math.pow(r, 2), 0) / downside.length : 0;
  const downsideStd = Math.sqrt(downsideVariance);
  const sortino = downsideStd > 0 ? (avgReturn / downsideStd) * Math.sqrt(252) : 0;
  
  const maxEquity = Math.max(...equity);
  const maxEquityIndex = equity.indexOf(maxEquity);
  const minEquityAfterMax = Math.min(...equity.slice(maxEquityIndex));
  const maxDrawdown = maxEquity - minEquityAfterMax;
  const maxDrawdownPercent = (maxDrawdown / maxEquity) * 100;
  
  const timePeriod = equity.length > 1 ? (equity.length - 1) / 252 : 1;
  const cagr = timePeriod > 0 ? Math.pow(equity[equity.length - 1]! / equity[0]!, 1 / timePeriod) - 1 : 0;
  const calmar = maxDrawdownPercent > 0 ? cagr * 100 / maxDrawdownPercent : 0;
  
  return {
    totalPnL,
    totalPnLPercent,
    cagr: cagr * 100,
    sharpe,
    sortino,
    calmar,
    maxDrawdown,
    maxDrawdownPercent,
    volatility: returnStd * Math.sqrt(252),
    tradeCount: totalTrades,
    winRate: (winningTrades.length / totalTrades) * 100,
    avgTradeDuration: trades.reduce((sum, t) => sum + (t.exitTime - t.entryTime), 0) / totalTrades / (1000 * 60 * 60 * 24),
    largestWin: winningTrades.length > 0 ? Math.max(...winningTrades.map(t => t.pnlPercent)) : 0,
    largestLoss: losingTrades.length > 0 ? Math.min(...losingTrades.map(t => t.pnlPercent)) : 0,
    turnover: 100,
    var95: returns.length > 0 ? returns.sort((a, b) => a - b)[Math.floor(returns.length * 0.05)] : 0,
    leverage: 95,
    beta: 1.0
  };
}

function calculateDrawdown(equity: number[]): number[] {
  const drawdown: number[] = [];
  let peak = equity[0];
  
  for (const value of equity) {
    if (value! > peak!) {
      peak = value!;
    }
    drawdown.push(((peak! - value!) / peak!) * 100);
  }
  
  return drawdown;
}