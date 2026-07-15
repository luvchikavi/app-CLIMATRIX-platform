'use client';

import { Surface, PanelLabel, DataTable, CellValue, ShareBar, type CanopyColumn } from '@/components/canopy';
import { DataQualityBadge } from '@/components/ui';
import { formatCO2e } from '@/lib/utils';
import type { DataQualitySummary } from '@/lib/api';

interface DataQualityReportProps {
  report: DataQualitySummary;
}

const SCORE_LABELS: Record<number, string> = {
  1: 'Verified data',
  2: 'Primary data',
  3: 'Activity average',
  4: 'Spend-based',
  5: 'Estimated',
};

const SCORE_DESCRIPTIONS: Record<number, string> = {
  1: 'Audited/verified data from primary sources (e.g., audited energy bills)',
  2: 'Non-audited data from primary sources (e.g., utility bills, invoices)',
  3: 'Physical activity data with average emission factors',
  4: 'Economic activity-based modeling (e.g., spend-based calculations)',
  5: 'Estimated data with high uncertainty (e.g., industry averages)',
};

interface ScoreRow {
  score: 1 | 2 | 3 | 4 | 5;
  activities: number;
  co2eKg: number;
  pct: number;
}

const columns: CanopyColumn<ScoreRow>[] = [
  {
    key: 'source',
    header: 'Source quality',
    render: (row) => (
      <div className="py-0.5">
        <div className="flex items-center gap-2">
          <DataQualityBadge score={row.score} size="sm" showLabel={false} />
          <span className="font-semibold">{SCORE_LABELS[row.score]}</span>
        </div>
        <p className="mt-0.5 max-w-[52ch] text-[12px] text-cy-muted">
          {SCORE_DESCRIPTIONS[row.score]}
        </p>
      </div>
    ),
  },
  {
    key: 'activities',
    header: 'Activities',
    align: 'right',
    render: (row) => row.activities,
  },
  {
    key: 'co2e',
    header: 'Emissions',
    align: 'right',
    render: (row) => <CellValue>{formatCO2e(row.co2eKg)}</CellValue>,
  },
  {
    key: 'share',
    header: 'Share',
    align: 'right',
    render: (row) => <ShareBar pct={row.pct} />,
  },
];

export function DataQualityReport({ report }: DataQualityReportProps) {
  const rows: ScoreRow[] = ([1, 2, 3, 4, 5] as const).map((score) => {
    const scoreData = report.by_score.find((s) => s.score === score);
    return {
      score,
      activities: scoreData?.activity_count ?? 0,
      co2eKg: scoreData?.total_co2e_kg ?? 0,
      pct: scoreData?.percentage ?? 0,
    };
  });

  const needsPrimaryData = report.weighted_average_score > 3;

  return (
    <div className="space-y-4">
      {/* Score */}
      <Surface>
        <PanelLabel>Data quality score</PanelLabel>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
          <p className="text-[16px] font-[650] tabular-nums text-cy-ink">
            {report.weighted_average_score.toFixed(2)}
            <small className="ml-1 text-[11.5px] font-medium text-cy-muted">/ 5 · 1 = best</small>
          </p>
          <div
            className="h-1.5 min-w-[160px] max-w-[280px] flex-1 overflow-hidden rounded-[3px] bg-cy-row"
            aria-hidden="true"
          >
            <div
              className="h-full rounded-[3px] bg-cy-accent"
              style={{ width: `${Math.min(100, (report.weighted_average_score / 5) * 100)}%` }}
            />
          </div>
        </div>
        <p className="mt-2 max-w-[62ch] text-[12.5px] text-cy-muted">
          {report.score_interpretation}
        </p>
        <p className="mt-2 text-[11.5px] text-cy-faint">
          {report.total_activities} activities · {report.period_name} · PCAF-aligned scoring
        </p>
      </Surface>

      {/* One merged view: distribution + definitions */}
      <Surface>
        <PanelLabel>Where your numbers come from</PanelLabel>
        <DataTable columns={columns} rows={rows} rowKey={(row) => row.score} />
      </Surface>

      {/* Improve */}
      <Surface>
        <PanelLabel>Raise the score</PanelLabel>
        <div className="space-y-0.5">
          {needsPrimaryData && (
            <div className="flex items-baseline gap-2.5 py-[9px] text-[13px]">
              <span className="relative top-px h-2 w-2 shrink-0 rounded-full border-[1.5px] border-cy-warn" aria-hidden="true" />
              <p className="text-cy-ink">
                Request primary data (invoices, bills) from suppliers{' '}
                <span className="text-[12px] text-cy-muted">— reduces reliance on estimated values</span>
              </p>
            </div>
          )}
          <div className="flex items-baseline gap-2.5 py-[9px] text-[13px]">
            <span className="relative top-px h-2 w-2 shrink-0 rounded-full border-[1.5px] border-cy-warn" aria-hidden="true" />
            <p className="text-cy-ink">
              Set up data collection for Scope 3 categories{' '}
              <span className="text-[12px] text-cy-muted">— improves coverage and accuracy</span>
            </p>
          </div>
          <div className="flex items-baseline gap-2.5 py-[9px] text-[13px]">
            <span className="relative top-px h-2 w-2 shrink-0 rounded-full border-[1.5px] border-cy-warn" aria-hidden="true" />
            <p className="text-cy-ink">
              Third-party verification of key sources{' '}
              <span className="text-[12px] text-cy-muted">— reaches DQ1 where it matters most</span>
            </p>
          </div>
          <div className="flex items-baseline gap-2.5 py-[9px] text-[13px]">
            <span className="relative top-px h-2 w-2 shrink-0 rounded-full bg-cy-accent" aria-hidden="true" />
            <p className="text-cy-ink">
              Document collection methods and keep evidence{' '}
              <span className="text-[12px] text-cy-muted">— your audit trail already covers this</span>
            </p>
          </div>
        </div>
      </Surface>
    </div>
  );
}
