'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import { useSiteStore } from '@/stores/site';
import { usePeriods, useActivities, useDeleteActivity, useUpdateActivity, useSites } from '@/hooks/useEmissions';
import { AppShell } from '@/components/layout';
import { PageHead } from '@/components/canopy';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
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
import { cn, formatQty } from '@/lib/utils';
import { Loader2, Trash2, Pencil, ChevronDown, X } from 'lucide-react';
import { SiteSelector } from '@/components/SiteSelector';
import { AddActivityModal } from '@/components/wizard/AddActivityModal';
import { api, ActivityWithEmission } from '@/lib/api';

const fieldLabel = 'mb-1.5 block text-[11px] font-bold tracking-[0.06em] uppercase text-cy-faint';
const fieldInput =
  'w-full rounded-[10px] border-0 bg-cy-row px-3 py-2.5 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent';

function ActivitiesContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated } = useAuthStore();

  // All useState hooks
  const [showWizard, setShowWizard] = useState(searchParams.get('add') === '1');
  const [selectedScope, setSelectedScope] = useState<number | null>(null);
  const [selectedBatch, setSelectedBatch] = useState<string | null>(null);
  const [batchDropdownOpen, setBatchDropdownOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [confirmState, setConfirmState] = useState<{open: boolean; onConfirm: () => void; title: string; message: string}>({open: false, onConfirm: () => {}, title: '', message: ''});
  const [editingActivity, setEditingActivity] = useState<ActivityWithEmission | null>(null);
  const [editForm, setEditForm] = useState({ description: '', quantity: 0, unit: '', data_quality_score: 5 });

  // All data fetching hooks (must be before any conditional returns)
  const { data: periods, isLoading: periodsLoading } = usePeriods();
  const { selectedPeriodId } = usePeriodStore();
  const { selectedSiteId } = useSiteStore();
  const { data: sites } = useSites();

  // Use selected period from store, fall back to first available period
  // Only trust the persisted period if it belongs to THIS org's list — a stale
  // localStorage value from another session/org would 404 every query.
  const activePeriodId = periods?.find((p) => p.id === selectedPeriodId)?.id ?? periods?.[0]?.id;
  const activePeriod = periods?.find((p) => p.id === activePeriodId) || periods?.[0];

  // Build filters including site
  const activityFilters: { scope?: number; site_id?: string } = {};
  if (selectedScope) activityFilters.scope = selectedScope;
  if (selectedSiteId) activityFilters.site_id = selectedSiteId;

  const { data: activities, isLoading: activitiesLoading } = useActivities(
    activePeriodId || '',
    Object.keys(activityFilters).length > 0 ? activityFilters : undefined
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
    // eslint-disable-next-line react-hooks/set-state-in-effect -- pre-existing intentional state sync on mount/deps change; no behavior change
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
        onError: (err: unknown) => {
          toast.error(err instanceof Error ? err.message : 'Failed to update activity');
        },
      }
    );
  };

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <PageHead
            title="Activities"
            subtitle={`Every committed emission line — uploads and manual entry alike · ${activePeriod?.name || '…'}`}
          />
        </div>
        <Button variant="primary" onClick={() => setShowWizard(true)}>
          + Add activity
        </Button>
      </div>

      {/* Filters — quiet pills, per the locked template */}
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="flex flex-wrap items-center gap-1.5">
          {([null, 1, 2, 3] as const).map((scope) => (
            <button
              key={scope ?? 'all'}
              type="button"
              onClick={() => setSelectedScope(scope)}
              className={cn(
                'cursor-pointer rounded-full px-3.5 py-1.5 text-[12.5px] font-semibold transition-colors',
                selectedScope === scope
                  ? 'bg-cy-accent-soft text-cy-accent'
                  : 'text-cy-muted hover:bg-cy-row'
              )}
            >
              {scope === null ? 'All' : `Scope ${scope}`}
            </button>
          ))}
        </div>

        {/* Site Filter */}
        <SiteSelector compact />

        {/* Batch/File Filter */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setBatchDropdownOpen(!batchDropdownOpen)}
            className={cn(
              'flex cursor-pointer items-center gap-2 rounded-full px-3.5 py-1.5 text-[12.5px] font-semibold transition-colors',
              selectedBatch ? 'bg-cy-accent-soft text-cy-accent' : 'text-cy-muted hover:bg-cy-row'
            )}
          >
            <span className="max-w-[160px] truncate">
              {selectedBatchInfo?.file_name || 'All imports'}
            </span>
            <ChevronDown
              className={`h-3.5 w-3.5 transition-transform ${batchDropdownOpen ? 'rotate-180' : ''}`}
            />
          </button>

          {batchDropdownOpen && (
            <>
              {/* Backdrop to close dropdown */}
              <div className="fixed inset-0 z-10" onClick={() => setBatchDropdownOpen(false)} />

              {/* Dropdown menu */}
              <div className="absolute top-full left-0 z-20 mt-1 max-h-64 w-72 overflow-y-auto rounded-xl bg-background-elevated py-1 shadow-lg">
                <button
                  className={cn(
                    'flex w-full items-center gap-2 px-3 py-2 text-left text-[12.5px] hover:bg-cy-row',
                    selectedBatch === null ? 'font-bold text-cy-accent' : 'text-foreground'
                  )}
                  onClick={() => {
                    setSelectedBatch(null);
                    setBatchDropdownOpen(false);
                  }}
                >
                  All imports
                </button>

                {importBatches && importBatches.length > 0 && (
                  <div className="border-t border-cy-row">
                    {importBatches.map((batch) => (
                      <button
                        key={batch.id}
                        className={cn(
                          'flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-[12.5px] hover:bg-cy-row',
                          selectedBatch === batch.id ? 'font-bold text-cy-accent' : 'text-foreground'
                        )}
                        onClick={() => {
                          setSelectedBatch(batch.id);
                          setBatchDropdownOpen(false);
                        }}
                      >
                        <span className="flex-1 truncate">{batch.file_name}</span>
                        <span className="whitespace-nowrap text-[11px] tabular-nums text-cy-muted">
                          {batch.successful_rows} rows
                        </span>
                      </button>
                    ))}
                  </div>
                )}

                {(!importBatches || importBatches.length === 0) && (
                  <div className="px-3 py-4 text-center text-[12.5px] text-cy-muted">
                    No imports yet
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-20" role="status" aria-live="polite">
          <Loader2 className="w-8 h-8 animate-spin text-primary" aria-hidden="true" />
          <span className="ml-3 text-foreground-muted">Loading activities...</span>
        </div>
      )}

      {/* Activities Table */}
      {!isLoading && (
        <Card>
          <CardHeader>
            <CardTitle>
              Activities{filteredActivities ? ` · ${filteredActivities.length}` : ''}
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
                    <TableHead>Site</TableHead>
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
                        {item.activity.is_demo && (
                          <Badge variant="warning" size="sm" className="mr-1.5">
                            Demo
                          </Badge>
                        )}
                        {item.activity.description}
                      </TableCell>
                      <TableCell className="text-xs text-foreground-muted">
                        {item.activity.site_id
                          ? sites?.find(s => s.id === item.activity.site_id)?.name || '—'
                          : <span className="text-foreground-muted/50">—</span>
                        }
                      </TableCell>
                      <TableCell className="text-foreground-muted font-mono text-xs">
                        {item.activity.activity_key}
                      </TableCell>
                      <TableCell className="text-foreground-muted">
                        {formatQty(item.activity.quantity)} {item.activity.unit}
                      </TableCell>
                      <TableCell className="text-right text-xs text-foreground-muted">
                        {item.emission?.factor_value
                          ? `${formatQty(item.emission.factor_value)} ${item.emission.factor_unit || ''}`
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
                            className="text-error hover:text-error hover:bg-error/10"
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
                      setShowWizard(true);
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
          <div className="relative w-full max-w-lg rounded-cy bg-background-elevated shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between px-6 pt-6 pb-2">
              <h2 className="text-[16px] font-bold tracking-[-0.01em] text-foreground">Edit activity</h2>
              <button
                onClick={() => setEditingActivity(null)}
                className="rounded-md p-1.5 text-cy-muted transition-colors hover:bg-cy-row hover:text-foreground"
                aria-label="Close"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Form */}
            <div className="space-y-4 px-6 py-4">
              <div>
                <label className={fieldLabel}>Description</label>
                <input
                  type="text"
                  value={editForm.description}
                  onChange={(e) => setEditForm(f => ({ ...f, description: e.target.value }))}
                  className={fieldInput}
                />
              </div>

              <div>
                <label className={fieldLabel}>Quantity</label>
                <input
                  type="number"
                  value={editForm.quantity}
                  onChange={(e) => setEditForm(f => ({ ...f, quantity: parseFloat(e.target.value) || 0 }))}
                  className={fieldInput}
                  min="0"
                  step="any"
                />
              </div>

              <div>
                <label className={fieldLabel}>Unit</label>
                <input
                  type="text"
                  value={editForm.unit}
                  onChange={(e) => setEditForm(f => ({ ...f, unit: e.target.value }))}
                  className={fieldInput}
                />
              </div>

              <div>
                <label className={fieldLabel}>Data quality score</label>
                <select
                  value={editForm.data_quality_score}
                  onChange={(e) => setEditForm(f => ({ ...f, data_quality_score: parseInt(e.target.value) }))}
                  className={fieldInput}
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
            <div className="flex items-center justify-end gap-2 px-6 pb-6 pt-2">
              <Button
                variant="ghost"
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
                leftIcon={updateActivity.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : undefined}
              >
                {updateActivity.isPending ? 'Saving…' : 'Save changes'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Add Activity — the ledger is the single home of manual entry */}
      {showWizard && activePeriodId && (
        <AddActivityModal
          periodId={activePeriodId}
          onClose={() => setShowWizard(false)}
          onSuccess={() => setShowWizard(false)}
        />
      )}
    </AppShell>
  );
}

export default function ActivitiesPage() {
  return (
    <Suspense fallback={null}>
      <ActivitiesContent />
    </Suspense>
  );
}
