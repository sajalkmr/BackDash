import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { TrendingUp, TrendingDown, BarChart3, Activity, Target, AlertTriangle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

interface BenchmarkData {
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

export const BenchmarkComparison: React.FC<BenchmarkComparisonProps> = ({
  backtestId,
  className = ""
}) => {
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkData | null>(null);
  const [selectedBenchmark, setSelectedBenchmark] = useState('BTC-USDT');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const availableBenchmarks = [
    { value: 'BTC-USDT', label: 'Bitcoin (BTC-USDT)' },
    { value: 'ETH-USDT', label: 'Ethereum (ETH-USDT)' },
    { value: 'BNB-USDT', label: 'Binance Coin (BNB-USDT)' },
    { value: 'ADA-USDT', label: 'Cardano (ADA-USDT)' },
    { value: 'SOL-USDT', label: 'Solana (SOL-USDT)' }
  ];

  const fetchBenchmarkComparison = async (benchmarkSymbol: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/v1/analytics/benchmark-compare/${backtestId}?benchmark_symbol=${benchmarkSymbol}`,
        { method: 'POST' }
      );
      
      if (!response.ok) {
        throw new Error(`Failed to fetch benchmark comparison: ${response.statusText}`);
      }
      
      const data = await response.json();
      setBenchmarkData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch benchmark comparison');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (backtestId) {
      fetchBenchmarkComparison(selectedBenchmark);
    }
  }, [backtestId, selectedBenchmark]);

  const formatPercentage = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  const formatNumber = (value: number, decimals: number = 2) => value.toFixed(decimals);

  const getPerformanceColor = (value: number) => {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getPerformanceIcon = (value: number) => {
    return value >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />;
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Benchmark Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-sm text-gray-600">Loading benchmark comparison...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            Benchmark Comparison Error
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-600">{error}</p>
          <Button 
            onClick={() => fetchBenchmarkComparison(selectedBenchmark)}
            className="mt-4"
            variant="outline"
          >
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Benchmark Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Benchmark Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-6">
            <label className="text-sm font-medium">Compare against:</label>
            <Select value={selectedBenchmark} onValueChange={setSelectedBenchmark}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {availableBenchmarks.map((benchmark) => (
                  <SelectItem key={benchmark.value} value={benchmark.value}>
                    {benchmark.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {benchmarkData && (
            <>
              {/* Performance Overview */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Strategy Return</p>
                      <p className={`text-2xl font-bold ${getPerformanceColor(benchmarkData.strategy_return)}`}>
                        {formatPercentage(benchmarkData.strategy_return)}
                      </p>
                    </div>
                    {getPerformanceIcon(benchmarkData.strategy_return)}
                  </div>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Benchmark Return</p>
                      <p className={`text-2xl font-bold ${getPerformanceColor(benchmarkData.benchmark_return)}`}>
                        {formatPercentage(benchmarkData.benchmark_return)}
                      </p>
                    </div>
                    {getPerformanceIcon(benchmarkData.benchmark_return)}
                  </div>
                </div>

                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Excess Return</p>
                      <p className={`text-2xl font-bold ${getPerformanceColor(benchmarkData.excess_return)}`}>
                        {formatPercentage(benchmarkData.excess_return)}
                      </p>
                    </div>
                    <Target className="h-6 w-6 text-green-600" />
                  </div>
                </div>
              </div>

              {/* Risk-Adjusted Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div className="text-center p-4 border rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Information Ratio</p>
                  <p className="text-xl font-semibold">{formatNumber(benchmarkData.information_ratio)}</p>
                  <Badge variant={benchmarkData.information_ratio > 0.5 ? "default" : "secondary"} className="mt-1">
                    {benchmarkData.information_ratio > 0.5 ? "Good" : "Poor"}
                  </Badge>
                </div>

                <div className="text-center p-4 border rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Tracking Error</p>
                  <p className="text-xl font-semibold">{formatPercentage(benchmarkData.tracking_error)}</p>
                  <Badge variant={benchmarkData.tracking_error < 10 ? "default" : "destructive"} className="mt-1">
                    {benchmarkData.tracking_error < 10 ? "Low" : "High"}
                  </Badge>
                </div>

                <div className="text-center p-4 border rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Beta</p>
                  <p className="text-xl font-semibold">{formatNumber(benchmarkData.beta)}</p>
                  <Badge variant="outline" className="mt-1">
                    {benchmarkData.beta > 1 ? "High Risk" : "Low Risk"}
                  </Badge>
                </div>

                <div className="text-center p-4 border rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Alpha</p>
                  <p className={`text-xl font-semibold ${getPerformanceColor(benchmarkData.alpha)}`}>
                    {formatPercentage(benchmarkData.alpha)}
                  </p>
                  <Badge variant={benchmarkData.alpha > 0 ? "default" : "secondary"} className="mt-1">
                    {benchmarkData.alpha > 0 ? "Outperform" : "Underperform"}
                  </Badge>
                </div>
              </div>

              {/* Correlation and Drawdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div className="p-4 border rounded-lg">
                  <h4 className="font-semibold mb-3">Correlation Analysis</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Correlation with {benchmarkData.benchmark_name}</span>
                      <span className="font-medium">{formatNumber(benchmarkData.correlation)}</span>
                    </div>
                    <Progress value={Math.abs(benchmarkData.correlation) * 100} className="h-2" />
                    <p className="text-xs text-gray-600">
                      {Math.abs(benchmarkData.correlation) > 0.7 ? "High correlation" : 
                       Math.abs(benchmarkData.correlation) > 0.3 ? "Moderate correlation" : "Low correlation"}
                    </p>
                  </div>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-semibold mb-3">Drawdown Comparison</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Strategy Max Drawdown</span>
                      <span className={`font-medium ${getPerformanceColor(-benchmarkData.strategy_max_drawdown)}`}>
                        {formatPercentage(-benchmarkData.strategy_max_drawdown)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Benchmark Max Drawdown</span>
                      <span className={`font-medium ${getPerformanceColor(-benchmarkData.benchmark_max_drawdown)}`}>
                        {formatPercentage(-benchmarkData.benchmark_max_drawdown)}
                      </span>
                    </div>
                    <Badge variant={benchmarkData.strategy_max_drawdown < benchmarkData.benchmark_max_drawdown ? "default" : "destructive"}>
                      {benchmarkData.strategy_max_drawdown < benchmarkData.benchmark_max_drawdown ? "Better Risk Control" : "Higher Risk"}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Performance Chart */}
              {benchmarkData.relative_performance && benchmarkData.relative_performance.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Activity className="h-5 w-5" />
                      Relative Performance Over Time
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={400}>
                      <LineChart data={benchmarkData.relative_performance}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="timestamp" 
                          tick={{ fontSize: 12 }}
                          angle={-45}
                          textAnchor="end"
                          height={80}
                        />
                        <YAxis tick={{ fontSize: 12 }} />
                        <Tooltip 
                          formatter={(value: number, name: string) => [
                            `${formatPercentage(value)}`,
                            name === 'strategy_return' ? 'Strategy' : 
                            name === 'benchmark_return' ? 'Benchmark' : 'Relative'
                          ]}
                          labelFormatter={(label) => new Date(label).toLocaleDateString()}
                        />
                        <Legend />
                        <Line 
                          type="monotone" 
                          dataKey="strategy_return" 
                          stroke="#2563eb" 
                          strokeWidth={2}
                          name="Strategy Return"
                          dot={false}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="benchmark_return" 
                          stroke="#64748b" 
                          strokeWidth={2}
                          name="Benchmark Return"
                          dot={false}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="relative_return" 
                          stroke="#16a34a" 
                          strokeWidth={2}
                          name="Relative Performance"
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}; 