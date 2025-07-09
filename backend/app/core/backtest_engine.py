"""
Enhanced Backtest Engine - Event-driven backtesting with advanced features
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
                # Find matching buy trade for PnL calculation
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
            warmup_period = 50
            
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
                
                # Record portfolio state
                portfolio.record_snapshot(current_time, {symbol: current_price})
            
            # Calculate final performance metrics
            if progress_callback:
                await progress_callback(90, "Calculating performance metrics...")
            
            result = self._calculate_comprehensive_metrics(
                portfolio=portfolio,
                market_data=market_data,
                strategy=strategy,
                start_time=start_time
            )
            
            if progress_callback:
                await progress_callback(100, "Backtest completed successfully")
            
            return result
            
        except Exception as e:
            if progress_callback:
                await progress_callback(-1, f"Error during backtest: {str(e)}")
            raise
    
    def _calculate_all_indicators(self, strategy: Strategy, market_data: pd.DataFrame) -> Dict:
        """Calculate all indicators needed for the strategy"""
        indicators = {}
        
        # Entry condition indicators
        for condition in strategy.entry_conditions:
            if condition.indicator.name not in indicators:
                indicator_data = self.indicators_engine.calculate_indicator(
                    data=market_data,
                    indicator_type=condition.indicator.type,
                    source=condition.indicator.source,
                    period=condition.indicator.period,
                    **condition.indicator.parameters
                )
                indicators[condition.indicator.name] = indicator_data
        
        # Exit condition indicators
        for condition in strategy.exit_conditions:
            if condition.indicator.name not in indicators:
                indicator_data = self.indicators_engine.calculate_indicator(
                    data=market_data,
                    indicator_type=condition.indicator.type,
                    source=condition.indicator.source,
                    period=condition.indicator.period,
                    **condition.indicator.parameters
                )
                indicators[condition.indicator.name] = indicator_data
        
        return indicators
    
    def _get_current_indicators(self, indicators_data: Dict, index: int) -> Dict:
        """Get indicator values at the current index"""
        current_values = {}
        
        for name, data in indicators_data.items():
            if isinstance(data, tuple):
                # Handle indicators with multiple outputs
                current_values[name] = [series.iloc[index] for series in data]
            else:
                current_values[name] = data.iloc[index]
                
        return current_values
    
    def _check_entry_signal(
        self, 
        strategy: Strategy, 
        indicators: Dict, 
        current_bar: pd.Series,
        previous_bar: Optional[pd.Series] = None
    ) -> bool:
        """Check if entry conditions are met"""
        return self.strategy_engine.evaluate_conditions(
            strategy.entry_conditions, indicators, current_bar, previous_bar
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
            strategy.exit_conditions, indicators, current_bar, previous_bar
        )
    
    def _check_risk_management(
        self, 
        strategy: Strategy, 
        current_price: float, 
        entry_trade: TradeResult
    ) -> bool:
        """Check risk management exit conditions (stop-loss and take-profit)"""
        if not strategy.risk_management or not entry_trade:
            return False
        
        entry_price = entry_trade.entry_price
        price_change_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Stop loss check
        if (strategy.risk_management.stop_loss_pct > 0 and 
            price_change_pct <= -strategy.risk_management.stop_loss_pct):
            return True
        
        # Take profit check
        if (strategy.risk_management.take_profit_pct > 0 and
            price_change_pct >= strategy.risk_management.take_profit_pct):
            return True
        
        return False
    
    def _calculate_position_size(
        self, 
        strategy: Strategy, 
        price: float, 
        available_cash: float
    ) -> float:
        """Calculate position size based on sizing method"""
        risk_params = strategy.risk_management
        
        if not risk_params or not risk_params.position_sizing_method:
            # Default: Full cash allocation
            return available_cash / price
        
        method = risk_params.position_sizing_method
        
        if method == "percentage":
            # Percentage of available cash
            pct = risk_params.position_sizing_value / 100
            return (available_cash * pct) / price
        elif method == "fixed_amount":
            # Fixed cash amount
            return min(risk_params.position_sizing_value, available_cash) / price
        elif method == "fixed_quantity":
            # Fixed quantity
            quantity = risk_params.position_sizing_value
            if quantity * price > available_cash:
                return available_cash / price
            return quantity
        
        # Fallback to using all available cash
        return available_cash / price
    
    def _calculate_fees(self, strategy: Strategy, trade_value: float) -> float:
        """Calculate trading fees"""
        return trade_value * (strategy.execution_parameters.commission_pct / 100)
    
    def _calculate_comprehensive_metrics(
        self,
        portfolio: Portfolio,
        market_data: pd.DataFrame,
        strategy: Strategy,
        start_time: datetime
    ) -> BacktestResult:
        """Calculate comprehensive performance metrics"""
        # Convert portfolio history to DataFrame
        portfolio_df = pd.DataFrame(portfolio.portfolio_history)
        
        # Basic metrics
        completed_trades = [
            trade for trade in portfolio.trade_history 
            if trade.exit_time is not None and trade.net_pnl is not None
        ]
        
        winning_trades = [t for t in completed_trades if t.net_pnl > 0]
        losing_trades = [t for t in completed_trades if t.net_pnl <= 0]
        
        total_trades = len(completed_trades)
        winning_count = len(winning_trades)
        losing_count = len(losing_trades)
        
        win_rate = (winning_count / total_trades) * 100 if total_trades > 0 else 0
        
        # PnL metrics
        total_pnl = sum(t.net_pnl for t in completed_trades) if completed_trades else 0
        avg_profit = sum(t.net_pnl for t in winning_trades) / winning_count if winning_count > 0 else 0
        avg_loss = sum(t.net_pnl for t in losing_trades) / losing_count if losing_count > 0 else 0
        
        # Profit factor
        gross_profit = sum(t.gross_pnl for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.gross_pnl for t in losing_trades)) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Sharpe and Sortino Ratio calculations
        if len(portfolio_df) >= 2:
            # Calculate daily returns
            portfolio_df['daily_return'] = portfolio_df['portfolio_value'].pct_change()
            
            # Annualized measures - assume 252 trading days per year
            risk_free_rate = 0.01 / 252  # Assume 1% annual risk-free rate
            excess_returns = portfolio_df['daily_return'].dropna() - risk_free_rate
            
            annualized_return = portfolio_df['daily_return'].mean() * 252
            annualized_std_dev = portfolio_df['daily_return'].std() * (252 ** 0.5)
            
            # Downside returns
            downside_returns = excess_returns[excess_returns < 0]
            downside_std_dev = downside_returns.std() * (252 ** 0.5) if len(downside_returns) > 0 else 0.0001
            
            sharpe_ratio = (annualized_return - (0.01)) / annualized_std_dev if annualized_std_dev > 0 else 0
            sortino_ratio = (annualized_return - (0.01)) / downside_std_dev if downside_std_dev > 0 else 0
        else:
            sharpe_ratio = 0
            sortino_ratio = 0
        
        # Maximum Drawdown
        portfolio_df['peak'] = portfolio_df['portfolio_value'].cummax()
        portfolio_df['drawdown'] = (portfolio_df['portfolio_value'] - portfolio_df['peak']) / portfolio_df['peak'] * 100
        
        max_drawdown = portfolio_df['drawdown'].min()
        
        # Calculate drawdown metrics
        drawdown_metrics = self._calculate_detailed_drawdown_metrics(portfolio_df, portfolio_df['drawdown'])
        
        # Calculate trade duration metrics
        duration_metrics = self._calculate_trade_duration_metrics(
            completed_trades, winning_trades, losing_trades
        )
        
        # Calculate consecutive win/loss metrics
        consecutive_metrics = self._calculate_consecutive_metrics(completed_trades)
        
        # Compile all metrics
        performance_metrics = PerformanceMetrics(
            initial_capital=portfolio.initial_capital,
            ending_capital=portfolio.portfolio_value,
            total_return_pct=((portfolio.portfolio_value - portfolio.initial_capital) / portfolio.initial_capital) * 100,
            annualized_return=annualized_return * 100,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            drawdown_metrics=DrawdownMetrics(
                max_drawdown=max_drawdown,
                max_drawdown_duration=drawdown_metrics['max_drawdown_duration'],
                avg_drawdown=drawdown_metrics['avg_drawdown'],
                avg_drawdown_duration=drawdown_metrics['avg_drawdown_duration'],
                drawdown_frequency=drawdown_metrics['drawdown_frequency'],
                recovery_factor=drawdown_metrics['recovery_factor'],
                ulcer_index=drawdown_metrics['ulcer_index']
            ),
            total_trades=total_trades,
            winning_trades=winning_count,
            losing_trades=losing_count,
            win_rate=win_rate,
            profit_factor=profit_factor,
            average_profit=avg_profit,
            average_loss=avg_loss,
            average_profit_loss_ratio=abs(avg_profit / avg_loss) if avg_loss != 0 else float('inf'),
            trading_metrics=TradingMetrics(
                max_consecutive_wins=consecutive_metrics['max_consecutive_wins'],
                max_consecutive_losses=consecutive_metrics['max_consecutive_losses'],
                largest_winning_trade=consecutive_metrics['largest_winning_trade'],
                largest_losing_trade=consecutive_metrics['largest_losing_trade'],
                avg_winning_trade=avg_profit,
                avg_losing_trade=avg_loss,
                avg_trade_duration_minutes=duration_metrics['avg_duration_minutes'],
                avg_winning_trade_duration=duration_metrics['avg_winning_duration'],
                avg_losing_trade_duration=duration_metrics['avg_losing_duration']
            )
        )
        
        # Create full backtest result
        result = BacktestResult(
            strategy=strategy,
            performance=performance_metrics,
            equity_curve=portfolio_df['portfolio_value'].tolist(),
            drawdown=portfolio_df['drawdown'].tolist(),
            trades=[t.dict() for t in completed_trades],
            execution_time_sec=(datetime.now() - start_time).total_seconds(),
            status="completed",
            timestamp=datetime.now()
        )
        
        return result
    
    def _calculate_detailed_drawdown_metrics(self, portfolio_df: pd.DataFrame, drawdown: pd.Series) -> Dict:
        """Calculate detailed drawdown metrics"""
        if drawdown.empty:
            return {
                'max_drawdown': 0.0,
                'max_drawdown_duration': 0,
                'avg_drawdown': 0.0,
                'avg_drawdown_duration': 0,
                'drawdown_frequency': 0.0,
                'recovery_factor': 0.0,
                'ulcer_index': 0.0
            }
        
        # Max drawdown is already calculated
        max_dd = drawdown.min()
        
        # Calculate drawdown durations
        in_drawdown = drawdown < 0
        
        # Find drawdown periods
        drawdown_starts = ((in_drawdown) & (~in_drawdown.shift(1).fillna(False))).to_numpy().nonzero()[0]
        drawdown_ends = ((~in_drawdown) & (in_drawdown.shift(1).fillna(False))).to_numpy().nonzero()[0]
        
        # Handle case where we start in drawdown
        if in_drawdown.iloc[0]:
            drawdown_starts = np.insert(drawdown_starts, 0, 0)
        
        # Handle case where we end in drawdown
        if in_drawdown.iloc[-1]:
            drawdown_ends = np.append(drawdown_ends, len(drawdown) - 1)
        
        drawdown_periods = []
        
        for i in range(min(len(drawdown_starts), len(drawdown_ends))):
            if drawdown_starts[i] < drawdown_ends[i]:  # Valid drawdown period
                period_drawdown = drawdown.iloc[drawdown_starts[i]:drawdown_ends[i]+1]
                max_period_dd = period_drawdown.min()
                duration = drawdown_ends[i] - drawdown_starts[i] + 1
                
                drawdown_periods.append({
                    'start': drawdown_starts[i],
                    'end': drawdown_ends[i],
                    'max_drawdown': max_period_dd,
                    'duration': duration
                })
        
        # Calculate metrics
        if drawdown_periods:
            max_dd_duration = max(period['duration'] for period in drawdown_periods)
            avg_dd = sum(period['max_drawdown'] for period in drawdown_periods) / len(drawdown_periods)
            avg_duration = sum(period['duration'] for period in drawdown_periods) / len(drawdown_periods)
            dd_frequency = len(drawdown_periods) / len(portfolio_df) * 100
        else:
            max_dd_duration = 0
            avg_dd = 0.0
            avg_duration = 0
            dd_frequency = 0.0
        
        # Recovery factor = total return / max drawdown
        total_return = (portfolio_df['portfolio_value'].iloc[-1] - portfolio_df['portfolio_value'].iloc[0]) / portfolio_df['portfolio_value'].iloc[0]
        recovery_factor = abs(total_return / (max_dd / 100)) if max_dd != 0 else float('inf')
        
        # Ulcer Index (square root of the mean of squared drawdowns)
        squared_dd = np.square(drawdown / 100)  # Convert percentage to decimal
        ulcer_index = np.sqrt(squared_dd.mean()) * 100  # Convert back to percentage
        
        return {
            'max_drawdown': max_dd,
            'max_drawdown_duration': max_dd_duration,
            'avg_drawdown': avg_dd,
            'avg_drawdown_duration': avg_duration,
            'drawdown_frequency': dd_frequency,
            'recovery_factor': recovery_factor,
            'ulcer_index': ulcer_index
        }
    
    def _calculate_trade_duration_metrics(self, completed_trades: list, winning_trades: list, losing_trades: list) -> Dict:
        """Calculate trade duration metrics"""
        def get_duration_hours(trades):
            if not trades:
                return 0
            durations = [t.duration_minutes for t in trades if t.duration_minutes is not None]
            return sum(durations) / (len(durations) * 60) if durations else 0
        
        all_durations = [t.duration_minutes for t in completed_trades if t.duration_minutes is not None]
        winning_durations = [t.duration_minutes for t in winning_trades if t.duration_minutes is not None]
        losing_durations = [t.duration_minutes for t in losing_trades if t.duration_minutes is not None]
        
        return {
            'avg_duration_minutes': sum(all_durations) / len(all_durations) if all_durations else 0,
            'avg_winning_duration': sum(winning_durations) / len(winning_durations) if winning_durations else 0,
            'avg_losing_duration': sum(losing_durations) / len(losing_durations) if losing_durations else 0,
            'avg_duration_hours': get_duration_hours(completed_trades),
            'avg_winning_duration_hours': get_duration_hours(winning_trades),
            'avg_losing_duration_hours': get_duration_hours(losing_trades)
        }
    
    def _calculate_consecutive_metrics(self, completed_trades: list) -> Dict:
        """Calculate consecutive win/loss metrics"""
        if not completed_trades:
            return {
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0,
                'largest_winning_trade': 0,
                'largest_losing_trade': 0
            }
        
        # Set initial values
        consec_wins = 0
        consec_losses = 0
        max_consec_wins = 0
        max_consec_losses = 0
        largest_win = 0
        largest_loss = 0
        
        for trade in completed_trades:
            # Update consecutive counters
            if trade.net_pnl > 0:
                consec_wins += 1
                consec_losses = 0
                max_consec_wins = max(max_consec_wins, consec_wins)
                largest_win = max(largest_win, trade.net_pnl)
            else:
                consec_losses += 1
                consec_wins = 0
                max_consec_losses = max(max_consec_losses, consec_losses)
                largest_loss = min(largest_loss, trade.net_pnl)
        
        return {
            'max_consecutive_wins': max_consec_wins,
            'max_consecutive_losses': max_consec_losses,
            'largest_winning_trade': largest_win,
            'largest_losing_trade': abs(largest_loss)
        } 