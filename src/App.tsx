import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { StrategyBuilder } from './components/strategy/StrategyBuilder';
import { PerformanceMetrics } from './components/analytics/PerformanceMetrics';
import { EquityChart } from './components/analytics/EquityChart';
import { TradesList } from './components/analytics/TradesList';
import { PriceChart } from './components/analytics/PriceChart';
import { Strategy, BacktestResult, OHLCVData } from './types/index';
import { getDefaultData, loadTickerData } from './data/realDataLoader';
import { mockOHLCVData } from './data/mockData';
import { runBacktest } from './utils/backtestEngine';
import { ReturnHeatmap } from './components/analytics/ReturnHeatmap';
import { PnlDistribution } from './components/analytics/PnlDistribution';
import { RiskVisuals } from './components/analytics/RiskVisuals';
import { BenchmarkComparison } from './components/analytics/BenchmarkComparison';
import { LoadingSpinner } from './components/LoadingSpinner';
import { getDataSummary } from './utils/chartDataOptimizer';

function App() {
  const [strategy, setStrategy] = useState<Strategy>({
    id: 'strategy_1',
    name: 'EMA Crossover Strategy',
    asset: 'AAPL',
    entryConditions: [
      {
        id: 'entry_1',
        indicator: 'EMA_20',
        operator: '>' as const,
        value: 0
      }
    ],
    exitConditions: [
      {
        id: 'exit_1',
        indicator: 'RSI',
        operator: '>' as const,
        value: 70
      }
    ],
    riskManagement: {
      stopLoss: 5,
      takeProfit: 10,
      positionSize: 100
    },
    indicators: []
  });

  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [currentData, setCurrentData] = useState<OHLCVData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingAsset, setIsLoadingAsset] = useState(false);
  const [dataSource, setDataSource] = useState<'real' | 'mock'>('real');
  const [loadingMessage, setLoadingMessage] = useState('Loading data...');
  const [dataInfo, setDataInfo] = useState<{ totalPoints: number; dateRange: { start: Date; end: Date } } | null>(null);

  useEffect(() => {
    const loadData = async () => {
      const startTime = performance.now();
      try {
        setLoadingMessage('Loading real data...');
        const data = await getDefaultData();
        
        if (data.length > 0) {
          setCurrentData(data);
          setDataSource('real');
          
          const summary = getDataSummary(data);
          setDataInfo({
            totalPoints: summary.totalPoints,
            dateRange: summary.dateRange
          });
        } else {
          setLoadingMessage('Loading mock data...');
          setCurrentData(mockOHLCVData);
          setDataSource('mock');
          
          const summary = getDataSummary(mockOHLCVData);
          setDataInfo({
            totalPoints: summary.totalPoints,
            dateRange: summary.dateRange
          });
        }
      } catch (error) {
        setLoadingMessage('Loading mock data...');
        setCurrentData(mockOHLCVData);
        setDataSource('mock');
        
        const summary = getDataSummary(mockOHLCVData);
        setDataInfo({
          totalPoints: summary.totalPoints,
          dateRange: summary.dateRange
        });
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
  }, []);

  const handleStrategyChange = useCallback(async (newStrategy: any) => {
    const updatedStrategy = {
      id: strategy.id,
      name: newStrategy.name,
      asset: newStrategy.asset,
      entryConditions: newStrategy.entryConditions,
      exitConditions: newStrategy.exitConditions,
      riskManagement: newStrategy.riskManagement,
      indicators: strategy.indicators
    };
    
    setStrategy(updatedStrategy);
    
    if (newStrategy.asset !== strategy.asset) {
      setIsLoadingAsset(true);
      try {
        if (dataSource === 'real') {
          setLoadingMessage(`Loading data for ${newStrategy.asset}...`);
          const data = await loadTickerData(newStrategy.asset);
          if (data.length > 0) {
            setCurrentData(data);
            
            const summary = getDataSummary(data);
            setDataInfo({
              totalPoints: summary.totalPoints,
              dateRange: summary.dateRange
            });
          } else {
            setCurrentData(mockOHLCVData);
            setDataSource('mock');
            
            const summary = getDataSummary(mockOHLCVData);
            setDataInfo({
              totalPoints: summary.totalPoints,
              dateRange: summary.dateRange
            });
          }
        } else {
          setCurrentData(mockOHLCVData);
          
          const summary = getDataSummary(mockOHLCVData);
          setDataInfo({
            totalPoints: summary.totalPoints,
            dateRange: summary.dateRange
          });
        }
      } catch (error) {
        setCurrentData(mockOHLCVData);
        setDataSource('mock');
        
        const summary = getDataSummary(mockOHLCVData);
        setDataInfo({
          totalPoints: summary.totalPoints,
          dateRange: summary.dateRange
        });
      } finally {
        setIsLoadingAsset(false);
      }
    }
  }, [strategy.asset, strategy.id, strategy.indicators, dataSource]);

  const handleRunBacktest = useCallback(async () => {
    if (currentData.length === 0) return;
    
    setIsRunning(true);
    
    try {
      await new Promise(resolve => setTimeout(resolve, 10));
      const result = runBacktest(currentData, strategy);
      setBacktestResult(result);
    } catch (error) {
      console.error('Backtest failed:', error);
    } finally {
      setIsRunning(false);
    }
  }, [currentData, strategy]);

  const handleReset = useCallback(() => {
    setBacktestResult(null);
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <LoadingSpinner message={loadingMessage} size="large" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      <Header onRunBacktest={handleRunBacktest} onReset={handleReset} isRunning={isRunning} />
      
      <div className="container mx-auto px-6 pt-2">
        <div className="flex items-center gap-4">
          <div className={`text-sm px-3 py-1 rounded-full inline-block ${
            dataSource === 'real' ? 'bg-green-600 text-white' : 'bg-yellow-600 text-white'
          }`}>
            Using {dataSource === 'real' ? 'Real' : 'Mock'} Data
            {isLoadingAsset && (
              <span className="ml-2">
                <LoadingSpinner size="small" />
              </span>
            )}
          </div>
          
          {dataInfo && (
            <div className="text-sm text-slate-400">
              {dataInfo.totalPoints.toLocaleString()} data points • 
              {dataInfo.dateRange.start.toLocaleDateString()} - {dataInfo.dateRange.end.toLocaleDateString()}
            </div>
          )}
        </div>
      </div>
      
      <div className="container mx-auto px-6 py-6 space-y-6">
        <StrategyBuilder onStrategyChange={handleStrategyChange} />
        
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <PriceChart data={currentData} result={backtestResult} />
          <EquityChart result={backtestResult} />
        </div>
        
        <PerformanceMetrics result={backtestResult} />
        
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <ReturnHeatmap result={backtestResult} />
          <PnlDistribution result={backtestResult} />
          <RiskVisuals result={backtestResult} />
          <BenchmarkComparison result={backtestResult} />
        </div>
        
        <TradesList result={backtestResult} />
      </div>
    </div>
  );
}

export default App;