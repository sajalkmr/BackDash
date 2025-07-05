import React from 'react';
import { BacktestResult } from '../types';
import { TrendingUp, TrendingDown, DollarSign, Percent, Clock, Target } from 'lucide-react';

interface PerformanceMetricsProps {
  result: BacktestResult | null;
}

export function PerformanceMetrics({ result }: PerformanceMetricsProps) {
  if (!result) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Performance Metrics</h2>
        <div className="text-slate-400 text-center py-8">
          Run a backtest to see performance metrics
        </div>
      </div>
    );
  }

  const { metrics } = result;

  const formatNumber = (num: number, decimals: number = 2) => {
    return num.toFixed(decimals);
  };

  const formatPercent = (num: number) => {
    return `${formatNumber(num)}%`;
  };

  const formatCurrency = (num: number) => {
    return `$${formatNumber(num)}`;
  };

  const MetricCard = ({ 
    title, 
    value, 
    icon: Icon, 
    color = 'text-blue-400',
    bgColor = 'bg-blue-500/10'
  }: {
    title: string;
    value: string;
    icon: any;
    color?: string;
    bgColor?: string;
  }) => (
    <div className={`${bgColor} p-4 rounded-lg border border-slate-600`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-slate-400 text-sm font-medium">{title}</p>
          <p className={`text-lg font-bold ${color}`}>{value}</p>
        </div>
        <Icon className={`w-6 h-6 ${color}`} />
      </div>
    </div>
  );

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-6">Performance Metrics</h2>
      
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard
          title="Total P&L"
          value={formatCurrency(metrics.totalPnL)}
          icon={DollarSign}
          color={metrics.totalPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}
          bgColor={metrics.totalPnL >= 0 ? 'bg-emerald-500/10' : 'bg-red-500/10'}
        />
        <MetricCard
          title="Total Return"
          value={formatPercent(metrics.totalPnLPercent)}
          icon={Percent}
          color={metrics.totalPnLPercent >= 0 ? 'text-emerald-400' : 'text-red-400'}
          bgColor={metrics.totalPnLPercent >= 0 ? 'bg-emerald-500/10' : 'bg-red-500/10'}
        />
        <MetricCard
          title="CAGR"
          value={formatPercent(metrics.cagr)}
          icon={TrendingUp}
          color="text-blue-400"
          bgColor="bg-blue-500/10"
        />
        <MetricCard
          title="Max Drawdown"
          value={formatPercent(metrics.maxDrawdownPercent)}
          icon={TrendingDown}
          color="text-red-400"
          bgColor="bg-red-500/10"
        />
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Risk Metrics */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">Risk Metrics</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-400">Sharpe Ratio</span>
              <span className="text-white font-medium">{formatNumber(metrics.sharpe)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Sortino Ratio</span>
              <span className="text-white font-medium">{formatNumber(metrics.sortino)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Calmar Ratio</span>
              <span className="text-white font-medium">{formatNumber(metrics.calmar)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Volatility</span>
              <span className="text-white font-medium">{formatPercent(metrics.volatility)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">VaR (95%)</span>
              <span className="text-white font-medium">{formatPercent(metrics.var95)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Beta</span>
              <span className="text-white font-medium">{formatNumber(metrics.beta)}</span>
            </div>
          </div>
        </div>

        {/* Trading Metrics */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">Trading Metrics</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-400">Total Trades</span>
              <span className="text-white font-medium">{metrics.tradeCount}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Win Rate</span>
              <span className="text-white font-medium">{formatPercent(metrics.winRate)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Avg Trade Duration</span>
              <span className="text-white font-medium">{formatNumber(metrics.avgTradeDuration)} days</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Largest Win</span>
              <span className="text-emerald-400 font-medium">{formatPercent(metrics.largestWin)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Largest Loss</span>
              <span className="text-red-400 font-medium">{formatPercent(metrics.largestLoss)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Turnover</span>
              <span className="text-white font-medium">{formatPercent(metrics.turnover)}</span>
            </div>
          </div>
        </div>

        {/* Additional Metrics */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">Additional Metrics</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-400">Max Drawdown ($)</span>
              <span className="text-red-400 font-medium">{formatCurrency(metrics.maxDrawdown)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Leverage</span>
              <span className="text-white font-medium">{formatPercent(metrics.leverage)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}