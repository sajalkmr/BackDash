"""
Enhanced Analytics Engine - Phase 4 Implementation
Advanced performance metrics, benchmark comparison, and multi-strategy analysis
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
from scipy import stats
import uuid

from ..models.backtest import BacktestResult
from ..models.analytics import (
    PerformanceAnalytics, CoreMetrics, TradingMetrics, RiskMetrics,
    DrawdownPeriod, MonthlyReturns, BenchmarkComparison, StrategyComparison,
    MultiStrategyAnalysis, CompleteAnalytics, ExportData, ComparisonType
)
from ..services.data_service import DataService

class EnhancedAnalyticsEngine:
    """Enhanced analytics engine with benchmark comparison and multi-strategy analysis"""
    
    def __init__(self):
        self.data_service = DataService()
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
    
    async def calculate_complete_analytics(
        self,
        backtest_result: BacktestResult,
        benchmark_symbol: Optional[str] = None,
        include_benchmark: bool = True,
        include_rolling_metrics: bool = True
    ) -> CompleteAnalytics:
        """Calculate complete analytics package"""
        
        # Calculate performance analytics
        performance = await self.calculate_performance_analytics(
            backtest_result, include_rolling_metrics
        )
        
        # Calculate benchmark comparison if requested
        benchmark_comparison = None
        if include_benchmark and benchmark_symbol:
            benchmark_comparison = await self.calculate_benchmark_comparison(
                backtest_result, benchmark_symbol
            )
        
        # Generate chart data
        chart_data = self._generate_chart_data(backtest_result)
        
        return CompleteAnalytics(
            performance=performance,
            benchmark_comparison=benchmark_comparison,
            **chart_data
        )
    
    async def calculate_performance_analytics(
        self,
        backtest_result: BacktestResult,
        include_rolling_metrics: bool = True
    ) -> PerformanceAnalytics:
        """Calculate comprehensive performance analytics"""
        
        # Calculate core metrics
        core_metrics = self._calculate_enhanced_core_metrics(backtest_result)
        
        # Calculate trading metrics
        trading_metrics = self._calculate_enhanced_trading_metrics(backtest_result)
        
        # Calculate risk metrics
        risk_metrics = self._calculate_enhanced_risk_metrics(backtest_result)
        
        # Calculate detailed breakdowns
        monthly_returns = self._calculate_monthly_returns(backtest_result)
        drawdown_periods = self._calculate_drawdown_periods(backtest_result)
        
        # Get return series
        daily_returns = self._get_daily_returns(backtest_result)
        trade_returns = [t.return_pct for t in backtest_result.trades if t.return_pct is not None]
        
        # Calculate rolling metrics if requested
        rolling_sharpe = []
        rolling_volatility = []
        rolling_returns = []
        
        if include_rolling_metrics and len(daily_returns) > 30:
            rolling_sharpe, rolling_volatility, rolling_returns = self._calculate_rolling_metrics(
                daily_returns, window=30
            )
        
        return PerformanceAnalytics(
            backtest_id=backtest_result.backtest_id,
            generated_at=datetime.now(),
            core_metrics=core_metrics,
            trading_metrics=trading_metrics,
            risk_metrics=risk_metrics,
            monthly_returns=monthly_returns,
            drawdown_periods=drawdown_periods,
            daily_returns=daily_returns,
            trade_returns=trade_returns,
            rolling_sharpe=rolling_sharpe,
            rolling_volatility=rolling_volatility,
            rolling_returns=rolling_returns
        )
    
    async def calculate_benchmark_comparison(
        self,
        backtest_result: BacktestResult,
        benchmark_symbol: str = "BTC-USDT"
    ) -> BenchmarkComparison:
        """Calculate benchmark comparison analysis"""
        
        # Get benchmark data for the same period
        benchmark_data = await self._get_benchmark_data(
            benchmark_symbol,
            backtest_result.start_date,
            backtest_result.end_date
        )
        
        if benchmark_data.empty:
            raise ValueError(f"No benchmark data available for {benchmark_symbol}")
        
        # Calculate benchmark returns
        benchmark_returns = benchmark_data['close'].pct_change().dropna()
        benchmark_total_return = ((benchmark_data['close'].iloc[-1] / benchmark_data['close'].iloc[0]) - 1) * 100
        
        # Get strategy returns
        strategy_returns = pd.Series(self._get_daily_returns(backtest_result))
        strategy_total_return = backtest_result.performance_metrics.total_return_pct
        
        # Align the return series
        min_length = min(len(strategy_returns), len(benchmark_returns))
        strategy_returns = strategy_returns.iloc[:min_length]
        benchmark_returns = benchmark_returns.iloc[:min_length]
        
        # Calculate comparison metrics
        excess_return = strategy_total_return - benchmark_total_return
        
        # Tracking error (standard deviation of excess returns)
        excess_returns_series = strategy_returns - benchmark_returns
        tracking_error = excess_returns_series.std() * np.sqrt(252) * 100  # Annualized
        
        # Information ratio
        information_ratio = (excess_returns_series.mean() * 252 * 100) / tracking_error if tracking_error > 0 else 0
        
        # Correlation
        correlation = strategy_returns.corr(benchmark_returns) if len(strategy_returns) > 1 else 0
        
        # Beta and Alpha (CAPM)
        if len(strategy_returns) > 1 and benchmark_returns.var() > 0:
            beta = strategy_returns.cov(benchmark_returns) / benchmark_returns.var()
            alpha = (strategy_returns.mean() - self.risk_free_rate/252 - beta * (benchmark_returns.mean() - self.risk_free_rate/252)) * 252 * 100
        else:
            beta = 1.0
            alpha = 0.0
        
        # Drawdown comparison
        strategy_max_drawdown = backtest_result.drawdown_metrics.max_drawdown_pct
        benchmark_drawdown = self._calculate_max_drawdown(benchmark_data['close'])
        
        # Generate benchmark equity curve
        benchmark_equity_curve = self._generate_benchmark_equity_curve(benchmark_data)
        
        # Generate relative performance data
        relative_performance = self._generate_relative_performance(
            backtest_result, benchmark_data
        )
        
        return BenchmarkComparison(
            benchmark_symbol=benchmark_symbol,
            benchmark_name=self._get_benchmark_name(benchmark_symbol),
            strategy_return=strategy_total_return,
            benchmark_return=benchmark_total_return,
            excess_return=excess_return,
            tracking_error=tracking_error,
            information_ratio=information_ratio,
            correlation=correlation,
            beta=beta,
            alpha=alpha,
            strategy_max_drawdown=strategy_max_drawdown,
            benchmark_max_drawdown=benchmark_drawdown,
            benchmark_equity_curve=benchmark_equity_curve,
            relative_performance=relative_performance
        )
    
    async def calculate_multi_strategy_analysis(
        self,
        backtest_results: List[BacktestResult]
    ) -> MultiStrategyAnalysis:
        """Calculate multi-strategy comparison analysis"""
        
        if len(backtest_results) < 2:
            raise ValueError("At least 2 strategies required for comparison")
        
        # Calculate individual strategy comparisons
        strategy_comparisons = []
        
        for result in backtest_results:
            comparison = StrategyComparison(
                strategy_id=result.backtest_id,
                strategy_name=result.strategy_name,
                total_return=result.performance_metrics.total_return_pct,
                cagr=result.performance_metrics.annual_return_pct,
                sharpe_ratio=result.performance_metrics.sharpe_ratio,
                max_drawdown=result.drawdown_metrics.max_drawdown_pct,
                volatility=result.performance_metrics.volatility_annual,
                sortino_ratio=result.performance_metrics.sortino_ratio,
                calmar_ratio=result.performance_metrics.calmar_ratio,
                total_trades=result.trading_metrics.total_trades,
                win_rate=result.trading_metrics.win_rate_pct
            )
            strategy_comparisons.append(comparison)
        
        # Add rankings
        strategy_comparisons = self._add_strategy_rankings(strategy_comparisons)
        
        # Calculate correlation matrix
        correlation_matrix = await self._calculate_strategy_correlations(backtest_results)
        
        # Find best performers
        best_return = max(strategy_comparisons, key=lambda x: x.total_return)
        best_sharpe = max(strategy_comparisons, key=lambda x: x.sharpe_ratio)
        lowest_drawdown = min(strategy_comparisons, key=lambda x: x.max_drawdown)
        
        # Calculate efficient frontier
        efficient_frontier = self._calculate_efficient_frontier(strategy_comparisons)
        
        return MultiStrategyAnalysis(
            comparison_id=str(uuid.uuid4()),
            generated_at=datetime.now(),
            strategies=strategy_comparisons,
            best_return_strategy=best_return.strategy_name,
            best_sharpe_strategy=best_sharpe.strategy_name,
            lowest_drawdown_strategy=lowest_drawdown.strategy_name,
            correlation_matrix=correlation_matrix,
            efficient_frontier=efficient_frontier
        )
    
    def _calculate_enhanced_core_metrics(self, result: BacktestResult) -> CoreMetrics:
        """Calculate enhanced core performance metrics"""
        
        return CoreMetrics(
            pnl_percent=result.performance_metrics.total_return_pct,
            pnl_dollars=result.total_pnl,
            cagr_percent=result.performance_metrics.annual_return_pct,
            sharpe_ratio=result.performance_metrics.sharpe_ratio,
            sortino_ratio=result.performance_metrics.sortino_ratio,
            calmar_ratio=result.performance_metrics.calmar_ratio,
            max_drawdown_percent=result.drawdown_metrics.max_drawdown_pct,
            max_drawdown_dollars=result.total_pnl * (result.drawdown_metrics.max_drawdown_pct / 100),
            volatility_percent=result.performance_metrics.volatility_annual
        )
    
    def _calculate_enhanced_trading_metrics(self, result: BacktestResult) -> TradingMetrics:
        """Calculate enhanced trading metrics"""
        
        trades = [t for t in result.trades if t.return_pct is not None]
        
        # Basic metrics
        basic_metrics = {
            'total_trades': result.trading_metrics.total_trades,
            'win_rate_percent': result.trading_metrics.win_rate_pct,
            'avg_trade_duration_hours': result.trading_metrics.avg_trade_duration_hours,
            'largest_win_percent': result.trading_metrics.best_trade_return_pct,
            'largest_loss_percent': result.trading_metrics.worst_trade_return_pct,
            'turnover_percent': 100.0,  # Simplified
            'profit_factor': result.trading_metrics.profit_factor,
            'avg_win_percent': result.trading_metrics.avg_win_return_pct,
            'avg_loss_percent': result.trading_metrics.avg_loss_return_pct
        }
        
        # Enhanced metrics
        if trades:
            returns = [t.return_pct for t in trades]
            wins = [r for r in returns if r > 0]
            losses = [r for r in returns if r <= 0]
            
            # Mathematical expectancy
            expectancy = np.mean(returns) if returns else 0
            
            # Ulcer Index (using equity curve)
            ulcer_index = self._calculate_ulcer_index(result)
            
            # Recovery factor
            recovery_factor = abs(basic_metrics['total_trades'] / basic_metrics['largest_loss_percent']) if basic_metrics['largest_loss_percent'] < 0 else 0
            
            # Consecutive wins/losses (already calculated in Phase 2)
            max_consecutive_wins = result.trading_metrics.max_consecutive_wins
            max_consecutive_losses = result.trading_metrics.max_consecutive_losses
        else:
            expectancy = ulcer_index = recovery_factor = 0
            max_consecutive_wins = max_consecutive_losses = 0
        
        return TradingMetrics(
            **basic_metrics,
            expectancy=expectancy,
            ulcer_index=ulcer_index,
            recovery_factor=recovery_factor,
            max_consecutive_wins=max_consecutive_wins,
            max_consecutive_losses=max_consecutive_losses
        )
    
    def _calculate_enhanced_risk_metrics(self, result: BacktestResult) -> RiskMetrics:
        """Calculate enhanced risk metrics"""
        
        daily_returns = self._get_daily_returns(result)
        
        if len(daily_returns) < 2:
            return self._get_empty_risk_metrics()
        
        returns_array = np.array(daily_returns)
        
        # Basic VaR
        var_95 = np.percentile(returns_array, 5) * 100
        var_99 = np.percentile(returns_array, 1) * 100
        
        # Conditional VaR (Expected Shortfall)
        cvar_95 = returns_array[returns_array <= np.percentile(returns_array, 5)].mean() * 100
        cvar_99 = returns_array[returns_array <= np.percentile(returns_array, 1)].mean() * 100
        
        # Omega ratio (probability weighted ratio of gains vs losses)
        gains = returns_array[returns_array > 0]
        losses = returns_array[returns_array <= 0]
        omega_ratio = (np.sum(gains) / len(gains)) / abs(np.sum(losses) / len(losses)) if len(losses) > 0 and len(gains) > 0 else 0
        
        # Kappa 3 (third-order risk measure)
        kappa_3 = stats.skew(returns_array) if len(returns_array) > 2 else 0
        
        # Gain to Pain ratio
        total_gains = np.sum(gains) if len(gains) > 0 else 0
        total_pains = abs(np.sum(losses)) if len(losses) > 0 else 1
        gain_pain_ratio = total_gains / total_pains if total_pains > 0 else 0
        
        # Sterling ratio (CAGR / Max Drawdown)
        sterling_ratio = result.performance_metrics.annual_return_pct / abs(result.drawdown_metrics.max_drawdown_pct) if result.drawdown_metrics.max_drawdown_pct != 0 else 0
        
        # Downside deviation
        downside_returns = returns_array[returns_array < 0]
        downside_deviation = np.std(downside_returns) * np.sqrt(252) * 100 if len(downside_returns) > 0 else 0
        
        return RiskMetrics(
            value_at_risk_95=var_95,
            value_at_risk_99=var_99,
            leverage_percent=100.0,  # Simplified
            beta_to_benchmark=None,  # Will be calculated in benchmark comparison
            max_consecutive_losses=result.trading_metrics.max_consecutive_losses,
            downside_deviation=downside_deviation,
            conditional_var_95=cvar_95,
            conditional_var_99=cvar_99,
            omega_ratio=omega_ratio,
            kappa_3=kappa_3,
            gain_pain_ratio=gain_pain_ratio,
            sterling_ratio=sterling_ratio
        )
    
    def _calculate_monthly_returns(self, result: BacktestResult) -> List[MonthlyReturns]:
        """Calculate monthly returns breakdown"""
        if not result.equity_curve:
            return []
        
        # Convert equity curve to DataFrame
        equity_df = pd.DataFrame(result.equity_curve)
        equity_df['timestamp'] = pd.to_datetime(equity_df['timestamp'])
        equity_df.set_index('timestamp', inplace=True)
        
        # Resample to monthly and calculate returns
        monthly_data = equity_df.resample('M').agg({
            'portfolio_value': 'last',
            'total_return_pct': 'last'
        })
        
        monthly_returns = []
        for i, (date, row) in enumerate(monthly_data.iterrows()):
            if i == 0:
                continue  # Skip first month (no previous month to compare)
            
            prev_value = monthly_data.iloc[i-1]['portfolio_value']
            current_value = row['portfolio_value']
            monthly_return = ((current_value - prev_value) / prev_value) * 100 if prev_value > 0 else 0
            
            # Count trades in this month
            month_start = date.replace(day=1)
            month_end = date
            trades_in_month = len([
                t for t in result.trades 
                if t.entry_time and month_start <= t.entry_time <= month_end
            ])
            
            monthly_returns.append(MonthlyReturns(
                year=date.year,
                month=date.month,
                return_percent=monthly_return,
                trades_count=trades_in_month,
                drawdown_percent=0,  # Simplified for now
                volatility_percent=0  # Simplified for now
            ))
        
        return monthly_returns
    
    def _calculate_drawdown_periods(self, result: BacktestResult) -> List[DrawdownPeriod]:
        """Calculate detailed drawdown periods"""
        if not result.equity_curve:
            return []
        
        # Convert to pandas for easier manipulation
        equity_df = pd.DataFrame(result.equity_curve)
        equity_df['timestamp'] = pd.to_datetime(equity_df['timestamp'])
        
        # Calculate running maximum and drawdown
        equity_df['running_max'] = equity_df['portfolio_value'].cummax()
        equity_df['drawdown'] = (equity_df['portfolio_value'] - equity_df['running_max']) / equity_df['running_max']
        
        # Find drawdown periods
        drawdown_periods = []
        in_drawdown = False
        start_idx = None
        peak_value = None
        
        for i, row in equity_df.iterrows():
            if row['drawdown'] < 0 and not in_drawdown:
                # Start of drawdown
                in_drawdown = True
                start_idx = i
                peak_value = row['running_max']
            elif row['drawdown'] >= 0 and in_drawdown:
                # End of drawdown
                in_drawdown = False
                if start_idx is not None:
                    start_row = equity_df.iloc[start_idx]
                    
                    # Find trough in this period
                    period_data = equity_df.iloc[start_idx:i+1]
                    trough_idx = period_data['portfolio_value'].idxmin()
                    trough_row = equity_df.iloc[trough_idx]
                    
                    duration_days = (row['timestamp'] - start_row['timestamp']).days
                    recovery_days = (row['timestamp'] - trough_row['timestamp']).days
                    
                    drawdown_periods.append(DrawdownPeriod(
                        start_date=start_row['timestamp'],
                        end_date=row['timestamp'],
                        peak_value=peak_value,
                        trough_value=trough_row['portfolio_value'],
                        drawdown_percent=abs(trough_row['drawdown']) * 100,
                        duration_days=duration_days,
                        recovery_days=recovery_days,
                        underwater_days=duration_days
                    ))
                
                start_idx = None
        
        return drawdown_periods
    
    def _get_daily_returns(self, result: BacktestResult) -> List[float]:
        """Get daily returns from equity curve"""
        if not result.equity_curve or len(result.equity_curve) < 2:
            return []
        
        returns = []
        for i in range(1, len(result.equity_curve)):
            prev_value = result.equity_curve[i-1]['portfolio_value']
            current_value = result.equity_curve[i]['portfolio_value']
            
            if prev_value > 0:
                daily_return = (current_value - prev_value) / prev_value
                returns.append(daily_return)
        
        return returns
    
    def _calculate_rolling_metrics(
        self, 
        daily_returns: List[float], 
        window: int = 30
    ) -> Tuple[List[float], List[float], List[float]]:
        """Calculate rolling metrics"""
        if len(daily_returns) < window:
            return [], [], []
        
        returns_series = pd.Series(daily_returns)
        
        # Rolling Sharpe ratio
        rolling_sharpe = []
        rolling_volatility = []
        rolling_returns = []
        
        for i in range(window, len(returns_series)):
            window_returns = returns_series.iloc[i-window:i]
            
            # Rolling return (annualized)
            rolling_ret = window_returns.mean() * 252
            rolling_returns.append(rolling_ret)
            
            # Rolling volatility (annualized)
            rolling_vol = window_returns.std() * np.sqrt(252)
            rolling_volatility.append(rolling_vol)
            
            # Rolling Sharpe
            excess_return = rolling_ret - self.risk_free_rate
            sharpe = excess_return / rolling_vol if rolling_vol > 0 else 0
            rolling_sharpe.append(sharpe)
        
        return rolling_sharpe, rolling_volatility, rolling_returns
    
    async def _get_benchmark_data(
        self, 
        benchmark_symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.DataFrame:
        """Get benchmark data for comparison"""
        try:
            # Use the data service to get benchmark data
            return await self.data_service.get_ohlcv_data(
                symbol=benchmark_symbol,
                timeframe="1d",  # Daily data for benchmark
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            print(f"Error getting benchmark data: {e}")
            return pd.DataFrame()
    
    def _calculate_max_drawdown(self, price_series: pd.Series) -> float:
        """Calculate maximum drawdown from price series"""
        running_max = price_series.cummax()
        drawdown = (price_series - running_max) / running_max
        return abs(drawdown.min()) * 100
    
    def _generate_benchmark_equity_curve(self, benchmark_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate benchmark equity curve data"""
        if benchmark_data.empty:
            return []
        
        # Normalize to start at 100
        initial_price = benchmark_data['close'].iloc[0]
        normalized_prices = (benchmark_data['close'] / initial_price) * 100
        
        return [
            {
                'timestamp': idx.isoformat(),
                'value': float(value),
                'return_pct': float((value - 100))
            }
            for idx, value in normalized_prices.items()
        ]
    
    def _generate_relative_performance(
        self, 
        result: BacktestResult, 
        benchmark_data: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Generate relative performance data"""
        if benchmark_data.empty or not result.equity_curve:
            return []
        
        # This would need alignment of timestamps - simplified for now
        return [
            {
                'timestamp': equity_point['timestamp'],
                'relative_return': equity_point['total_return_pct'] - 0,  # Simplified
                'strategy_return': equity_point['total_return_pct'],
                'benchmark_return': 0  # Would need proper alignment
            }
            for equity_point in result.equity_curve[:10]  # Limit for example
        ]
    
    def _get_benchmark_name(self, symbol: str) -> str:
        """Get human-readable benchmark name"""
        name_mapping = {
            'BTC-USDT': 'Bitcoin',
            'ETH-USDT': 'Ethereum',
            'BNB-USDT': 'Binance Coin',
            'ADA-USDT': 'Cardano',
            'SOL-USDT': 'Solana'
        }
        return name_mapping.get(symbol, symbol)
    
    def _add_strategy_rankings(self, strategies: List[StrategyComparison]) -> List[StrategyComparison]:
        """Add rankings to strategy comparisons"""
        # Sort and rank by different metrics
        by_return = sorted(strategies, key=lambda x: x.total_return, reverse=True)
        by_sharpe = sorted(strategies, key=lambda x: x.sharpe_ratio, reverse=True)
        by_drawdown = sorted(strategies, key=lambda x: x.max_drawdown)  # Lower is better
        
        # Add rankings
        for i, strategy in enumerate(strategies):
            strategy.rank_return = by_return.index(strategy) + 1
            strategy.rank_sharpe = by_sharpe.index(strategy) + 1
            strategy.rank_drawdown = by_drawdown.index(strategy) + 1
        
        return strategies
    
    async def _calculate_strategy_correlations(
        self, 
        results: List[BacktestResult]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate correlation matrix between strategies"""
        if len(results) < 2:
            return {}
        
        # Get return series for each strategy
        returns_data = {}
        for result in results:
            daily_returns = self._get_daily_returns(result)
            if daily_returns:
                returns_data[result.strategy_name] = daily_returns
        
        # Calculate correlation matrix
        correlation_matrix = {}
        for name1, returns1 in returns_data.items():
            correlation_matrix[name1] = {}
            for name2, returns2 in returns_data.items():
                if name1 == name2:
                    correlation_matrix[name1][name2] = 1.0
                else:
                    # Align series lengths
                    min_length = min(len(returns1), len(returns2))
                    if min_length > 1:
                        correlation = pd.Series(returns1[:min_length]).corr(pd.Series(returns2[:min_length]))
                        correlation_matrix[name1][name2] = float(correlation) if not pd.isna(correlation) else 0.0
                    else:
                        correlation_matrix[name1][name2] = 0.0
        
        return correlation_matrix
    
    def _calculate_efficient_frontier(
        self, 
        strategies: List[StrategyComparison]
    ) -> List[Dict[str, float]]:
        """Calculate efficient frontier for strategy combinations"""
        # Simplified efficient frontier calculation
        frontier_points = []
        
        for strategy in strategies:
            frontier_points.append({
                'risk': strategy.volatility,
                'return': strategy.total_return,
                'sharpe': strategy.sharpe_ratio,
                'strategy': strategy.strategy_name
            })
        
        # Sort by risk and filter for efficient strategies
        frontier_points.sort(key=lambda x: x['risk'])
        
        return frontier_points
    
    def _calculate_ulcer_index(self, result: BacktestResult) -> float:
        """Calculate Ulcer Index for risk measurement"""
        if not result.equity_curve:
            return 0
        
        values = [point['portfolio_value'] for point in result.equity_curve]
        equity_series = pd.Series(values)
        
        # Calculate running maximum
        running_max = equity_series.cummax()
        
        # Calculate percentage drawdown
        drawdown_pct = ((equity_series - running_max) / running_max) * 100
        
        # Ulcer Index is the square root of the mean of squared drawdowns
        ulcer_index = np.sqrt((drawdown_pct ** 2).mean())
        
        return float(ulcer_index)
    
    def _generate_chart_data(self, result: BacktestResult) -> Dict[str, Any]:
        """Generate chart data for frontend"""
        
        # Equity curve
        equity_curve = [
            {
                'timestamp': point['timestamp'],
                'value': point['portfolio_value'],
                'return_pct': point['total_return_pct']
            }
            for point in result.equity_curve
        ]
        
        # Drawdown chart
        drawdown_chart = []
        if result.equity_curve:
            values = [point['portfolio_value'] for point in result.equity_curve]
            equity_series = pd.Series(values)
            running_max = equity_series.cummax()
            drawdowns = ((equity_series - running_max) / running_max) * 100
            
            drawdown_chart = [
                {
                    'timestamp': result.equity_curve[i]['timestamp'],
                    'drawdown': float(drawdowns.iloc[i])
                }
                for i in range(len(drawdowns))
            ]
        
        # Returns distribution
        daily_returns = self._get_daily_returns(result)
        returns_distribution = []
        if daily_returns:
            hist, bins = np.histogram(daily_returns, bins=50)
            returns_distribution = [
                {
                    'bin_start': float(bins[i]),
                    'bin_end': float(bins[i+1]),
                    'count': int(hist[i]),
                    'frequency': float(hist[i] / len(daily_returns))
                }
                for i in range(len(hist))
            ]
        
        return {
            'equity_curve': equity_curve,
            'drawdown_chart': drawdown_chart,
            'returns_distribution': returns_distribution,
            'monthly_heatmap': [],  # Would implement based on monthly returns
            'rolling_metrics_chart': []  # Would implement based on rolling metrics
        }
    
    def _get_empty_risk_metrics(self) -> RiskMetrics:
        """Return empty risk metrics"""
        return RiskMetrics(
            value_at_risk_95=0,
            value_at_risk_99=0,
            leverage_percent=100,
            beta_to_benchmark=None,
            max_consecutive_losses=0,
            downside_deviation=0
        ) 