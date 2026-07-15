import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { canopyFont } from './font';
import { Rail, RailProps } from './Rail';

/**
 * Canopy app frame: forest rail + sage canvas, content floating on surfaces.
 * Phase 1 is presentational; batch 2.1 replaces layout/AppShell with this and
 * carries over its auth/trial logic.
 */
export interface ShellProps {
  rail: RailProps;
  children: ReactNode;
  className?: string;
}

export function Shell({ rail, children, className }: ShellProps) {
  return (
    <div
      className={cn(
        canopyFont.variable,
        'min-h-full bg-cy-canvas font-cy text-[13.5px] leading-[1.55] text-cy-ink antialiased',
        className
      )}
    >
      <div className="lg:grid lg:grid-cols-[224px_1fr]">
        <Rail {...rail} />
        <main className="px-5 pt-6 pb-11 lg:px-9 lg:pt-7">{children}</main>
      </div>
    </div>
  );
}

/** Page heading: 20px title (the largest type in the app) + one guiding line. */
export function PageHead({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-[22px]">
      <h2 className="text-[20px] font-[650] tracking-[-0.01em] text-cy-ink">{title}</h2>
      {subtitle && <p className="mt-[3px] text-[13px] text-cy-muted">{subtitle}</p>}
    </div>
  );
}
