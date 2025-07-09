"""
Enhanced Backtest Engine - Event-driven backtesting with advanced features
Strategic integration from 'mine' project with enhanced capabilities
"""

from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import asyncio
import uuid

from ..models.strategy import Strategy
from ..models.backtest import (
    BacktestResult, TradeResult, PerformanceMetrics, 
    DrawdownMetrics, TradingMetrics, TradeAction
)
from .strategy_engine import StrategyEngine
from .indicators import TechnicalIndicators

class Portfolio:
    """Portfolio management for backtesting"""
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}
        self.portfolio_value = initial_capital
        self.trade_history = []
        self.portfolio_history = []
        
    def execute_trade(
        self, 
        symbol: str, 
        action: TradeAction, 
        quantity: float, 
        price: float, 
        timestamp: datetime,
        fees: float = 0,
        slippage_bps: float = 0
    ) -> Optional[TradeResult]:
        """Execute a trade and update portfolio"""
        
        # Apply slippage
        slippage_factor = 1 + (slippage_bps / 10000)
        if action in [TradeAction.BUY, TradeAction.SHORT]:
            execution_price = price * slippage_factor
        else:
            execution_price = price / slippage_factor
        
        trade_value = quantity * execution_price
        total_cost = trade_value + fees
        
        # Create trade record
        trade = TradeResult(
            trade_id=str(uuid.uuid4()),
            symbol=symbol,
            action=action,
            entry_time=timestamp,
            entry_price=execution_price,
            quantity=quantity,
            commission=fees
        )
        
        # Update portfolio based on action
        if action == TradeAction.BUY:
            if self.cash >= total_cost:
                self.cash -= total_cost
                self.positions[symbol] = self.positions.get(symbol, 0) + quantity
                self.trade_history.append(trade)
                return trade
        elif action == TradeAction.SELL:
            if symbol in self.positions and self.positions[symbol] >= quantity:
                self.cash += trade_value - fees
                self.positions[symbol] -= quantity
                if self.positions[symbol] == 0:
                    del self.positions[symbol]
                
                # Calculate PnL for sell trade
                trade.exit_time = timestamp
                trade.exit_price = execution_price
                # Find matching buy trade for PnL calculation (simplified)
                for prev_trade in reversed(self.trade_history):
                    if (prev_trade.symbol == symbol and 
                        prev_trade.action == TradeAction.BUY and 
                        prev_trade.exit_time is None):
                        
                        trade.gross_pnl = (execution_price - prev_trade.entry_price) * quantity
                        trade.net_pnl = trade.gross_pnl - fees - prev_trade.commission
                        trade.return_pct = (trade.gross_pnl / (prev_trade.entry_price * quantity)) * 100
                        
                        # Update the buy trade
                        prev_trade.exit_time = timestamp
                        prev_trade.exit_price = execution_price
                        prev_trade.gross_pnl = trade.gross_pnl
                        prev_trade.net_pnl = trade.net_pnl
                        prev_trade.return_pct = trade.return_pct
                        
                        if trade.exit_time and trade.entry_time:
                            duration = trade.exit_time - trade.entry_time
                            trade.duration_minutes = int(duration.total_seconds() / 60)
                            prev_trade.duration_minutes = trade.duration_minutes
                        break
                
                self.trade_history.append(trade)
                return trade
        
        return None
    
    def update_portfolio_value(self, current_prices: Dict[str, float]):
        """Update total portfolio value"""
        position_value = sum(
            quantity * current_prices.get(symbol, 0)
            for symbol, quantity in self.positions.items()
        )
        self.portfolio_value = self.cash + position_value
    
    def record_snapshot(self, timestamp: datetime, current_prices: Dict[str, float]):
        """Record portfolio snapshot"""
        self.update_portfolio_value(current_prices)
        
        snapshot = {
            'timestamp': timestamp,
            'portfolio_value': self.portfolio_value,
            'cash': self.cash,
            'positions_value': self.portfolio_value - self.cash,
            'total_return_pct': ((self.portfolio_value - self.initial_capital) / self.initial_capital) * 100
        }
        
        self.portfolio_history.append(snapshot)

