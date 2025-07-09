import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Download, FileText, FileSpreadsheet, FileImage, 
  Database, Settings, CheckCircle, AlertCircle, 
  Clock, Zap
} from 'lucide-react';

interface ExportOptions {
  format: 'JSON' | 'CSV' | 'Excel' | 'PDF';
  includeCharts: boolean;
  includeTradeDetails: boolean;
  includeDailyData: boolean;
  includeRollingMetrics: boolean;
  includeBenchmarkComparison: boolean;
}

interface ExportProgress {
  status: 'idle' | 'preparing' | 'generating' | 'completed' | 'error';
  progress: number;
  message: string;
  downloadUrl?: string;
}

interface ExportAnalyticsProps {
  backtestId: string;
  className?: string;
}

export const ExportAnalytics: React.FC<ExportAnalyticsProps> = ({
  backtestId,
  className = ""
}) => {
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'JSON',
    includeCharts: true,
    includeTradeDetails: true,
    includeDailyData: true,
    includeRollingMetrics: true,
    includeBenchmarkComparison: true
  });

  const [exportProgress, setExportProgress] = useState<ExportProgress>({
    status: 'idle',
    progress: 0,
    message: 'Ready to export'
  });

  const [availableFormats] = useState([
    { value: 'JSON', label: 'JSON', icon: Database, description: 'Machine-readable format with all data' },
    { value: 'CSV', label: 'CSV', icon: FileSpreadsheet, description: 'Comma-separated values for spreadsheets' },
    { value: 'Excel', label: 'Excel', icon: FileSpreadsheet, description: 'Multi-sheet Excel workbook' },
    { value: 'PDF', label: 'PDF', icon: FileText, description: 'Professional report format' }
  ]);

  const handleExport = async () => {
    setExportProgress({
      status: 'preparing',
      progress: 10,
      message: 'Preparing export...'
    });

    try {
      // Step 1: Validate analytics exist
      const analyticsResponse = await fetch(`/api/v1/analytics/get/${backtestId}`);
      if (!analyticsResponse.ok) {
        throw new Error('Analytics data not found. Please generate analytics first.');
      }

      setExportProgress({
        status: 'generating',
        progress: 30,
        message: 'Generating export file...'
      });

      // Step 2: Request export
      const exportResponse = await fetch(`/api/v1/analytics/export/${backtestId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          export_format: exportOptions.format,
          include_charts: exportOptions.includeCharts,
          include_trade_details: exportOptions.includeTradeDetails,
          include_daily_data: exportOptions.includeDailyData,
          include_rolling_metrics: exportOptions.includeRollingMetrics,
          include_benchmark_comparison: exportOptions.includeBenchmarkComparison
        })
      });

      if (!exportResponse.ok) {
        throw new Error(`Export failed: ${exportResponse.statusText}`);
      }

      setExportProgress({
        status: 'generating',
        progress: 70,
        message: 'Processing data...'
      });

      const exportData = await exportResponse.json();
      
      setExportProgress({
        status: 'generating',
        progress: 90,
        message: 'Finalizing export...'
      });

      // Step 3: Create download
      await createDownload(exportData.export_data, exportOptions.format);

      setExportProgress({
        status: 'completed',
        progress: 100,
        message: 'Export completed successfully!'
      });

    } catch (error) {
      setExportProgress({
        status: 'error',
        progress: 0,
        message: error instanceof Error ? error.message : 'Export failed'
      });
    }
  };

  const createDownload = async (exportData: any, format: string) => {
    let content: string;
    let mimeType: string;
    let fileName: string;

    switch (format) {
      case 'JSON':
        content = JSON.stringify(exportData, null, 2);
        mimeType = 'application/json';
        fileName = `analytics_${backtestId}_${new Date().toISOString().split('T')[0]}.json`;
        break;
      
      case 'CSV':
        content = exportData.export_content || '';
        mimeType = 'text/csv';
        fileName = `analytics_${backtestId}_${new Date().toISOString().split('T')[0]}.csv`;
        break;
      
      case 'Excel':
        // For base64 encoded Excel files
        const binaryString = atob(exportData.export_content);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const blob = new Blob([bytes], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        const url = URL.createObjectURL(blob);
        fileName = `analytics_${backtestId}_${new Date().toISOString().split('T')[0]}.xlsx`;
        
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        a.click();
        URL.revokeObjectURL(url);
        return;
      
      case 'PDF':
        // For base64 encoded PDF files
        const pdfBinaryString = atob(exportData.export_content);
        const pdfBytes = new Uint8Array(pdfBinaryString.length);
        for (let i = 0; i < pdfBinaryString.length; i++) {
          pdfBytes[i] = pdfBinaryString.charCodeAt(i);
        }
        const pdfBlob = new Blob([pdfBytes], { type: 'application/pdf' });
        const pdfUrl = URL.createObjectURL(pdfBlob);
        fileName = `analytics_${backtestId}_${new Date().toISOString().split('T')[0]}.pdf`;
        
        const pdfLink = document.createElement('a');
        pdfLink.href = pdfUrl;
        pdfLink.download = fileName;
        pdfLink.click();
        URL.revokeObjectURL(pdfUrl);
        return;
      
      default:
        throw new Error(`Unsupported format: ${format}`);
    }

    // For text-based formats
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    a.click();
    
    URL.revokeObjectURL(url);
  };

  const resetExport = () => {
    setExportProgress({
      status: 'idle',
      progress: 0,
      message: 'Ready to export'
    });
  };

  const getStatusIcon = () => {
    switch (exportProgress.status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      case 'preparing':
      case 'generating':
        return <Clock className="h-5 w-5 text-blue-600 animate-spin" />;
      default:
        return <Zap className="h-5 w-5 text-gray-600" />;
    }
  };

  const getStatusColor = () => {
    switch (exportProgress.status) {
      case 'completed':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      case 'preparing':
      case 'generating':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  const isExporting = exportProgress.status === 'preparing' || exportProgress.status === 'generating';

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Download className="h-5 w-5" />
          Export Analytics
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Export Format Selection */}
        <div className="space-y-3">
          <label className="text-sm font-medium">Export Format</label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {availableFormats.map((format) => {
              const IconComponent = format.icon;
              return (
                <div
                  key={format.value}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    exportOptions.format === format.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setExportOptions(prev => ({ ...prev, format: format.value as any }))}
                >
                  <div className="flex items-center gap-3">
                    <IconComponent className="h-6 w-6 text-gray-600" />
                    <div>
                      <p className="font-medium">{format.label}</p>
                      <p className="text-xs text-gray-600">{format.description}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Export Options */}
        <div className="space-y-3">
          <label className="text-sm font-medium">Export Options</label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="includeCharts"
                  checked={exportOptions.includeCharts}
                  onCheckedChange={(checked) => 
                    setExportOptions(prev => ({ ...prev, includeCharts: checked as boolean }))
                  }
                />
                <label htmlFor="includeCharts" className="text-sm">Include Charts & Visualizations</label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="includeTradeDetails"
                  checked={exportOptions.includeTradeDetails}
                  onCheckedChange={(checked) => 
                    setExportOptions(prev => ({ ...prev, includeTradeDetails: checked as boolean }))
                  }
                />
                <label htmlFor="includeTradeDetails" className="text-sm">Include Individual Trade Details</label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="includeDailyData"
                  checked={exportOptions.includeDailyData}
                  onCheckedChange={(checked) => 
                    setExportOptions(prev => ({ ...prev, includeDailyData: checked as boolean }))
                  }
                />
                <label htmlFor="includeDailyData" className="text-sm">Include Daily Portfolio Data</label>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="includeRollingMetrics"
                  checked={exportOptions.includeRollingMetrics}
                  onCheckedChange={(checked) => 
                    setExportOptions(prev => ({ ...prev, includeRollingMetrics: checked as boolean }))
                  }
                />
                <label htmlFor="includeRollingMetrics" className="text-sm">Include Rolling Metrics</label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="includeBenchmarkComparison"
                  checked={exportOptions.includeBenchmarkComparison}
                  onCheckedChange={(checked) => 
                    setExportOptions(prev => ({ ...prev, includeBenchmarkComparison: checked as boolean }))
                  }
                />
                <label htmlFor="includeBenchmarkComparison" className="text-sm">Include Benchmark Comparison</label>
              </div>
            </div>
          </div>
        </div>

        {/* Export Status */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Export Status</span>
            <Badge variant={exportProgress.status === 'completed' ? 'default' : 'secondary'}>
              {exportProgress.status.toUpperCase()}
            </Badge>
          </div>

          <div className="flex items-center gap-3">
            {getStatusIcon()}
            <span className={`text-sm ${getStatusColor()}`}>
              {exportProgress.message}
            </span>
          </div>

          {isExporting && (
            <Progress value={exportProgress.progress} className="w-full" />
          )}
        </div>

        {/* Export Actions */}
        <div className="flex items-center justify-between pt-4 border-t">
          <div className="text-xs text-gray-600">
            {exportOptions.format === 'PDF' ? 'Professional report format' :
             exportOptions.format === 'Excel' ? 'Multi-sheet workbook with formatting' :
             exportOptions.format === 'CSV' ? 'Multiple CSV files for analysis' :
             'Complete data in machine-readable format'}
          </div>

          <div className="flex items-center gap-2">
            {exportProgress.status === 'completed' && (
              <Button variant="outline" onClick={resetExport}>
                Export Again
              </Button>
            )}
            
            {exportProgress.status === 'error' && (
              <Button variant="outline" onClick={resetExport}>
                Reset
              </Button>
            )}

            <Button 
              onClick={handleExport}
              disabled={isExporting}
              className="flex items-center gap-2"
            >
              {isExporting ? (
                <>
                  <Clock className="h-4 w-4 animate-spin" />
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4" />
                  Export Data
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Format-specific information */}
        <div className="text-xs text-gray-600 bg-gray-50 p-3 rounded">
          <p className="font-medium mb-1">Export Details:</p>
          {exportOptions.format === 'JSON' && (
            <p>Includes complete analytics data, backtest results, and metadata in JSON format.</p>
          )}
          {exportOptions.format === 'CSV' && (
            <p>Multiple CSV files: performance metrics, trades, daily data, and risk analysis.</p>
          )}
          {exportOptions.format === 'Excel' && (
            <p>Multi-sheet Excel workbook with formatted tables, charts, and summary dashboard.</p>
          )}
          {exportOptions.format === 'PDF' && (
            <p>Professional PDF report with tables, charts, and detailed performance analysis.</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}; 