import React, { useEffect, useState } from 'react';
import { backtestSocket } from '../services/websocket';
import { LoadingSpinner } from './LoadingSpinner';

interface BacktestProgressProps {
  taskId: string;
  onComplete?: (result: any) => void;
}

export function BacktestProgress({ taskId, onComplete }: BacktestProgressProps) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('pending');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const connectWebSocket = async () => {
      try {
        await backtestSocket.connect(`/backtest/${taskId}`);
        
        const unsubscribe = backtestSocket.subscribe((data) => {
          setProgress(data.progress);
          setStatus(data.status);
          setMessage(data.message);
          
          if (data.status === 'completed' && onComplete) {
            onComplete(data.result);
          }
        });

        return () => {
          unsubscribe();
          backtestSocket.disconnect();
        };
      } catch (error) {
        console.error('WebSocket connection failed:', error);
        setMessage('Connection failed. Retrying...');
      }
    };

    connectWebSocket();
  }, [taskId, onComplete]);

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          Backtest Progress
        </h3>
        <span className={`px-2 py-1 text-sm rounded-full ${
          status === 'completed' ? 'bg-green-100 text-green-800' :
          status === 'failed' ? 'bg-red-100 text-red-800' :
          'bg-blue-100 text-blue-800'
        }`}>
          {status}
        </span>
      </div>

      <div className="mb-4">
        <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
          <span>{message}</span>
          <span>{progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${
              status === 'completed' ? 'bg-green-500' :
              status === 'failed' ? 'bg-red-500' :
              'bg-blue-500'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {status === 'running' && (
        <div className="flex justify-center">
          <LoadingSpinner size="small" />
        </div>
      )}
    </div>
  );
} 