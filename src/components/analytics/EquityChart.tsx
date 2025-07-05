import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { BacktestResult } from '../types';

interface EquityChartProps {
  result: BacktestResult | null;
}

export function EquityChart({ result }: EquityChartProps) {
  if (!result) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Equity Curve</h2>
        <div className="text-slate-400 text-center py-8">
          Run a backtest to see equity curve
        </div>
      </div>
    );
  }

  const chartData = result.equity.map((value, index) => ({
    index,
    equity: value,
    drawdown: -(result.drawdown?.[index] ?? 0)
  }));

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-6">Equity Curve & Drawdown</h2>
      
      <div className="space-y-6">
        {/* Equity Curve */}
        <div className="h-64">
          <h3 className="text-lg font-semibold text-white mb-4">Portfolio Value</h3>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="index" 
                stroke="#9CA3AF"
                fontSize={12}
              />
              <YAxis 
                stroke="#9CA3AF"
                fontSize={12}
                tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F3F4F6'
                }}
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Portfolio Value']}
                labelFormatter={(label) => `Day ${label}`}
              />
              <Area
                type="monotone"
                dataKey="equity"
                stroke="#10B981"
                strokeWidth={2}
                fill="url(#equityGradient)"
                fillOpacity={0.6}
              />
              <defs>
                <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Drawdown Chart */}
        <div className="h-48">
          <h3 className="text-lg font-semibold text-white mb-4">Drawdown</h3>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="index" 
                stroke="#9CA3AF"
                fontSize={12}
              />
              <YAxis 
                stroke="#9CA3AF"
                fontSize={12}
                tickFormatter={(value) => `${value.toFixed(1)}%`}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F3F4F6'
                }}
                formatter={(value: number) => [`${value.toFixed(2)}%`, 'Drawdown']}
                labelFormatter={(label) => `Day ${label}`}
              />
              <Area
                type="monotone"
                dataKey="drawdown"
                stroke="#EF4444"
                strokeWidth={2}
                fill="url(#drawdownGradient)"
                fillOpacity={0.6}
              />
              <defs>
                <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#EF4444" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#EF4444" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}