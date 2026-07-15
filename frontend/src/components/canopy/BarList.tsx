import { cn } from '@/lib/utils';

/**
 * Bars before digits (design contract §0.1): label + soft track + accent
 * fill, the number quiet on the right. Replaces category-breakdown lists.
 */
export interface BarListItem {
  label: string;
  /** formatted display value, e.g. "38,383 t" */
  value: string;
  /** 0–100, relative to the largest item */
  pct: number;
  scope?: 1 | 2 | 3;
}

const scopeFills = {
  1: 'bg-cy-scope1',
  2: 'bg-cy-scope2',
  3: 'bg-cy-scope3',
};

export function BarList({ items, className }: { items: BarListItem[]; className?: string }) {
  return (
    <div className={cn('space-y-3', className)}>
      {items.map((item) => (
        <div key={item.label}>
          <div className="mb-[5px] flex justify-between gap-4 text-[12.5px]">
            <span className="min-w-0 truncate text-cy-ink">{item.label}</span>
            <span className="whitespace-nowrap tabular-nums text-cy-muted">
              <b className="font-semibold text-cy-ink">{item.value}</b>
            </span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-[3px] bg-cy-row">
            <div
              className={cn(
                'h-full rounded-[3px]',
                item.scope ? scopeFills[item.scope] : 'bg-cy-accent'
              )}
              style={{ width: `${Math.max(0, Math.min(100, item.pct))}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
