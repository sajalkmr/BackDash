import { OHLCVData } from '../types';

const indicatorCache = new Map<string, number[]>();
const CACHE_SIZE_LIMIT = 200;

function clearCacheIfNeeded(): void {
  if (indicatorCache.size > CACHE_SIZE_LIMIT) {
    const entries = Array.from(indicatorCache.entries());
    const toKeep = Math.floor(CACHE_SIZE_LIMIT * 0.7);
    indicatorCache.clear();
    entries.slice(-toKeep).forEach(([key, value]) => {
      indicatorCache.set(key, value);
    });
  }
}

export function calculateEMA(data: number[], period: number): number[] {
  const cacheKey = `EMA_${period}_${data.length}`;
  if (indicatorCache.has(cacheKey)) {
    return indicatorCache.get(cacheKey)!;
  }

  const ema: number[] = new Array(data.length);
  const multiplier = 2 / (period + 1);
  
  let sum = 0;
  for (let i = 0; i < period && i < data.length; i++) {
    sum += data[i]!;
  }
  ema[period - 1] = sum / period;
  
  for (let i = period; i < data.length; i++) {
    ema[i] = (data[i]! - ema[i - 1]!) * multiplier + ema[i - 1]!;
  }
  
  indicatorCache.set(cacheKey, ema);
  clearCacheIfNeeded();
  
  return ema;
}

export function calculateRSI(data: number[], period: number = 14): number[] {
  const cacheKey = `RSI_${period}_${data.length}`;
  if (indicatorCache.has(cacheKey)) {
    return indicatorCache.get(cacheKey)!;
  }

  const rsi: number[] = new Array(data.length);
  
  if (data.length < period + 1) {
    indicatorCache.set(cacheKey, rsi);
    return rsi;
  }
  
  const gains: number[] = new Array(data.length - 1);
  const losses: number[] = new Array(data.length - 1);
  
  for (let i = 1; i < data.length; i++) {
    const change = data[i]! - data[i - 1]!;
    gains[i - 1] = change > 0 ? change : 0;
    losses[i - 1] = change < 0 ? Math.abs(change) : 0;
  }
  
  let avgGain = 0;
  let avgLoss = 0;
  
  for (let i = 0; i < period; i++) {
    avgGain += gains[i]!;
    avgLoss += losses[i]!;
  }
  
  avgGain /= period;
  avgLoss /= period;
  
  for (let i = period; i < data.length; i++) {
    if (i > period) {
      avgGain = (avgGain * (period - 1) + gains[i - 1]!) / period;
      avgLoss = (avgLoss * (period - 1) + losses[i - 1]!) / period;
    }
    
    const rs = avgGain / (avgLoss || 1);
    rsi[i] = 100 - (100 / (1 + rs));
  }
  
  indicatorCache.set(cacheKey, rsi);
  clearCacheIfNeeded();
  
  return rsi;
}

export function calculateMACD(data: number[], fastPeriod: number = 12, slowPeriod: number = 26, signalPeriod: number = 9) {
  const cacheKey = `MACD_${fastPeriod}_${slowPeriod}_${signalPeriod}_${data.length}`;
  if (indicatorCache.has(cacheKey)) {
    const cached = indicatorCache.get(cacheKey)!;
    const midPoint = Math.floor(cached.length / 3);
    return {
      macdLine: cached.slice(0, midPoint),
      signalLine: cached.slice(midPoint, midPoint * 2),
      histogram: cached.slice(midPoint * 2)
    };
  }

  const fastEMA = calculateEMA(data, fastPeriod);
  const slowEMA = calculateEMA(data, slowPeriod);
  
  const macdLine: number[] = new Array(data.length);
  const signalLine: number[] = new Array(data.length);
  const histogram: number[] = new Array(data.length);
  
  for (let i = 0; i < data.length; i++) {
    if (fastEMA[i] !== undefined && slowEMA[i] !== undefined) {
      macdLine[i] = fastEMA[i]! - slowEMA[i]!;
    }
  }
  
  const validMACD = macdLine.filter(v => v !== undefined);
  const signal = calculateEMA(validMACD, signalPeriod);
  let signalIndex = 0;
  
  for (let i = 0; i < macdLine.length; i++) {
    if (macdLine[i] !== undefined) {
      if (signal[signalIndex] !== undefined) {
        signalLine[i] = signal[signalIndex]!;
        histogram[i] = macdLine[i]! - signalLine[i]!;
      }
      signalIndex++;
    }
  }
  
  const combined = [...macdLine, ...signalLine, ...histogram];
  indicatorCache.set(cacheKey, combined);
  clearCacheIfNeeded();
  
  return { macdLine, signalLine, histogram };
}

