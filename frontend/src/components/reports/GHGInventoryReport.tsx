'use client';

import { useState } from 'react';
import {
  Surface,
  PanelLabel,
  StatCells,
  DataTable,
  CellValue,
  type CanopyColumn,
  type StatCell,
} from '@/components/canopy';
import { Badge, DataQualityBadge } from '@/components/ui';
import { cn, formatNumber, categoryNames } from '@/lib/utils';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { GHGInventoryReport as GHGInventoryReportType } from '@/lib/api';

interface GHGInventoryReportProps {
  report: GHGInventoryReportType;
}

/** Quiet key–value row (the mock's `.kv`). */
function Kv({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-3.5 py-1.5 text-[12.5px]">
      <span className="min-w-[130px] shrink-0 text-cy-faint">{label}</span>
      <span className="font-semibold text-cy-ink">{children}</span>
    </div>
  );
}

const scopeDots: Record<number, string> = {
  1: 'bg-cy-scope1',
  2: 'bg-cy-scope2',
  3: 'bg-cy-scope3',
};

type ScopeSource = GHGInventoryReportType['scope_1']['sources'][number];

const sourceColumns: CanopyColumn<ScopeSource>[] = [
  {
    key: 'source',
    header: 'Emission source',
    render: (source) => <span className="font-semibold">{source.display_name}</span>,
  },
  {
    key: 'category',
    header: 'Category',
    render: (source) => (
      <span className="text-cy-muted">
        {categoryNames[source.category_code] || source.category_code}
      </span>
    ),
  },
  {
    key: 'activities',
    header: 'Activities',
    align: 'right',
    render: (source) => source.activity_count,
  },
  {
    key: 'quantity',
    header: 'Quantity',
    align: 'right',
    render: (source) => `${formatNumber(source.total_quantity, 1)} ${source.unit}`,
  },
  {
    key: 'co2e',
    header: 't CO₂e',
    align: 'right',
    render: (source) => <CellValue>{formatNumber(source.total_co2e_tonnes, 2)}</CellValue>,
  },
  {
    key: 'dq',
    header: 'Quality',
    align: 'right',
    render: (source) => (
      <DataQualityBadge
        score={Math.round(source.avg_data_quality) as 1 | 2 | 3 | 4 | 5}
        size="sm"
        showLabel={false}
      />
    ),
  },
];

