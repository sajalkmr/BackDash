import React from 'react';
import { BacktestResult, Trade } from '../../types';
import { ResponsiveContainer, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Bar, Cell } from 'recharts';

interface PnlDistributionProps {
  result: BacktestResult | null;
}

const processPnlData = (trades: Trade[]) => {
    if (!trades || trades.length === 0) return [];
    
    const pnlValues = trades.map(t => t.pnl);
    const maxPnl = Math.max(...pnlValues);
    const minPnl = Math.min(...pnlValues);

    const numBins = 20;
    const binSize = (maxPnl - minPnl) / numBins;

    const bins = Array.from({ length: numBins }, (_, i) => {
        const binStart = minPnl + i * binSize;
        return {
            name: `${binStart.toFixed(0)} to ${(binStart + binSize).toFixed(0)}`,
            count: 0,
            binStart,
        };
    });

    pnlValues.forEach(pnl => {
        let binIndex = Math.floor((pnl - minPnl) / binSize);
        
        // Ensure binIndex is within the valid range
        if (binIndex < 0) binIndex = 0;
        if (binIndex >= numBins) binIndex = numBins - 1;

        const bin = bins[binIndex];
        if (bin) {
            bin.count++;
        }
    });

    return bins;
}

export function PnlDistribution({ result }: PnlDistributionProps) {
  if (!result || !result.trades || result.trades.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 h-full">
        <h2 className="text-xl font-bold text-white mb-4">P&L Distribution</h2>
        <div className="text-slate-400 text-center py-8 h-full flex items-center justify-center">
          <p>No trade data available to generate chart.</p>
        </div>
      </div>
    );
  }

  const data = processPnlData(result.trades);
  if (!data) return null;

  return (
    <div className="bg-slate-800 rounded-lg p-6 h-[400px]">
      <h2 className="text-xl font-bold text-white mb-4">P&L Distribution</h2>
      <ResponsiveContainer width="100%" height="90%">
        <BarChart 
            data={data} 
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            barCategoryGap="0%"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="name" tick={{ fill: '#94A3B8', fontSize: 12 }} interval={3} />
          <YAxis tick={{ fill: '#94A3B8' }} label={{ value: 'Frequency', angle: -90, position: 'insideLeft', fill: '#94A3B8' }} />
          <Tooltip 
            cursor={{ fill: 'rgba(167, 139, 250, 0.1)' }}
            contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #334155' }}
            labelStyle={{ color: '#F8FAFC' }}
          />
          <Bar dataKey="count" name="Number of Trades">
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.binStart >= 0 ? '#10B981' : '#EF4444'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
} 