import { OHLCVData } from '../types';

// Generate realistic OHLCV data for AAPL
export function generateMockOHLCVData(): OHLCVData[] {
  const data: OHLCVData[] = [];
  const startDate = new Date('2020-01-01');
  const endDate = new Date('2024-01-01');
  let currentPrice = 150;
  
  for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
    // Skip weekends
    if (d.getDay() === 0 || d.getDay() === 6) continue;
    
    const volatility = 0.02;
    const drift = 0.0002;
    
    // Generate realistic price movement
    const randomFactor = (Math.random() - 0.5) * volatility;
    const trendFactor = drift + Math.sin(d.getTime() / (1000 * 60 * 60 * 24 * 365)) * 0.001;
    
    const open = currentPrice;
    const change = open * (trendFactor + randomFactor);
    const close = open + change;
    
    // Generate high and low based on intraday volatility
    const intradayVolatility = 0.01;
    const high = Math.max(open, close) + Math.random() * open * intradayVolatility;
    const low = Math.min(open, close) - Math.random() * open * intradayVolatility;
    
    // Generate volume (millions of shares)
    const volume = Math.floor(Math.random() * 50000000 + 20000000);
    
    data.push({
      timestamp: d.getTime(),
      open: Number(open.toFixed(2)),
      high: Number(high.toFixed(2)),
      low: Number(low.toFixed(2)),
      close: Number(close.toFixed(2)),
      volume
    });
    
    currentPrice = close;
  }
  
  return data;
}

export const mockOHLCVData = generateMockOHLCVData();