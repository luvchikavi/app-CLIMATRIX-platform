import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

/**
 * Canopy table: row-tint separators (the --cy-row tint, no borders), 10.5px
 * uppercase headers, quiet right-aligned numbers.
 */
export interface CanopyColumn<T> {
  key: string;
  header: ReactNode;
  align?: 'left' | 'right';
  render: (row: T, index: number) => ReactNode;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  className,
}: {
  columns: CanopyColumn<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string | number;
  className?: string;
}) {
  return (
    <table className={cn('w-full border-collapse text-[13px]', className)}>
      <thead>
        <tr>
          {columns.map((col) => (
            <th
              key={col.key}
              className={cn(
                'pb-2.5 text-[10.5px] font-bold tracking-[0.07em] uppercase text-cy-faint',
                col.align === 'right' ? 'text-right' : 'text-left'
              )}
            >
              {col.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => (
          <tr key={rowKey(row, index)}>
            {columns.map((col) => (
              <td
                key={col.key}
                className={cn(
                  'border-t border-cy-row py-[9px] text-cy-ink',
                  col.align === 'right' && 'text-right tabular-nums text-cy-muted'
                )}
              >
                {col.render(row, index)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Emphasized numeric cell value. */
export function CellValue({ children }: { children: ReactNode }) {
  return <b className="font-semibold text-cy-ink">{children}</b>;
}

/** Share-bar cell helper: small accent bar scaled to pct, then the number. */
export function ShareBar({ pct, maxWidth = 60 }: { pct: number; maxWidth?: number }) {
  return (
    <>
      <span
        aria-hidden="true"
        className="mr-2 inline-block h-1 rounded-[2px] bg-cy-accent align-[2px]"
        style={{ width: `${Math.max(2, (Math.max(0, Math.min(100, pct)) / 100) * maxWidth)}px` }}
      />
      {pct.toFixed(1)}%
    </>
  );
}
