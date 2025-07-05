import React from 'react';
import { DraggableTool } from './DraggableTool';
import { AVAILABLE_INDICATORS } from '../../types';
import { TrendingUp } from 'lucide-react';

export function Toolbox() {
  return (
    <div className="bg-slate-800/50 p-5 rounded-lg border border-slate-700">
      <h2 className="text-xl font-bold text-white mb-6">Toolbox</h2>
      <div className="space-y-6">
        <div>
          <div className="flex items-center space-x-2 mb-3">
            <TrendingUp size={18} className="text-teal-400" />
            <h3 className="text-slate-300 font-semibold">Technical Indicators</h3>
          </div>
          <div className="space-y-2 pl-1">
            {AVAILABLE_INDICATORS.map(ind => (
              <DraggableTool key={ind} id={`tool-indicator-${ind}`} data={{ type: 'indicator', indicator: ind }}>
                <div className="bg-slate-700 p-2.5 rounded-md text-sm text-white hover:bg-slate-600 transition-colors">
                  {ind}
                </div>
              </DraggableTool>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
} 