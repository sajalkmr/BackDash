import React from 'react';
import { TrendingUp, Settings, PlayCircle, RefreshCw } from 'lucide-react';

interface HeaderProps {
  onRunBacktest: () => void;
  onReset: () => void;
  isRunning: boolean;
}

export function Header({ onRunBacktest, onReset, isRunning }: HeaderProps) {
  return (
    <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-8 h-8 text-emerald-400" />
            <h1 className="text-2xl font-bold text-white">BacktestPro</h1>
          </div>
          <div className="text-slate-400 text-sm ml-4">
            Advanced Trading Strategy Platform
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={onReset}
            disabled={isRunning}
            className="flex items-center space-x-2 bg-slate-600 hover:bg-slate-500 disabled:bg-slate-700 disabled:text-slate-500 text-white px-6 py-2 rounded-lg font-medium transition-colors duration-200"
          >
            <RefreshCw className="w-5 h-5" />
            <span>Reset</span>
          </button>
          <button
            onClick={onRunBacktest}
            disabled={isRunning}
            className="flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 disabled:from-slate-600 disabled:to-slate-700 text-white px-6 py-2 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl"
          >
            <PlayCircle className="w-5 h-5" />
            <span>{isRunning ? 'Running...' : 'Run Backtest'}</span>
          </button>
          
          <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors duration-200">
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  );
}