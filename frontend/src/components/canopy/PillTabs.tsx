'use client';

import { cn } from '@/lib/utils';

/**
 * Pill tab rail: the active tab sits on an accent-soft pill, the rest are
 * quiet text. Replaces flat tab rows (reports).
 */
export interface PillTab {
  id: string;
  label: string;
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
    <div className={cn('flex flex-wrap gap-1.5', className)} role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={tab.id === value}
          onClick={() => onChange?.(tab.id)}
          className={cn(
            'cursor-pointer rounded-full px-3.5 py-[7px] text-[12.5px] font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cy-accent',
            tab.id === value ? 'bg-cy-accent-soft text-cy-accent' : 'text-cy-muted hover:text-cy-ink'
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
