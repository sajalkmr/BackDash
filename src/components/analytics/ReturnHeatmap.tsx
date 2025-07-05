import React from 'react';
import { BacktestResult, Trade } from '../../types';
import { ResponsiveContainer, CartesianGrid, XAxis, YAxis, Tooltip, Legend, ScatterChart, Scatter, Cell, ZAxis } from 'recharts';

interface ReturnHeatmapProps {
  result: BacktestResult | null;
}

const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const getYears = (trades: Trade[]) => {
    if (!trades || trades.length === 0) return [];
    const firstTrade = trades[0];
    const lastTrade = trades[trades.length - 1];
    if (!firstTrade || !lastTrade) return [];
    const firstYear = new Date(firstTrade.entryTime).getFullYear();
    const lastYear = new Date(lastTrade.exitTime).getFullYear();
    return Array.from({ length: lastYear - firstYear + 1 }, (_, i) => firstYear + i);
};

const processDataForHeatmap = (trades: Trade[]) => {
    if (!trades || trades.length === 0) return null;

    const yearsList = getYears(trades);
    if (!yearsList) return null;

    const data = yearsList.reduce((acc, year) => {
        acc[year] = months.reduce((monthAcc, month) => {
            monthAcc[month] = 0;
            return monthAcc;
        }, {} as { [key: string]: number });
        return acc;
    }, {} as { [key: string]: { [key: string]: number } });

    trades.forEach(trade => {
        const exitDate = new Date(trade.exitTime);
        const year = exitDate.getFullYear();
        const monthIndex = exitDate.getMonth();
        const month = months[monthIndex];

        if (data[year] && month) {
            data[year][month]! += trade.pnlPercent;
        }
    });

    const chartData = yearsList.flatMap((year) => 
        months.map((month, monthIndex) => {
            const yearData = data[year];
            return {
                year: year.toString(),
                month: monthIndex,
                value: yearData ? yearData[month] ?? 0 : 0,
            };
        })
    );

    return chartData;
};

export function ReturnHeatmap({ result }: ReturnHeatmapProps) {
  if (!result || !result.trades || result.trades.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 h-full">
        <h2 className="text-xl font-bold text-white mb-4">Monthly Returns (%)</h2>
        <div className="text-slate-400 text-center py-8 h-full flex items-center justify-center">
          <p>No trade data available to generate heatmap.</p>
        </div>
      </div>
    );
  }

  const data = processDataForHeatmap(result.trades);
  if (!data) return null;

  const yearsList = getYears(result.trades)?.map(String) || [];
  if (!yearsList) return null;

  const getColor = (value: number) => {
    if (value > 0.01) return '#10B981'; // Emerald 500
    if (value < -0.01) return '#EF4444'; // Red 500
    return '#334155'; // Slate 700
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6 h-[400px]">
      <h2 className="text-xl font-bold text-white mb-4">Monthly Returns (%)</h2>
      <ResponsiveContainer width="100%" height="90%">
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid stroke="#334155" />
          <XAxis 
            type="category" 
            dataKey="year" 
            name="Year"
            domain={yearsList}
            tick={{ fill: '#94A3B8' }}
          />
          <YAxis 
            type="number" 
            dataKey="month" 
            name="Month"
            tickFormatter={(tick) => months[tick] || ''}
            domain={[-1, 12]}
            tick={{ fill: '#94A3B8' }}
          />
          <ZAxis type="number" dataKey="value" range={[100, 1000]} />
          <Tooltip 
            cursor={{ strokeDasharray: '3 3' }} 
            contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #334155' }}
            labelStyle={{ color: '#F8FAFC' }}
            formatter={(value: any, name: any, props: any) => {
                if (name === "Month") return months[value];
                if (name === "value") return `${(value as number).toFixed(2)}%`;
                return value;
            }}
          />
          <Scatter name="Monthly Returns" data={data} shape="square">
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.value)} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
} 