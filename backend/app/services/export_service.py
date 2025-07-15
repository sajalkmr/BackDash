"""
Enhanced Export Service - Phase 4 Implementation
Comprehensive data export capabilities for analytics and backtest results
"""

import pandas as pd
import json
import io
import base64
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import asyncio
from pathlib import Path

# Optional dependencies for advanced exports
try:
    import xlsxwriter
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from ..models.analytics import CompleteAnalytics, ExportData
from ..models.backtest import BacktestResult

class EnhancedExportService:
    """Enhanced export service with multiple format support"""
    
    def __init__(self):
        self.supported_formats = ['JSON', 'CSV']
        if EXCEL_AVAILABLE:
            self.supported_formats.append('Excel')
        if PDF_AVAILABLE:
            self.supported_formats.append('PDF')
    
    async def export_analytics(
        self,
        analytics: CompleteAnalytics,
        backtest_result: BacktestResult,
        export_format: str,
        include_charts: bool = True,
        include_trade_details: bool = True,
        include_daily_data: bool = True,
        include_rolling_metrics: bool = True,
        include_benchmark_comparison: bool = True
    ) -> ExportData:
        """Export analytics data in specified format"""
        
        if export_format not in self.supported_formats:
            raise ValueError(f"Unsupported export format: {export_format}")
        
        export_id = f"export_{analytics.performance.backtest_id}_{datetime.now().isoformat()}"
        
        # Prepare base data
        export_data = ExportData(
            export_id=export_id,
            export_type=export_format,
            generated_at=datetime.now(),
            performance_data=self._prepare_performance_data(analytics),
            trade_data=self._prepare_trade_data(backtest_result),
            daily_data=self._prepare_daily_data(analytics),
            chart_configs=self._prepare_chart_configs(analytics) if include_charts else [],
            strategy_config=self._prepare_strategy_config(backtest_result),
            backtest_params=self._prepare_backtest_params(backtest_result)
        )
        
        # Generate format-specific content
        if export_format == 'JSON':
            export_data.export_content = await self._export_json(analytics, backtest_result)
        elif export_format == 'CSV':
            export_data.export_content = await self._export_csv(analytics, backtest_result)
        elif export_format == 'Excel' and EXCEL_AVAILABLE:
            export_data.export_content = await self._export_excel(analytics, backtest_result)
        elif export_format == 'PDF' and PDF_AVAILABLE:
            export_data.export_content = await self._export_pdf(analytics, backtest_result, include_charts)
        else:
            # Fallback to JSON if format not supported
            export_data.export_content = await self._export_json(analytics, backtest_result)
        
        return export_data
    
    def _prepare_performance_data(self, analytics: CompleteAnalytics) -> Dict[str, Any]:
        """Prepare performance data for export"""
        return {
            'core_metrics': {
                'total_return_pct': analytics.performance.core_metrics.pnl_percent,
                'total_return_dollars': analytics.performance.core_metrics.pnl_dollars,
                'cagr_pct': analytics.performance.core_metrics.cagr_percent,
                'sharpe_ratio': analytics.performance.core_metrics.sharpe_ratio,
                'sortino_ratio': analytics.performance.core_metrics.sortino_ratio,
                'calmar_ratio': analytics.performance.core_metrics.calmar_ratio,
                'max_drawdown_pct': analytics.performance.core_metrics.max_drawdown_percent,
                'max_drawdown_dollars': analytics.performance.core_metrics.max_drawdown_dollars,
                'volatility_pct': analytics.performance.core_metrics.volatility_percent
            },
            'trading_metrics': {
                'total_trades': analytics.performance.trading_metrics.total_trades,
                'win_rate_pct': analytics.performance.trading_metrics.win_rate_percent,
                'avg_trade_duration_hours': analytics.performance.trading_metrics.avg_trade_duration_hours,
                'largest_win_pct': analytics.performance.trading_metrics.largest_win_percent,
                'largest_loss_pct': analytics.performance.trading_metrics.largest_loss_percent,
                'profit_factor': analytics.performance.trading_metrics.profit_factor,
                'expectancy': analytics.performance.trading_metrics.expectancy,
                'max_consecutive_wins': analytics.performance.trading_metrics.max_consecutive_wins,
                'max_consecutive_losses': analytics.performance.trading_metrics.max_consecutive_losses
            },
            'risk_metrics': {
                'var_95_pct': analytics.performance.risk_metrics.value_at_risk_95,
                'var_99_pct': analytics.performance.risk_metrics.value_at_risk_99,
                'cvar_95_pct': analytics.performance.risk_metrics.conditional_var_95,
                'cvar_99_pct': analytics.performance.risk_metrics.conditional_var_99,
                'downside_deviation': analytics.performance.risk_metrics.downside_deviation,
                'omega_ratio': analytics.performance.risk_metrics.omega_ratio,
                'gain_pain_ratio': analytics.performance.risk_metrics.gain_pain_ratio,
                'ulcer_index': analytics.performance.trading_metrics.ulcer_index
            }
        }
    
    def _prepare_trade_data(self, backtest_result: BacktestResult) -> List[Dict[str, Any]]:
        """Prepare individual trade data for export"""
        trades_data = []
        
        for trade in backtest_result.trades:
            trade_dict = {
                'trade_id': trade.trade_id,
                'symbol': trade.symbol,
                'side': trade.side,
                'entry_time': trade.entry_time.isoformat() if trade.entry_time else None,
                'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'quantity': trade.quantity,
                'pnl_dollars': trade.pnl_dollars,
                'pnl_percent': trade.return_pct,
                'duration_hours': trade.duration_hours,
                'entry_reason': trade.entry_reason,
                'exit_reason': trade.exit_reason,
                'commission': getattr(trade, 'commission', 0),
                'slippage': getattr(trade, 'slippage', 0)
            }
            trades_data.append(trade_dict)
        
        return trades_data
    
    def _prepare_daily_data(self, analytics: CompleteAnalytics) -> List[Dict[str, Any]]:
        """Prepare daily portfolio data for export"""
        daily_data = []
        
        for i, equity_point in enumerate(analytics.equity_curve):
            daily_dict = {
                'date': equity_point['timestamp'],
                'portfolio_value': equity_point['value'],
                'total_return_pct': equity_point.get('return_pct', 0),
                'daily_return_pct': analytics.performance.daily_returns[i] if i < len(analytics.performance.daily_returns) else 0,
                'drawdown_pct': analytics.drawdown_chart[i]['drawdown'] if i < len(analytics.drawdown_chart) else 0
            }
            
            # Add rolling metrics if available
            if analytics.performance.rolling_sharpe and i < len(analytics.performance.rolling_sharpe):
                daily_dict['rolling_sharpe_30d'] = analytics.performance.rolling_sharpe[i]
            if analytics.performance.rolling_volatility and i < len(analytics.performance.rolling_volatility):
                daily_dict['rolling_volatility_30d'] = analytics.performance.rolling_volatility[i]
            
            daily_data.append(daily_dict)
        
        return daily_data
    
    def _prepare_chart_configs(self, analytics: CompleteAnalytics) -> List[Dict[str, Any]]:
        """Prepare chart configuration data for export"""
        chart_configs = []
        
        # Equity curve chart
        if analytics.equity_curve:
            chart_configs.append({
                'chart_type': 'equity_curve',
                'title': 'Portfolio Equity Curve',
                'data': analytics.equity_curve,
                'x_axis': 'timestamp',
                'y_axis': 'value',
                'chart_style': 'line'
            })
        
        # Drawdown chart
        if analytics.drawdown_chart:
            chart_configs.append({
                'chart_type': 'drawdown',
                'title': 'Portfolio Drawdown',
                'data': analytics.drawdown_chart,
                'x_axis': 'timestamp',
                'y_axis': 'drawdown',
                'chart_style': 'area'
            })
        
        # Returns distribution
        if analytics.returns_distribution:
            chart_configs.append({
                'chart_type': 'returns_distribution',
                'title': 'Daily Returns Distribution',
                'data': analytics.returns_distribution,
                'x_axis': 'bin_start',
                'y_axis': 'frequency',
                'chart_style': 'histogram'
            })
        
        # Monthly heatmap
        if analytics.monthly_heatmap:
            chart_configs.append({
                'chart_type': 'monthly_heatmap',
                'title': 'Monthly Returns Heatmap',
                'data': analytics.monthly_heatmap,
                'chart_style': 'heatmap'
            })
        
        return chart_configs
    
    def _prepare_strategy_config(self, backtest_result: BacktestResult) -> Dict[str, Any]:
        """Prepare strategy configuration for export"""
        return {
            'strategy_name': backtest_result.strategy_name,
            'symbol': backtest_result.symbol,
            'start_date': backtest_result.start_date.isoformat(),
            'end_date': backtest_result.end_date.isoformat(),
            'initial_capital': backtest_result.initial_capital,
            'strategy_type': getattr(backtest_result, 'strategy_type', 'Unknown'),
            'parameters': getattr(backtest_result, 'strategy_parameters', {})
        }
    
    def _prepare_backtest_params(self, backtest_result: BacktestResult) -> Dict[str, Any]:
        """Prepare backtest parameters for export"""
        return {
            'backtest_id': backtest_result.backtest_id,
            'created_at': backtest_result.created_at.isoformat(),
            'execution_time_seconds': getattr(backtest_result, 'execution_time_seconds', 0),
            'data_points': len(backtest_result.equity_curve) if backtest_result.equity_curve else 0,
            'commission_rate': getattr(backtest_result, 'commission_rate', 0),
            'slippage_rate': getattr(backtest_result, 'slippage_rate', 0)
        }
    
    async def _export_json(self, analytics: CompleteAnalytics, backtest_result: BacktestResult) -> str:
        """Export data as JSON"""
        export_dict = {
            'analytics': analytics.dict(),
            'backtest_result': {
                'backtest_id': backtest_result.backtest_id,
                'strategy_name': backtest_result.strategy_name,
                'symbol': backtest_result.symbol,
                'performance_summary': {
                    'total_return': backtest_result.performance_metrics.total_return_pct,
                    'annual_return': backtest_result.performance_metrics.annual_return_pct,
                    'volatility': backtest_result.performance_metrics.volatility_annual,
                    'sharpe_ratio': backtest_result.performance_metrics.sharpe_ratio,
                    'max_drawdown': backtest_result.drawdown_metrics.max_drawdown_pct
                },
                'trades_summary': {
                    'total_trades': backtest_result.trading_metrics.total_trades,
                    'win_rate': backtest_result.trading_metrics.win_rate_pct,
                    'profit_factor': backtest_result.trading_metrics.profit_factor
                }
            },
            'export_metadata': {
                'generated_at': datetime.now().isoformat(),
                'export_format': 'JSON',
                'data_version': '2.0'
            }
        }
        
        return json.dumps(export_dict, indent=2, default=str)
    
    async def _export_csv(self, analytics: CompleteAnalytics, backtest_result: BacktestResult) -> str:
        """Export data as CSV format (ZIP of multiple CSV files)"""
        csv_files = {}
        
        # Performance metrics CSV
        performance_df = pd.DataFrame([self._prepare_performance_data(analytics)['core_metrics']])
        csv_files['performance_metrics.csv'] = performance_df.to_csv(index=False)
        
        # Trading metrics CSV
        trading_df = pd.DataFrame([self._prepare_performance_data(analytics)['trading_metrics']])
        csv_files['trading_metrics.csv'] = trading_df.to_csv(index=False)
        
        # Risk metrics CSV
        risk_df = pd.DataFrame([self._prepare_performance_data(analytics)['risk_metrics']])
        csv_files['risk_metrics.csv'] = risk_df.to_csv(index=False)
        
        # Trades CSV
        if self._prepare_trade_data(backtest_result):
            trades_df = pd.DataFrame(self._prepare_trade_data(backtest_result))
            csv_files['trades.csv'] = trades_df.to_csv(index=False)
        
        # Daily data CSV
        if self._prepare_daily_data(analytics):
            daily_df = pd.DataFrame(self._prepare_daily_data(analytics))
            csv_files['daily_data.csv'] = daily_df.to_csv(index=False)
        
        # Monthly returns CSV
        if analytics.performance.monthly_returns:
            monthly_df = pd.DataFrame([mr.dict() for mr in analytics.performance.monthly_returns])
            csv_files['monthly_returns.csv'] = monthly_df.to_csv(index=False)
        
        # Return as concatenated CSV content (in real implementation, would create ZIP)
        return '\n\n'.join([f"=== {filename} ===\n{content}" for filename, content in csv_files.items()])
    
    async def _export_excel(self, analytics: CompleteAnalytics, backtest_result: BacktestResult) -> str:
        """Export data as Excel format"""
        if not EXCEL_AVAILABLE:
            raise ImportError("Excel export requires xlsxwriter package")
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1
            })
            
            currency_format = workbook.add_format({'num_format': '$#,##0.00'})
            percent_format = workbook.add_format({'num_format': '0.00%'})
            number_format = workbook.add_format({'num_format': '#,##0.00'})
            
            # Summary sheet
            summary_data = {
                'Metric': ['Total Return', 'CAGR', 'Sharpe Ratio', 'Max Drawdown', 'Volatility', 'Total Trades', 'Win Rate', 'Profit Factor'],
                'Value': [
                    analytics.performance.core_metrics.pnl_percent / 100,
                    analytics.performance.core_metrics.cagr_percent / 100,
                    analytics.performance.core_metrics.sharpe_ratio,
                    analytics.performance.core_metrics.max_drawdown_percent / 100,
                    analytics.performance.core_metrics.volatility_percent / 100,
                    analytics.performance.trading_metrics.total_trades,
                    analytics.performance.trading_metrics.win_rate_percent / 100,
                    analytics.performance.trading_metrics.profit_factor
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Performance metrics sheet
            perf_data = self._prepare_performance_data(analytics)
            perf_df = pd.DataFrame([perf_data['core_metrics']])
            perf_df.to_excel(writer, sheet_name='Performance', index=False)
            
            # Trades sheet
            if self._prepare_trade_data(backtest_result):
                trades_df = pd.DataFrame(self._prepare_trade_data(backtest_result))
                trades_df.to_excel(writer, sheet_name='Trades', index=False)
            
            # Daily data sheet
            if self._prepare_daily_data(analytics):
                daily_df = pd.DataFrame(self._prepare_daily_data(analytics))
                daily_df.to_excel(writer, sheet_name='Daily Data', index=False)
            
            # Apply formatting
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                worksheet.set_row(0, 20, header_format)
                worksheet.set_column('A:Z', 15)
        
        output.seek(0)
        return base64.b64encode(output.read()).decode('utf-8')
    
    async def _export_pdf(self, analytics: CompleteAnalytics, backtest_result: BacktestResult, include_charts: bool = True) -> str:
        """Export data as PDF format"""
        if not PDF_AVAILABLE:
            raise ImportError("PDF export requires reportlab package")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        story.append(Paragraph(f"Backtest Analytics Report", title_style))
        story.append(Paragraph(f"Strategy: {backtest_result.strategy_name}", styles['Heading2']))
        story.append(Paragraph(f"Symbol: {backtest_result.symbol}", styles['Normal']))
        story.append(Paragraph(f"Period: {backtest_result.start_date.strftime('%Y-%m-%d')} to {backtest_result.end_date.strftime('%Y-%m-%d')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Performance Summary Table
        story.append(Paragraph("Performance Summary", styles['Heading2']))
        
        performance_data = [
            ['Metric', 'Value'],
            ['Total Return', f"{analytics.performance.core_metrics.pnl_percent:.2f}%"],
            ['CAGR', f"{analytics.performance.core_metrics.cagr_percent:.2f}%"],
            ['Sharpe Ratio', f"{analytics.performance.core_metrics.sharpe_ratio:.2f}"],
            ['Sortino Ratio', f"{analytics.performance.core_metrics.sortino_ratio:.2f}"],
            ['Calmar Ratio', f"{analytics.performance.core_metrics.calmar_ratio:.2f}"],
            ['Max Drawdown', f"{analytics.performance.core_metrics.max_drawdown_percent:.2f}%"],
            ['Volatility', f"{analytics.performance.core_metrics.volatility_percent:.2f}%"]
        ]
        
        performance_table = Table(performance_data, colWidths=[3*inch, 2*inch])
        performance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(performance_table)
        story.append(Spacer(1, 20))
        
        # Trading Summary
        story.append(Paragraph("Trading Summary", styles['Heading2']))
        
        trading_data = [
            ['Metric', 'Value'],
            ['Total Trades', str(analytics.performance.trading_metrics.total_trades)],
            ['Win Rate', f"{analytics.performance.trading_metrics.win_rate_percent:.2f}%"],
            ['Profit Factor', f"{analytics.performance.trading_metrics.profit_factor:.2f}"],
            ['Avg Trade Duration', f"{analytics.performance.trading_metrics.avg_trade_duration_hours:.1f} hours"],
            ['Largest Win', f"{analytics.performance.trading_metrics.largest_win_percent:.2f}%"],
            ['Largest Loss', f"{analytics.performance.trading_metrics.largest_loss_percent:.2f}%"],
            ['Expectancy', f"{analytics.performance.trading_metrics.expectancy:.4f}"]
        ]
        
        trading_table = Table(trading_data, colWidths=[3*inch, 2*inch])
        trading_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(trading_table)
        story.append(Spacer(1, 20))
        
        # Risk Metrics
        story.append(Paragraph("Risk Analysis", styles['Heading2']))
        
        risk_data = [
            ['Metric', 'Value'],
            ['VaR (95%)', f"{analytics.performance.risk_metrics.value_at_risk_95:.2f}%"],
            ['VaR (99%)', f"{analytics.performance.risk_metrics.value_at_risk_99:.2f}%"],
            ['CVaR (95%)', f"{analytics.performance.risk_metrics.conditional_var_95:.2f}%"],
            ['Downside Deviation', f"{analytics.performance.risk_metrics.downside_deviation:.2f}%"],
            ['Omega Ratio', f"{analytics.performance.risk_metrics.omega_ratio:.2f}"],
            ['Gain/Pain Ratio', f"{analytics.performance.risk_metrics.gain_pain_ratio:.2f}"],
            ['Max Consecutive Losses', str(analytics.performance.risk_metrics.max_consecutive_losses)]
        ]
        
        risk_table = Table(risk_data, colWidths=[3*inch, 2*inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(risk_table)
        
        # Add benchmark comparison if available
        if analytics.benchmark_comparison:
            story.append(Spacer(1, 20))
            story.append(Paragraph("Benchmark Comparison", styles['Heading2']))
            
            benchmark_data = [
                ['Metric', 'Strategy', 'Benchmark', 'Difference'],
                ['Total Return', 
                 f"{analytics.benchmark_comparison.strategy_return:.2f}%",
                 f"{analytics.benchmark_comparison.benchmark_return:.2f}%",
                 f"{analytics.benchmark_comparison.excess_return:.2f}%"],
                ['Max Drawdown',
                 f"{analytics.benchmark_comparison.strategy_max_drawdown:.2f}%",
                 f"{analytics.benchmark_comparison.benchmark_max_drawdown:.2f}%",
                 f"{analytics.benchmark_comparison.strategy_max_drawdown - analytics.benchmark_comparison.benchmark_max_drawdown:.2f}%"]
            ]
            
            benchmark_table = Table(benchmark_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            benchmark_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(benchmark_table)
        
        # Footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=1
        )
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by GoQuant Analytics Engine", footer_style))
        
        doc.build(story)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats"""
        return self.supported_formats
    
    async def validate_export_request(self, export_format: str, analytics: CompleteAnalytics) -> bool:
        """Validate export request"""
        if export_format not in self.supported_formats:
            return False
        
        if not analytics or not analytics.performance:
            return False
        
        return True 