import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, AreaChart, Area, ComposedChart
} from 'recharts';
import { 
  TrendingUp, TrendingDown, Target, Shield, Activity, 
  AlertTriangle, CheckCircle, Minus, ArrowUp, ArrowDown
} from 'lucide-react';

interface BenchmarkComparison {
  benchmark_symbol: string;
  benchmark_name: string;
  strategy_return: number;
  benchmark_return: number;
  excess_return: number;
  tracking_error: number;
  information_ratio: number;
  correlation: number;
  beta: number;
  alpha: number;
  strategy_max_drawdown: number;
  benchmark_max_drawdown: number;
  benchmark_equity_curve: Array<{
    timestamp: string;
    value: number;
    return_pct: number;
  }>;
  relative_performance: Array<{
    timestamp: string;
    relative_return: number;
    strategy_return: number;
    benchmark_return: number;
  }>;
}

interface BenchmarkComparisonProps {
  backtestId: string;
  className?: string;
}

const AVAILABLE_BENCHMARKS = [
  { value: 'BTC-USDT', label: 'Bitcoin (BTC)', description: 'Leading cryptocurrency' },
  { value: 'ETH-USDT', label: 'Ethereum (ETH)', description: 'Smart contract platform' },
  { value: 'BNB-USDT', label: 'Binance Coin (BNB)', description: 'Exchange token' },
  { value: 'ADA-USDT', label: 'Cardano (ADA)', description: 'Proof-of-stake blockchain' },
  { value: 'SOL-USDT', label: 'Solana (SOL)', description: 'High-performance blockchain' },
  { value: 'DOT-USDT', label: 'Polkadot (DOT)', description: 'Interoperability protocol' }
];

