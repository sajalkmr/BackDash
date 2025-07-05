import React, { useEffect, useState } from 'react';
import { strategySocket } from '../services/websocket';

interface StrategyMonitorProps {
  strategyId: string;
}

interface SignalUpdate {
  timestamp: string;
  entry_signal: boolean;
  exit_signal: boolean;
  indicators: Record<string, number>;
  current_price: number;
}

export function StrategyMonitor({ strategyId }: StrategyMonitorProps) {
  const [updates, setUpdates] = useState<SignalUpdate[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const connectWebSocket = async () => {
      try {
        await strategySocket.connect(`/strategy/${strategyId}`);
        setConnected(true);
        
        const unsubscribe = strategySocket.subscribe((data) => {
          setUpdates(prev => [...prev, data].slice(-10));
        });

        return () => {
          unsubscribe();
          strategySocket.disconnect();
          setConnected(false);
        };
      } catch (error) {
        console.error('WebSocket connection failed:', error);
        setConnected(false);
      }
    };

    connectWebSocket();
  }, [strategyId]);

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          Strategy Monitor
        </h3>
        <span className={`w-2 h-2 rounded-full ${
          connected ? 'bg-green-500' : 'bg-red-500'
        }`} />
      </div>

      <div className="space-y-4">
        {updates.map((update, index) => (
          <div
            key={index}
            className="p-3 bg-gray-50 rounded-lg"
          >
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>{new Date(update.timestamp).toLocaleTimeString()}</span>
              <span>${update.current_price.toFixed(2)}</span>
            </div>

            <div className="flex space-x-4">
              <div className={`px-2 py-1 rounded text-sm ${
                update.entry_signal
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                Entry Signal
              </div>
              <div className={`px-2 py-1 rounded text-sm ${
                update.exit_signal
                  ? 'bg-red-100 text-red-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                Exit Signal
              </div>
            </div>

            <div className="mt-2 grid grid-cols-2 gap-2">
              {Object.entries(update.indicators).map(([name, value]) => (
                <div
                  key={name}
                  className="text-sm text-gray-600"
                >
                  <span className="font-medium">{name}:</span>{' '}
                  {value.toFixed(4)}
                </div>
              ))}
            </div>
          </div>
        ))}

        {updates.length === 0 && (
          <div className="text-center text-gray-500 py-4">
            Waiting for updates...
          </div>
        )}
      </div>
    </div>
  );
} 