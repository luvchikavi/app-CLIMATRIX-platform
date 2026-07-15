'use client';

import { Loader2 } from 'lucide-react';
import { useRemoveSampleData, useSampleDataStatus } from '@/hooks/useSampleData';

/**
 * Quiet one-line sample-data notice (Canopy) — a dot and a sentence, never a
 * box. Offers the one-click undo; success/error toasts live in the hook and
 * this line unmounts on success.
 */
export function SampleDataBanner() {
  const { data: status } = useSampleDataStatus();
  const removeSample = useRemoveSampleData();

  if (!status?.loaded) return null;

  return (
    <div className="flex items-center gap-2 text-[12.5px] text-cy-muted">
      <span className="w-[7px] h-[7px] rounded-full bg-cy-accent shrink-0" aria-hidden="true" />
      <span>You&apos;re viewing sample data — kept separate from your own</span>
      <span className="text-cy-faint" aria-hidden="true">·</span>
      <button
        onClick={() => removeSample.mutate()}
        disabled={removeSample.isPending}
        className="flex items-center gap-1.5 font-bold text-cy-accent shrink-0 disabled:opacity-60"
      >
        {removeSample.isPending && <Loader2 className="w-3 h-3 animate-spin" />}
        {removeSample.isPending ? 'Removing…' : 'Clear sample'}
      </button>
    </div>
  );
}
