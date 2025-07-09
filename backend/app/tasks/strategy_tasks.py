"""
Celery tasks for strategy validation and processing
"""

from celery import current_task
from typing import Dict, Any
import asyncio
from datetime import datetime

from ..celery_app import celery_app
from ..core.strategy_engine import StrategyEngine
from ..models.strategy import Strategy
from ..core.websocket_manager import manager
from ..core.redis_manager import redis_manager

@celery_app.task(bind=True, name="validate_strategy_task")
def validate_strategy_task(self, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate strategy configuration in background
    
    Args:
        strategy_data: Strategy configuration dictionary
        
    Returns:
        Validation result dictionary
    """
    task_id = self.request.id
    
    try:
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={
                'stage': 'validation',
                'progress': 0,
                'message': 'Starting strategy validation...',
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Store task info in Redis
        redis_manager.store_task_info(task_id, {
            'type': 'strategy_validation',
            'status': 'running',
            'progress': 0,
            'message': 'Starting strategy validation...',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })
        
        # Progress callback
        def progress_callback(progress: float, message: str):
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'stage': 'validation',
                    'progress': int(progress),
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            redis_manager.update_task_progress(task_id, int(progress), message)
            
            # Broadcast via WebSocket
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(manager.broadcast_progress(task_id, {
                    'task_id': task_id,
                    'status': 'running',
                    'progress': int(progress),
                    'message': message
                }))
            except RuntimeError:
                pass
        
        # Initialize strategy engine
        strategy_engine = StrategyEngine()
        
        # Parse strategy
        progress_callback(20, "Parsing strategy configuration...")
        strategy = Strategy.parse_obj(strategy_data)
        
        # Validate indicators
        progress_callback(40, "Validating technical indicators...")
        indicator_validation = []
        for indicator in strategy.signal_generation.indicators:
            validation_result = {
                'indicator': indicator.type,
                'valid': True,
                'issues': []
            }
            
            # Check indicator parameters
            if indicator.period <= 0:
                validation_result['valid'] = False
                validation_result['issues'].append("Period must be positive")
            
            if indicator.type == "macd":
                if indicator.fast_period >= indicator.slow_period:
                    validation_result['valid'] = False
                    validation_result['issues'].append("Fast period must be less than slow period")
            
            indicator_validation.append(validation_result)
        
        # Validate conditions
        progress_callback(60, "Validating entry/exit conditions...")
        condition_validation = {
            'entry_conditions_valid': len(strategy.signal_generation.entry_conditions) > 0,
            'exit_conditions_valid': len(strategy.signal_generation.exit_conditions) > 0,
            'logical_structure_valid': True
        }
        
        # Validate risk management
        progress_callback(80, "Validating risk management...")
        risk_validation = {
            'stop_loss_valid': True,
            'take_profit_valid': True,
            'position_sizing_valid': True
        }
        
        if strategy.risk_management.stop_loss_pct is not None:
            if strategy.risk_management.stop_loss_pct <= 0 or strategy.risk_management.stop_loss_pct > 100:
                risk_validation['stop_loss_valid'] = False
        
        if strategy.risk_management.take_profit_pct is not None:
            if strategy.risk_management.take_profit_pct <= 0:
                risk_validation['take_profit_valid'] = False
        
        # Compile final result
        progress_callback(100, "Validation completed")
        
        validation_result = {
            'strategy_name': strategy.name,
            'overall_valid': all([
                all(ind['valid'] for ind in indicator_validation),
                condition_validation['entry_conditions_valid'],
                condition_validation['exit_conditions_valid'],
                risk_validation['stop_loss_valid'],
                risk_validation['take_profit_valid'],
                risk_validation['position_sizing_valid']
            ]),
            'indicator_validation': indicator_validation,
            'condition_validation': condition_validation,
            'risk_validation': risk_validation,
            'validation_timestamp': datetime.now().isoformat()
        }
        
        # Store result
        redis_manager.store_task_result(task_id, validation_result)
        
        # Final status update
        current_task.update_state(
            state='SUCCESS',
            meta={
                'stage': 'completed',
                'progress': 100,
                'message': 'Strategy validation completed',
                'timestamp': datetime.now().isoformat(),
                'result': validation_result
            }
        )
        
        return validation_result
        
    except Exception as e:
        error_message = f"Strategy validation failed: {str(e)}"
        
        current_task.update_state(
            state='FAILURE',
            meta={
                'stage': 'failed',
                'progress': 0,
                'message': error_message,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
        )
        
        redis_manager.store_task_error(task_id, str(e))
        raise

@celery_app.task(name="optimize_strategy_task")
def optimize_strategy_task(
    strategy_data: Dict[str, Any],
    optimization_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Optimize strategy parameters (placeholder for future implementation)
    
    Args:
        strategy_data: Strategy configuration
        optimization_params: Optimization parameters
        
    Returns:
        Optimization results
    """
    # Placeholder implementation
    return {
        'optimized_parameters': {},
        'optimization_score': 0.0,
        'message': 'Strategy optimization not yet implemented'
    } 