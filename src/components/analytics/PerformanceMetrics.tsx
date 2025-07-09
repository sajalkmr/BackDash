import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  TrendingUp, TrendingDown, Activity, BarChart3, PieChart, 
  Target, Shield, Zap, AlertTriangle, RefreshCw, Download
} from 'lucide-react';
import { BenchmarkComparison } from './BenchmarkComparison';
import { MultiStrategyComparison } from './MultiStrategyComparison';
import { ExportAnalytics } from './ExportAnalytics';

interface AnalyticsData {
  performance: {
    core_metrics: {
      pnl_percent: number;
      pnl_dollars: number;
      cagr_percent: number;
      sharpe_ratio: number;
      sortino_ratio: number;
      calmar_ratio: number;
      max_drawdown_percent: number;
      max_drawdown_dollars: number;
      volatility_percent: number;
    };
    trading_metrics: {
      total_trades: number;
      win_rate_percent: number;
      avg_trade_duration_hours: number;
      largest_win_percent: number;
      largest_loss_percent: number;
      profit_factor: number;
      expectancy: number;
      max_consecutive_wins: number;
      max_consecutive_losses: number;
    };
    risk_metrics: {
      value_at_risk_95: number;
      value_at_risk_99: number;
      conditional_var_95: number;
      conditional_var_99: number;
      downside_deviation: number;
      omega_ratio: number;
      gain_pain_ratio: number;
    };
  };
  benchmark_comparison?: {
    benchmark_symbol: string;
    excess_return: number;
    information_ratio: number;
    correlation: number;
    alpha: number;
    beta: number;
  };
}

interface PerformanceMetricsProps {
  backtestId: string | null;
  availableStrategies?: Array<{
    id: string;
    name: string;
    status: 'completed' | 'running' | 'failed';
  }>;
}

