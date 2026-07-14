'use client';

/**
 * The whole footprint in ONE compact band: total + each scope's share and
 * activity count. Replaces the five oversized KPI cards — no cell is taller
 * than its content, and market-based Scope 2 only appears when it has a
 * value. Scope cells stay clickable for the drill-down.
 */

import { Card } from '@/components/ui';
import { cn, formatCO2e } from '@/lib/utils';

interface ScopeStat {
  scope: 1 | 2 | 3;
  label: string;
  value: number; // kg
  percentage: number;
  activityCount: number;
}

interface FootprintBandProps {
  total: number; // kg
  periodName: string;
  activityCount: number;
  scopes: ScopeStat[];
  /** kg; the cell renders only when this is a real, non-zero value. */
  marketBased?: number | null;
  onScopeClick?: (scope: 1 | 2 | 3) => void;
}

const SCOPE_DOT: Record<1 | 2 | 3, string> = {
  1: 'bg-scope1',
  2: 'bg-scope2',
  3: 'bg-scope3',
};

export function FootprintBand({
  total,
  periodName,
  activityCount,
  scopes,
  marketBased,
  onScopeClick,
}: FootprintBandProps) {
  return (
    <Card padding="none" className="overflow-hidden">
      <div className="flex flex-wrap divide-x divide-border">
        {/* Total */}
        <div className="px-5 py-4 min-w-[180px]">
          <p className="text-xs font-medium text-foreground-muted uppercase tracking-wide">
            Total emissions
          </p>
          <p className="text-2xl font-bold text-foreground mt-0.5 tracking-tight">
            {formatCO2e(total)}
          </p>
          <p className="text-xs text-foreground-muted mt-0.5">
            {periodName} · {activityCount} activities
          </p>
        </div>

        {/* Scopes */}
        {scopes.map((s) => {
          const clickable = s.activityCount > 0 && !!onScopeClick;
          return (
            <button
              key={s.label}
              type="button"
              disabled={!clickable}
              onClick={() => clickable && onScopeClick(s.scope)}
              className={cn(
                'px-5 py-4 text-left flex-1 min-w-[150px] transition-colors',
                clickable ? 'hover:bg-background-muted cursor-pointer' : 'cursor-default'
              )}
              title={clickable ? 'Click for breakdown' : undefined}
            >
              <p className="flex items-center gap-1.5 text-xs font-medium text-foreground-muted">
                <span className={cn('w-2 h-2 rounded-full shrink-0', SCOPE_DOT[s.scope])} />
                {s.label}
              </p>
              <p className="text-2xl font-bold text-foreground mt-0.5 tracking-tight">
                {formatCO2e(s.value)}
                <span className="text-sm font-medium text-foreground-muted ml-1.5">
                  {s.percentage.toFixed(0)}%
                </span>
              </p>
              <p className="text-xs text-foreground-muted mt-0.5">
                {s.activityCount} activities
              </p>
            </button>
          );
        })}

        {/* Market-based Scope 2 — only when reported */}
        {marketBased != null && marketBased > 0 && (
          <div className="px-5 py-4 min-w-[150px]">
            <p className="flex items-center gap-1.5 text-xs font-medium text-foreground-muted">
              <span className="w-2 h-2 rounded-full shrink-0 bg-scope2" />
              Scope 2 · Market-based
            </p>
            <p className="text-2xl font-bold text-foreground mt-0.5 tracking-tight">
              {formatCO2e(marketBased)}
            </p>
          </div>
        )}
      </div>
    </Card>
  );
}
