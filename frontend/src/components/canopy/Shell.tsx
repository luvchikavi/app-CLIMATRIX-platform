import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { canopyFont } from './font';
import { Rail, RailProps } from './Rail';

/**
 * Canopy app frame: forest rail + sage canvas, content floating on surfaces.
 * Presentational — layout/AppShell wraps it with auth/setup/trial logic;
 * /design-preview renders it with static props.
 */
export interface ShellProps {
  rail: RailProps;
  /** the quiet top-right cluster (period · theme · user) */
  topbar?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Shell({ rail, topbar, children, className }: ShellProps) {
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
        <main id="main-content" className="min-w-0 px-5 pt-4 pb-11 lg:px-9">
          {topbar ? <div className="mb-3">{topbar}</div> : <div className="pt-3" />}
          {children}
        </main>
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
