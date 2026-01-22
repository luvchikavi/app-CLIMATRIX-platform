'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, ImportBatch } from '@/lib/api';
import { Button, Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import { FileSpreadsheet, CheckCircle, AlertCircle, Clock, Trash2, ChevronDown, ChevronUp, Eye } from 'lucide-react';
import { cn } from '@/lib/utils';

// Simple relative time formatter (no external dependency)
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return 'just now';
  if (diffMin < 60) return `${diffMin} minute${diffMin === 1 ? '' : 's'} ago`;
  if (diffHour < 24) return `${diffHour} hour${diffHour === 1 ? '' : 's'} ago`;
  if (diffDay < 7) return `${diffDay} day${diffDay === 1 ? '' : 's'} ago`;

  return date.toLocaleDateString();
}

interface ImportHistoryProps {
  periodId?: string;
  limit?: number;
}

export function ImportHistory({ periodId, limit = 10 }: ImportHistoryProps) {
  const [expandedBatch, setExpandedBatch] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: batches, isLoading, error } = useQuery({
    queryKey: ['import-batches', periodId, limit],
    queryFn: () => api.getImportBatches(periodId, limit),
    staleTime: 30 * 1000, // 30 seconds
  });

  const { data: batchActivities, isLoading: loadingActivities } = useQuery({
    queryKey: ['import-batch-activities', expandedBatch],
    queryFn: () => expandedBatch ? api.getImportBatchActivities(expandedBatch) : null,
    enabled: !!expandedBatch,
  });

  const deleteMutation = useMutation({
    mutationFn: ({ batchId, deleteActivities }: { batchId: string; deleteActivities: boolean }) =>
      api.deleteImportBatch(batchId, deleteActivities),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['import-batches'] });
      queryClient.invalidateQueries({ queryKey: ['activities'] });
      setExpandedBatch(null);
    },
  });

  const getStatusIcon = (status: ImportBatch['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-success" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-error" />;
      case 'partial':
        return <AlertCircle className="w-4 h-4 text-warning" />;
      case 'processing':
      case 'pending':
        return <Clock className="w-4 h-4 text-foreground-muted animate-pulse" />;
    }
  };

  const getStatusText = (batch: ImportBatch) => {
    if (batch.status === 'completed') {
      return `${batch.successful_rows} imported`;
    }
    if (batch.status === 'partial') {
      return `${batch.successful_rows} imported, ${batch.failed_rows} failed`;
    }
    if (batch.status === 'failed') {
      return 'Import failed';
    }
    return batch.status;
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5" />
            Import History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-foreground-muted">Loading...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5" />
            Import History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-error">Failed to load import history</p>
        </CardContent>
      </Card>
    );
  }

  if (!batches || batches.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5" />
            Import History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-foreground-muted">No imports yet. Upload a file to get started.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileSpreadsheet className="w-5 h-5" />
          Import History
          <span className="text-xs font-normal text-foreground-muted ml-2">
            ({batches.length} imports)
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {batches.map((batch) => (
            <div key={batch.id} className="border border-border rounded-lg overflow-hidden">
              {/* Batch Header */}
              <div
                className={cn(
                  "flex items-center justify-between p-3 hover:bg-background-muted/50 transition-colors",
                  expandedBatch === batch.id && "bg-background-muted/50"
                )}
              >
                <div
                  className="flex items-center gap-3 flex-1 cursor-pointer"
                  onClick={() => setExpandedBatch(expandedBatch === batch.id ? null : batch.id)}
                >
                  {getStatusIcon(batch.status)}
                  <div>
                    <p className="font-medium text-sm">{batch.file_name}</p>
                    <p className="text-xs text-foreground-muted">
                      {formatRelativeTime(batch.uploaded_at)}
                      {' · '}
                      {getStatusText(batch)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-foreground-muted">
                    {batch.total_rows} rows
                  </span>
                  {/* Quick Delete Button - Always Visible */}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-error/60 hover:text-error hover:bg-error/10 h-7 w-7 p-0"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Delete import "${batch.file_name}"?\n\nThis will also delete ${batch.successful_rows} imported activities.`)) {
                        deleteMutation.mutate({ batchId: batch.id, deleteActivities: true });
                      }
                    }}
                    disabled={deleteMutation.isPending}
                    title="Delete this import and its activities"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                  <div
                    className="cursor-pointer"
                    onClick={() => setExpandedBatch(expandedBatch === batch.id ? null : batch.id)}
                  >
                    {expandedBatch === batch.id ? (
                      <ChevronUp className="w-4 h-4 text-foreground-muted" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-foreground-muted" />
                    )}
                  </div>
                </div>
              </div>

              {/* Expanded Details */}
              {expandedBatch === batch.id && (
                <div className="border-t border-border p-3 bg-background-muted/30">
                  {/* Summary */}
                  <div className="grid grid-cols-3 gap-4 mb-3">
                    <div className="text-center">
                      <p className="text-lg font-semibold text-success">{batch.successful_rows}</p>
                      <p className="text-xs text-foreground-muted">Imported</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-semibold text-error">{batch.failed_rows}</p>
                      <p className="text-xs text-foreground-muted">Failed</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-semibold text-foreground-muted">{batch.total_rows}</p>
                      <p className="text-xs text-foreground-muted">Total</p>
                    </div>
                  </div>

                  {/* Activities Preview */}
                  {loadingActivities ? (
                    <p className="text-sm text-foreground-muted">Loading activities...</p>
                  ) : batchActivities && batchActivities.activities.length > 0 ? (
                    <div className="mb-3">
                      <p className="text-xs font-medium text-foreground-muted mb-2">
                        Activities ({batchActivities.activity_count})
                      </p>
                      <div className="max-h-40 overflow-y-auto space-y-1">
                        {batchActivities.activities.slice(0, 10).map((activity) => (
                          <div
                            key={activity.id}
                            className="flex items-center justify-between text-xs p-2 bg-background rounded border border-border"
                          >
                            <span className="font-medium">{activity.description || activity.activity_key}</span>
                            <span className="text-foreground-muted">
                              {activity.quantity} {activity.unit}
                            </span>
                          </div>
                        ))}
                        {batchActivities.activities.length > 10 && (
                          <p className="text-xs text-foreground-muted text-center py-1">
                            +{batchActivities.activities.length - 10} more activities
                          </p>
                        )}
                      </div>
                    </div>
                  ) : null}

                  {/* Info Text */}
                  <p className="text-xs text-foreground-muted">
                    Imported on {new Date(batch.uploaded_at).toLocaleDateString()} at {new Date(batch.uploaded_at).toLocaleTimeString()}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