class BacktestEngine:
    """Enhanced backtesting execution engine"""
    
    def __init__(self):
        self.strategy_engine = StrategyEngine()
        self.indicators_engine = TechnicalIndicators()
        
    async def run_backtest(
        self,
        strategy: Strategy,
        market_data: pd.DataFrame,
        initial_capital: float = 100000,
        progress_callback: Optional[callable] = None
    ) -> BacktestResult:
        """
        Execute comprehensive strategy backtest
        
        Args:
            strategy: Strategy configuration
            market_data: OHLCV market data
            initial_capital: Starting capital
            progress_callback: Optional callback for progress updates
            
        Returns:
            Complete backtest results with metrics
        """
        start_time = datetime.now()
        
        try:
            # Initialize portfolio
            portfolio = Portfolio(initial_capital)
            
            # Calculate indicators
            if progress_callback:
                await progress_callback(10, "Calculating technical indicators...")
            
            indicators_data = self._calculate_all_indicators(strategy, market_data)
            
            # Prepare backtesting
            symbol = strategy.asset_selection.symbol
            current_position = 0.0
            entry_trade = None
            warmup_period = 50  # Skip first 50 bars for indicator warmup
            
            total_bars = len(market_data)
            
            # Main backtesting loop
            for i in range(total_bars):
                if progress_callback and i % 100 == 0:
                    progress = 10 + (i / total_bars) * 80
                    await progress_callback(progress, f"Processing bar {i+1}/{total_bars}")
                
                current_bar = market_data.iloc[i]
                current_time = current_bar.name
                current_price = current_bar['close']
                previous_bar = market_data.iloc[i-1] if i > 0 else None
                
                # Skip warmup period
                if i < warmup_period:
                    portfolio.record_snapshot(current_time, {symbol: current_price})
                    continue
                
                # Get current indicator values
                current_indicators = self._get_current_indicators(indicators_data, i)
                
                # Update strategy engine state
                self.strategy_engine.update_previous_state(current_indicators)
                
                # Check signals
                if current_position == 0:  # No position
                    if self._check_entry_signal(strategy, current_indicators, current_bar, previous_bar):
                        # Calculate position size
                        position_size = self._calculate_position_size(
                            strategy, current_price, portfolio.cash
                        )
                        
                        if position_size > 0:
                            # Execute buy order
                            fees = self._calculate_fees(strategy, position_size * current_price)
                            trade = portfolio.execute_trade(
                                symbol=symbol,
                                action=TradeAction.BUY,
                                quantity=position_size,
                                price=current_price,
                                timestamp=current_time,
                                fees=fees,
                                slippage_bps=strategy.execution_parameters.slippage_bps
                            )
                            
                            if trade:
                                current_position = position_size
                                entry_trade = trade
                
                else:  # Have position
                    # Check exit conditions
                    exit_signal = self._check_exit_signal(strategy, current_indicators, current_bar, previous_bar)
                    
                    # Check risk management
                    risk_exit = self._check_risk_management(
                        strategy, current_price, entry_trade
                    ) if entry_trade else False
                    
                    if exit_signal or risk_exit:
                        # Execute sell order
                        fees = self._calculate_fees(strategy, current_position * current_price)
                        trade = portfolio.execute_trade(
                            symbol=symbol,
                            action=TradeAction.SELL,
                            quantity=current_position,
                            price=current_price,
                            timestamp=current_time,
                            fees=fees,
                            slippage_bps=strategy.execution_parameters.slippage_bps
                        )
                        
                        if trade:
                            current_position = 0.0
                            entry_trade = None
                
                # Record portfolio snapshot
                portfolio.record_snapshot(current_time, {symbol: current_price})
            
            if progress_callback:
                await progress_callback(95, "Calculating performance metrics...")
            
            # Calculate comprehensive metrics
            metrics = self._calculate_comprehensive_metrics(
                portfolio, market_data, strategy, start_time
            )
            
            if progress_callback:
                await progress_callback(100, "Backtest completed successfully!")
            
            return metrics
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Return error result
            return BacktestResult(
                backtest_id=str(uuid.uuid4()),
                strategy_name=strategy.name,
                symbol=strategy.asset_selection.symbol,
                timeframe="unknown",
                start_date=market_data.index[0] if not market_data.empty else datetime.now(),
                end_date=market_data.index[-1] if not market_data.empty else datetime.now(),
                duration_days=0,
                initial_capital=initial_capital,
                final_capital=initial_capital,
                total_pnl=0,
                performance_metrics=PerformanceMetrics(
                    total_return_pct=0, annual_return_pct=0, monthly_return_pct=0,
                    daily_return_pct=0, sharpe_ratio=0, sortino_ratio=0,
                    calmar_ratio=0, volatility_annual=0, downside_deviation=0
                ),
                drawdown_metrics=DrawdownMetrics(
                    max_drawdown_pct=0, max_drawdown_duration_days=0,
                    avg_drawdown_pct=0, avg_drawdown_duration_days=0,
                    drawdown_periods=0, recovery_factor=0,
                    time_underwater_pct=0, max_time_to_recovery_days=0
                ),
                trading_metrics=TradingMetrics(
                    total_trades=0, winning_trades=0, losing_trades=0,
                    win_rate_pct=0, profit_factor=0, avg_trade_return_pct=0,
                    avg_win_return_pct=0, avg_loss_return_pct=0,
                    avg_trade_duration_hours=0, avg_win_duration_hours=0,
                    avg_loss_duration_hours=0, best_trade_return_pct=0,
                    worst_trade_return_pct=0, max_consecutive_wins=0,
                    max_consecutive_losses=0
                ),
                trades=portfolio.trade_history,
                status="failed",
                execution_time_seconds=execution_time,
                error_message=str(e)
            )
    
    def _calculate_all_indicators(self, strategy: Strategy, market_data: pd.DataFrame) -> Dict:
        """Calculate all required indicators"""
        indicator_configs = []
        
        for indicator in strategy.signal_generation.indicators:
            config = {
                'type': indicator.type,
                'period': indicator.period,
                'source': indicator.source
            }
            
            if indicator.type == "macd":
                config.update({
                    'fast_period': indicator.fast_period,
                    'slow_period': indicator.slow_period,
                    'signal_period': indicator.signal_period
                })
            elif indicator.type == "bb":
                config['std_dev'] = indicator.std_dev
            elif indicator.type == "stoch":
                config.update({
                    'k_period': indicator.k_period,
                    'd_period': indicator.d_period
                })
            
            indicator_configs.append(config)
        
        return TechnicalIndicators.calculate_multiple_indicators(market_data, indicator_configs)
    
    def _get_current_indicators(self, indicators_data: Dict, index: int) -> Dict:
        """Get indicator values at current index"""
        current_indicators = {}
        
        for name, data in indicators_data.items():
            if isinstance(data, pd.Series) and len(data) > index:
                value = data.iloc[index]
                current_indicators[name] = float(value) if not pd.isna(value) else 0.0
        
        return current_indicators
    
    def _check_entry_signal(
        self, 
        strategy: Strategy, 
        indicators: Dict, 
        current_bar: pd.Series,
        previous_bar: Optional[pd.Series] = None
    ) -> bool:
        """Check if entry conditions are met"""
        return self.strategy_engine.evaluate_conditions(
            strategy.signal_generation.entry_conditions,
            indicators,
            current_bar,
            previous_bar
        )
    
    def _check_exit_signal(
        self, 
        strategy: Strategy, 
        indicators: Dict, 
        current_bar: pd.Series,
        previous_bar: Optional[pd.Series] = None
    ) -> bool:
        """Check if exit conditions are met"""
        return self.strategy_engine.evaluate_conditions(
            strategy.signal_generation.exit_conditions,
            indicators,
            current_bar,
            previous_bar
        )
    
    def _check_risk_management(
        self, 
        strategy: Strategy, 
        current_price: float, 
        entry_trade: TradeResult
    ) -> bool:
        """Check risk management rules"""
        if not entry_trade:
            return False
        
        # Stop loss check
        if strategy.risk_management.stop_loss_pct:
            loss_pct = ((entry_trade.entry_price - current_price) / entry_trade.entry_price) * 100
            if loss_pct >= strategy.risk_management.stop_loss_pct:
                return True
        
        # Take profit check
        if strategy.risk_management.take_profit_pct:
            profit_pct = ((current_price - entry_trade.entry_price) / entry_trade.entry_price) * 100
            if profit_pct >= strategy.risk_management.take_profit_pct:
                return True
        
        return False
    
    def _calculate_position_size(
        self, 
        strategy: Strategy, 
        price: float, 
        available_cash: float
    ) -> float:
        """Calculate position size based on strategy parameters"""
        if strategy.execution_parameters.quantity_type == "percentage":
            percentage = strategy.execution_parameters.quantity_value / 100
            target_value = available_cash * percentage
            return target_value / price
        elif strategy.execution_parameters.quantity_type == "risk_based":
            # Risk-based position sizing (simplified)
            risk_amount = available_cash * (strategy.execution_parameters.quantity_value / 100)
            if strategy.risk_management.stop_loss_pct:
                stop_distance = price * (strategy.risk_management.stop_loss_pct / 100)
                return risk_amount / stop_distance
            else:
                return available_cash * 0.1 / price  # Default 10%
        else:
            # Fixed quantity
            return strategy.execution_parameters.quantity_value
    
    def _calculate_fees(self, strategy: Strategy, trade_value: float) -> float:
        """Calculate trading fees"""
        return trade_value * (strategy.execution_parameters.fees_bps / 10000)
    
    def _calculate_comprehensive_metrics(
        self,
        portfolio: Portfolio,
        market_data: pd.DataFrame,
        strategy: Strategy,
        start_time: datetime
    ) -> BacktestResult:
        """Calculate comprehensive performance metrics"""
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Basic metrics
        initial_capital = portfolio.initial_capital
        final_capital = portfolio.portfolio_value
        total_pnl = final_capital - initial_capital
        
        # Time period
        start_date = market_data.index[0]
        end_date = market_data.index[-1]
        duration_days = (end_date - start_date).days
        
        # Calculate returns series
        portfolio_df = pd.DataFrame(portfolio.portfolio_history)
        if not portfolio_df.empty:
            portfolio_df.set_index('timestamp', inplace=True)
            returns = portfolio_df['portfolio_value'].pct_change().dropna()
        else:
            returns = pd.Series([])
        
        # Performance metrics
        total_return_pct = (total_pnl / initial_capital) * 100
        annual_return_pct = (total_return_pct / duration_days) * 365 if duration_days > 0 else 0
        
        # Risk metrics
        if len(returns) > 1:
            volatility_annual = returns.std() * np.sqrt(252) * 100
            sharpe_ratio = (annual_return_pct / volatility_annual) if volatility_annual > 0 else 0
            downside_returns = returns[returns < 0]
            downside_deviation = downside_returns.std() * np.sqrt(252) * 100 if len(downside_returns) > 0 else 0
            sortino_ratio = (annual_return_pct / downside_deviation) if downside_deviation > 0 else 0
        else:
            volatility_annual = 0
            sharpe_ratio = 0
            downside_deviation = 0
            sortino_ratio = 0
        
        # Drawdown metrics
        if not portfolio_df.empty:
            rolling_max = portfolio_df['portfolio_value'].cummax()
            drawdown = (portfolio_df['portfolio_value'] - rolling_max) / rolling_max * 100
            max_drawdown_pct = drawdown.min()
            
            # Calculate detailed drawdown metrics
            drawdown_metrics = self._calculate_detailed_drawdown_metrics(portfolio_df, drawdown)
        else:
            max_drawdown_pct = 0
            drawdown_metrics = {
                'max_drawdown_duration_days': 0,
                'avg_drawdown_pct': 0,
                'avg_drawdown_duration_days': 0,
                'drawdown_periods': 0,
                'time_underwater_pct': 0,
                'max_time_to_recovery_days': 0
            }
        
        calmar_ratio = (annual_return_pct / abs(max_drawdown_pct)) if max_drawdown_pct != 0 else 0
        
        # Trading metrics
        completed_trades = [t for t in portfolio.trade_history if t.exit_time is not None]
        winning_trades = [t for t in completed_trades if t.net_pnl and t.net_pnl > 0]
        losing_trades = [t for t in completed_trades if t.net_pnl and t.net_pnl <= 0]
        
        total_trades = len(completed_trades)
        win_rate_pct = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        
        gross_profit = sum(t.gross_pnl for t in winning_trades if t.gross_pnl)
        gross_loss = abs(sum(t.gross_pnl for t in losing_trades if t.gross_pnl))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        
        avg_trade_return_pct = np.mean([t.return_pct for t in completed_trades if t.return_pct]) if completed_trades else 0
        avg_win_return_pct = np.mean([t.return_pct for t in winning_trades if t.return_pct]) if winning_trades else 0
        avg_loss_return_pct = np.mean([t.return_pct for t in losing_trades if t.return_pct]) if losing_trades else 0
        
        # Calculate trade duration metrics
        trade_duration_metrics = self._calculate_trade_duration_metrics(completed_trades, winning_trades, losing_trades)
        
        # Calculate consecutive wins/losses
        consecutive_metrics = self._calculate_consecutive_metrics(completed_trades)
        
        # Create result
        return BacktestResult(
            backtest_id=str(uuid.uuid4()),
            strategy_name=strategy.name,
            symbol=strategy.asset_selection.symbol,
            timeframe="1h",  # Default, could be parameterized
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days,
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_pnl=total_pnl,
            performance_metrics=PerformanceMetrics(
                total_return_pct=total_return_pct,
                annual_return_pct=annual_return_pct,
                monthly_return_pct=annual_return_pct / 12,
                daily_return_pct=annual_return_pct / 365,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                volatility_annual=volatility_annual,
                downside_deviation=downside_deviation
            ),
            drawdown_metrics=DrawdownMetrics(
                max_drawdown_pct=max_drawdown_pct,
                max_drawdown_duration_days=drawdown_metrics['max_drawdown_duration_days'],
                avg_drawdown_pct=drawdown_metrics['avg_drawdown_pct'],
                avg_drawdown_duration_days=drawdown_metrics['avg_drawdown_duration_days'],
                drawdown_periods=drawdown_metrics['drawdown_periods'],
                recovery_factor=abs(total_return_pct / max_drawdown_pct) if max_drawdown_pct != 0 else 0,
                time_underwater_pct=drawdown_metrics['time_underwater_pct'],
                max_time_to_recovery_days=drawdown_metrics['max_time_to_recovery_days']
            ),
            trading_metrics=TradingMetrics(
                total_trades=total_trades,
                winning_trades=len(winning_trades),
                losing_trades=len(losing_trades),
                win_rate_pct=win_rate_pct,
                profit_factor=profit_factor,
                avg_trade_return_pct=avg_trade_return_pct,
                avg_win_return_pct=avg_win_return_pct,
                avg_loss_return_pct=avg_loss_return_pct,
                avg_trade_duration_hours=trade_duration_metrics['avg_trade_duration_hours'],
                avg_win_duration_hours=trade_duration_metrics['avg_win_duration_hours'],
                avg_loss_duration_hours=trade_duration_metrics['avg_loss_duration_hours'],
                best_trade_return_pct=max([t.return_pct for t in completed_trades if t.return_pct], default=0),
                worst_trade_return_pct=min([t.return_pct for t in completed_trades if t.return_pct], default=0),
                max_consecutive_wins=consecutive_metrics['max_consecutive_wins'],
                max_consecutive_losses=consecutive_metrics['max_consecutive_losses']
            ),
            trades=portfolio.trade_history,
            status="completed",
            execution_time_seconds=execution_time,
            equity_curve=[
                {
                    "timestamp": snapshot["timestamp"].isoformat(),
                    "portfolio_value": snapshot["portfolio_value"],
                    "total_return_pct": snapshot["total_return_pct"]
                }
                for snapshot in portfolio.portfolio_history
            ]
        )
    
    def _calculate_detailed_drawdown_metrics(self, portfolio_df: pd.DataFrame, drawdown: pd.Series) -> Dict:
        """Calculate detailed drawdown metrics"""
        # Find drawdown periods (when drawdown < 0)
        underwater = drawdown < 0
        
        # Get periods where portfolio is underwater
        underwater_periods = []
        start_idx = None
        
        for i, is_underwater in enumerate(underwater):
            if is_underwater and start_idx is None:
                start_idx = i
            elif not is_underwater and start_idx is not None:
                underwater_periods.append((start_idx, i-1))
                start_idx = None
        
        # Handle case where last period is underwater
        if start_idx is not None:
            underwater_periods.append((start_idx, len(underwater)-1))
        
        if not underwater_periods:
            return {
                'max_drawdown_duration_days': 0,
                'avg_drawdown_pct': 0,
                'avg_drawdown_duration_days': 0,
                'drawdown_periods': 0,
                'time_underwater_pct': 0,
                'max_time_to_recovery_days': 0
            }
        
        # Calculate metrics for each drawdown period
        drawdown_durations = []
        drawdown_magnitudes = []
        recovery_times = []
        
        for start, end in underwater_periods:
            # Duration in days
            start_time = portfolio_df.index[start]
            end_time = portfolio_df.index[end]
            duration_days = (end_time - start_time).days
            drawdown_durations.append(duration_days)
            
            # Magnitude (minimum drawdown in this period)
            period_drawdown = drawdown.iloc[start:end+1]
            drawdown_magnitudes.append(period_drawdown.min())
            
            # Recovery time (simplified - time from end of drawdown to next high)
            if end < len(portfolio_df) - 1:
                recovery_start = end
                portfolio_values = portfolio_df['portfolio_value'].iloc[recovery_start:]
                peak_value = portfolio_df['portfolio_value'].iloc[start-1] if start > 0 else portfolio_df['portfolio_value'].iloc[0]
                
                recovery_idx = None
                for j, value in enumerate(portfolio_values):
                    if value >= peak_value:
                        recovery_idx = j
                        break
                
                if recovery_idx is not None:
                    recovery_time = portfolio_df.index[recovery_start + recovery_idx]
                    recovery_duration = (recovery_time - end_time).days
                    recovery_times.append(recovery_duration)
        
        # Calculate summary statistics
        max_drawdown_duration_days = max(drawdown_durations) if drawdown_durations else 0
        avg_drawdown_duration_days = np.mean(drawdown_durations) if drawdown_durations else 0
        avg_drawdown_pct = np.mean(drawdown_magnitudes) if drawdown_magnitudes else 0
        
        # Time underwater percentage
        total_underwater_periods = sum(drawdown_durations)
        total_periods = len(portfolio_df)
        time_underwater_pct = (total_underwater_periods / total_periods * 100) if total_periods > 0 else 0
        
        # Max time to recovery
        max_time_to_recovery_days = max(recovery_times) if recovery_times else 0
        
        return {
            'max_drawdown_duration_days': max_drawdown_duration_days,
            'avg_drawdown_pct': avg_drawdown_pct,
            'avg_drawdown_duration_days': avg_drawdown_duration_days,
            'drawdown_periods': len(underwater_periods),
            'time_underwater_pct': time_underwater_pct,
            'max_time_to_recovery_days': max_time_to_recovery_days
        }
    
    def _calculate_trade_duration_metrics(self, completed_trades: list, winning_trades: list, losing_trades: list) -> Dict:
        """Calculate trade duration metrics"""
        def get_duration_hours(trades):
            durations = []
            for trade in trades:
                if trade.duration_minutes is not None:
                    durations.append(trade.duration_minutes / 60.0)  # Convert to hours
            return durations
        
        all_durations = get_duration_hours(completed_trades)
        win_durations = get_duration_hours(winning_trades)
        loss_durations = get_duration_hours(losing_trades)
        
        return {
            'avg_trade_duration_hours': np.mean(all_durations) if all_durations else 0,
            'avg_win_duration_hours': np.mean(win_durations) if win_durations else 0,
            'avg_loss_duration_hours': np.mean(loss_durations) if loss_durations else 0
        }
    
    def _calculate_consecutive_metrics(self, completed_trades: list) -> Dict:
        """Calculate consecutive wins and losses"""
        if not completed_trades:
            return {'max_consecutive_wins': 0, 'max_consecutive_losses': 0}
        
        # Sort trades by entry time to ensure chronological order
        sorted_trades = sorted(completed_trades, key=lambda t: t.entry_time)
        
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_consecutive_wins = 0
        current_consecutive_losses = 0
        
        for trade in sorted_trades:
            if trade.net_pnl and trade.net_pnl > 0:  # Winning trade
                current_consecutive_wins += 1
                current_consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_consecutive_wins)
            elif trade.net_pnl and trade.net_pnl <= 0:  # Losing trade
                current_consecutive_losses += 1
                current_consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_consecutive_losses)
        
        return {
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses
        } 