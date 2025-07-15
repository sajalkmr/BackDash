import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, LineChart, Line, Cell, PieChart, Pie
} from 'recharts';
import { 
  TrendingUp, TrendingDown, Award, AlertTriangle, 
  Target, Shield, Zap, Activity, Users, Crown
} from 'lucide-react';

interface StrategyComparison {
  strategy_id: string;
  strategy_name: string;
  total_return: number;
  cagr: number;
  sharpe_ratio: number;
  max_drawdown: number;
  volatility: number;
  sortino_ratio: number;
  calmar_ratio: number;
  total_trades: number;
  win_rate: number;
  rank_return: number;
  rank_sharpe: number;
  rank_drawdown: number;
}

interface MultiStrategyAnalysis {
  comparison_id: string;
  generated_at: string;
  strategies: StrategyComparison[];
  best_return_strategy: string;
  best_sharpe_strategy: string;
  lowest_drawdown_strategy: string;
  correlation_matrix: Record<string, Record<string, number>>;
  efficient_frontier: Array<{
    risk: number;
    return: number;
    sharpe: number;
    strategy: string;
  }>;
}

interface MultiStrategyComparisonProps {
  backtestIds: string[];
  className?: string;
}

export const MultiStrategyComparison: React.FC<MultiStrategyComparisonProps> = ({
  backtestIds,
  className = ""
}) => {
  const [analysis, setAnalysis] = useState<MultiStrategyAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMetric, setSelectedMetric] = useState<'return' | 'sharpe' | 'drawdown'>('return');

  useEffect(() => {
    if (backtestIds.length >= 2) {
      loadMultiStrategyAnalysis();
    }
  }, [backtestIds]);

  const loadMultiStrategyAnalysis = async () => {
    if (backtestIds.length < 2) {
      setError('At least 2 strategies required for comparison');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/analytics/multi-strategy-compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          backtest_ids: backtestIds,
          comparison_type: 'multi_strategy'
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to load comparison: ${response.statusText}`);
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load comparison');
    } finally {
      setLoading(false);
    }
  };

  const getMetricColor = (value: number, metric: string) => {
    if (metric === 'drawdown') {
      return value < -10 ? 'text-red-600' : value < -5 ? 'text-yellow-600' : 'text-green-600';
    }
    return value > 0 ? 'text-green-600' : 'text-red-600';
  };

  const getRankBadgeColor = (rank: number, total: number) => {
    if (rank === 1) return 'bg-yellow-500';
    if (rank <= total * 0.3) return 'bg-green-500';
    if (rank <= total * 0.7) return 'bg-blue-500';
    return 'bg-gray-500';
  };

  const formatPercentage = (value: number) => `${value.toFixed(2)}%`;
  const formatNumber = (value: number) => value.toFixed(2);

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="flex items-center justify-center space-y-4">
            <div className="text-center">
              <Activity className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
              <p className="text-sm text-gray-600">Analyzing strategies...</p>
              <Progress value={75} className="w-48 mt-2" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center">
            <AlertTriangle className="h-8 w-8 text-red-600 mx-auto mb-4" />
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={loadMultiStrategyAnalysis} variant="outline">
              Retry Analysis
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!analysis) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center">
            <Users className="h-8 w-8 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">Select at least 2 strategies to compare</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Prepare chart data
  const comparisonData = analysis.strategies.map(strategy => ({
    name: strategy.strategy_name.length > 15 
      ? strategy.strategy_name.substring(0, 15) + '...' 
      : strategy.strategy_name,
    fullName: strategy.strategy_name,
    return: strategy.total_return,
    sharpe: strategy.sharpe_ratio,
    drawdown: Math.abs(strategy.max_drawdown),
    volatility: strategy.volatility,
    trades: strategy.total_trades,
    winRate: strategy.win_rate
  }));

  const scatterData = analysis.strategies.map(strategy => ({
    x: strategy.volatility,
    y: strategy.total_return,
    name: strategy.strategy_name,
    sharpe: strategy.sharpe_ratio,
    size: strategy.total_trades
  }));

  const correlationData = Object.entries(analysis.correlation_matrix).map(([strategy1, correlations]) =>
    Object.entries(correlations).map(([strategy2, correlation]) => ({
      strategy1,
      strategy2,
      correlation: correlation * 100
    }))
  ).flat();

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header with Champions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Crown className="h-5 w-5 text-yellow-600" />
            Strategy Champions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <Award className="h-6 w-6 text-yellow-600 mx-auto mb-2" />
              <p className="text-sm text-gray-600">Best Return</p>
              <p className="font-semibold text-yellow-700">{analysis.best_return_strategy}</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg border border-green-200">
              <Target className="h-6 w-6 text-green-600 mx-auto mb-2" />
              <p className="text-sm text-gray-600">Best Sharpe</p>
              <p className="font-semibold text-green-700">{analysis.best_sharpe_strategy}</p>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
              <Shield className="h-6 w-6 text-blue-600 mx-auto mb-2" />
              <p className="text-sm text-gray-600">Lowest Drawdown</p>
              <p className="font-semibold text-blue-700">{analysis.lowest_drawdown_strategy}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Comparison */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Strategy Comparison ({analysis.strategies.length} Strategies)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={selectedMetric} onValueChange={(value) => setSelectedMetric(value as any)}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="return">Returns</TabsTrigger>
              <TabsTrigger value="sharpe">Risk-Adjusted</TabsTrigger>
              <TabsTrigger value="drawdown">Risk Analysis</TabsTrigger>
            </TabsList>

            <TabsContent value="return" className="space-y-4">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={comparisonData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip 
                      formatter={(value: number, name: string) => [
                        `${value.toFixed(2)}%`, 
                        name === 'return' ? 'Total Return' : name
                      ]}
                      labelFormatter={(label) => comparisonData.find(d => d.name === label)?.fullName || label}
                    />
                    <Bar dataKey="return" fill="#3B82F6" name="Total Return (%)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </TabsContent>

            <TabsContent value="sharpe" className="space-y-4">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={comparisonData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip 
                      formatter={(value: number) => [value.toFixed(2), 'Sharpe Ratio']}
                      labelFormatter={(label) => comparisonData.find(d => d.name === label)?.fullName || label}
                    />
                    <Bar dataKey="sharpe" fill="#10B981" name="Sharpe Ratio" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </TabsContent>

            <TabsContent value="drawdown" className="space-y-4">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={comparisonData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip 
                      formatter={(value: number) => [`-${value.toFixed(2)}%`, 'Max Drawdown']}
                      labelFormatter={(label) => comparisonData.find(d => d.name === label)?.fullName || label}
                    />
                    <Bar dataKey="drawdown" fill="#EF4444" name="Max Drawdown (%)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Risk-Return Scatter Plot */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Risk-Return Profile
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart data={scatterData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="x" 
                  name="Volatility" 
                  unit="%" 
                  label={{ value: 'Volatility (%)', position: 'insideBottom', offset: -10 }}
                />
                <YAxis 
                  dataKey="y" 
                  name="Return" 
                  unit="%" 
                  label={{ value: 'Total Return (%)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  formatter={(value: number, name: string) => [
                    `${value.toFixed(2)}%`, 
                    name === 'x' ? 'Volatility' : 'Total Return'
                  ]}
                  labelFormatter={(label, payload) => {
                    if (payload && payload[0]) {
                      const data = payload[0].payload;
                      return `${data.name} (Sharpe: ${data.sharpe.toFixed(2)})`;
                    }
                    return label;
                  }}
                />
                <Scatter dataKey="y" fill="#8884d8">
                  {scatterData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.sharpe > 1 ? '#10B981' : entry.sharpe > 0.5 ? '#F59E0B' : '#EF4444'} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 flex items-center justify-center space-x-6 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span>Excellent (Sharpe > 1.0)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <span>Good (Sharpe > 0.5)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <span>Poor (Sharpe ≤ 0.5)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Comparison Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Metrics Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Strategy</th>
                  <th className="text-right p-2">Total Return</th>
                  <th className="text-right p-2">CAGR</th>
                  <th className="text-right p-2">Sharpe</th>
                  <th className="text-right p-2">Sortino</th>
                  <th className="text-right p-2">Max DD</th>
                  <th className="text-right p-2">Volatility</th>
                  <th className="text-right p-2">Trades</th>
                  <th className="text-right p-2">Win Rate</th>
                  <th className="text-center p-2">Ranks</th>
                </tr>
              </thead>
              <tbody>
                {analysis.strategies.map((strategy, index) => (
                  <tr key={strategy.strategy_id} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                    <td className="p-2 font-medium">{strategy.strategy_name}</td>
                    <td className={`text-right p-2 ${getMetricColor(strategy.total_return, 'return')}`}>
                      {formatPercentage(strategy.total_return)}
                    </td>
                    <td className={`text-right p-2 ${getMetricColor(strategy.cagr, 'return')}`}>
                      {formatPercentage(strategy.cagr)}
                    </td>
                    <td className="text-right p-2">{formatNumber(strategy.sharpe_ratio)}</td>
                    <td className="text-right p-2">{formatNumber(strategy.sortino_ratio)}</td>
                    <td className={`text-right p-2 ${getMetricColor(strategy.max_drawdown, 'drawdown')}`}>
                      {formatPercentage(strategy.max_drawdown)}
                    </td>
                    <td className="text-right p-2">{formatPercentage(strategy.volatility)}</td>
                    <td className="text-right p-2">{strategy.total_trades}</td>
                    <td className="text-right p-2">{formatPercentage(strategy.win_rate)}</td>
                    <td className="text-center p-2">
                      <div className="flex justify-center space-x-1">
                        <Badge 
                          className={`text-xs px-1 py-0 ${getRankBadgeColor(strategy.rank_return, analysis.strategies.length)} text-white`}
                        >
                          R{strategy.rank_return}
                        </Badge>
                        <Badge 
                          className={`text-xs px-1 py-0 ${getRankBadgeColor(strategy.rank_sharpe, analysis.strategies.length)} text-white`}
                        >
                          S{strategy.rank_sharpe}
                        </Badge>
                        <Badge 
                          className={`text-xs px-1 py-0 ${getRankBadgeColor(strategy.rank_drawdown, analysis.strategies.length)} text-white`}
                        >
                          D{strategy.rank_drawdown}
                        </Badge>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4 text-xs text-gray-600">
            <p>Ranks: R = Return, S = Sharpe Ratio, D = Drawdown (1 = best)</p>
          </div>
        </CardContent>
      </Card>

      {/* Strategy Correlation Matrix */}
      {Object.keys(analysis.correlation_matrix).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Strategy Correlation Matrix</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr>
                    <th className="text-left p-2">Strategy</th>
                    {Object.keys(analysis.correlation_matrix).map(strategy => (
                      <th key={strategy} className="text-center p-2 min-w-20">
                        {strategy.length > 10 ? strategy.substring(0, 10) + '...' : strategy}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(analysis.correlation_matrix).map(([strategy1, correlations]) => (
                    <tr key={strategy1}>
                      <td className="p-2 font-medium">
                        {strategy1.length > 15 ? strategy1.substring(0, 15) + '...' : strategy1}
                      </td>
                      {Object.entries(correlations).map(([strategy2, correlation]) => (
                        <td 
                          key={strategy2} 
                          className={`text-center p-2 ${
                            correlation > 0.7 ? 'bg-red-100 text-red-800' :
                            correlation > 0.3 ? 'bg-yellow-100 text-yellow-800' :
                            correlation < -0.3 ? 'bg-blue-100 text-blue-800' :
                            'bg-green-100 text-green-800'
                          }`}
                        >
                          {correlation.toFixed(2)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4 flex items-center justify-center space-x-6 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-100 border border-red-300 rounded"></div>
                <span>High Correlation (>0.7)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-yellow-100 border border-yellow-300 rounded"></div>
                <span>Moderate (0.3-0.7)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-100 border border-green-300 rounded"></div>
                <span>Low (-0.3-0.3)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-blue-100 border border-blue-300 rounded"></div>
                <span>Negative (<-0.3)</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};