'use client';

/**
 * The single manual-entry point for the ledger — "Add Activity" has exactly one
 * home (the Activities page opens this; the Data Hub links to it). Wraps the
 * step wizard in a focus-trapped modal.
 */

import { ActivityWizard } from '@/components/wizard';
import { useWizardStore } from '@/stores/wizard';
import { useFocusTrap } from '@/hooks/useFocusTrap';
import { ArrowLeft, X } from 'lucide-react';

function WizardBackButton() {
  const step = useWizardStore((s) => s.step);
  const goBack = useWizardStore((s) => s.goBack);

  if (step === 'scope') return null;

  return (
    <button
      onClick={goBack}
      className="flex items-center gap-1 px-3 py-2 text-sm text-foreground-muted hover:text-foreground hover:bg-background-muted rounded-lg transition-colors"
    >
      <ArrowLeft className="w-4 h-4" />
      Back
    </button>
  );
}

interface AddActivityModalProps {
  periodId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export function AddActivityModal({ periodId, onClose, onSuccess }: AddActivityModalProps) {
  const trapRef = useFocusTrap<HTMLDivElement>(true);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Add Activity"
    >
      <div
        className="absolute inset-0 bg-neutral-950/50 backdrop-blur-sm"
        onClick={onClose}
      />

      <div
        ref={trapRef}
        className="relative bg-background-elevated rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden animate-fade-in-up"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div>
            <h2 className="text-lg font-semibold text-foreground">Add Activity</h2>
            <p className="text-sm text-foreground-muted">
              Record one emission line by hand — it lands in the ledger like any import
            </p>
          </div>
          <div className="flex items-center gap-2">
            <WizardBackButton />
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-background-muted transition-colors"
            >
              <X className="w-5 h-5 text-foreground-muted" />
            </button>
          </div>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
          <ActivityWizard periodId={periodId} onSuccess={onSuccess} />
        </div>
      </div>
    </div>
  );
}
