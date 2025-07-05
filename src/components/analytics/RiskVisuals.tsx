import React from 'react';
import { BacktestResult } from '../../types';
import { ResponsiveContainer, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Bar, Cell } from 'recharts';

interface RiskVisualsProps {
  result: BacktestResult | null;
}

const processRiskData = (metrics: BacktestResult['metrics']) => {
    if (!metrics) return [];

    return [
        { name: 'Sharpe', value: metrics.sharpe, fill: '#8884d8' },
        { name: 'Sortino', value: metrics.sortino, fill: '#82ca9d' },
        { name: 'Calmar', value: metrics.calmar, fill: '#ffc658' },
        { name: 'Volatility', value: metrics.volatility, fill: '#ff8042' },
        { name: 'VaR (95%)', value: Math.abs(metrics.var95), fill: '#d0ed57' },
    ];
}

export function RiskVisuals({ result }: RiskVisualsProps) {
    if (!result || !result.metrics) {
        return (
          <div className="bg-slate-800 rounded-lg p-6 h-full">
            <h2 className="text-xl font-bold text-white mb-4">Risk Metrics</h2>
            <div className="text-slate-400 text-center py-8 h-full flex items-center justify-center">
              <p>No metrics available to display.</p>
            </div>
          </div>
        );
    }

    const data = processRiskData(result.metrics);

    return (
        <div className="bg-slate-800 rounded-lg p-6 h-[400px]">
          <h2 className="text-xl font-bold text-white mb-4">Risk Metric Ratios</h2>
          <ResponsiveContainer width="100%" height="90%">
            <BarChart data={data} layout="vertical" margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" tick={{ fill: '#94A3B8' }} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#94A3B8' }} width={80} />
              <Tooltip 
                cursor={{ fill: 'rgba(167, 139, 250, 0.1)' }}
                contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #334155' }}
                labelStyle={{ color: '#F8FAFC' }}
                formatter={(value: any) => value.toFixed(2)}
              />
              <Bar dataKey="value" name="Ratio Value">
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
    );
} 