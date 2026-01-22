'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/stores/auth';
import { usePeriods, useActivities, useDeleteActivity } from '@/hooks/useEmissions';
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
} from '@/components/ui';
import { Plus, Loader2, Trash2, ArrowLeft, Filter, FileSpreadsheet, ChevronDown } from 'lucide-react';
import { api, ImportBatch } from '@/lib/api';

export default function ActivitiesPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  // All useState hooks
  const [selectedScope, setSelectedScope] = useState<number | null>(null);
  const [selectedBatch, setSelectedBatch] = useState<string | null>(null);
  const [batchDropdownOpen, setBatchDropdownOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  // All data fetching hooks (must be before any conditional returns)
  const { data: periods, isLoading: periodsLoading } = usePeriods();
  const activePeriodId = periods?.[0]?.id;

  const { data: activities, isLoading: activitiesLoading } = useActivities(
    activePeriodId || '',
    selectedScope ? { scope: selectedScope } : undefined
  );

  const deleteActivity = useDeleteActivity(activePeriodId || '');

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
            <p className="text-foreground-muted mt-1">
              {periods?.[0]?.name || 'Loading...'}
            </p>
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
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            if (confirm('Delete this activity?')) {
                              deleteActivity.mutate(item.activity.id);
                            }
                          }}
                          className="text-danger hover:text-danger hover:bg-danger/10"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
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
    </AppShell>
  );
}
