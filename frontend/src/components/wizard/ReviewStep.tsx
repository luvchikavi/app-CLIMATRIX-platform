'use client';

import { useWizardStore } from '@/stores/wizard';
import { useCreateActivity } from '@/hooks/useEmissions';
import { Check, Loader2, AlertCircle, Plus, Trash2, Info, Package } from 'lucide-react';
import { useState } from 'react';
import { Button, Card, ScopeBadge } from '@/components/ui';
import { formatCO2e } from '@/lib/utils';

interface ReviewStepProps {
  periodId: string;
  onSuccess?: () => void;
}

export function ReviewStep({ periodId, onSuccess }: ReviewStepProps) {
  const entry = useWizardStore((s) => s.entry);
  const selectedFactor = useWizardStore((s) => s.selectedFactor);
  const entries = useWizardStore((s) => s.entries);
  const addEntry = useWizardStore((s) => s.addEntry);
  const removeEntry = useWizardStore((s) => s.removeEntry);
  const clearEntries = useWizardStore((s) => s.clearEntries);
  const reset = useWizardStore((s) => s.reset);
  const getTotalCO2e = useWizardStore((s) => s.getTotalCO2e);

  const createActivity = useCreateActivity(periodId);
  const [submitResult, setSubmitResult] = useState<{
    success: boolean;
    count?: number;
    totalCO2e?: number;
    error?: string;
  } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Calculate preview emission using actual factor
  const previewCO2e = selectedFactor && entry.quantity
    ? entry.quantity * (selectedFactor.co2e_factor || 0)
    : 0;

  // Calculate running total including current entry
  const runningTotal = getTotalCO2e() + previewCO2e;

  // Handle "Save & Add Another" - just adds to queue, doesn't submit
  const handleAddAnother = () => {
    addEntry(); // This resets form but keeps entries
  };

  // Submit all entries (current + accumulated)
  const handleSubmitAll = async () => {
    setIsSubmitting(true);
    setSubmitResult(null);

    try {
      // First add current entry to the list
      addEntry();

      // Get all entries to submit
      const allEntries = useWizardStore.getState().entries;

      if (allEntries.length === 0) {
        setSubmitResult({
          success: false,
          error: 'No entries to submit',
        });
        setIsSubmitting(false);
        return;
      }

      let totalCO2e = 0;
      let successCount = 0;

      // Submit each entry
      for (const e of allEntries) {
        const result = await createActivity.mutateAsync({
          scope: e.scope,
          category_code: e.category_code,
          activity_key: e.activity_key,
          description: e.description,
          quantity: e.quantity,
          unit: e.unit,
          activity_date: e.activity_date || new Date().toISOString().split('T')[0],
        });

        if (result.emission) {
          totalCO2e += result.emission.co2e_kg;
        }
        successCount++;
      }

      setSubmitResult({
        success: true,
        count: successCount,
        totalCO2e,
      });

      // Reset everything after success
      setTimeout(() => {
        reset();
        onSuccess?.();
      }, 2500);
    } catch (error) {
      setSubmitResult({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to submit activities',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Submit just the current entry
  const handleSubmitCurrent = async () => {
    setIsSubmitting(true);
    setSubmitResult(null);

    try {
      const activityDate = entry.activity_date || new Date().toISOString().split('T')[0];

      const result = await createActivity.mutateAsync({
        scope: entry.scope as 1 | 2 | 3,
        category_code: entry.category_code!,
        activity_key: entry.activity_key!,
        description: entry.description!,
        quantity: entry.quantity!,
        unit: entry.unit!,
        activity_date: activityDate,
      });

      setSubmitResult({
        success: true,
        count: 1,
        totalCO2e: result.emission?.co2e_kg || 0,
      });

      // Reset just current entry, keep accumulated ones
      setTimeout(() => {
        useWizardStore.getState().reset();
        onSuccess?.();
      }, 2000);
    } catch (error) {
      setSubmitResult({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to create activity',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-foreground">Review & Submit</h2>
        <p className="text-foreground-muted">Confirm your activity entry</p>
      </div>

      {/* Summary card */}
      <Card padding="lg" className="border-2">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-foreground-muted">Scope</span>
            <div className="mt-1">
              <ScopeBadge scope={entry.scope as 1 | 2 | 3} />
            </div>
          </div>
          <div>
            <span className="text-sm text-foreground-muted">Category</span>
            <p className="font-semibold text-foreground">{entry.category_code}</p>
          </div>
          <div className="col-span-2">
            <span className="text-sm text-foreground-muted">Activity Type</span>
            <p className="font-semibold text-foreground">{selectedFactor?.display_name}</p>
          </div>
          <div className="col-span-2">
            <span className="text-sm text-foreground-muted">Description</span>
            <p className="font-semibold text-foreground">{entry.description}</p>
          </div>
          <div>
            <span className="text-sm text-foreground-muted">Quantity</span>
            <p className="font-semibold text-foreground">
              {entry.quantity?.toLocaleString()} {entry.unit}
            </p>
          </div>
          <div>
            <span className="text-sm text-foreground-muted">Emission Factor</span>
            <p className="font-semibold text-foreground">
              {selectedFactor?.co2e_factor} {selectedFactor?.factor_unit || `kg CO2e/${entry.unit}`}
            </p>
          </div>
        </div>

        {/* Emission Factor Source Info */}
        {selectedFactor && (
          <div className="mt-4 pt-4 border-t border-border">
            <div className="flex items-center gap-2 text-sm text-foreground-muted">
              <Info className="w-4 h-4" />
              <span>
                Source: <strong>{selectedFactor.source || 'DEFRA'}</strong>
                {selectedFactor.year && ` (${selectedFactor.year})`}
                {selectedFactor.region && ` | Region: ${selectedFactor.region}`}
              </span>
            </div>
          </div>
        )}

        {/* Estimated emission preview */}
        <div className="mt-4 pt-4 border-t border-border">
          <div className="flex items-center justify-between">
            <span className="text-sm text-foreground-muted">Estimated Emission</span>
            <span className="text-xl font-bold text-primary">{formatCO2e(previewCO2e)}</span>
          </div>
          <p className="text-xs text-foreground-muted mt-1 font-mono">
            {entry.quantity} {entry.unit} x {selectedFactor?.co2e_factor} = {previewCO2e.toFixed(2)} kg CO2e
          </p>
        </div>
      </Card>

      {/* FIX-7: Accumulated Entries Panel */}
      {entries.length > 0 && (
        <Card padding="md" className="bg-info/5 border-info/20">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Package className="w-5 h-5 text-info" />
              <span className="font-semibold text-foreground">
                Queued Entries ({entries.length})
              </span>
            </div>
            <div className="text-right">
              <span className="text-sm text-foreground-muted">Running Total</span>
              <p className="text-lg font-bold text-info">{formatCO2e(getTotalCO2e())}</p>
            </div>
          </div>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {entries.map((e, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2 bg-background rounded-lg text-sm"
              >
                <div className="flex items-center gap-2">
                  <ScopeBadge scope={e.scope} size="sm" />
                  <span className="font-medium">{e.display_name || e.activity_key}</span>
                  <span className="text-foreground-muted">
                    {e.quantity?.toLocaleString()} {e.unit}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-primary">
                    {formatCO2e((e.quantity || 0) * (e.co2e_factor || 0))}
                  </span>
                  <button
                    onClick={() => removeEntry(idx)}
                    className="p-1 text-foreground-muted hover:text-error transition-colors"
                    title="Remove entry"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
          {entries.length > 1 && (
            <div className="mt-3 pt-3 border-t border-info/20 flex justify-end">
              <Button
                variant="ghost"
                size="sm"
                onClick={clearEntries}
                className="text-error hover:text-error"
              >
                Clear All
              </Button>
            </div>
          )}
        </Card>
      )}

      {/* Grand Total (including current entry) */}
      {(entries.length > 0 || previewCO2e > 0) && (
        <div className="p-4 bg-primary/10 rounded-xl border border-primary/20">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-foreground">
              Total to Submit ({entries.length + (entry.quantity ? 1 : 0)} entries)
            </span>
            <span className="text-2xl font-bold text-primary">{formatCO2e(runningTotal)}</span>
          </div>
        </div>
      )}

      {/* Result */}
      {submitResult?.success && (
        <div className="p-6 bg-success/10 border-2 border-success/20 rounded-xl animate-fade-in">
          <div className="flex items-center gap-2 text-success">
            <Check className="w-5 h-5" />
            <span className="font-semibold">
              {submitResult.count === 1 ? 'Activity' : `${submitResult.count} Activities`} Submitted Successfully
            </span>
          </div>
          <div className="mt-4">
            <p className="text-3xl font-bold text-success">
              {formatCO2e(submitResult.totalCO2e || 0)}
            </p>
            <p className="text-sm text-success/80 mt-2">
              Total emissions saved to database
            </p>
          </div>
        </div>
      )}

      {submitResult?.error && (
        <div className="p-4 bg-error/10 border-2 border-error/20 rounded-xl">
          <div className="flex items-center gap-2 text-error">
            <AlertCircle className="w-5 h-5" />
            <span className="font-semibold">Error</span>
          </div>
          <p className="text-error/90 mt-2">{submitResult.error}</p>
        </div>
      )}

      {/* Actions */}
      {!submitResult?.success && (
        <div className="flex flex-wrap items-center gap-3">
          <Button
            variant="outline"
            onClick={handleAddAnother}
            disabled={isSubmitting}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Save & Add Another
          </Button>
          {entries.length > 0 ? (
            <Button
              variant="primary"
              onClick={handleSubmitAll}
              disabled={isSubmitting}
              isLoading={isSubmitting}
            >
              Submit All ({entries.length + 1} entries)
            </Button>
          ) : (
            <Button
              variant="primary"
              onClick={handleSubmitCurrent}
              disabled={isSubmitting}
              isLoading={isSubmitting}
            >
              Submit Activity
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
