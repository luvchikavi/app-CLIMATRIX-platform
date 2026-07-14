'use client';

import { Card } from '@/components/ui';
import { LoadSampleDataButton } from '@/components/LoadSampleDataButton';
import { useSampleDataStatus } from '@/hooks/useSampleData';

/**
 * Front-page hero for brand-new orgs: one click brings the whole app alive
 * with the sample dataset. Hides itself entirely while sample data is
 * loaded (or status is unknown) — the banner owns that state.
 */
export function SampleDataHero() {
  const { data: status } = useSampleDataStatus();

  if (!status || status.loaded) return null;

  return (
    <Card padding="lg" className="border-primary/30 bg-primary-light/30">
      <div className="flex flex-col md:flex-row md:items-center gap-4 md:gap-6">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-foreground">See Climatrix in action</h3>
          <p className="text-sm text-foreground-muted mt-1 max-w-2xl">
            Load a realistic sample dataset — a full year of an industrial company&apos;s
            energy data. Your dashboard, GHG report and reduction scenarios come alive
            instantly, and one click removes it all again.
          </p>
        </div>
        <LoadSampleDataButton variant="primary" className="shrink-0" />
      </div>
    </Card>
  );
}