export const BenchmarkComparison: React.FC<BenchmarkComparisonProps> = ({
  backtestId,
  className = ""
}) => {
  const [comparison, setComparison] = useState<BenchmarkComparison | null>(null);
  const [selectedBenchmark, setSelectedBenchmark] = useState('BTC-USDT');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadBenchmarkComparison();
  }, [backtestId, selectedBenchmark]);

  const loadBenchmarkComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/analytics/benchmark-compare/${backtestId}?benchmark_symbol=${selectedBenchmark}`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`Failed to load benchmark comparison: ${response.statusText}`);
      }

      const data = await response.json();
      setComparison(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load benchmark comparison');
    } finally {
      setLoading(false);
    }
  };

  const getPerformanceIcon = (value: number) => {
    if (value > 0) return <ArrowUp className="h-4 w-4 text-green-600" />;
    if (value < 0) return <ArrowDown className="h-4 w-4 text-red-600" />;
    return <Minus className="h-4 w-4 text-gray-600" />;
  };

  const getPerformanceColor = (value: number) => {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getBadgeVariant = (value: number, threshold: number = 0) => {
    if (value > threshold) return 'default';
    return 'secondary';
  };

  const formatPercentage = (value: number) => `${value.toFixed(2)}%`;
  const formatNumber = (value: number) => value.toFixed(3);

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="flex items-center justify-center space-y-4">
            <div className="text-center">
              <Activity className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
              <p className="text-sm text-gray-600">Comparing with benchmark...</p>
              <Progress value={60} className="w-48 mt-2" />
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
            <Button onClick={loadBenchmarkComparison} variant="outline">
              Retry Comparison
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!comparison) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center">
            <Target className="h-8 w-8 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No benchmark comparison available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Prepare chart data
  const performanceData = comparison.benchmark_equity_curve.map((point, index) => {
    const relativePoint = comparison.relative_performance[index];
    return {
      timestamp: new Date(point.timestamp).toLocaleDateString(),
      strategy: point.value,
      benchmark: 100 + point.return_pct,
      relative: relativePoint?.relative_return || 0
    };
  });

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Benchmark Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Benchmark Selection
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Select value={selectedBenchmark} onValueChange={setSelectedBenchmark}>
              <SelectTrigger className="w-64">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {AVAILABLE_BENCHMARKS.map(benchmark => (
                  <SelectItem key={benchmark.value} value={benchmark.value}>
                    <div>
                      <p className="font-medium">{benchmark.label}</p>
                      <p className="text-xs text-gray-600">{benchmark.description}</p>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button onClick={loadBenchmarkComparison} variant="outline">
              Update Comparison
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Performance Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Performance vs {comparison.benchmark_name}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Returns Comparison */}
            <div className="space-y-4">
              <h4 className="font-medium text-gray-700">Returns Comparison</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Strategy Return</span>
                  <div className="flex items-center gap-2">
                    {getPerformanceIcon(comparison.strategy_return)}
                    <span className={`font-medium ${getPerformanceColor(comparison.strategy_return)}`}>
                      {formatPercentage(comparison.strategy_return)}
                    </span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Benchmark Return</span>
                  <div className="flex items-center gap-2">
                    {getPerformanceIcon(comparison.benchmark_return)}
                    <span className={`font-medium ${getPerformanceColor(comparison.benchmark_return)}`}>
                      {formatPercentage(comparison.benchmark_return)}
                    </span>
                  </div>
                </div>
                <div className="flex justify-between items-center pt-2 border-t">
                  <span className="text-sm font-medium">Excess Return</span>
                  <div className="flex items-center gap-2">
                    {getPerformanceIcon(comparison.excess_return)}
                    <Badge variant={getBadgeVariant(comparison.excess_return)}>
                      {formatPercentage(comparison.excess_return)}
                    </Badge>
                  </div>
                </div>
              </div>
            </div>

            {/* Risk-Adjusted Metrics */}
            <div className="space-y-4">
              <h4 className="font-medium text-gray-700">Risk-Adjusted Performance</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Information Ratio</span>
                  <Badge variant={getBadgeVariant(comparison.information_ratio, 0.5)}>
                    {formatNumber(comparison.information_ratio)}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Tracking Error</span>
                  <span className="font-medium">{formatPercentage(comparison.tracking_error)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Correlation</span>
                  <Badge variant={comparison.correlation > 0.7 ? 'secondary' : 'default'}>
                    {formatNumber(comparison.correlation)}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Beta</span>
                  <span className="font-medium">{formatNumber(comparison.beta)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Alpha</span>
                  <div className="flex items-center gap-2">
                    {getPerformanceIcon(comparison.alpha)}
                    <span className={`font-medium ${getPerformanceColor(comparison.alpha)}`}>
                      {formatPercentage(comparison.alpha)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Risk Comparison */}
            <div className="space-y-4">
              <h4 className="font-medium text-gray-700">Risk Comparison</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Strategy Max DD</span>
                  <span className="font-medium text-red-600">
                    {formatPercentage(comparison.strategy_max_drawdown)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Benchmark Max DD</span>
                  <span className="font-medium text-red-600">
                    {formatPercentage(comparison.benchmark_max_drawdown)}
                  </span>
                </div>
                <div className="flex justify-between items-center pt-2 border-t">
                  <span className="text-sm font-medium">DD Difference</span>
                  <div className="flex items-center gap-2">
                    {comparison.strategy_max_drawdown < comparison.benchmark_max_drawdown ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 text-red-600" />
                    )}
                    <Badge variant={
                      comparison.strategy_max_drawdown < comparison.benchmark_max_drawdown ? 'default' : 'secondary'
                    }>
                      {formatPercentage(comparison.strategy_max_drawdown - comparison.benchmark_max_drawdown)}
                    </Badge>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Cumulative Performance Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis />
                <Tooltip 
                  formatter={(value: number, name: string) => [
                    `${value.toFixed(2)}${name === 'relative' ? '%' : ''}`, 
                    name === 'strategy' ? 'Strategy' : 
                    name === 'benchmark' ? comparison.benchmark_name : 
                    'Relative Performance'
                  ]}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="strategy" 
                  stroke="#3B82F6" 
                  strokeWidth={2}
                  name="Strategy"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey="benchmark" 
                  stroke="#10B981" 
                  strokeWidth={2}
                  name={comparison.benchmark_name}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Relative Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Relative Performance (Strategy vs Benchmark)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis />
                <Tooltip 
                  formatter={(value: number) => [`${value.toFixed(2)}%`, 'Relative Performance']}
                />
                <Area 
                  type="monotone" 
                  dataKey="relative" 
                  stroke="#8884d8" 
                  fill="#8884d8" 
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 text-sm text-gray-600">
            <p>Positive values indicate strategy outperformance, negative values indicate underperformance.</p>
          </div>
        </CardContent>
      </Card>

      {/* Key Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Key Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <h4 className="font-medium">Performance Analysis</h4>
              <div className="space-y-2 text-sm">
                {comparison.excess_return > 0 ? (
                  <div className="flex items-center gap-2 text-green-700">
                    <CheckCircle className="h-4 w-4" />
                    <span>Strategy outperformed benchmark by {formatPercentage(comparison.excess_return)}</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-red-700">
                    <AlertTriangle className="h-4 w-4" />
                    <span>Strategy underperformed benchmark by {formatPercentage(Math.abs(comparison.excess_return))}</span>
                  </div>
                )}
                
                {comparison.information_ratio > 0.5 ? (
                  <div className="flex items-center gap-2 text-green-700">
                    <CheckCircle className="h-4 w-4" />
                    <span>Good risk-adjusted performance (IR: {formatNumber(comparison.information_ratio)})</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-yellow-700">
                    <AlertTriangle className="h-4 w-4" />
                    <span>Moderate risk-adjusted performance (IR: {formatNumber(comparison.information_ratio)})</span>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-medium">Risk Analysis</h4>
              <div className="space-y-2 text-sm">
                {comparison.strategy_max_drawdown < comparison.benchmark_max_drawdown ? (
                  <div className="flex items-center gap-2 text-green-700">
                    <CheckCircle className="h-4 w-4" />
                    <span>Lower maximum drawdown than benchmark</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-red-700">
                    <AlertTriangle className="h-4 w-4" />
                    <span>Higher maximum drawdown than benchmark</span>
                  </div>
                )}
                
                {comparison.correlation < 0.8 ? (
                  <div className="flex items-center gap-2 text-green-700">
                    <CheckCircle className="h-4 w-4" />
                    <span>Good diversification benefit (correlation: {formatNumber(comparison.correlation)})</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-yellow-700">
                    <AlertTriangle className="h-4 w-4" />
                    <span>High correlation with benchmark ({formatNumber(comparison.correlation)})</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};