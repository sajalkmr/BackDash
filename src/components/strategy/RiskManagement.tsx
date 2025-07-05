import React from 'react';
import { RiskManagement as RiskManagementType } from '../../types';

interface RiskManagementProps {
  settings: RiskManagementType;
  onUpdate: (field: keyof RiskManagementType, value: number) => void;
}

interface InputFieldProps {
  label: string;
  value: number;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

function InputField({ label, value, onChange }: InputFieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-400 mb-2">{label}</label>
      <input
        type="number"
        value={value}
        onChange={onChange}
        className="bg-slate-800 text-white border border-slate-700 rounded-md px-3 py-2 w-full"
      />
    </div>
  );
}

export function RiskManagement({ settings, onUpdate }: RiskManagementProps) {
  return (
    <div className="bg-slate-800/50 rounded-lg p-5 border-t-4 border-yellow-500">
      <h3 className="text-xl font-bold text-white mb-4">Risk Management</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <InputField 
          label="Stop Loss (%)"
          value={settings.stopLoss}
          onChange={(e) => onUpdate('stopLoss', parseFloat(e.target.value) || 0)}
        />
        <InputField 
          label="Take Profit (%)"
          value={settings.takeProfit}
          onChange={(e) => onUpdate('takeProfit', parseFloat(e.target.value) || 0)}
        />
        <InputField 
          label="Position Size"
          value={settings.positionSize}
          onChange={(e) => onUpdate('positionSize', parseFloat(e.target.value) || 0)}
        />
      </div>
    </div>
  );
} 