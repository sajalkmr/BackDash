import React from 'react';
import { BacktestResult, Trade } from '../types';
import { TrendingUp, TrendingDown, Clock, DollarSign } from 'lucide-react';

interface TradesListProps {
  result: BacktestResult | null;
}

export function TradesList({ result }: TradesListProps) {
  if (!result || result.trades.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Trades</h2>
        <div className="text-slate-400 text-center py-8">
          {result ? 'No trades executed' : 'Run a backtest to see trades'}
        </div>
      </div>
    );
  }

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString();
  };

  const formatDuration = (entryTime: number, exitTime: number) => {
    const duration = (exitTime - entryTime) / (1000 * 60 * 60 * 24);
    return `${duration.toFixed(1)} days`;
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white">Trade History</h2>
        <div className="text-sm text-slate-400">
          {result.trades.length} trades executed
        </div>
      </div>

      <div className="overflow-y-auto h-[400px] relative border border-slate-700 rounded-lg scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-800">
            <tr className="border-b border-slate-700">
              <th className="text-left py-3 px-2 text-slate-400 font-medium">Entry Date</th>
              <th className="text-left py-3 px-2 text-slate-400 font-medium">Exit Date</th>
              <th className="text-right py-3 px-2 text-slate-400 font-medium">Entry Price</th>
              <th className="text-right py-3 px-2 text-slate-400 font-medium">Exit Price</th>
              <th className="text-right py-3 px-2 text-slate-400 font-medium">Quantity</th>
              <th className="text-right py-3 px-2 text-slate-400 font-medium">Duration</th>
              <th className="text-right py-3 px-2 text-slate-400 font-medium">P&L ($)</th>
              <th className="text-right py-3 px-2 text-slate-400 font-medium">P&L (%)</th>
            </tr>
          </thead>
          <tbody>
            {result.trades.map((trade, index) => (
              <tr 
                key={trade.id} 
                className={`border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors duration-200 ${
                  index % 2 === 0 ? 'bg-slate-800' : 'bg-slate-800/50'
                }`}
              >
                <td className="py-3 px-2 text-white">
                  {formatDate(trade.entryTime)}
                </td>
                <td className="py-3 px-2 text-white">
                  {formatDate(trade.exitTime)}
                </td>
                <td className="py-3 px-2 text-right text-white">
                  ${trade.entryPrice.toFixed(2)}
                </td>
                <td className="py-3 px-2 text-right text-white">
                  ${trade.exitPrice.toFixed(2)}
                </td>
                <td className="py-3 px-2 text-right text-white">
                  {trade.quantity}
                </td>
                <td className="py-3 px-2 text-right text-slate-400">
                  {formatDuration(trade.entryTime, trade.exitTime)}
                </td>
                <td className={`py-3 px-2 text-right font-medium ${
                  trade.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'
                }`}>
                  ${trade.pnl.toFixed(2)}
                </td>
                <td className={`py-3 px-2 text-right font-medium ${
                  trade.pnlPercent >= 0 ? 'text-emerald-400' : 'text-red-400'
                }`}>
                  {trade.pnlPercent.toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Trade Summary */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-700/30 p-4 rounded-lg">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
            <span className="text-slate-400">Winning Trades</span>
          </div>
          <div className="text-xl font-bold text-emerald-400 mt-1">
            {result.trades.filter(t => t.pnl > 0).length}
          </div>
        </div>

        <div className="bg-slate-700/30 p-4 rounded-lg">
          <div className="flex items-center space-x-2">
            <TrendingDown className="w-5 h-5 text-red-400" />
            <span className="text-slate-400">Losing Trades</span>
          </div>
          <div className="text-xl font-bold text-red-400 mt-1">
            {result.trades.filter(t => t.pnl < 0).length}
          </div>
        </div>

        <div className="bg-slate-700/30 p-4 rounded-lg">
          <div className="flex items-center space-x-2">
            <DollarSign className="w-5 h-5 text-blue-400" />
            <span className="text-slate-400">Avg P&L</span>
          </div>
          <div className="text-xl font-bold text-blue-400 mt-1">
            ${(result.trades.reduce((sum, t) => sum + t.pnl, 0) / result.trades.length).toFixed(2)}
          </div>
        </div>

        <div className="bg-slate-700/30 p-4 rounded-lg">
          <div className="flex items-center space-x-2">
            <Clock className="w-5 h-5 text-yellow-400" />
            <span className="text-slate-400">Avg Duration</span>
          </div>
          <div className="text-xl font-bold text-yellow-400 mt-1">
            {(result.trades.reduce((sum, t) => sum + (t.exitTime - t.entryTime), 0) / result.trades.length / (1000 * 60 * 60 * 24)).toFixed(1)} days
          </div>
        </div>
      </div>
    </div>
  );
}