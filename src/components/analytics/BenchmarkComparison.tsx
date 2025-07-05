import React from 'react';
import { BacktestResult } from '../../types';
import { ResponsiveContainer, LineChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Line } from 'recharts';

interface BenchmarkComparisonProps {
  result: BacktestResult | null;
}

const processChartData = (result: BacktestResult) => {
    if (!result || !result.equity || !result.benchmark) return [];
    
    return result.equity.map((equity, index) => ({
        name: index,
        strategy: equity,
        benchmark: result.benchmark[index] || 0
    }));
}


export function BenchmarkComparison({ result }: BenchmarkComparisonProps) {
    if (!result) {
        return (
          <div className="bg-slate-800 rounded-lg p-6 h-full">
            <h2 className="text-xl font-bold text-white mb-4">Strategy vs. Benchmark</h2>
            <div className="text-slate-400 text-center py-8 h-full flex items-center justify-center">
              <p>Run a backtest to see the comparison.</p>
            </div>
          </div>
        );
    }

    const data = processChartData(result);

    return (
        <div className="bg-slate-800 rounded-lg p-6 h-[400px]">
          <h2 className="text-xl font-bold text-white mb-4">Strategy vs. Benchmark (Buy & Hold)</h2>
          <ResponsiveContainer width="100%" height="90%">
            <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" tick={{ fill: '#94A3B8' }} />
              <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} tick={{ fill: '#94A3B8' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #334155' }}
                labelStyle={{ color: '#F8FAFC' }}
                formatter={(value: any) => `$${value.toFixed(2)}`}
              />
              <Legend wrapperStyle={{ color: '#F8FAFC' }} />
              <Line type="monotone" dataKey="strategy" name="Strategy Equity" stroke="#8884d8" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="benchmark" name="Benchmark Equity" stroke="#82ca9d" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
    );
} 