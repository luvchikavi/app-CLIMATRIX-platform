import { cn } from '@/lib/utils';

/**
 * The footprint row: quiet label/value cells with scope dots. Numbers cap at
 * 16px — never the largest thing on screen (design contract §0.2). Replaces
 * KPICard grids and StatBand.
 */
export interface StatCell {
  label: string;
  value: string;
  /** unit or share, rendered small after the value (e.g. "t CO₂e", "28%") */
  sub?: string;
  /** renders the GHG scope dot before the label */
  scope?: 1 | 2 | 3;
}

const scopeDots = {
  1: 'bg-cy-scope1',
  2: 'bg-cy-scope2',
  3: 'bg-cy-scope3',
};

export function StatCells({ cells, className }: { cells: StatCell[]; className?: string }) {
  return (
    <div className={cn('flex flex-wrap gap-x-11 gap-y-2.5', className)}>
      {cells.map((cell) => (
        <div key={cell.label}>
          <p className="text-[16px] font-[650] tabular-nums text-cy-ink">
            {cell.value}
            {cell.sub && (
              <small className="ml-1 text-[11.5px] font-medium text-cy-muted">{cell.sub}</small>
            )}
          </p>
          <p className="mt-0.5 flex items-center gap-1.5 text-[11.5px] text-cy-muted">
            {cell.scope && (
              <span
                aria-hidden="true"
                className={cn('inline-block h-[7px] w-[7px] rounded-full', scopeDots[cell.scope])}
              />
            )}
            {cell.label}
          </p>
        </div>
      ))}
    </div>
  );
}
