import React from 'react';
import { GripVertical, Trash2 } from 'lucide-react';
import type { DraggableSyntheticListeners } from '@dnd-kit/core';
import { Condition, AVAILABLE_INDICATORS, AVAILABLE_OPERATORS } from '../../types';

interface ConditionRowProps {
  condition: Condition;
  onUpdate: (id: string, newCondition: Partial<Condition>) => void;
  onDelete: (id: string) => void;
  isDragging: boolean;
  index: number;
  dragHandleProps?: DraggableSyntheticListeners;
}

export function ConditionRow({ condition, onUpdate, onDelete, isDragging, index, dragHandleProps }: ConditionRowProps) {
  return (
    <div className={`flex items-center space-x-2 p-3 rounded-lg ${isDragging ? 'bg-slate-700' : 'bg-slate-900'}`}>
      <button {...dragHandleProps} className="text-slate-500 hover:text-white cursor-grab">
        <GripVertical size={20} />
      </button>
      <span className="text-slate-400 font-mono text-sm">#{index}</span>
      
      <select
        value={condition.indicator}
        onChange={(e) => onUpdate(condition.id, { indicator: e.target.value })}
        className="bg-slate-800 text-white border border-slate-700 rounded-md px-3 py-2 text-sm w-48"
      >
        {AVAILABLE_INDICATORS.map(ind => <option key={ind} value={ind}>{ind}</option>)}
      </select>
      
      <select
        value={condition.operator}
        onChange={(e) => onUpdate(condition.id, { operator: e.target.value })}
        className="bg-slate-800 text-white border border-slate-700 rounded-md px-3 py-2 text-sm"
      >
        {AVAILABLE_OPERATORS.map(op => <option key={op} value={op}>{op}</option>)}
      </select>
      
      <input
        type="number"
        value={condition.value}
        onChange={(e) => onUpdate(condition.id, { value: parseFloat(e.target.value) || 0 })}
        className="bg-slate-800 text-white border border-slate-700 rounded-md px-3 py-2 text-sm w-24"
      />
      
      <button 
        onClick={() => onDelete(condition.id)}
        className="text-slate-500 hover:text-red-500 ml-auto"
      >
        <Trash2 size={18} />
      </button>
    </div>
  );
} 