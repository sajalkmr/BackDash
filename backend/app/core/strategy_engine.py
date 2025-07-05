"""
Enhanced Strategy Engine - Advanced logic evaluation and signal processing
Strategic integration from 'mine' project with enhanced capabilities
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from ..models.strategy import LogicalExpression, LogicalCondition, Strategy

class StrategyEngine:
    """Enhanced engine for evaluating strategy conditions and signals"""
    
    def __init__(self):
        self.previous_indicators = {}
        self.signal_history = []
        
    def evaluate_conditions(
        self, 
        expression: LogicalExpression, 
        indicators: Dict[str, float], 
        current_bar: pd.Series,
        previous_bar: Optional[pd.Series] = None
    ) -> bool:
        """Evaluate a logical expression against current market data"""
        if not expression.conditions:
            return False
        
        condition_results = []
        for condition in expression.conditions:
            result = self._evaluate_condition(condition, indicators, current_bar, previous_bar)
            condition_results.append(result)
        
        if not expression.operators:
            return condition_results[0] if condition_results else False
        
        return self._apply_operators(condition_results, expression.operators)
    
    def _evaluate_condition(
        self, 
        condition: LogicalCondition, 
        indicators: Dict[str, float], 
        current_bar: pd.Series,
        previous_bar: Optional[pd.Series] = None
    ) -> bool:
        """Evaluate a single logical condition with enhanced operators"""
        if condition.operator in ["crosses_above", "crosses_below"]:
            return self._evaluate_crossover(condition, indicators, current_bar, previous_bar)
        
        left_value = self._get_operand_value(condition.left_operand, indicators, current_bar)
        right_value = self._get_operand_value(condition.right_operand, indicators, current_bar)
        
        if condition.operator == ">":
            return left_value > right_value
        elif condition.operator == "<":
            return left_value < right_value
        elif condition.operator == ">=":
            return left_value >= right_value
        elif condition.operator == "<=":
            return left_value <= right_value
        elif condition.operator == "=" or condition.operator == "==":
            return abs(left_value - right_value) < 1e-6  # Floating point equality
        elif condition.operator == "!=":
            return abs(left_value - right_value) >= 1e-6
        else:
            raise ValueError(f"Unsupported operator: {condition.operator}")
    
    def _evaluate_crossover(
        self,
        condition: LogicalCondition,
        indicators: Dict[str, float],
        current_bar: pd.Series,
        previous_bar: Optional[pd.Series] = None
    ) -> bool:
        """Evaluate crossover conditions (crosses_above, crosses_below)"""
        if previous_bar is None:
            return False
        
        left_current = self._get_operand_value(condition.left_operand, indicators, current_bar)
        right_current = self._get_operand_value(condition.right_operand, indicators, current_bar)
        
        if hasattr(self, 'previous_indicators') and self.previous_indicators:
            left_previous = self._get_operand_value(condition.left_operand, self.previous_indicators, previous_bar)
            right_previous = self._get_operand_value(condition.right_operand, self.previous_indicators, previous_bar)
        else:
            left_previous = left_current
            right_previous = right_current
        
        if condition.operator == "crosses_above":
            return (left_previous <= right_previous) and (left_current > right_current)
        elif condition.operator == "crosses_below":
            return (left_previous >= right_previous) and (left_current < right_current)
        
        return False
    
    def _get_operand_value(
        self, 
        operand: Any, 
        indicators: Dict[str, float], 
        current_bar: pd.Series
    ) -> float:
        """Get the numeric value of an operand with enhanced resolution"""
        if isinstance(operand, (int, float)):
            return float(operand)
        
        if isinstance(operand, str):
            operand_str = operand.lower()
            
            for indicator_name, value in indicators.items():
                if operand_str == indicator_name.lower():
                    return float(value) if not pd.isna(value) else 0.0
            
            price_fields = ['open', 'high', 'low', 'close', 'volume']
            if operand_str in price_fields:
                return float(current_bar[operand_str])
            
            if operand_str == 'hl2':
                return (float(current_bar['high']) + float(current_bar['low'])) / 2
            elif operand_str == 'hlc3':
                return (float(current_bar['high']) + float(current_bar['low']) + float(current_bar['close'])) / 3
            elif operand_str == 'ohlc4':
                return (float(current_bar['open']) + float(current_bar['high']) + 
                       float(current_bar['low']) + float(current_bar['close'])) / 4
            
            try:
                return float(operand)
            except ValueError:
                pass
            
            raise ValueError(f"Cannot resolve operand: {operand}")
        
        return 0.0
    
    def _apply_operators(self, results: List[bool], operators: List[str]) -> bool:
        """Apply logical operators to combine condition results with enhanced logic"""
        if len(results) == 1:
            return results[0]
        
        if len(operators) != len(results) - 1:
            raise ValueError("Number of operators must be one less than number of conditions")
        
        combined_result = results[0]
        
        for i, operator in enumerate(operators):
            next_result = results[i + 1]
            
            if operator.upper() == "AND":
                combined_result = combined_result and next_result
            elif operator.upper() == "OR":
                combined_result = combined_result or next_result
            elif operator.upper() == "NOT":
                combined_result = combined_result and (not next_result)
            else:
                raise ValueError(f"Unsupported logical operator: {operator}")
        
        return combined_result
    
    def validate_strategy(self, strategy: Strategy) -> Dict[str, Any]:
        """Validate strategy configuration and parameters"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks": {
                "indicators_valid": True,
                "conditions_valid": True,
                "risk_management_valid": True,
                "execution_parameters_valid": True
            }
        }
        
        try:
            for indicator in strategy.signal_generation.indicators:
                if indicator.period <= 0:
                    validation_result["errors"].append(f"Indicator {indicator.type} has invalid period: {indicator.period}")
                    validation_result["checks"]["indicators_valid"] = False
                
                if indicator.type == "macd":
                    if indicator.fast_period >= indicator.slow_period:
                        validation_result["errors"].append("MACD fast period must be less than slow period")
                        validation_result["checks"]["indicators_valid"] = False
            
            entry_conditions = strategy.signal_generation.entry_conditions
            exit_conditions = strategy.signal_generation.exit_conditions
            
            if not entry_conditions.conditions:
                validation_result["errors"].append("No entry conditions defined")
                validation_result["checks"]["conditions_valid"] = False
            
            if not exit_conditions.conditions:
                validation_result["warnings"].append("No exit conditions defined - using stop loss/take profit only")
            
            if (strategy.risk_management.stop_loss_pct and 
                strategy.risk_management.stop_loss_pct > 50):
                validation_result["warnings"].append("Stop loss > 50% may be too high")
            
            if strategy.execution_parameters.quantity_value <= 0:
                validation_result["errors"].append("Quantity value must be positive")
                validation_result["checks"]["execution_parameters_valid"] = False
            
            if strategy.execution_parameters.fees_bps > 1000:  # 10%
                validation_result["warnings"].append("Fees > 10% seem very high")
            
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["valid"] = False
        
        validation_result["valid"] = len(validation_result["errors"]) == 0
        
        return validation_result
    
    def update_previous_state(self, indicators: Dict[str, float]):
        """Update previous indicators for crossover calculations"""
        self.previous_indicators = indicators.copy()
    
    def get_signal_summary(self, strategy: Strategy, indicators: Dict, current_bar: pd.Series) -> Dict:
        """Get detailed signal analysis"""
        entry_signal = self.evaluate_conditions(
            strategy.signal_generation.entry_conditions,
            indicators,
            current_bar
        )
        
        exit_signal = self.evaluate_conditions(
            strategy.signal_generation.exit_conditions,
            indicators,
            current_bar
        )
        
        return {
            "entry_signal": entry_signal,
            "exit_signal": exit_signal,
            "indicators": indicators,
            "current_price": float(current_bar['close']),
            "timestamp": current_bar.name.isoformat() if hasattr(current_bar.name, 'isoformat') else str(current_bar.name)
        } 