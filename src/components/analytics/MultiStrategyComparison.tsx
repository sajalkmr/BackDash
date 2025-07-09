import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Trophy, TrendingUp, Shield, BarChart3, Target, 
  Users, Zap, AlertTriangle, Download, RefreshCw
} from 'lucide-react';
import { 
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, 
  Radar, BarChart, Bar
} from 'recharts';

interface StrategyComparison {
  strategy_id: string;
  strategy_name: string;
  total_return: number;
  cagr: number;
  sharpe_ratio: number;
  max_drawdown: number;
  volatility: number;
  rank_return: number;
  rank_sharpe: number;
  rank_drawdown: number;
  sortino_ratio: number;
  calmar_ratio: number;
  total_trades: number;
  win_rate: number;
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
  availableStrategies: Array<{
    id: string;
    name: string;
    status: 'completed' | 'running' | 'failed';
  }>;
  className?: string;
}

export const MultiStrategyComparison: React.FC<MultiStrategyComparisonProps> = ({
  availableStrategies,
  className = ""
}) => {
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([]);
  const [analysis, setAnalysis] = useState<MultiStrategyAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  const completedStrategies = availableStrategies.filter(s => s.status === 'completed');

  const runComparison = async () => {
    if (selectedStrategies.length < 2) {
      setError('Please select at least 2 strategies for comparison');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/analytics/multi-strategy-compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          backtest_ids: selectedStrategies,
          comparison_type: 'multi_strategy',
          include_rolling_metrics: true
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to compare strategies: ${response.statusText}`);
      }

      const data = await response.json();
      setAnalysis(data);
      setActiveTab('overview');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to compare strategies');
    } finally {
      setLoading(false);
    }
  };

  const toggleStrategy = (strategyId: string) => {
    setSelectedStrategies(prev =>
      prev.includes(strategyId)
        ? prev.filter(id => id !== strategyId)
        : [...prev, strategyId]
    );
  };

  const formatPercentage = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  const formatNumber = (value: number, decimals: number = 2) => value.toFixed(decimals);

  const getPerformanceColor = (value: number, isInverse: boolean = false) => {
    const positive = isInverse ? value < 0 : value > 0;
    if (positive) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getRankBadgeVariant = (rank: number, total: number) => {
    if (rank === 1) return 'default';
    if (rank <= total / 3) return 'secondary';
    return 'outline';
  };

  const prepareRadarData = () => {
    if (!analysis) return [];
    
    return analysis.strategies.map(strategy => ({
      strategy: strategy.strategy_name.substring(0, 10) + '...',
      return: Math.max(0, strategy.total_return),
      sharpe: Math.max(0, strategy.sharpe_ratio * 10), // Scale for visualization
      drawdown: Math.max(0, 100 + strategy.max_drawdown), // Make positive for radar
      winRate: strategy.win_rate,
      calmar: Math.max(0, strategy.calmar_ratio * 10)
    }));
  };

  const prepareEfficientFrontierData = () => {
    if (!analysis) return [];
    
    return analysis.strategies.map(strategy => ({
      risk: strategy.volatility,
      return: strategy.total_return,
      name: strategy.strategy_name,
      sharpe: strategy.sharpe_ratio,
      size: Math.max(50, strategy.sharpe_ratio * 100) // Bubble size based on Sharpe
    }));
  };

  if (completedStrategies.length < 2) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Multi-Strategy Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <p className="text-gray-600">
              You need at least 2 completed backtests to perform strategy comparison.
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Run more backtests and return here to compare their performance.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Strategy Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Multi-Strategy Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-medium mb-3">Select Strategies to Compare:</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {completedStrategies.map(strategy => (
                  <div key={strategy.id} className="flex items-center space-x-2 p-3 border rounded-lg">
                    <Checkbox
                      id={strategy.id}
                      checked={selectedStrategies.includes(strategy.id)}
                      onCheckedChange={() => toggleStrategy(strategy.id)}
                    />
                    <label htmlFor={strategy.id} className="text-sm font-medium cursor-pointer flex-1">
                      {strategy.name}
                    </label>
                    <Badge variant="secondary">{strategy.status}</Badge>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-4">
              <Button 
                onClick={runComparison}
                disabled={selectedStrategies.length < 2 || loading}
                className="flex items-center gap-2"
              >
                {loading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <BarChart3 className="h-4 w-4" />
                )}
                {loading ? 'Comparing...' : 'Compare Strategies'}
              </Button>
              
              <p className="text-sm text-gray-600">
                {selectedStrategies.length} of {completedStrategies.length} strategies selected
              </p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-600">{error}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {analysis && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Trophy className="h-5 w-5" />
                Strategy Analysis Results
              </span>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
                <Badge variant="outline">
                  {new Date(analysis.generated_at).toLocaleDateString()}
                </Badge>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="rankings">Rankings</TabsTrigger>
                <TabsTrigger value="analysis">Analysis</TabsTrigger>
                <TabsTrigger value="correlation">Correlation</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-6 mt-6">
                {/* Top Performers */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="h-5 w-5 text-green-600" />
                      <span className="font-medium">Best Return</span>
                    </div>
                    <p className="text-xl font-bold text-green-600">{analysis.best_return_strategy}</p>
                  </div>

                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Zap className="h-5 w-5 text-blue-600" />
                      <span className="font-medium">Best Sharpe Ratio</span>
                    </div>
                    <p className="text-xl font-bold text-blue-600">{analysis.best_sharpe_strategy}</p>
                  </div>

                  <div className="bg-purple-50 p-4 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Shield className="h-5 w-5 text-purple-600" />
                      <span className="font-medium">Lowest Drawdown</span>
                    </div>
                    <p className="text-xl font-bold text-purple-600">{analysis.lowest_drawdown_strategy}</p>
                  </div>
                </div>

                {/* Performance Overview Table */}
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse border border-gray-200">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="border border-gray-200 p-3 text-left">Strategy</th>
                        <th className="border border-gray-200 p-3 text-right">Total Return</th>
                        <th className="border border-gray-200 p-3 text-right">CAGR</th>
                        <th className="border border-gray-200 p-3 text-right">Sharpe Ratio</th>
                        <th className="border border-gray-200 p-3 text-right">Max Drawdown</th>
                        <th className="border border-gray-200 p-3 text-right">Volatility</th>
                        <th className="border border-gray-200 p-3 text-right">Win Rate</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysis.strategies.map(strategy => (
                        <tr key={strategy.strategy_id} className="hover:bg-gray-50">
                          <td className="border border-gray-200 p-3 font-medium">{strategy.strategy_name}</td>
                          <td className={`border border-gray-200 p-3 text-right font-medium ${getPerformanceColor(strategy.total_return)}`}>
                            {formatPercentage(strategy.total_return)}
                          </td>
                          <td className={`border border-gray-200 p-3 text-right ${getPerformanceColor(strategy.cagr)}`}>
                            {formatPercentage(strategy.cagr)}
                          </td>
                          <td className={`border border-gray-200 p-3 text-right ${getPerformanceColor(strategy.sharpe_ratio)}`}>
                            {formatNumber(strategy.sharpe_ratio)}
                          </td>
                          <td className={`border border-gray-200 p-3 text-right ${getPerformanceColor(strategy.max_drawdown, true)}`}>
                            {formatPercentage(strategy.max_drawdown)}
                          </td>
                          <td className="border border-gray-200 p-3 text-right">
                            {formatPercentage(strategy.volatility)}
                          </td>
                          <td className={`border border-gray-200 p-3 text-right ${getPerformanceColor(strategy.win_rate - 50)}`}>
                            {formatPercentage(strategy.win_rate)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </TabsContent>

              <TabsContent value="rankings" className="space-y-6 mt-6">
                {/* Rankings Cards */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Return Rankings */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Return Rankings</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {analysis.strategies
                          .sort((a, b) => a.rank_return - b.rank_return)
                          .map(strategy => (
                            <div key={strategy.strategy_id} className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <Badge variant={getRankBadgeVariant(strategy.rank_return, analysis.strategies.length)}>
                                  #{strategy.rank_return}
                                </Badge>
                                <span className="text-sm">{strategy.strategy_name}</span>
                              </div>
                              <span className={`text-sm font-medium ${getPerformanceColor(strategy.total_return)}`}>
                                {formatPercentage(strategy.total_return)}
                              </span>
                            </div>
                          ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Sharpe Rankings */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Sharpe Ratio Rankings</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {analysis.strategies
                          .sort((a, b) => a.rank_sharpe - b.rank_sharpe)
                          .map(strategy => (
                            <div key={strategy.strategy_id} className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <Badge variant={getRankBadgeVariant(strategy.rank_sharpe, analysis.strategies.length)}>
                                  #{strategy.rank_sharpe}
                                </Badge>
                                <span className="text-sm">{strategy.strategy_name}</span>
                              </div>
                              <span className={`text-sm font-medium ${getPerformanceColor(strategy.sharpe_ratio)}`}>
                                {formatNumber(strategy.sharpe_ratio)}
                              </span>
                            </div>
                          ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Drawdown Rankings */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Drawdown Rankings</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {analysis.strategies
                          .sort((a, b) => a.rank_drawdown - b.rank_drawdown)
                          .map(strategy => (
                            <div key={strategy.strategy_id} className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <Badge variant={getRankBadgeVariant(strategy.rank_drawdown, analysis.strategies.length)}>
                                  #{strategy.rank_drawdown}
                                </Badge>
                                <span className="text-sm">{strategy.strategy_name}</span>
                              </div>
                              <span className={`text-sm font-medium ${getPerformanceColor(strategy.max_drawdown, true)}`}>
                                {formatPercentage(strategy.max_drawdown)}
                              </span>
                            </div>
                          ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="analysis" className="space-y-6 mt-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Efficient Frontier */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Efficient Frontier</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={400}>
                        <ScatterChart data={prepareEfficientFrontierData()}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            dataKey="risk" 
                            type="number" 
                            name="Volatility %" 
                            tick={{ fontSize: 12 }}
                          />
                          <YAxis 
                            dataKey="return" 
                            type="number" 
                            name="Return %" 
                            tick={{ fontSize: 12 }}
                          />
                          <Tooltip 
                            formatter={(value: number, name: string) => [
                              name === 'return' ? formatPercentage(value) : formatNumber(value),
                              name === 'return' ? 'Return' : 'Risk'
                            ]}
                            labelFormatter={(value) => `Strategy: ${value}`}
                          />
                          <Scatter 
                            dataKey="return" 
                            fill="#2563eb"
                          />
                        </ScatterChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* Performance Radar */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Performance Radar</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={400}>
                        <RadarChart data={prepareRadarData()}>
                          <PolarGrid />
                          <PolarAngleAxis dataKey="strategy" tick={{ fontSize: 10 }} />
                          <PolarRadiusAxis 
                            angle={0} 
                            domain={[0, 100]} 
                            tick={{ fontSize: 8 }}
                          />
                          {analysis.strategies.map((strategy, index) => (
                            <Radar
                              key={strategy.strategy_id}
                              name={strategy.strategy_name}
                              dataKey="return"
                              stroke={`hsl(${index * (360 / analysis.strategies.length)}, 70%, 50%)`}
                              fill={`hsl(${index * (360 / analysis.strategies.length)}, 70%, 50%)`}
                              fillOpacity={0.1}
                            />
                          ))}
                          <Legend />
                        </RadarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="correlation" className="space-y-6 mt-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Strategy Correlation Matrix</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {Object.keys(analysis.correlation_matrix).length > 0 ? (
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse border border-gray-200">
                          <thead>
                            <tr className="bg-gray-50">
                              <th className="border border-gray-200 p-2 text-left">Strategy</th>
                              {Object.keys(analysis.correlation_matrix).map(strategy => (
                                <th key={strategy} className="border border-gray-200 p-2 text-center text-xs">
                                  {strategy.substring(0, 8)}...
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {Object.entries(analysis.correlation_matrix).map(([strategy1, correlations]) => (
                              <tr key={strategy1}>
                                <td className="border border-gray-200 p-2 font-medium text-xs">
                                  {strategy1.substring(0, 8)}...
                                </td>
                                {Object.entries(correlations).map(([strategy2, correlation]) => (
                                  <td key={strategy2} className="border border-gray-200 p-2 text-center">
                                    <span 
                                      className={`text-xs font-medium px-2 py-1 rounded ${
                                        Math.abs(correlation) > 0.7 ? 'bg-red-100 text-red-800' :
                                        Math.abs(correlation) > 0.3 ? 'bg-yellow-100 text-yellow-800' :
                                        'bg-green-100 text-green-800'
                                      }`}
                                    >
                                      {formatNumber(correlation)}
                                    </span>
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="text-gray-600 text-center py-8">
                        Correlation data not available
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  );
}; 