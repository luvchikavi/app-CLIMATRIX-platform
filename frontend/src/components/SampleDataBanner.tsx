'use client';

import { FlaskConical, Loader2 } from 'lucide-react';
import { useRemoveSampleData, useSampleDataStatus } from '@/hooks/useSampleData';

/**
 * Persistent banner shown at the top of the app while the sample dataset is
 * loaded: tells the user they're looking at demo data and offers the
 * one-click undo. Success/error toasts live in the hook — this banner
 * unmounts on success.
 */
export function SampleDataBanner() {
  const { data: status } = useSampleDataStatus();
  const removeSample = useRemoveSampleData();

  if (!status?.loaded) return null;

  return (
    <div className="flex items-center justify-between gap-3 px-4 py-2 rounded-lg border text-sm mb-4 bg-warning-50 border-warning/30 text-foreground">
      <span className="flex items-center gap-2">
        <FlaskConical className="w-4 h-4 shrink-0 text-warning" />
        <span>
          <span className="font-semibold">Sample data is loaded</span> — you&apos;re exploring
          Climatrix with the Galil Steel demo dataset. It&apos;s kept separate from your own data.
        </span>
      </span>
      <button
        onClick={() => removeSample.mutate()}
        disabled={removeSample.isPending}
        className="flex items-center gap-1.5 font-semibold underline shrink-0 disabled:opacity-60"
      >
        {removeSample.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
        {removeSample.isPending ? 'Removing…' : 'Remove sample data'}
      </button>
    </div>
  );
}
