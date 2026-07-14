'use client';

import { FlaskConical, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui';
import { useLoadSampleData, useSampleDataStatus } from '@/hooks/useSampleData';

interface LoadSampleDataButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  /** Extra line of context rendered under the button (empty-state placements). */
  caption?: string;
  className?: string;
}

/**
 * "Load sample data" — seeds the user's own org with the flagged Galil Steel
 * demo dataset so an empty dashboard/Data Hub comes alive in one click.
 * Renders nothing while sample data is already loaded (the global banner
 * owns the remove affordance). Success/error toasts live in the hook — this
 * component unmounts on success.
 */
export function LoadSampleDataButton({
  variant = 'outline',
  caption,
  className,
}: LoadSampleDataButtonProps) {
  const { data: status } = useSampleDataStatus();
  const loadSample = useLoadSampleData();

  if (!status || status.loaded) return null;

  return (
    <div className={className}>
      <Button
        variant={variant}
        onClick={() => loadSample.mutate()}
        disabled={loadSample.isPending}
        leftIcon={
          loadSample.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <FlaskConical className="w-4 h-4" />
          )
        }
      >
        {loadSample.isPending ? 'Loading sample data…' : 'Load sample data'}
      </Button>
      {caption && <p className="mt-2 text-xs text-foreground-muted">{caption}</p>}
    </div>
  );
}
