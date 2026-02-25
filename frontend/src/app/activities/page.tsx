'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import { usePeriods, useActivities, useDeleteActivity, useUpdateActivity } from '@/hooks/useEmissions';
import { AppShell } from '@/components/layout';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  ScopeBadge,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  EmptyState,
  ConfirmDialog,
  toast,
} from '@/components/ui';
import { Plus, Loader2, Trash2, Pencil, ArrowLeft, Filter, FileSpreadsheet, ChevronDown, Calendar, X } from 'lucide-react';
import { api, ImportBatch, ActivityWithEmission } from '@/lib/api';

export default function ActivitiesPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  // All useState hooks
  const [selectedScope, setSelectedScope] = useState<number | null>(null);
  const [selectedBatch, setSelectedBatch] = useState<string | null>(null);
  const [batchDropdownOpen, setBatchDropdownOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [confirmState, setConfirmState] = useState<{open: boolean; onConfirm: () => void; title: string; message: string}>({open: false, onConfirm: () => {}, title: '', message: ''});
  const [editingActivity, setEditingActivity] = useState<ActivityWithEmission | null>(null);
  const [editForm, setEditForm] = useState({ description: '', quantity: 0, unit: '', data_quality_score: 5 });

  // All data fetching hooks (must be before any conditional returns)
  const { data: periods, isLoading: periodsLoading } = usePeriods();
  const { selectedPeriodId, setSelectedPeriodId } = usePeriodStore();

  // Use selected period from store, fall back to first available period
  const activePeriodId = selectedPeriodId || periods?.[0]?.id;
  const activePeriod = periods?.find((p) => p.id === activePeriodId) || periods?.[0];

  const { data: activities, isLoading: activitiesLoading } = useActivities(
    activePeriodId || '',
    selectedScope ? { scope: selectedScope } : undefined
  );

  const deleteActivity = useDeleteActivity(activePeriodId || '');
  const updateActivity = useUpdateActivity(activePeriodId || '');

  // Fetch import batches for filter dropdown
  const { data: importBatches } = useQuery({
    queryKey: ['import-batches', activePeriodId],
    queryFn: () => api.getImportBatches(activePeriodId, 50),
    enabled: !!activePeriodId,
  });

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

  const isLoading = periodsLoading || activitiesLoading;

  // Filter activities by scope and/or batch
  const filteredActivities = activities?.filter((a) => {
    const matchesScope = selectedScope === null || a.activity.scope === selectedScope;
    const matchesBatch = selectedBatch === null || a.activity.import_batch_id === selectedBatch;
    return matchesScope && matchesBatch;
  });

  // Get the selected batch info for display
  const selectedBatchInfo = selectedBatch
    ? importBatches?.find((b) => b.id === selectedBatch)
    : null;

  const openEditModal = (item: ActivityWithEmission) => {
    setEditForm({
      description: item.activity.description,
      quantity: item.activity.quantity,
      unit: item.activity.unit,
      data_quality_score: item.activity.data_quality_score ?? 5,
    });
    setEditingActivity(item);
  };

  const handleEditSave = () => {
    if (!editingActivity) return;
    updateActivity.mutate(
      {
        activityId: editingActivity.activity.id,
        data: {
          description: editForm.description,
          quantity: editForm.quantity,
          unit: editForm.unit,
          data_quality_score: editForm.data_quality_score,
        },
      },
      {
        onSuccess: () => {
          toast.success('Activity updated successfully');
          setEditingActivity(null);
        },
        onError: (err: any) => {
          toast.error(err?.message || 'Failed to update activity');
        },
      }
    );
  };

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
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
            <h1 className="text-2xl font-bold text-foreground">All Activities</h1>
            {periods && periods.length > 1 ? (
              <div className="flex items-center gap-2 mt-1">
                <Calendar className="w-4 h-4 text-foreground-muted" />
                <select
                  value={activePeriodId || ''}
                  onChange={(e) => setSelectedPeriodId(e.target.value || null)}
                  className="text-sm bg-transparent border border-border rounded-lg px-2 py-1 text-foreground-muted focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {periods.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
            ) : (
              <p className="text-foreground-muted mt-1">
                {activePeriod?.name || 'Loading...'}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            onClick={() => router.push('/dashboard?wizard=true')}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Add Activity
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-6">
        {/* Scope Filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-foreground-muted" />
          <span className="text-sm text-foreground-muted mr-2">Scope:</span>
          <Button
            variant={selectedScope === null ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setSelectedScope(null)}
          >
            All
          </Button>
          <Button
            variant={selectedScope === 1 ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setSelectedScope(1)}
          >
            1
          </Button>
          <Button
            variant={selectedScope === 2 ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setSelectedScope(2)}
          >
            2
          </Button>
          <Button
            variant={selectedScope === 3 ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setSelectedScope(3)}
          >
            3
          </Button>
        </div>

        {/* Batch/File Filter */}
        <div className="flex items-center gap-2">
          <FileSpreadsheet className="w-4 h-4 text-foreground-muted" />
          <span className="text-sm text-foreground-muted mr-2">Import:</span>
          <div className="relative">
            <Button
              variant={selectedBatch ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setBatchDropdownOpen(!batchDropdownOpen)}
              className="min-w-[180px] justify-between"
            >
              <span className="truncate max-w-[140px]">
                {selectedBatchInfo?.file_name || 'All Imports'}
              </span>
              <ChevronDown className={`w-4 h-4 ml-2 transition-transform ${batchDropdownOpen ? 'rotate-180' : ''}`} />
            </Button>

            {batchDropdownOpen && (
              <>
                {/* Backdrop to close dropdown */}
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setBatchDropdownOpen(false)}
                />

                {/* Dropdown menu */}
                <div className="absolute top-full left-0 mt-1 w-72 max-h-64 overflow-y-auto bg-card border border-border rounded-lg shadow-lg z-20">
                  <button
                    className={`w-full px-3 py-2 text-left text-sm hover:bg-background-muted flex items-center gap-2 ${
                      selectedBatch === null ? 'bg-primary/10 text-primary font-medium' : 'text-foreground'
                    }`}
                    onClick={() => {
                      setSelectedBatch(null);
                      setBatchDropdownOpen(false);
                    }}
                  >
                    <FileSpreadsheet className="w-4 h-4" />
                    All Imports
                  </button>

                  {importBatches && importBatches.length > 0 && (
                    <div className="border-t border-border">
                      {importBatches.map((batch) => (
                        <button
                          key={batch.id}
                          className={`w-full px-3 py-2 text-left text-sm hover:bg-background-muted flex items-center justify-between gap-2 ${
                            selectedBatch === batch.id ? 'bg-primary/10 text-primary font-medium' : 'text-foreground'
                          }`}
                          onClick={() => {
                            setSelectedBatch(batch.id);
                            setBatchDropdownOpen(false);
                          }}
                        >
                          <span className="truncate flex-1">{batch.file_name}</span>
                          <span className="text-xs text-foreground-muted whitespace-nowrap">
                            {batch.successful_rows} rows
                          </span>
                        </button>
                      ))}
                    </div>
                  )}

                  {(!importBatches || importBatches.length === 0) && (
                    <div className="px-3 py-4 text-sm text-foreground-muted text-center">
                      No imports yet
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-foreground-muted">Loading activities...</span>
        </div>
      )}

      {/* Activities Table */}
      {!isLoading && (
        <Card>
          <CardHeader>
            <CardTitle>
              Activities
              {filteredActivities && (
                <span className="ml-2 px-2 py-0.5 text-xs font-medium rounded-full bg-background-muted text-foreground-muted">
                  {filteredActivities.length}
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {filteredActivities && filteredActivities.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Scope</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Activity</TableHead>
                    <TableHead>Quantity</TableHead>
                    <TableHead className="text-right">EF</TableHead>
                    <TableHead className="text-right">CO2e</TableHead>
                    <TableHead className="text-right">Source</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredActivities.map((item) => (
                    <TableRow key={item.activity.id}>
                      <TableCell>
                        <ScopeBadge scope={item.activity.scope as 1 | 2 | 3} />
                      </TableCell>
                      <TableCell className="font-mono text-xs text-foreground-muted">
                        {item.activity.category_code}
                      </TableCell>
                      <TableCell className="font-medium text-foreground max-w-xs truncate">
                        {item.activity.description}
                      </TableCell>
                      <TableCell className="text-foreground-muted font-mono text-xs">
                        {item.activity.activity_key}
                      </TableCell>
                      <TableCell className="text-foreground-muted">
                        {item.activity.quantity.toLocaleString()} {item.activity.unit}
                      </TableCell>
                      <TableCell className="text-right text-xs text-foreground-muted">
                        {item.emission?.factor_value
                          ? `${item.emission.factor_value.toLocaleString(undefined, { maximumFractionDigits: 4 })} ${item.emission.factor_unit || ''}`
                          : '-'}
                      </TableCell>
                      <TableCell className="text-right font-semibold text-foreground">
                        {item.emission?.co2e_kg.toLocaleString(undefined, {
                          maximumFractionDigits: 2,
                        })}
                        <span className="text-foreground-muted font-normal ml-1">kg</span>
                      </TableCell>
                      <TableCell className="text-right text-xs text-foreground-muted">
                        {item.emission?.factor_source || '-'}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditModal(item)}
                            className="text-foreground-muted hover:text-primary hover:bg-primary/10"
                          >
                            <Pencil className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setConfirmState({
                                open: true,
                                onConfirm: () => { deleteActivity.mutate(item.activity.id); setConfirmState(s => ({...s, open: false})); },
                                title: 'Delete Activity',
                                message: 'Delete this activity?',
                              });
                            }}
                            className="text-danger hover:text-danger hover:bg-danger/10"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <EmptyState
                title="No activities found"
                description={
                  selectedScope && selectedBatch
                    ? `No Scope ${selectedScope} activities in "${selectedBatchInfo?.file_name}"`
                    : selectedScope
                    ? `No Scope ${selectedScope} activities in this period`
                    : selectedBatch
                    ? `No activities in "${selectedBatchInfo?.file_name}"`
                    : 'Add your first activity to start tracking emissions'
                }
                action={{
                  label: selectedScope || selectedBatch ? 'Clear Filters' : 'Add Activity',
                  onClick: () => {
                    if (selectedScope || selectedBatch) {
                      setSelectedScope(null);
                      setSelectedBatch(null);
                    } else {
                      router.push('/dashboard?wizard=true');
                    }
                  },
                }}
              />
            )}
          </CardContent>
        </Card>
      )}
      <ConfirmDialog
        isOpen={confirmState.open}
        onClose={() => setConfirmState(s => ({...s, open: false}))}
        onConfirm={confirmState.onConfirm}
        title={confirmState.title}
        message={confirmState.message}
        variant="danger"
        confirmLabel="Delete"
      />

      {/* Edit Activity Modal */}
      {editingActivity && (
        <div
          className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in"
          style={{ zIndex: 'var(--z-modal)' }}
          onClick={(e) => { if (e.target === e.currentTarget) setEditingActivity(null); }}
        >
          <div className="relative w-full max-w-lg bg-background-elevated border border-border rounded-xl shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between px-6 pt-6 pb-2">
              <h2 className="text-lg font-semibold text-foreground">Edit Activity</h2>
              <button
                onClick={() => setEditingActivity(null)}
                className="p-1 rounded-lg text-foreground-muted hover:text-foreground hover:bg-background-muted transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Form */}
            <div className="px-6 py-4 space-y-4">
              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Description</label>
                <input
                  type="text"
                  value={editForm.description}
                  onChange={(e) => setEditForm(f => ({ ...f, description: e.target.value }))}
                  className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>

              {/* Quantity */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Quantity</label>
                <input
                  type="number"
                  value={editForm.quantity}
                  onChange={(e) => setEditForm(f => ({ ...f, quantity: parseFloat(e.target.value) || 0 }))}
                  className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  min="0"
                  step="any"
                />
              </div>

              {/* Unit */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Unit</label>
                <input
                  type="text"
                  value={editForm.unit}
                  onChange={(e) => setEditForm(f => ({ ...f, unit: e.target.value }))}
                  className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>

              {/* Data Quality Score */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Data Quality Score</label>
                <select
                  value={editForm.data_quality_score}
                  onChange={(e) => setEditForm(f => ({ ...f, data_quality_score: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                >
                  <option value={1}>1 - Highest quality</option>
                  <option value={2}>2 - High quality</option>
                  <option value={3}>3 - Medium quality</option>
                  <option value={4}>4 - Low quality</option>
                  <option value={5}>5 - Lowest quality</option>
                </select>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 px-6 pb-6 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setEditingActivity(null)}
                disabled={updateActivity.isPending}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleEditSave}
                disabled={updateActivity.isPending || !editForm.description.trim() || editForm.quantity <= 0}
                leftIcon={updateActivity.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : undefined}
              >
                {updateActivity.isPending ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
