import React from 'react';
import { Strategy, AVAILABLE_ASSETS, RiskManagement } from '../../types';
import { ConditionBlock } from './ConditionBlock';
import { RiskManagement as RiskManagementComponent } from './RiskManagement';
import { DroppableArea } from './DroppableArea';

interface CanvasProps {
  strategy: Strategy;
  setStrategy: React.Dispatch<React.SetStateAction<Strategy>>;
}

export function Canvas({ strategy, setStrategy }: CanvasProps) {
  
  const setEntryConditions = (updater: React.SetStateAction<Strategy['entryConditions']>) => {
    setStrategy(prev => ({ ...prev, entryConditions: typeof updater === 'function' ? updater(prev.entryConditions) : updater }));
  };

  const setExitConditions = (updater: React.SetStateAction<Strategy['exitConditions']>) => {
    setStrategy(prev => ({ ...prev, exitConditions: typeof updater === 'function' ? updater(prev.exitConditions) : updater }));
  };

  const handleRiskUpdate = (field: keyof RiskManagement, value: number) => {
    setStrategy(prev => ({ 
      ...prev, 
      riskManagement: {
        ...prev.riskManagement,
        [field]: value
      } 
    }));
  };
  
  const handleMetaUpdate = (field: string, value: string) => {
    setStrategy(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="bg-slate-800/50 p-5 rounded-lg border border-slate-700 flex-grow space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4 bg-slate-900/50 rounded-lg">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Strategy Name</label>
              <input
                type="text"
                value={strategy.name}
                onChange={(e) => handleMetaUpdate('name', e.target.value)}
                className="bg-slate-800 text-white border border-slate-700 rounded-md px-3 py-2 w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Asset</label>
              <select
                value={strategy.asset}
                onChange={(e) => handleMetaUpdate('asset', e.target.value)}
                className="bg-slate-800 text-white border border-slate-700 rounded-md px-3 py-2 w-full"
              >
                {AVAILABLE_ASSETS.map(asset => <option key={asset} value={asset}>{asset}</option>)}
              </select>
            </div>
        </div>

        <DroppableArea id="entry-conditions">
            <ConditionBlock 
                title="Entry Conditions" 
                borderColor="border-teal-500"
                conditions={strategy.entryConditions}
                setConditions={setEntryConditions}
            />
        </DroppableArea>
        <DroppableArea id="exit-conditions">
            <ConditionBlock 
                title="Exit Conditions" 
                borderColor="border-red-500"
                conditions={strategy.exitConditions}
                setConditions={setExitConditions}
            />
        </DroppableArea>
        
        <RiskManagementComponent
            settings={strategy.riskManagement}
            onUpdate={handleRiskUpdate}
        />
    </div>
  );
} 