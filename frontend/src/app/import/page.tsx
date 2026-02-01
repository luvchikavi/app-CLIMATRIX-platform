'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import { usePeriods, useOrganization, useSites } from '@/hooks/useEmissions';
import { api, ImportPreview, ImportResult, SmartImportResult, UnifiedImportPreview, UnifiedImportResult, UnifiedSheetPreview } from '@/lib/api';
import { AppShell } from '@/components/layout';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  ScopeBadge,
} from '@/components/ui';
import { cn, formatCO2e } from '@/lib/utils';
import {
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  ArrowLeft,
  Download,
  Trash2,
  Play,
  FileText,
  Sparkles,
  Brain,
  Zap,
  Layers,
  Eye,
  ChevronDown,
  ChevronRight,
  Activity,
  BarChart3,
  Building2,
  MapPin,
  Calendar,
} from 'lucide-react';
import { ImportHistory } from '@/components/ImportHistory';
import { useActivities } from '@/hooks/useEmissions';
import { useQueryClient } from '@tanstack/react-query';

type ImportStep = 'upload' | 'preview' | 'unified-preview' | 'importing' | 'result';
type ImportMode = 'standard' | 'smart' | 'unified';

function ImportContent() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { selectedPeriodId, setSelectedPeriodId } = usePeriodStore();

  const [step, setStep] = useState<ImportStep>('upload');
  const [importMode, setImportMode] = useState<ImportMode>('standard');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [smartResult, setSmartResult] = useState<SmartImportResult | null>(null);
  const [unifiedPreview, setUnifiedPreview] = useState<UnifiedImportPreview | null>(null);
  const [unifiedResult, setUnifiedResult] = useState<UnifiedImportResult | null>(null);
  const [selectedSheets, setSelectedSheets] = useState<Set<string>>(new Set());
  const [expandedSheets, setExpandedSheets] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [showBatchDetails, setShowBatchDetails] = useState(false);
  const [batchActivities, setBatchActivities] = useState<Array<{
    id: string;
    scope: number;
    category_code: string;
    activity_key: string;
    description: string;
    quantity: number;
    unit: string;
    activity_date: string | null;
    emission: {
      co2e_kg: number | null;
      factor_value: number | null;
      factor_unit: string | null;
      factor_source: string | null;
      formula: string | null;
    } | null;
  }>>([]);
  const [loadingBatchDetails, setLoadingBatchDetails] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [selectedSiteId, setSelectedSiteId] = useState<string | null>(null);

  const [mounted, setMounted] = useState(false);
  const queryClient = useQueryClient();

  // All data fetching hooks (must be before any conditional returns)
  const { data: periods } = usePeriods();
  const { data: organization } = useOrganization();
  const { data: sites } = useSites();

  // Use shared period store, fallback to first period
  const periodId = selectedPeriodId || periods?.[0]?.id;
  const currentPeriod = periods?.find((p) => p.id === periodId);

  // Set default period if none selected
  useEffect(() => {
    if (periods?.length && !selectedPeriodId) {
      setSelectedPeriodId(periods[0].id);
    }
  }, [periods, selectedPeriodId, setSelectedPeriodId]);

  // Fetch activities to show current data status
  const { data: activities, isLoading: activitiesLoading } = useActivities(periodId || '');

  // All useCallback hooks (must be before any conditional returns)
  const handleFileSelect = useCallback(async (selectedFile: File) => {
    const fileName = selectedFile.name.toLowerCase();
    if (!fileName.endsWith('.csv') && !fileName.endsWith('.xlsx')) {
      setError('Please upload a CSV or Excel (.xlsx) file');
      return;
    }

    setFile(selectedFile);
    setError(null);
    setIsLoading(true);

    try {
      if (!periodId) throw new Error('No reporting period selected');
      const previewData = await api.previewImport(periodId, selectedFile);
      setPreview(previewData);
      setStep('preview');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to preview file');
    } finally {
      setIsLoading(false);
    }
  }, [periodId]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      if (importMode === 'unified') {
        handleUnifiedFileSelect(droppedFile);
      } else if (importMode === 'smart') {
        handleSmartFileSelect(droppedFile);
      } else {
        handleFileSelect(droppedFile);
      }
    }
  }, [handleFileSelect, importMode]);

  // Unified AI Import handler
  const handleUnifiedFileSelect = useCallback(async (selectedFile: File) => {
    const fileName = selectedFile.name.toLowerCase();
    if (!fileName.endsWith('.csv') && !fileName.endsWith('.xlsx') && !fileName.endsWith('.xls')) {
      setError('Please upload a CSV or Excel (.xlsx, .xls) file');
      return;
    }

    setFile(selectedFile);
    setError(null);
    setIsLoading(true);

    try {
      const unifiedPreviewData = await api.unifiedImportPreview(selectedFile);
      setUnifiedPreview(unifiedPreviewData);

      // Auto-select all importable sheets
      const importableSheets = new Set<string>(
        unifiedPreviewData.sheets
          .filter(s => s.is_importable)
          .map(s => s.sheet_name)
      );
      setSelectedSheets(importableSheets);

      setStep('unified-preview');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unified import analysis failed');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleUnifiedImport = async () => {
    if (!file || !periodId || !unifiedPreview) return;

    setStep('importing');
    setError(null);

    try {
      const unifiedResultData = await api.unifiedImport(periodId, file, selectedSiteId || undefined);
      setUnifiedResult(unifiedResultData);
      setStep('result');

      // Invalidate all relevant queries to refresh dashboard data
      queryClient.invalidateQueries({ queryKey: ['activities'] });
      queryClient.invalidateQueries({ queryKey: ['import-batches'] });
      queryClient.invalidateQueries({ queryKey: ['report-summary'] });
      queryClient.invalidateQueries({ queryKey: ['periods'] });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unified import failed');
      setStep('unified-preview');
    }
  };

  const toggleSheetSelection = (sheetName: string) => {
    const newSelected = new Set(selectedSheets);
    if (newSelected.has(sheetName)) {
      newSelected.delete(sheetName);
    } else {
      newSelected.add(sheetName);
    }
    setSelectedSheets(newSelected);
  };

  const toggleSheetExpanded = (sheetName: string) => {
    const newExpanded = new Set(expandedSheets);
    if (newExpanded.has(sheetName)) {
      newExpanded.delete(sheetName);
    } else {
      newExpanded.add(sheetName);
    }
    setExpandedSheets(newExpanded);
  };

  // Smart Import handler
  const handleSmartFileSelect = useCallback(async (selectedFile: File) => {
    const fileName = selectedFile.name.toLowerCase();
    if (!fileName.endsWith('.csv') && !fileName.endsWith('.xlsx')) {
      setError('Please upload a CSV or Excel (.xlsx) file');
      return;
    }

    setFile(selectedFile);
    setError(null);
    setIsLoading(true);

    try {
      if (!periodId) throw new Error('No reporting period selected');
      const smartResultData = await api.smartImport(periodId, selectedFile);
      setSmartResult(smartResultData);
      setStep('result');

      // Invalidate all relevant queries to refresh dashboard data
      queryClient.invalidateQueries({ queryKey: ['activities'] });
      queryClient.invalidateQueries({ queryKey: ['import-batches'] });
      queryClient.invalidateQueries({ queryKey: ['report-summary'] });
      queryClient.invalidateQueries({ queryKey: ['periods'] });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Smart import failed');
    } finally {
      setIsLoading(false);
    }
  }, [periodId, queryClient]);

  // All useEffect hooks
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isAuthenticated) {
      router.push('/');
    }
  }, [mounted, isAuthenticated, router]);

  // Conditional return AFTER all hooks
  if (!mounted || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  const handleImport = async () => {
    if (!file || !periodId) return;

    setStep('importing');
    setError(null);

    try {
      const importResult = await api.importActivities(periodId, file, selectedSiteId || undefined);
      setResult(importResult);
      setStep('result');

      // Invalidate all relevant queries to refresh dashboard data
      queryClient.invalidateQueries({ queryKey: ['activities'] });
      queryClient.invalidateQueries({ queryKey: ['import-batches'] });
      queryClient.invalidateQueries({ queryKey: ['report-summary'] });
      queryClient.invalidateQueries({ queryKey: ['periods'] });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed');
      setStep('preview');
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setSmartResult(null);
    setUnifiedPreview(null);
    setUnifiedResult(null);
    setSelectedSheets(new Set());
    setExpandedSheets(new Set());
    setError(null);
    setStep('upload');
    setShowBatchDetails(false);
    setBatchActivities([]);
  };

  const loadBatchActivities = async (batchId: string) => {
    setLoadingBatchDetails(true);
    try {
      const data = await api.getImportBatchActivities(batchId);
      setBatchActivities(data.activities);
      setShowBatchDetails(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load batch activities');
    } finally {
      setLoadingBatchDetails(false);
    }
  };

  // Clear period data handler
  const handleClearPeriodData = async () => {
    if (!periodId) return;

    const confirmed = confirm(
      `⚠️ Delete ALL activities for ${currentPeriod?.name || 'this period'}?\n\n` +
      `This will permanently delete:\n` +
      `• ${activities?.length || 0} activities\n` +
      `• All associated emissions\n` +
      `• All import batches\n\n` +
      `This action cannot be undone.`
    );

    if (!confirmed) return;

    setIsClearing(true);
    try {
      const result = await api.deletePeriodActivities(periodId);
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['activities'] });
      queryClient.invalidateQueries({ queryKey: ['import-batches'] });
      queryClient.invalidateQueries({ queryKey: ['report-summary'] });
      setError(null);
      alert(`✅ Successfully deleted ${result.deleted_activities} activities and ${result.deleted_emissions} emissions.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clear data');
    } finally {
      setIsClearing(false);
    }
  };

  // Clear ALL organization data handler
  const handleClearAllData = async () => {
    const confirmed = confirm(
      `🚨 DELETE ALL DATA for your organization?\n\n` +
      `This will permanently delete:\n` +
      `• ALL activities across ALL periods\n` +
      `• ALL associated emissions\n` +
      `• ALL import batches\n\n` +
      `⚠️ THIS ACTION CANNOT BE UNDONE!\n\n` +
      `Type "DELETE" in the next prompt to confirm.`
    );

    if (!confirmed) return;

    const doubleConfirm = prompt('Type "DELETE" to confirm deleting ALL organization data:');
    if (doubleConfirm !== 'DELETE') {
      alert('Operation cancelled. Data was NOT deleted.');
      return;
    }

    setIsClearing(true);
    try {
      const result = await api.deleteOrganizationActivities(true);
      // Invalidate all queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['activities'] });
      queryClient.invalidateQueries({ queryKey: ['import-batches'] });
      queryClient.invalidateQueries({ queryKey: ['report-summary'] });
      setError(null);
      alert(`✅ Successfully deleted ALL data: ${result.deleted_activities} activities and ${result.deleted_emissions} emissions.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clear data');
    } finally {
      setIsClearing(false);
    }
  };

  const downloadTemplate = async (scope: '1-2' | '3') => {
    try {
      await api.downloadTemplate(scope);
    } catch (err) {
      setError('Failed to download template');
    }
  };

  // Export import results as CSV
  const exportImportResults = () => {
    if (!batchActivities || batchActivities.length === 0) {
      setError('No activities to export. Click "View Activities with EF" first.');
      return;
    }

    // Build CSV content
    const headers = [
      'Scope',
      'Category Code',
      'Activity Key',
      'Description',
      'Quantity',
      'Unit',
      'Activity Date',
      'Emission Factor',
      'Factor Unit',
      'CO2e (kg)',
      'Factor Source'
    ];

    const rows = batchActivities.map(act => [
      act.scope,
      act.category_code,
      act.activity_key,
      `"${(act.description || '').replace(/"/g, '""')}"`, // Escape quotes in description
      act.quantity,
      act.unit,
      act.activity_date || '',
      act.emission?.factor_value || '',
      act.emission?.factor_unit || '',
      act.emission?.co2e_kg || '',
      act.emission?.factor_source || ''
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    // Download as CSV
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `import_results_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  // Export import error log as CSV
  const exportErrorLog = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let errors: Array<any> = [];

    if (result?.errors && result.errors.length > 0) {
      errors = result.errors;
    } else if (unifiedResult?.errors && unifiedResult.errors.length > 0) {
      errors = unifiedResult.errors;
    }

    if (errors.length === 0) {
      setError('No errors to export.');
      return;
    }

    // Build CSV content with enhanced columns
    const headers = ['Row', 'Sheet', 'Activity Key', 'Category', 'Quantity', 'Unit', 'Error'];
    const rows = errors.map(err => [
      err.row || '',
      err.sheet || '',
      err.activity_key || '',
      err.category_code || '',
      err.quantity !== undefined ? err.quantity : '',
      err.unit || '',
      `"${(Array.isArray(err.errors) ? err.errors.join('; ') : (err.error || err.errors || '')).replace(/"/g, '""')}"`
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    // Download as CSV
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `import_errors_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  return (
    <AppShell>
      {/* Compact Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/dashboard')}
            leftIcon={<ArrowLeft className="w-4 h-4" />}
          >
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Import Activities</h1>
          </div>
        </div>

        {/* Compact Info Bar */}
        {step === 'upload' && (
          <div className="flex items-center gap-4">
            {/* Organization */}
            {organization && (
              <div className="flex items-center gap-1.5 text-foreground-muted">
                <Building2 className="w-4 h-4" />
                <span className="text-sm font-medium">{organization.name}</span>
              </div>
            )}

            {/* Period Selector */}
            {periods && periods.length > 0 && (
              <select
                value={periodId || ''}
                onChange={(e) => setSelectedPeriodId(e.target.value)}
                className="h-9 px-3 text-sm font-medium border border-primary/30 rounded-lg bg-primary/5 text-primary focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {periods.map((period) => (
                  <option key={period.id} value={period.id}>
                    {period.name}
                  </option>
                ))}
              </select>
            )}

            {/* Activity Count */}
            {!activitiesLoading && activities && (
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-background-muted rounded-lg">
                <Activity className="w-4 h-4 text-foreground-muted" />
                <span className="text-sm font-medium text-foreground">
                  {activities.length} activities
                </span>
              </div>
            )}

            {/* Site Selector (if available) */}
            {sites && sites.length > 0 && (
              <select
                value={selectedSiteId || ''}
                onChange={(e) => setSelectedSiteId(e.target.value || null)}
                className="h-9 px-3 text-sm border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">All Sites</option>
                {sites.filter(s => s.is_active).map((site) => (
                  <option key={site.id} value={site.id}>
                    {site.name}
                  </option>
                ))}
              </select>
            )}
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-4 p-3 bg-error/10 border border-error/20 rounded-lg flex items-center gap-3">
          <AlertTriangle className="w-4 h-4 text-error flex-shrink-0" />
          <p className="text-sm text-error flex-1">{error}</p>
          <button onClick={() => setError(null)} className="text-error/60 hover:text-error">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Upload Step - Clean Design */}
      {step === 'upload' && (
        <div className="max-w-3xl mx-auto">
          <Card>
            {/* Import Mode Tabs */}
            <div className="flex border-b border-border">
              <button
                onClick={() => setImportMode('standard')}
                className={cn(
                  'flex items-center gap-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors',
                  importMode === 'standard'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-foreground-muted hover:text-foreground'
                )}
              >
                <FileSpreadsheet className="w-4 h-4" />
                Standard
              </button>
              <button
                onClick={() => setImportMode('unified')}
                className={cn(
                  'flex items-center gap-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors',
                  importMode === 'unified'
                    ? 'border-emerald-500 text-emerald-600'
                    : 'border-transparent text-foreground-muted hover:text-foreground'
                )}
              >
                <Layers className="w-4 h-4" />
                Universal AI
              </button>
              <button
                onClick={() => setImportMode('smart')}
                className={cn(
                  'flex items-center gap-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors',
                  importMode === 'smart'
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-foreground-muted hover:text-foreground'
                )}
              >
                <Sparkles className="w-4 h-4" />
                Quick AI
              </button>
            </div>

            <CardContent className="p-6">
              {/* Mode Description - Compact */}
              <p className="text-sm text-foreground-muted mb-4">
                {importMode === 'standard' && 'For CLIMATRIX templates with structured sheets (1.1 Stationary, 2.1 Electricity, etc.)'}
                {importMode === 'unified' && 'AI-powered import for any file format - handles multi-sheet Excel, messy headers, any structure'}
                {importMode === 'smart' && 'Quick import for simple files - AI auto-detects columns and maps to emission factors'}
              </p>

              {/* Drop Zone - Compact */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={cn(
                  'relative border-2 border-dashed rounded-xl p-8 text-center transition-all',
                  isDragging
                    ? importMode === 'unified' ? 'border-emerald-500 bg-emerald-500/5'
                    : importMode === 'smart' ? 'border-purple-500 bg-purple-500/5'
                    : 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50',
                  isLoading && 'opacity-50 pointer-events-none'
                )}
              >
                {isLoading ? (
                  <div className="flex flex-col items-center">
                    {importMode === 'unified' ? (
                      <Layers className="w-10 h-10 text-emerald-500 animate-pulse" />
                    ) : importMode === 'smart' ? (
                      <Brain className="w-10 h-10 text-purple-500 animate-pulse" />
                    ) : (
                      <Loader2 className="w-10 h-10 text-primary animate-spin" />
                    )}
                    <p className="mt-3 text-sm text-foreground-muted">Analyzing file...</p>
                  </div>
                ) : (
                  <>
                    <Upload className={cn(
                      "w-10 h-10 mx-auto",
                      importMode === 'unified' ? 'text-emerald-400' :
                      importMode === 'smart' ? 'text-purple-400' : 'text-foreground-muted'
                    )} />
                    <p className="mt-3 text-base font-medium text-foreground">
                      Drop your file here or click to browse
                    </p>
                    <p className="text-xs text-foreground-muted mt-1">
                      CSV or Excel (.xlsx) files
                    </p>
                    <input
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          if (importMode === 'unified') {
                            handleUnifiedFileSelect(file);
                          } else if (importMode === 'smart') {
                            handleSmartFileSelect(file);
                          } else {
                            handleFileSelect(file);
                          }
                        }
                      }}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                  </>
                )}
              </div>

              {/* Footer - Templates & Info */}
              <div className="mt-4 pt-4 border-t border-border flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => downloadTemplate('1-2')}
                    leftIcon={<Download className="w-3 h-3" />}
                    className="text-xs"
                  >
                    Scope 1&2 Template
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => downloadTemplate('3')}
                    leftIcon={<Download className="w-3 h-3" />}
                    className="text-xs"
                  >
                    Scope 3 Template
                  </Button>
                </div>
                <div className="text-xs text-foreground-muted">
                  Required: <code className="bg-background-muted px-1 rounded">scope</code>,{' '}
                  <code className="bg-background-muted px-1 rounded">category_code</code>,{' '}
                  <code className="bg-background-muted px-1 rounded">activity_key</code>,{' '}
                  <code className="bg-background-muted px-1 rounded">quantity</code>,{' '}
                  <code className="bg-background-muted px-1 rounded">unit</code>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Data Management - Compact */}
          {activities && activities.length > 0 && (
            <div className="mt-4 flex items-center justify-between p-3 bg-background-muted rounded-lg">
              <span className="text-sm text-foreground-muted">
                Manage existing data:
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push('/dashboard')}
                  leftIcon={<BarChart3 className="w-3 h-3" />}
                  className="text-xs"
                >
                  Dashboard
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs text-warning hover:bg-warning/10"
                  onClick={handleClearPeriodData}
                  disabled={isClearing}
                  leftIcon={isClearing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
                >
                  Clear Period
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs text-error hover:bg-error/10"
                  onClick={handleClearAllData}
                  disabled={isClearing}
                  leftIcon={<Trash2 className="w-3 h-3" />}
                >
                  Clear All
                </Button>
              </div>
            </div>
          )}

          {/* Import History - Compact */}
          <div className="mt-6">
            <ImportHistory periodId={periodId} limit={3} />
          </div>
        </div>
      )}

      {/* Preview Step */}
      {step === 'preview' && preview && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  <FileSpreadsheet className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Total Rows</p>
                  <p className="text-xl font-bold text-foreground">{preview.total_rows}</p>
                </div>
              </div>
            </Card>
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-success/10">
                  <CheckCircle2 className="w-5 h-5 text-success" />
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Valid</p>
                  <p className="text-xl font-bold text-success">{preview.valid_rows}</p>
                </div>
              </div>
            </Card>
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-error/10">
                  <XCircle className="w-5 h-5 text-error" />
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Invalid</p>
                  <p className="text-xl font-bold text-error">{preview.invalid_rows}</p>
                </div>
              </div>
            </Card>
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-info/10">
                  <FileText className="w-5 h-5 text-info" />
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Columns</p>
                  <p className="text-xl font-bold text-foreground">{preview.columns_found.length}</p>
                </div>
              </div>
            </Card>
          </div>

          {/* Missing Columns Warning */}
          {preview.columns_missing.length > 0 && (
            <Card padding="md" className="bg-warning/10 border-warning/20">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-warning">Missing Required Columns</p>
                  <p className="text-warning/80 text-sm mt-1">
                    The following columns were not found:{' '}
                    {preview.columns_missing.map((col) => (
                      <code key={col} className="bg-warning/20 px-1 rounded mx-1">
                        {col}
                      </code>
                    ))}
                  </p>
                </div>
              </div>
            </Card>
          )}

          {/* Preview Table */}
          <Card>
            <CardHeader>
              <CardTitle>Preview (first {Math.min(preview.rows.length, 100)} rows)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left p-3 font-medium text-foreground-muted">Row</th>
                      <th className="text-left p-3 font-medium text-foreground-muted">Status</th>
                      <th className="text-left p-3 font-medium text-foreground-muted">Scope</th>
                      <th className="text-left p-3 font-medium text-foreground-muted">Activity</th>
                      <th className="text-left p-3 font-medium text-foreground-muted">Quantity</th>
                      <th className="text-left p-3 font-medium text-foreground-muted">Issues</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.rows.slice(0, 20).map((row) => (
                      <tr
                        key={row.row_number}
                        className={cn(
                          'border-b border-border-muted',
                          !row.is_valid && 'bg-error/5'
                        )}
                      >
                        <td className="p-3 text-foreground-muted">{row.row_number}</td>
                        <td className="p-3">
                          {row.is_valid ? (
                            <CheckCircle2 className="w-4 h-4 text-success" />
                          ) : (
                            <XCircle className="w-4 h-4 text-error" />
                          )}
                        </td>
                        <td className="p-3">
                          {row.scope && <ScopeBadge scope={row.scope as 1 | 2 | 3} size="sm" />}
                        </td>
                        <td className="p-3">
                          <div>
                            <p className="font-medium text-foreground">{row.description || '-'}</p>
                            <p className="text-xs text-foreground-muted font-mono">{row.activity_key}</p>
                          </div>
                        </td>
                        <td className="p-3 text-foreground">
                          {row.quantity?.toLocaleString()} {row.unit}
                        </td>
                        <td className="p-3">
                          {row.errors.length > 0 && (
                            <div className="text-error text-xs">
                              {row.errors.map((e, i) => (
                                <p key={i}>{e}</p>
                              ))}
                            </div>
                          )}
                          {row.warnings.length > 0 && (
                            <div className="text-warning text-xs">
                              {row.warnings.map((w, i) => (
                                <p key={i}>{w}</p>
                              ))}
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              onClick={handleReset}
              leftIcon={<Trash2 className="w-4 h-4" />}
            >
              Cancel
            </Button>
            <div className="flex items-center gap-3">
              <span className="text-sm text-foreground-muted">
                {preview.valid_rows} rows will be imported
              </span>
              <Button
                variant="primary"
                onClick={handleImport}
                disabled={preview.valid_rows === 0}
                leftIcon={<Play className="w-4 h-4" />}
              >
                Import {preview.valid_rows} Activities
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Unified Preview Step */}
      {step === 'unified-preview' && unifiedPreview && (
        <div className="space-y-6">
          {/* File Summary */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-500/10">
                  <FileSpreadsheet className="w-5 h-5 text-emerald-500" />
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">File Type</p>
                  <p className="text-lg font-bold text-foreground">{unifiedPreview.file_type}</p>
                </div>
              </div>
            </Card>
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  <Layers className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Total Sheets</p>
                  <p className="text-lg font-bold text-foreground">{unifiedPreview.total_sheets}</p>
                </div>
              </div>
            </Card>
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-success/10">
                  <CheckCircle2 className="w-5 h-5 text-success" />
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Importable</p>
                  <p className="text-lg font-bold text-success">{unifiedPreview.importable_sheets}</p>
                </div>
              </div>
            </Card>
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-info/10">
                  <FileText className="w-5 h-5 text-info" />
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Activities</p>
                  <p className="text-lg font-bold text-foreground">{unifiedPreview.total_activities}</p>
                </div>
              </div>
            </Card>
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-500/10">
                  <Brain className="w-5 h-5 text-purple-500" />
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Selected</p>
                  <p className="text-lg font-bold text-purple-600">{selectedSheets.size}</p>
                </div>
              </div>
            </Card>
          </div>

          {/* Warnings */}
          {unifiedPreview.warnings.length > 0 && (
            <Card padding="md" className="bg-warning/10 border-warning/20">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-warning">Warnings</p>
                  <ul className="text-warning/80 text-sm mt-1 space-y-1">
                    {unifiedPreview.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </Card>
          )}

          {/* Sheet List with Selectors */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-emerald-500" />
                Sheet Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {unifiedPreview.sheets.map((sheet) => (
                  <div
                    key={sheet.sheet_name}
                    className={cn(
                      'border rounded-lg transition-all',
                      sheet.is_importable ? 'border-border hover:border-primary/50' : 'border-border-muted bg-background-muted/50',
                      selectedSheets.has(sheet.sheet_name) && 'ring-2 ring-emerald-500/50 border-emerald-500'
                    )}
                  >
                    {/* Sheet Header */}
                    <div className="flex items-center gap-4 p-4">
                      {/* Checkbox */}
                      {sheet.is_importable && (
                        <input
                          type="checkbox"
                          checked={selectedSheets.has(sheet.sheet_name)}
                          onChange={() => toggleSheetSelection(sheet.sheet_name)}
                          className="w-5 h-5 rounded text-emerald-500 focus:ring-emerald-500"
                        />
                      )}

                      {/* Sheet Info */}
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-foreground">{sheet.sheet_name}</h4>
                          {sheet.detected_scope && (
                            <ScopeBadge scope={sheet.detected_scope as 1 | 2 | 3} size="sm" />
                          )}
                          {sheet.detected_category && (
                            <span className="px-2 py-0.5 text-xs rounded-full bg-info/10 text-info">
                              {sheet.detected_category}
                            </span>
                          )}
                          {!sheet.is_importable && (
                            <span className="px-2 py-0.5 text-xs rounded-full bg-foreground-muted/20 text-foreground-muted">
                              {sheet.skip_reason || 'Not importable'}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-4 mt-1 text-sm text-foreground-muted">
                          <span>{sheet.total_rows} rows</span>
                          <span>{sheet.columns.length} columns</span>
                          <span>Header at row {sheet.header_row + 1}</span>
                          {sheet.activities_preview.length > 0 && (
                            <span className="text-emerald-600 font-medium">
                              {sheet.activities_preview.length} activities detected
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Expand Button */}
                      {sheet.is_importable && sheet.activities_preview.length > 0 && (
                        <button
                          onClick={() => toggleSheetExpanded(sheet.sheet_name)}
                          className="p-2 rounded-lg hover:bg-background-muted transition-colors"
                        >
                          {expandedSheets.has(sheet.sheet_name) ? (
                            <ChevronDown className="w-5 h-5 text-foreground-muted" />
                          ) : (
                            <ChevronRight className="w-5 h-5 text-foreground-muted" />
                          )}
                        </button>
                      )}
                    </div>

                    {/* Expanded View: Column Mappings & Activities Preview */}
                    {expandedSheets.has(sheet.sheet_name) && sheet.is_importable && (
                      <div className="border-t border-border p-4 bg-background-muted/30 space-y-4">
                        {/* Column Mappings */}
                        <div>
                          <h5 className="text-sm font-medium text-foreground mb-2 flex items-center gap-2">
                            <Brain className="w-4 h-4 text-purple-500" />
                            AI Column Mappings
                          </h5>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {sheet.column_mappings.map((mapping, i) => (
                              <div key={i} className="p-2 bg-background rounded-lg text-sm">
                                <p className="text-foreground-muted truncate">{mapping.original_header}</p>
                                <div className="flex items-center gap-2 mt-1">
                                  <span className="font-mono text-xs text-purple-600">
                                    {mapping.activity_key || mapping.column_type}
                                  </span>
                                  <span className={cn(
                                    'text-xs px-1.5 py-0.5 rounded',
                                    mapping.confidence >= 0.8 ? 'bg-success/10 text-success' :
                                    mapping.confidence >= 0.5 ? 'bg-warning/10 text-warning' :
                                    'bg-foreground-muted/10 text-foreground-muted'
                                  )}>
                                    {Math.round(mapping.confidence * 100)}%
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Activities Preview */}
                        {sheet.activities_preview.length > 0 && (
                          <div>
                            <h5 className="text-sm font-medium text-foreground mb-2 flex items-center gap-2">
                              <Eye className="w-4 h-4 text-info" />
                              Activities Preview (first {Math.min(sheet.activities_preview.length, 5)})
                            </h5>
                            <div className="overflow-x-auto">
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="border-b border-border">
                                    <th className="text-left p-2 font-medium text-foreground-muted">Activity</th>
                                    <th className="text-left p-2 font-medium text-foreground-muted">Description</th>
                                    <th className="text-right p-2 font-medium text-foreground-muted">Quantity</th>
                                    <th className="text-left p-2 font-medium text-foreground-muted">Unit</th>
                                    <th className="text-right p-2 font-medium text-foreground-muted">Confidence</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {sheet.activities_preview.slice(0, 5).map((act, i) => (
                                    <tr key={i} className="border-b border-border-muted">
                                      <td className="p-2 font-mono text-xs text-purple-600">{act.activity_key}</td>
                                      <td className="p-2 text-foreground max-w-xs truncate">{act.description}</td>
                                      <td className="p-2 text-right text-foreground font-medium">
                                        {act.quantity.toLocaleString()}
                                      </td>
                                      <td className="p-2 text-foreground-muted">{act.unit}</td>
                                      <td className="p-2 text-right">
                                        <span className={cn(
                                          'text-xs px-2 py-0.5 rounded',
                                          act.confidence >= 0.8 ? 'bg-success/10 text-success' :
                                          act.confidence >= 0.5 ? 'bg-warning/10 text-warning' :
                                          'bg-foreground-muted/10 text-foreground-muted'
                                        )}>
                                          {Math.round(act.confidence * 100)}%
                                        </span>
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}

                        {/* Warnings */}
                        {sheet.warnings.length > 0 && (
                          <div className="text-sm text-warning">
                            {sheet.warnings.map((w, i) => (
                              <p key={i}>{w}</p>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              onClick={handleReset}
              leftIcon={<Trash2 className="w-4 h-4" />}
            >
              Cancel
            </Button>
            <div className="flex items-center gap-3">
              <span className="text-sm text-foreground-muted">
                {selectedSheets.size} sheets selected ({unifiedPreview.sheets
                  .filter(s => selectedSheets.has(s.sheet_name))
                  .reduce((sum, s) => sum + s.activities_preview.length, 0)} activities)
              </span>
              <Button
                variant="primary"
                onClick={handleUnifiedImport}
                disabled={selectedSheets.size === 0}
                leftIcon={<Play className="w-4 h-4" />}
              >
                Import Selected
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Importing Step */}
      {step === 'importing' && (
        <div className="max-w-md mx-auto text-center py-20">
          <Loader2 className="w-16 h-16 text-primary animate-spin mx-auto" />
          <h2 className="text-xl font-bold text-foreground mt-6">Importing Activities</h2>
          <p className="text-foreground-muted mt-2">
            Please wait while we process your data...
          </p>
        </div>
      )}

      {/* Result Step */}
      {step === 'result' && result && (
        <div className="max-w-2xl mx-auto">
          <Card padding="lg">
            <div className="text-center">
              {result.failed === 0 ? (
                <div className="p-4 rounded-full bg-success/10 w-fit mx-auto">
                  <CheckCircle2 className="w-16 h-16 text-success" />
                </div>
              ) : (
                <div className="p-4 rounded-full bg-warning/10 w-fit mx-auto">
                  <AlertTriangle className="w-16 h-16 text-warning" />
                </div>
              )}

              <h2 className="text-2xl font-bold text-foreground mt-6">
                {result.failed === 0 ? 'Import Complete!' : 'Import Completed with Errors'}
              </h2>

              <div className="grid grid-cols-3 gap-4 mt-8">
                <div className="p-4 bg-background-muted rounded-xl">
                  <p className="text-3xl font-bold text-foreground">{result.total_rows}</p>
                  <p className="text-sm text-foreground-muted mt-1">Total Rows</p>
                </div>
                <div className="p-4 bg-success/10 rounded-xl">
                  <p className="text-3xl font-bold text-success">{result.imported}</p>
                  <p className="text-sm text-success/80 mt-1">Imported</p>
                </div>
                <div className="p-4 bg-error/10 rounded-xl">
                  <p className="text-3xl font-bold text-error">{result.failed}</p>
                  <p className="text-sm text-error/80 mt-1">Failed</p>
                </div>
              </div>

              {result.errors && result.errors.length > 0 && (
                <div className="mt-6 text-left">
                  <h3 className="font-semibold text-foreground mb-2">Errors ({result.errors.length} total)</h3>
                  <div className="bg-error/5 border border-error/20 rounded-lg p-4 max-h-60 overflow-y-auto space-y-3">
                    {result.errors.slice(0, 10).map((err, i) => (
                      <div key={i} className="text-sm border-b border-error/10 pb-2 last:border-0">
                        <div className="flex items-center gap-2 text-error font-medium">
                          <span>Row {err.row || i + 1}</span>
                          {err.activity_key && (
                            <span className="text-xs bg-error/10 px-2 py-0.5 rounded">{err.activity_key}</span>
                          )}
                        </div>
                        {(err.quantity !== undefined || err.unit) && (
                          <div className="text-xs text-foreground-muted mt-1">
                            Data: {err.quantity !== undefined ? `${err.quantity} ` : ''}{err.unit || ''}
                            {err.category_code && ` (${err.category_code})`}
                          </div>
                        )}
                        <div className="text-error/90 mt-1">
                          {Array.isArray(err.errors) ? err.errors.join(' | ') : (err.errors || 'Unknown error')}
                        </div>
                      </div>
                    ))}
                    {result.errors && result.errors.length > 10 && (
                      <p className="text-sm text-error/60 pt-2">
                        ...and {result.errors.length - 10} more errors. Export error log for full list.
                      </p>
                    )}
                  </div>
                </div>
              )}

              <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
                <Button variant="outline" onClick={handleReset}>
                  Import Another File
                </Button>
                {result.import_batch_id && (
                  <Button
                    variant="outline"
                    onClick={() => loadBatchActivities(result.import_batch_id!)}
                    disabled={loadingBatchDetails}
                    leftIcon={loadingBatchDetails ? <Loader2 className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
                  >
                    {loadingBatchDetails ? 'Loading...' : 'View Activities with EF'}
                  </Button>
                )}
                {result.errors && result.errors.length > 0 && (
                  <Button
                    variant="outline"
                    onClick={exportErrorLog}
                    leftIcon={<Download className="w-4 h-4" />}
                    className="text-error border-error/50 hover:bg-error/10"
                  >
                    Export Error Log
                  </Button>
                )}
                {batchActivities.length > 0 && (
                  <Button
                    variant="outline"
                    onClick={exportImportResults}
                    leftIcon={<Download className="w-4 h-4" />}
                    className="text-success border-success/50 hover:bg-success/10"
                  >
                    Export Results CSV
                  </Button>
                )}
                <Button
                  variant="primary"
                  onClick={() => {
                    // Redirect to dashboard with batch filter pre-selected
                    const batchId = result.import_batch_id;
                    router.push(batchId ? `/dashboard?batchId=${batchId}` : '/dashboard');
                  }}
                >
                  View Import Results
                </Button>
              </div>

              {/* Imported Activities with Emission Factors */}
              {showBatchDetails && batchActivities.length > 0 && (
                <div className="mt-8 text-left">
                  <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                    <FileSpreadsheet className="w-5 h-5 text-primary" />
                    Imported Activities ({batchActivities.length})
                  </h3>
                  <div className="overflow-x-auto border border-border rounded-lg">
                    <table className="w-full text-sm">
                      <thead className="bg-background-muted">
                        <tr className="border-b border-border">
                          <th className="text-left p-3 font-medium text-foreground-muted">Scope</th>
                          <th className="text-left p-3 font-medium text-foreground-muted">Category</th>
                          <th className="text-left p-3 font-medium text-foreground-muted">Activity</th>
                          <th className="text-left p-3 font-medium text-foreground-muted">Description</th>
                          <th className="text-right p-3 font-medium text-foreground-muted">Quantity</th>
                          <th className="text-right p-3 font-medium text-foreground-muted">EF</th>
                          <th className="text-right p-3 font-medium text-foreground-muted">CO2e (kg)</th>
                          <th className="text-left p-3 font-medium text-foreground-muted">Source</th>
                        </tr>
                      </thead>
                      <tbody>
                        {batchActivities.map((act) => (
                          <tr key={act.id} className="border-b border-border-muted hover:bg-background-muted/50">
                            <td className="p-3">
                              <ScopeBadge scope={act.scope as 1 | 2 | 3} size="sm" />
                            </td>
                            <td className="p-3 font-mono text-xs text-foreground-muted">{act.category_code}</td>
                            <td className="p-3 font-mono text-xs text-primary">{act.activity_key}</td>
                            <td className="p-3 text-foreground max-w-xs truncate">{act.description}</td>
                            <td className="p-3 text-right text-foreground">
                              {act.quantity.toLocaleString()} <span className="text-foreground-muted">{act.unit}</span>
                            </td>
                            <td className="p-3 text-right text-foreground-muted">
                              {act.emission?.factor_value
                                ? `${act.emission.factor_value.toLocaleString(undefined, { maximumFractionDigits: 4 })}`
                                : '-'}
                              {act.emission?.factor_unit && (
                                <span className="text-xs ml-1">{act.emission.factor_unit}</span>
                              )}
                            </td>
                            <td className="p-3 text-right font-semibold text-foreground">
                              {act.emission?.co2e_kg
                                ? act.emission.co2e_kg.toLocaleString(undefined, { maximumFractionDigits: 2 })
                                : '-'}
                            </td>
                            <td className="p-3 text-xs text-foreground-muted">
                              {act.emission?.factor_source || '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Smart Import Result */}
      {step === 'result' && smartResult && !result && (
        <div className="max-w-2xl mx-auto">
          <Card padding="lg" className="bg-gradient-to-r from-purple-500/5 to-blue-500/5">
            <div className="text-center">
              <div className="p-4 rounded-full bg-purple-500/10 w-fit mx-auto">
                <Sparkles className="w-16 h-16 text-purple-500" />
              </div>

              <h2 className="text-2xl font-bold text-foreground mt-6">
                Smart Import Queued
              </h2>
              <p className="text-foreground-muted mt-2">
                {smartResult.message}
              </p>

              {/* AI Detection Summary */}
              <div className="mt-8 text-left">
                <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                  <Brain className="w-5 h-5 text-purple-500" />
                  AI Detection Results
                </h3>

                <div className="bg-background rounded-xl p-4 space-y-4">
                  <div>
                    <p className="text-sm text-foreground-muted">File Structure</p>
                    <p className="font-medium text-foreground">
                      {smartResult.ai_mapping_preview.detected_structure.replace('_', ' ')}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm text-foreground-muted mb-2">Detected Columns</p>
                    <div className="space-y-2">
                      {smartResult.ai_mapping_preview.detected_columns.map((col, i) => (
                        <div key={i} className="flex items-center justify-between p-2 bg-background-muted rounded-lg">
                          <span className="text-foreground">{col.header}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-purple-600 font-mono">{col.maps_to}</span>
                            <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-600">
                              {col.confidence}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {smartResult.ai_mapping_preview.date_column && (
                    <div>
                      <p className="text-sm text-foreground-muted">Date Column</p>
                      <p className="font-medium text-foreground">{smartResult.ai_mapping_preview.date_column}</p>
                    </div>
                  )}

                  {smartResult.ai_mapping_preview.warnings.length > 0 && (
                    <div>
                      <p className="text-sm text-warning mb-2">Warnings</p>
                      {smartResult.ai_mapping_preview.warnings.map((w, i) => (
                        <p key={i} className="text-sm text-warning/80">{w}</p>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-8 flex items-center justify-center gap-4">
                <Button variant="outline" onClick={handleReset}>
                  Import Another File
                </Button>
                <Button
                  variant="primary"
                  onClick={() => router.push('/dashboard')}
                >
                  Go to Dashboard
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Unified Import Result */}
      {step === 'result' && unifiedResult && !result && !smartResult && (
        <div className="max-w-2xl mx-auto">
          <Card padding="lg" className="bg-gradient-to-r from-emerald-500/5 to-teal-500/5">
            <div className="text-center">
              {unifiedResult.failed === 0 ? (
                <div className="p-4 rounded-full bg-emerald-500/10 w-fit mx-auto">
                  <CheckCircle2 className="w-16 h-16 text-emerald-500" />
                </div>
              ) : (
                <div className="p-4 rounded-full bg-warning/10 w-fit mx-auto">
                  <AlertTriangle className="w-16 h-16 text-warning" />
                </div>
              )}

              <h2 className="text-2xl font-bold text-foreground mt-6">
                {unifiedResult.success ? 'Import Complete!' : 'Import Completed with Errors'}
              </h2>

              {/* Total CO2e */}
              <div className="mt-4 p-4 bg-emerald-500/10 rounded-xl inline-block">
                <p className="text-sm text-emerald-600">Total Emissions Imported</p>
                <p className="text-3xl font-bold text-emerald-600">
                  {formatCO2e(unifiedResult.total_co2e_kg)}
                </p>
              </div>

              <div className="grid grid-cols-3 gap-4 mt-8">
                <div className="p-4 bg-background-muted rounded-xl">
                  <p className="text-3xl font-bold text-foreground">{unifiedResult.total_activities}</p>
                  <p className="text-sm text-foreground-muted mt-1">Total Activities</p>
                </div>
                <div className="p-4 bg-success/10 rounded-xl">
                  <p className="text-3xl font-bold text-success">{unifiedResult.imported}</p>
                  <p className="text-sm text-success/80 mt-1">Imported</p>
                </div>
                <div className="p-4 bg-error/10 rounded-xl">
                  <p className="text-3xl font-bold text-error">{unifiedResult.failed}</p>
                  <p className="text-sm text-error/80 mt-1">Failed</p>
                </div>
              </div>

              {/* By Scope Breakdown */}
              {Object.keys(unifiedResult.by_scope).length > 0 && (
                <div className="mt-6 text-left">
                  <h3 className="font-semibold text-foreground mb-2">By Scope</h3>
                  <div className="grid grid-cols-3 gap-2">
                    {Object.entries(unifiedResult.by_scope).map(([scope, count]) => (
                      <div key={scope} className="p-3 bg-background rounded-lg text-center">
                        <p className="text-lg font-bold text-foreground">{count}</p>
                        <p className="text-xs text-foreground-muted">{scope}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Errors */}
              {unifiedResult.errors.length > 0 && (
                <div className="mt-6 text-left">
                  <h3 className="font-semibold text-foreground mb-2">Errors</h3>
                  <div className="bg-error/5 border border-error/20 rounded-lg p-4 max-h-40 overflow-y-auto">
                    {unifiedResult.errors.slice(0, 10).map((err, i) => (
                      <div key={i} className="text-sm text-error mb-2">
                        <span className="font-medium">
                          {err.sheet ? `${err.sheet} Row ${err.row}` : `Row ${err.row}`}:
                        </span>{' '}
                        {err.error}
                      </div>
                    ))}
                    {unifiedResult.errors.length > 10 && (
                      <p className="text-sm text-error/60">
                        ...and {unifiedResult.errors.length - 10} more errors
                      </p>
                    )}
                  </div>
                </div>
              )}

              <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
                <Button variant="outline" onClick={handleReset}>
                  Import Another File
                </Button>
                {unifiedResult.errors && unifiedResult.errors.length > 0 && (
                  <Button
                    variant="outline"
                    onClick={exportErrorLog}
                    leftIcon={<Download className="w-4 h-4" />}
                    className="text-error border-error/50 hover:bg-error/10"
                  >
                    Export Error Log
                  </Button>
                )}
                <Button
                  variant="primary"
                  onClick={() => {
                    // Redirect to dashboard with batch filter pre-selected
                    const batchId = unifiedResult.import_batch_id;
                    router.push(batchId ? `/dashboard?batchId=${batchId}` : '/dashboard');
                  }}
                >
                  View Import Results
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </AppShell>
  );
}

function ImportLoading() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-primary animate-spin" />
    </div>
  );
}

export default function ImportPage() {
  return (
    <Suspense fallback={<ImportLoading />}>
      <ImportContent />
    </Suspense>
  );
}
