import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { OHLCVData, BacktestResult } from '../types';

interface PriceChartProps {
  data: OHLCVData[];
  result: BacktestResult | null;
}

export function PriceChart({ data, result }: PriceChartProps) {
  const chartData = data.slice(-500).map((item, index) => ({
    index,
    price: item.close,
    date: new Date(item.timestamp).toLocaleDateString(),
    volume: item.volume
  }));

  // Add trade markers
  const tradeMarkers = result?.trades.map(trade => {
    const entryIndex = data.findIndex(d => d.timestamp >= trade.entryTime);
    const exitIndex = data.findIndex(d => d.timestamp >= trade.exitTime);
    
    return {
      entry: { index: entryIndex - (data.length - 500), price: trade.entryPrice },
      exit: { index: exitIndex - (data.length - 500), price: trade.exitPrice },
      profitable: trade.pnl > 0
    };
  }).filter(marker => marker.entry.index >= 0 && marker.exit.index >= 0) || [];

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-6">Price Chart with Trade Signals</h2>
      
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="index" 
              stroke="#9CA3AF"
              fontSize={12}
              tickFormatter={(value) => {
                const item = chartData[value];
                return item ? item.date : '';
              }}
            />
            <YAxis 
              stroke="#9CA3AF"
              fontSize={12}
              domain={['dataMin - 5', 'dataMax + 5']}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#F3F4F6'
              }}
              formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
              labelFormatter={(label) => {
                const item = chartData[label];
                return item ? `Date: ${item.date}` : '';
              }}
            />
            <Line
              type="monotone"
              dataKey="price"
              stroke="#3B82F6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, stroke: '#3B82F6', strokeWidth: 2 }}
            />
            
            {/* Trade Entry/Exit Markers */}
            {tradeMarkers.map((marker, index) => (
              <g key={index}>
                {/* Entry marker */}
                <ReferenceLine
                  x={marker.entry.index}
                  stroke={marker.profitable ? '#10B981' : '#EF4444'}
                  strokeWidth={2}
                  strokeDasharray="5 5"
                />
                {/* Exit marker */}
                <ReferenceLine
                  x={marker.exit.index}
                  stroke={marker.profitable ? '#10B981' : '#EF4444'}
                  strokeWidth={2}
                  strokeDasharray="2 2"
                />
              </g>
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center space-x-6 mt-4 text-sm">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-0.5 bg-blue-500"></div>
          <span className="text-slate-400">Price</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-0.5 border-t-2 border-dashed border-emerald-500"></div>
          <span className="text-slate-400">Profitable Trade</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-0.5 border-t-2 border-dashed border-red-500"></div>
          <span className="text-slate-400">Losing Trade</span>
        </div>
      </div>
    </div>
  );
}