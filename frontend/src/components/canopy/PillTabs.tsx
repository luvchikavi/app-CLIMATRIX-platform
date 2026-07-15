'use client';

import { Fragment } from 'react';
import { cn } from '@/lib/utils';

/**
 * Pill tab rail: the active tab sits on an accent-soft pill, the rest are
 * quiet text. Replaces flat tab rows (reports).
 *
 * Tabs can carry a `tone` — 'warn' marks the process tabs (audit/verify/
 * export) with the amber family so they read as a different kind of thing
 * than the report views. `dividerBefore` draws a hairline gap before a tab,
 * splitting the rail into groups.
 */
export interface PillTab {
  id: string;
  label: string;
  /** 'accent' (default) = report views · 'warn' = process tabs */
  tone?: 'accent' | 'warn';
  /** draw a vertical hairline before this tab */
  dividerBefore?: boolean;
}

export function PillTabs({
  tabs,
  value,
  onChange,
  className,
}: {
  tabs: PillTab[];
  value: string;
  onChange?: (id: string) => void;
  className?: string;
}) {
  return (
    <div className={cn('flex flex-wrap items-center gap-1.5', className)} role="tablist">
      {tabs.map((tab) => {
        const active = tab.id === value;
        const warn = tab.tone === 'warn';
        return (
          <Fragment key={tab.id}>
            {tab.dividerBefore && (
              <span aria-hidden="true" className="mx-1.5 h-5 w-px shrink-0 bg-cy-row" />
            )}
            <button
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => onChange?.(tab.id)}
              className={cn(
                'cursor-pointer rounded-full px-3.5 py-[7px] text-[12.5px] font-semibold focus-visible:outline-2 focus-visible:outline-offset-2',
                warn ? 'focus-visible:outline-cy-warn' : 'focus-visible:outline-cy-accent',
                active
                  ? warn
                    ? 'bg-cy-warn-soft text-cy-warn'
                    : 'bg-cy-accent-soft text-cy-accent'
                  : warn
                    ? 'text-cy-warn/70 hover:bg-cy-warn-soft/50 hover:text-cy-warn'
                    : 'text-cy-muted hover:text-cy-ink'
              )}
            >
              {tab.label}
            </button>
          </Fragment>
        );
      })}
    </div>
  );
}
