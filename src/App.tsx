import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Header } from './components/Header';
import { StrategyBuilder } from './components/strategy/StrategyBuilder';
import { EquityChart } from './components/analytics/EquityChart';
import { PerformanceMetrics } from './components/analytics/PerformanceMetrics';
import { BenchmarkComparison } from './components/analytics/BenchmarkComparison';
import { RiskVisuals } from './components/analytics/RiskVisuals';
import { TradesList } from './components/analytics/TradesList';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <Header title="BackDash" />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<StrategyBuilder />} />
            <Route path="/analytics" element={
              <div className="space-y-8">
                <EquityChart />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <PerformanceMetrics />
                  <BenchmarkComparison />
                </div>
                <RiskVisuals />
                <TradesList />
              </div>
            } />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;