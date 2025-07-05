import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Header } from './components/Header';
import { StrategyBuilder } from './components/strategy/StrategyBuilder';
import { EquityChart } from './components/analytics/EquityChart';
import { PerformanceMetrics } from './components/analytics/PerformanceMetrics';
import { BenchmarkComparison } from './components/analytics/BenchmarkComparison';
import { RiskVisuals } from './components/analytics/RiskVisuals';
import { TradesList } from './components/analytics/TradesList';
import { BacktestProgress } from './components/BacktestProgress';
import { StrategyMonitor } from './components/StrategyMonitor';
import { BacktestResult } from './types';

function App() {
  const [activeBacktest, setActiveBacktest] = useState<string | null>(null);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [activeStrategy, setActiveStrategy] = useState<string | null>(null);

  const handleBacktestComplete = (result: BacktestResult) => {
    setBacktestResult(result);
    setActiveBacktest(null);
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-100">
        <Header title="BackDash" />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route 
              path="/" 
              element={
                <div className="space-y-8">
                  <StrategyBuilder
                    onStrategyStart={setActiveStrategy}
                    onBacktestStart={setActiveBacktest}
                  />
                  {activeBacktest && (
                    <BacktestProgress
                      taskId={activeBacktest}
                      onComplete={handleBacktestComplete}
                    />
                  )}
                  {activeStrategy && (
                    <StrategyMonitor
                      strategyId={activeStrategy}
                    />
                  )}
                </div>
              } 
            />
            <Route 
              path="/analytics" 
              element={
                <div className="space-y-8">
                  <EquityChart data={backtestResult?.equity_curve} />
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <PerformanceMetrics data={backtestResult?.metrics.performance} />
                    <BenchmarkComparison data={backtestResult?.metrics.benchmark} />
                  </div>
                  <RiskVisuals data={backtestResult?.metrics.risk} />
                  <TradesList trades={backtestResult?.trades} />
                </div>
              } 
            />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;