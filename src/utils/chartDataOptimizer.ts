import { OHLCVData } from '../types';

export function optimizeChartData(data: OHLCVData[], maxPoints: number = 500): OHLCVData[] {
  if (data.length <= maxPoints) return data;
  
  const result: OHLCVData[] = [];
  const skipFactor = Math.ceil(data.length / maxPoints);
  
  for (let i = 0; i < data.length; i += skipFactor) {
    const chunk = data.slice(i, Math.min(i + skipFactor, data.length));
    
    if (chunk.length > 0) {
      result.push(chunk[0]);
    }
  }
  
  if (data.length > 0 && result[result.length - 1] !== data[data.length - 1]) {
    result.push(data[data.length - 1]);
  }
  
  return result;
}

export function getSummaryStats(data: OHLCVData[]) {
  if (!data || data.length === 0) {
    return {
      highestPrice: 0,
      lowestPrice: 0,
      averagePrice: 0,
      startPrice: 0,
      endPrice: 0,
      priceChange: 0,
      percentChange: 0,
      volatility: 0
    };
  }
  
  const prices = data.map(d => d.close);
  const highestPrice = Math.max(...prices);
  const lowestPrice = Math.min(...prices);
  const averagePrice = prices.reduce((a, b) => a + b, 0) / prices.length;
  const startPrice = prices[0];
  const endPrice = prices[prices.length - 1];
  const priceChange = endPrice - startPrice;
  const percentChange = (priceChange / startPrice) * 100;
  
  let sumSquaredDiff = 0;
  for (const price of prices) {
    sumSquaredDiff += Math.pow(price - averagePrice, 2);
  }
  const volatility = Math.sqrt(sumSquaredDiff / prices.length);
  
  return {
    highestPrice,
    lowestPrice,
    averagePrice,
    startPrice,
    endPrice,
    priceChange,
    percentChange,
    volatility
  };
}

export async function processDataInBatches<T, U>(
  data: T[],
  processFn: (items: T[]) => Promise<U[]>,
  batchSize = 1000
): Promise<U[]> {
  const results: U[] = [];
  
  for (let i = 0; i < data.length; i += batchSize) {
    const batch = data.slice(i, i + batchSize);
    const batchResults = await processFn(batch);
    results.push(...batchResults);
    
    if (i % (batchSize * 10) === 0 && i > 0) {
      await new Promise(resolve => setTimeout(resolve, 0));
    }
  }
  
  return results;
} 