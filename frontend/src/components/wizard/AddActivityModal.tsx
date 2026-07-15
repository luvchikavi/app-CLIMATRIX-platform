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
      className="flex items-center gap-1 rounded-[10px] px-3 py-2 text-[12.5px] font-semibold text-cy-muted transition-colors hover:bg-cy-row hover:text-foreground"
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
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />

      <div
        ref={trapRef}
        className="relative bg-background-elevated rounded-cy shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden animate-fade-in-up"
      >
        <div className="flex items-center justify-between px-6 pb-3 pt-5">
          <div>
            <h2 className="text-[16px] font-bold tracking-[-0.01em] text-foreground">Add activity</h2>
            <p className="text-[12.5px] text-cy-muted">
              Record one emission line by hand — it lands in the ledger like any import
            </p>
          </div>
          <div className="flex items-center gap-2">
            <WizardBackButton />
            <button
              onClick={onClose}
              className="rounded-md p-1.5 text-cy-muted transition-colors hover:bg-cy-row hover:text-foreground"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
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
