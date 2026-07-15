'use client';

/**
 * The density template's stat strip: one slim band of divide-x cells, no
 * cell taller than its content. Use instead of a grid of KPI cards.
 */

import { Card } from './Card';
import { cn } from '@/lib/utils';

export interface StatBandCell {
  label: React.ReactNode;
  value: React.ReactNode;
  sub?: React.ReactNode;
  /** Extra classes on the value line (e.g. a status color). */
  valueClassName?: string;
}

export interface StatBandProps {
  cells: StatBandCell[];
  className?: string;
}

export function StatBand({ cells, className }: StatBandProps) {
  return (
    <Card padding="none" className={cn('overflow-hidden', className)}>
      <div className="flex flex-wrap divide-x divide-border">
        {cells.map((cell, i) => (
          <div key={i} className="px-5 py-3 min-w-[140px]">
            <p className="flex items-center gap-1.5 text-xs font-medium text-foreground-muted whitespace-nowrap">
              {cell.label}
            </p>
            <p
              className={cn(
                'text-xl font-bold text-foreground mt-0.5 tracking-tight',
                cell.valueClassName
              )}
            >
              {cell.value}
            </p>
            {cell.sub != null && (
              <p className="text-xs text-foreground-muted mt-0.5">{cell.sub}</p>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}