export function GHGInventoryReport({ report }: GHGInventoryReportProps) {
  const [expandedScopes, setExpandedScopes] = useState<Record<number, boolean>>({
    1: true,
    2: true,
    3: false,
  });

  const toggleScope = (scope: number) => {
    setExpandedScopes(prev => ({ ...prev, [scope]: !prev[scope] }));
  };

  const summary = report.executive_summary;

  const totalsCells: StatCell[] = [
    {
      label: 'Total',
      value: formatNumber(summary.total_emissions_tonnes, 1),
      sub: 't CO₂e',
    },
    {
      label: 'Scope 1',
      value: formatNumber(summary.scope_1_tonnes, 1),
      sub: `${summary.scope_1_percentage.toFixed(1)}%`,
      scope: 1,
    },
    {
      label: 'Scope 2',
      value: formatNumber(summary.scope_2_tonnes, 1),
      sub: `${summary.scope_2_percentage.toFixed(1)}%`,
      scope: 2,
    },
    {
      label: 'Scope 3',
      value: formatNumber(summary.scope_3_tonnes, 1),
      sub: `${summary.scope_3_percentage.toFixed(1)}%`,
      scope: 3,
    },
  ];

  const comparison = report.base_year_comparison;

  return (
    <div className="space-y-4">
      {/* Inventory header */}
      <Surface>
        <PanelLabel>Inventory</PanelLabel>
        <Kv label="Organization">{report.organization.name}</Kv>
        <Kv label="Period">
          {report.reporting_period} ·{' '}
          {new Date(report.boundaries.reporting_period_start).toLocaleDateString()} –{' '}
          {new Date(report.boundaries.reporting_period_end).toLocaleDateString()}
        </Kv>
        <Kv label="Boundary">
          {report.boundaries.consolidation_approach} · {report.boundaries.included_facilities}
        </Kv>
        {report.organization.industry && (
          <Kv label="Industry">{report.organization.industry}</Kv>
        )}
        <Kv label="Standard">ISO 14064-1 · GHG Protocol</Kv>
        <Kv label="Report date">{new Date(report.report_date).toLocaleDateString()}</Kv>
      </Surface>

      {/* Totals */}
      <Surface>
        <PanelLabel>Totals</PanelLabel>
        <StatCells cells={totalsCells} />
        <p className="mt-3 text-[11.5px] text-cy-faint">
          {summary.total_activities} activities · top sources:{' '}
          {summary.top_emission_sources.slice(0, 3).join(' · ')}
        </p>
        <p className="mt-1.5 flex items-center gap-2 text-[12px] text-cy-muted">
          <DataQualityBadge
            score={Math.round(summary.data_quality_score) as 1 | 2 | 3 | 4 | 5}
            size="sm"
          />
          Weighted data quality {summary.data_quality_score.toFixed(2)} —{' '}
          {report.data_quality_interpretation}
        </p>
      </Surface>

      {/* Scope details */}
      {[report.scope_1, report.scope_2, report.scope_3].map((scopeData) => (
        <Surface key={scopeData.scope} padding="none" className="px-6 py-4">
          <button
            type="button"
            onClick={() => toggleScope(scopeData.scope)}
            className="flex w-full cursor-pointer items-center justify-between gap-4 text-left"
            aria-expanded={expandedScopes[scopeData.scope]}
          >
            <span className="flex items-center gap-2.5 text-[13.5px] font-semibold text-cy-ink">
              <span
                aria-hidden="true"
                className={cn('inline-block h-[7px] w-[7px] rounded-full', scopeDots[scopeData.scope])}
              />
              {scopeData.scope_name}
            </span>
            <span className="flex items-center gap-3">
              <span className="text-[13px] font-semibold tabular-nums text-cy-ink">
                {formatNumber(scopeData.total_co2e_tonnes, 1)} t
                <span className="ml-2 font-normal text-cy-muted">
                  {scopeData.percentage_of_total.toFixed(1)}%
                </span>
              </span>
              {expandedScopes[scopeData.scope] ? (
                <ChevronUp className="h-4 w-4 text-cy-faint" />
              ) : (
                <ChevronDown className="h-4 w-4 text-cy-faint" />
              )}
            </span>
          </button>
          {expandedScopes[scopeData.scope] && (
            <div className="mt-3.5">
              <p className="mb-3 flex items-center gap-2 text-[12px] text-cy-muted">
                {scopeData.activity_count} activities · avg quality{' '}
                <DataQualityBadge
                  score={Math.round(scopeData.avg_data_quality) as 1 | 2 | 3 | 4 | 5}
                  size="sm"
                  showLabel={false}
                />
              </p>
              {scopeData.sources.length > 0 ? (
                <DataTable
                  columns={sourceColumns}
                  rows={scopeData.sources}
                  rowKey={(_, index) => index}
                />
              ) : (
                <p className="py-3 text-[12.5px] text-cy-muted">
                  No {scopeData.scope_name.toLowerCase()} emissions recorded.
                </p>
              )}
            </div>
          )}
        </Surface>
      ))}

      {/* Methodology, base year & verification */}
      <Surface>
        <PanelLabel>Methodology &amp; base year</PanelLabel>
        <Kv label="Calculation">{report.methodology.calculation_approach}</Kv>
        <Kv label="GWP set">{report.methodology.gwp_values}</Kv>
        <Kv label="Factor sources">{report.methodology.emission_factor_sources.join(' · ')}</Kv>
        {report.methodology.exclusions.length > 0 && (
          <Kv label="Exclusions">{report.methodology.exclusions.join(' · ')}</Kv>
        )}
        {report.methodology.assumptions.length > 0 && (
          <Kv label="Assumptions">{report.methodology.assumptions.join(' · ')}</Kv>
        )}
        {report.organization.base_year && (
          <Kv label="Base year">
            {report.organization.base_year}
            {comparison && (
              <>
                {' '}· {formatNumber(comparison.base_year_emissions_tonnes, 1)} t →{' '}
                {formatNumber(comparison.current_emissions_tonnes, 1)} t ·{' '}
                <span
                  className={
                    comparison.percentage_change < 0 ? 'text-cy-accent' : 'text-error'
                  }
                >
                  {comparison.percentage_change > 0 ? '+' : ''}
                  {comparison.percentage_change.toFixed(1)}%
                </span>
              </>
            )}
          </Kv>
        )}
        <div className="mt-2 flex flex-wrap items-center gap-2 text-[12.5px] text-cy-muted">
          <Badge
            variant={
              report.verification.status === 'verified'
                ? 'success'
                : report.verification.status === 'audit'
                ? 'warning'
                : 'default'
            }
            size="sm"
          >
            {report.verification.status.charAt(0).toUpperCase() + report.verification.status.slice(1)}
          </Badge>
          {report.verification.assurance_level && (
            <span>
              Assurance: <span className="capitalize">{report.verification.assurance_level}</span>
            </span>
          )}
          {report.verification.verified_by && (
            <span>
              Verified by {report.verification.verified_by}
              {report.verification.verified_at &&
                ` on ${new Date(report.verification.verified_at).toLocaleDateString()}`}
            </span>
          )}
        </div>
        {report.verification.verification_statement && (
          <p className="mt-1.5 text-[12px] italic text-cy-muted">
            &quot;{report.verification.verification_statement}&quot;
          </p>
        )}
      </Surface>
    </div>
  );
}