const valueCache = new Map<string, number>();
const VALUE_CACHE_SIZE_LIMIT = 500;

function clearValueCacheIfNeeded(): void {
  if (valueCache.size > VALUE_CACHE_SIZE_LIMIT) {
    const entries = Array.from(valueCache.entries());
    const toKeep = Math.floor(VALUE_CACHE_SIZE_LIMIT * 0.7);
    valueCache.clear();
    entries.slice(-toKeep).forEach(([key, value]) => {
      valueCache.set(key, value);
    });
  }
}

export function getIndicatorValue(data: OHLCVData[], indicator: string, index: number): number {
  const cacheKey = `${indicator}_${index}_${data.length}`;
  
  if (valueCache.has(cacheKey)) {
    return valueCache.get(cacheKey)!;
  }

  let value = 0;
  const prices = data.slice(0, index + 1).map(d => d.close);
  const currentIndex = prices.length - 1;

  switch (indicator) {
    case 'EMA (20)':
      value = calculateEMA(prices, 20)[currentIndex] || 0;
      break;
    case 'RSI (14)':
      value = calculateRSI(prices, 14)[currentIndex] || 0;
      break;
    case 'MACD (12, 26, 9)':
      value = calculateMACD(prices).macdLine[currentIndex] || 0;
      break;
    case 'Bollinger Bands (20, 2)':
      value = 0;
      break;
    case 'Price':
      value = data[index]?.close || 0;
      break;
    default:
      if (indicator.startsWith('EMA_')) {
        const period = parseInt(indicator.split('_')[1] || '20');
        value = calculateEMA(prices, period)[currentIndex] || 0;
      } else {
        console.warn(`Unknown indicator: ${indicator}`);
        value = 0;
      }
  }
  
  valueCache.set(cacheKey, value);
  clearValueCacheIfNeeded();
  
  return value;
}

export function clearIndicatorCaches(): void {
  indicatorCache.clear();
  valueCache.clear();
}

export function calculateIndicator(data: OHLCVData[], type: string, period: number): number[] {
  switch (type.toLowerCase()) {
    case 'sma': return calculateSMA(data.map(d => d.close), period);
    case 'ema': return calculateEMA(data.map(d => d.close), period);
    case 'rsi': return calculateRSI(data.map(d => d.close), period);
    case 'macd': return calculateMACD(data.map(d => d.close));
    case 'bb': return calculateBollingerBands(data.map(d => d.close), period);
    default: return [];
  }
}

function calculateSMA(data: number[], period: number): number[] {
  const result = new Array(data.length).fill(0);
  
  for (let i = period - 1; i < data.length; i++) {
    let sum = 0;
    for (let j = 0; j < period; j++) {
      sum += data[i - j];
    }
    result[i] = sum / period;
  }
  
  return result;
}

function calculateBollingerBands(data: number[], period: number): number[] {
  const sma = calculateSMA(data, period);
  const result = new Array(data.length).fill(0);
  
  for (let i = period - 1; i < data.length; i++) {
    let sum = 0;
    for (let j = 0; j < period; j++) {
      sum += Math.pow(data[i - j] - sma[i], 2);
    }
    const std = Math.sqrt(sum / period);
    result[i] = std * 2;
  }
  
  return result;
}