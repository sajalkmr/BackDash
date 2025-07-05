import { OHLCVData } from '../types';

// Optimize data for chart rendering while preserving all data for backtesting
export function optimizeDataForCharts(data: OHLCVData[], maxPoints: number = 1000): OHLCVData[] {
  if (data.length <= maxPoints) {
    return data;
  }

  const optimized: OHLCVData[] = [];
  const step = data.length / maxPoints;
  
  for (let i = 0; i < maxPoints; i++) {
    const index = Math.floor(i * step);
    optimized.push(data[index]!);
  }
  
  // Always include the last data point
  if (optimized[optimized.length - 1]?.timestamp !== data[data.length - 1]?.timestamp) {
    optimized.push(data[data.length - 1]!);
  }
  
  return optimized;
}

// Get data summary for performance metrics display
export function getDataSummary(data: OHLCVData[]): {
  totalPoints: number;
  dateRange: { start: Date; end: Date };
  priceRange: { min: number; max: number };
} {
  if (data.length === 0) {
    return {
      totalPoints: 0,
      dateRange: { start: new Date(), end: new Date() },
      priceRange: { min: 0, max: 0 }
    };
  }

  const prices = data.map(d => d.close);
  const timestamps = data.map(d => d.timestamp);
  
  return {
    totalPoints: data.length,
    dateRange: {
      start: new Date(Math.min(...timestamps)),
      end: new Date(Math.max(...timestamps))
    },
    priceRange: {
      min: Math.min(...prices),
      max: Math.max(...prices)
    }
  };
}

// Batch process data for better performance
export function processDataInBatches<T>(
  data: T[],
  batchSize: number,
  processor: (batch: T[]) => void
): void {
  for (let i = 0; i < data.length; i += batchSize) {
    const batch = data.slice(i, i + batchSize);
    processor(batch);
    
    // Allow UI to update between batches
    if (i % (batchSize * 10) === 0) {
      // Small delay every 10 batches to keep UI responsive
      setTimeout(() => {}, 0);
    }
  }
} 