export function PerformanceMetrics({ backtestId, availableStrategies = [] }: PerformanceMetricsProps) {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchAnalytics = async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      // First try to get existing analytics
      let analyticsResponse = await fetch(`/api/v1/analytics/get/${id}`);
      
      if (!analyticsResponse.ok) {
        // If not found, generate new analytics
        const generateResponse = await fetch(`/api/v1/analytics/generate/${id}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            benchmark_symbol: 'BTC-USDT',
            include_benchmark: true,
            include_rolling_metrics: true
          })
        });
        
        if (!generateResponse.ok) {
          throw new Error('Failed to generate analytics');
        }
        
        const generateData = await generateResponse.json();
        setAnalyticsData(generateData.analytics);
      } else {
        const data = await analyticsResponse.json();
        setAnalyticsData(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (backtestId) {
      fetchAnalytics(backtestId);
    }
  }, [backtestId]);

  const formatPercentage = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  const formatCurrency = (value: number) => `$${value.toLocaleString()}`;
  const formatNumber = (value: number, decimals: number = 2) => value.toFixed(decimals);

  const getPerformanceColor = (value: number, isInverse: boolean = false) => {
    const positive = isInverse ? value < 0 : value > 0;
    if (positive) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getPerformanceIcon = (value: number) => {
    return value >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />;
  };

  if (!backtestId) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Performance Analytics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Activity className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 text-lg mb-2">No Backtest Selected</p>
            <p className="text-gray-500">Run a backtest to see comprehensive performance analytics.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Performance Analytics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading analytics...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            Analytics Error
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <AlertTriangle className="h-16 w-16 text-red-400 mx-auto mb-4" />
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={() => fetchAnalytics(backtestId)} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!analyticsData) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Performance Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <p className="text-gray-600">No analytics data available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Performance Analytics
            </span>
            <Badge variant="outline">Enhanced Analytics v2.0</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-6">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="risk">Risk</TabsTrigger>
              <TabsTrigger value="trading">Trading</TabsTrigger>
              <TabsTrigger value="benchmark">Benchmark</TabsTrigger>
              <TabsTrigger value="compare">Compare</TabsTrigger>
              <TabsTrigger value="export">Export</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6 mt-6">
              {/* Core Performance Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Total Return</p>
                      <p className={`text-3xl font-bold ${getPerformanceColor(analyticsData.performance.core_metrics.pnl_percent)}`}>
                        {formatPercentage(analyticsData.performance.core_metrics.pnl_percent)}
                      </p>
                      <p className="text-sm text-gray-600">
                        {formatCurrency(analyticsData.performance.core_metrics.pnl_dollars)}
                      </p>
                    </div>
                    {getPerformanceIcon(analyticsData.performance.core_metrics.pnl_percent)}
                  </div>
                </div>

                <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Sharpe Ratio</p>
                      <p className={`text-3xl font-bold ${getPerformanceColor(analyticsData.performance.core_metrics.sharpe_ratio)}`}>
                        {formatNumber(analyticsData.performance.core_metrics.sharpe_ratio)}
                      </p>
                      <p className="text-sm text-gray-600">Risk-adjusted return</p>
                    </div>
                    <Zap className="h-8 w-8 text-blue-600" />
                  </div>
                </div>

                <div className="bg-gradient-to-br from-red-50 to-red-100 p-6 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Max Drawdown</p>
                      <p className={`text-3xl font-bold ${getPerformanceColor(analyticsData.performance.core_metrics.max_drawdown_percent, true)}`}>
                        {formatPercentage(analyticsData.performance.core_metrics.max_drawdown_percent)}
                      </p>
                      <p className="text-sm text-gray-600">
                        {formatCurrency(analyticsData.performance.core_metrics.max_drawdown_dollars)}
                      </p>
                    </div>
                    <Shield className="h-8 w-8 text-red-600" />
                  </div>
                </div>
              </div>

              {/* Additional Core Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 border rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">CAGR</p>
                  <p className={`text-xl font-semibold ${getPerformanceColor(analyticsData.performance.core_metrics.cagr_percent)}`}>
                    {formatPercentage(analyticsData.performance.core_metrics.cagr_percent)}
                  </p>
                </div>

                <div className="text-center p-4 border rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Sortino Ratio</p>
                  <p className={`text-xl font-semibold ${getPerformanceColor(analyticsData.performance.core_metrics.sortino_ratio)}`}>
                    {formatNumber(analyticsData.performance.core_metrics.sortino_ratio)}
                  </p>
                </div>

                <div className="text-center p-4 border rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Calmar Ratio</p>
                  <p className={`text-xl font-semibold ${getPerformanceColor(analyticsData.performance.core_metrics.calmar_ratio)}`}>
                    {formatNumber(analyticsData.performance.core_metrics.calmar_ratio)}
                  </p>
                </div>

                <div className="text-center p-4 border rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Volatility</p>
                  <p className="text-xl font-semibold text-gray-700">
                    {formatPercentage(analyticsData.performance.core_metrics.volatility_percent)}
                  </p>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="risk" className="space-y-6 mt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="p-4 border rounded-lg">
                  <h4 className="font-semibold mb-3 text-red-600">Value at Risk</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">VaR (95%)</span>
                      <span className="font-medium text-red-600">
                        {formatPercentage(analyticsData.performance.risk_metrics.value_at_risk_95)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">VaR (99%)</span>
                      <span className="font-medium text-red-600">
                        {formatPercentage(analyticsData.performance.risk_metrics.value_at_risk_99)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-semibold mb-3 text-purple-600">Conditional VaR</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">CVaR (95%)</span>
                      <span className="font-medium text-purple-600">
                        {formatPercentage(analyticsData.performance.risk_metrics.conditional_var_95)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">CVaR (99%)</span>
                      <span className="font-medium text-purple-600">
                        {formatPercentage(analyticsData.performance.risk_metrics.conditional_var_99)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-semibold mb-3 text-blue-600">Risk Ratios</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Omega Ratio</span>
                      <span className="font-medium">
                        {formatNumber(analyticsData.performance.risk_metrics.omega_ratio)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Gain/Pain Ratio</span>
                      <span className="font-medium">
                        {formatNumber(analyticsData.performance.risk_metrics.gain_pain_ratio)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="trading" className="space-y-6 mt-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 border rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Total Trades</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {analyticsData.performance.trading_metrics.total_trades}
                  </p>
                </div>

                <div className="text-center p-4 border rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Win Rate</p>
                  <p className={`text-2xl font-bold ${getPerformanceColor(analyticsData.performance.trading_metrics.win_rate_percent - 50)}`}>
                    {formatPercentage(analyticsData.performance.trading_metrics.win_rate_percent)}
                  </p>
                </div>

                <div className="text-center p-4 border rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Profit Factor</p>
                  <p className={`text-2xl font-bold ${getPerformanceColor(analyticsData.performance.trading_metrics.profit_factor - 1)}`}>
                    {formatNumber(analyticsData.performance.trading_metrics.profit_factor)}
                  </p>
                </div>

                <div className="text-center p-4 border rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Expectancy</p>
                  <p className={`text-2xl font-bold ${getPerformanceColor(analyticsData.performance.trading_metrics.expectancy)}`}>
                    {formatNumber(analyticsData.performance.trading_metrics.expectancy, 4)}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 border rounded-lg">
                  <h4 className="font-semibold mb-3">Trade Performance</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Largest Win</span>
                      <span className={`font-medium ${getPerformanceColor(analyticsData.performance.trading_metrics.largest_win_percent)}`}>
                        {formatPercentage(analyticsData.performance.trading_metrics.largest_win_percent)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Largest Loss</span>
                      <span className={`font-medium ${getPerformanceColor(analyticsData.performance.trading_metrics.largest_loss_percent)}`}>
                        {formatPercentage(analyticsData.performance.trading_metrics.largest_loss_percent)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Avg Trade Duration</span>
                      <span className="font-medium">
                        {formatNumber(analyticsData.performance.trading_metrics.avg_trade_duration_hours)} hrs
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-semibold mb-3">Consecutive Trades</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Max Consecutive Wins</span>
                      <span className="font-medium text-green-600">
                        {analyticsData.performance.trading_metrics.max_consecutive_wins}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Max Consecutive Losses</span>
                      <span className="font-medium text-red-600">
                        {analyticsData.performance.trading_metrics.max_consecutive_losses}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="benchmark" className="mt-6">
              <BenchmarkComparison backtestId={backtestId} />
            </TabsContent>

            <TabsContent value="compare" className="mt-6">
              <MultiStrategyComparison availableStrategies={availableStrategies} />
            </TabsContent>

            <TabsContent value="export" className="mt-6">
              <ExportAnalytics backtestId={backtestId} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}