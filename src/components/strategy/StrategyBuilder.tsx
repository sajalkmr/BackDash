import React, { useState, useEffect } from 'react';
import { DndContext, DragEndEvent } from '@dnd-kit/core';
import { Strategy, Condition } from '../../types';
import { Toolbox } from './Toolbox';
import { Canvas } from './Canvas';

interface StrategyBuilderProps {
  onStrategyChange: (strategy: Strategy) => void;
}

const initialStrategy: Strategy = {
  name: 'EMA Crossover Strategy',
  asset: 'AAPL',
  entryConditions: [
    { id: '1', indicator: 'EMA (20)', operator: '>', value: 0 }
  ],
  exitConditions: [
    { id: '2', indicator: 'RSI (14)', operator: '>', value: 70 }
  ],
  riskManagement: {
    stopLoss: 5,
    takeProfit: 10,
    positionSize: 100,
  }
};

export function StrategyBuilder({ onStrategyChange }: StrategyBuilderProps) {
  const [strategy, setStrategy] = useState<Strategy>(initialStrategy);

  useEffect(() => {
    onStrategyChange(strategy);
  }, [strategy, onStrategyChange]);

  const handleDragEnd = (event: DragEndEvent) => {
    const { over, active } = event;
    if (!over) return;

    const toolData = active.data.current;

    if (toolData?.['type'] === 'indicator') {
      const newCondition: Condition = {
        id: Date.now().toString(),
        indicator: toolData['indicator'],
        operator: '>',
        value: 0
      };
      if (over.id === 'entry-conditions') {
        setStrategy(s => ({ ...s, entryConditions: [...s.entryConditions, newCondition] }));
      } else if (over.id === 'exit-conditions') {
        setStrategy(s => ({ ...s, exitConditions: [...s.exitConditions, newCondition] }));
      }
    }
  };

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div className="bg-slate-900 min-h-screen p-8 text-white">
        <div className="max-w-8xl mx-auto">
          <header className="mb-8">
            <h1 className="text-3xl font-bold">Strategy Builder</h1>
            <p className="text-slate-400">Drag tools from the toolbox to the canvas to build your strategy.</p>
          </header>

          <div className="flex flex-col lg:flex-row gap-8">
            <div className="lg:w-1/4">
              <Toolbox />
            </div>
            <div className="lg:w-3/4">
              <Canvas strategy={strategy} setStrategy={setStrategy} />
            </div>
          </div>
        </div>
      </div>
    </DndContext>
  );
} 