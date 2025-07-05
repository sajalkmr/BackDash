import { OHLCVData } from '../types';

// Available tickers from the CSV file
export const AVAILABLE_TICKERS = [
  'AAPL', 'AXP', 'BA', 'CAT', 'CSCO', 'CVX', 'DIS', 'DWDP', 'GE', 'GS',
  'HD', 'IBM', 'INTC', 'JNJ', 'JPM', 'KO', 'MCD', 'MMM', 'MRK', 'MSFT',
  'NKE', 'PFE', 'PG', 'TRV', 'UNH', 'UTX', 'V', 'VZ', 'WMT', 'XOM'
];

// Cache for parsed CSV data
let csvCache: { text: string; timestamp: number } | null = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

// Cache for parsed ticker data
const tickerDataCache = new Map<string, { data: OHLCVData[]; timestamp: number }>();
const TICKER_CACHE_DURATION = 10 * 60 * 1000; // 10 minutes

// Optimized CSV parsing with better performance
function parseTickerDataOptimized(csvText: string, ticker: string): OHLCVData[] {
  const lines = csvText.split('\n');
  if (lines.length < 3) return [];
  
  // Second row contains ticker symbols - find the starting index
  const tickerRow = lines[1]?.split(',') || [];
  let tickerStartIndex = -1;
  
  // Use a more efficient search
  for (let i = 0; i < tickerRow.length; i++) {
    if (tickerRow[i] === ticker) {
      tickerStartIndex = i;
      break;
    }
  }
  
  if (tickerStartIndex === -1) {
    console.warn(`No data found for ticker: ${ticker}`);
    return [];
  }
  
  // Each ticker has 5 columns: Close, High, Low, Open, Volume
  const tickerIndices = {
    close: tickerStartIndex,
    high: tickerStartIndex + 1,
    low: tickerStartIndex + 2,
    open: tickerStartIndex + 3,
    volume: tickerStartIndex + 4
  };
  
  // Verify that we have all the required columns
  if (tickerIndices.volume >= tickerRow.length) {
    console.warn(`Insufficient columns for ticker: ${ticker}`);
    return [];
  }
  
  const data: OHLCVData[] = [];
  const maxIndex = tickerIndices.volume;
  
  // Pre-allocate array size for better performance (use all available data)
  const estimatedSize = Math.max(lines.length - 2, 1000);
  data.length = estimatedSize;
  let dataIndex = 0;
  
  // Parse data rows (starting from line 2) with optimized parsing
  for (let i = 2; i < lines.length; i++) {
    const line = lines[i];
    if (!line || line.length < 10) continue; // Skip empty or very short lines
    
    const values = line.split(',');
    if (values.length <= maxIndex) continue;
    
    const dateStr = values[0];
    const closeStr = values[tickerIndices.close];
    const highStr = values[tickerIndices.high];
    const lowStr = values[tickerIndices.low];
    const openStr = values[tickerIndices.open];
    const volumeStr = values[tickerIndices.volume];
    
    // Quick validation
    if (!dateStr || !closeStr || !highStr || !lowStr || !openStr || !volumeStr) {
      continue;
    }
    
    // Use Number() instead of parseFloat() for better performance
    const close = Number(closeStr);
    const high = Number(highStr);
    const low = Number(lowStr);
    const open = Number(openStr);
    const volume = Number(volumeStr);
    
    // Skip if any value is NaN or missing
    if (isNaN(close) || isNaN(high) || isNaN(low) || isNaN(open) || isNaN(volume)) {
      continue;
    }
    
    // Use Date.parse() for better performance
    const timestamp = Date.parse(dateStr);
    if (isNaN(timestamp)) continue;
    
    // Expand array if needed
    if (dataIndex >= data.length) {
      data.length = Math.min(data.length * 2, lines.length - 2);
    }
    
    data[dataIndex++] = {
      timestamp,
      open,
      high,
      low,
      close,
      volume
    };
  }
  
  // Trim the array to actual size
  data.length = dataIndex;
  
  return data;
}

// Get cached CSV data or fetch it
async function getCachedCSV(): Promise<string> {
  const now = Date.now();
  
  // Check if we have valid cached data
  if (csvCache && (now - csvCache.timestamp) < CACHE_DURATION) {
    return csvCache.text;
  }
  
  // Fetch new data
  const response = await fetch('/dow_jones_data.csv');
  const csvText = await response.text();
  
  // Cache the new data
  csvCache = { text: csvText, timestamp: now };
  
  return csvText;
}

// Load data for a specific ticker with caching
export async function loadTickerData(ticker: string): Promise<OHLCVData[]> {
  const now = Date.now();
  
  // Check cache first
  const cached = tickerDataCache.get(ticker);
  if (cached && (now - cached.timestamp) < TICKER_CACHE_DURATION) {
    return cached.data;
  }
  
  try {
    const csvText = await getCachedCSV();
    const data = parseTickerDataOptimized(csvText, ticker);
    
    // Cache the parsed data
    tickerDataCache.set(ticker, { data, timestamp: now });
    
    return data;
  } catch (error) {
    console.error(`Error loading data for ${ticker}:`, error);
    return [];
  }
}

// Load data for multiple tickers with parallel processing
export async function loadMultipleTickerData(tickers: string[]): Promise<Record<string, OHLCVData[]>> {
  const result: Record<string, OHLCVData[]> = {};
  
  // Load data in parallel for better performance
  const promises = tickers.map(async (ticker) => {
    const data = await loadTickerData(ticker);
    return { ticker, data };
  });
  
  const results = await Promise.all(promises);
  
  for (const { ticker, data } of results) {
    result[ticker] = data;
  }
  
  return result;
}

// Get default data (AAPL) for immediate use
export async function getDefaultData(): Promise<OHLCVData[]> {
  return await loadTickerData('AAPL');
}

// Clear cache (useful for testing or memory management)
export function clearCache(): void {
  csvCache = null;
  tickerDataCache.clear();
} 