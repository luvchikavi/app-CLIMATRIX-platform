'use client';

/**
 * ISO 14064-1 inventory, density template: header band (what + who) →
 * footprint strip → one sources/quality row → scope tables → collapsed
 * methodology → base-year and verification finish lines. No card taller
 * than its content, nothing shown twice.
 */

import { useState } from 'react';
import {
  Card,
  StatBand,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  Badge,
  ScopeBadge,
  DataQualityBadge,
} from '@/components/ui';
import { cn, formatNumber, categoryNames } from '@/lib/utils';
import {
  TrendingDown,
  TrendingUp,
  FileCheck,
  ChevronDown,
  ChevronUp,
  Info,
} from 'lucide-react';
import type { GHGInventoryReport as GHGInventoryReportType } from '@/lib/api';

interface GHGInventoryReportProps {
  report: GHGInventoryReportType;
}

const SCOPE_DOT: Record<1 | 2 | 3, string> = {
  1: 'bg-scope1',
  2: 'bg-scope2',
  3: 'bg-scope3',
};

export function GHGInventoryReport({ report }: GHGInventoryReportProps) {
  const [expandedScopes, setExpandedScopes] = useState<Record<number, boolean>>({
    1: true,
    2: true,
    3: false,
  });
  const [showMethodology, setShowMethodology] = useState(false);

  const toggleScope = (scope: number) => {
    setExpandedScopes(prev => ({ ...prev, [scope]: !prev[scope] }));
  };

  const scopes = [report.scope_1, report.scope_2, report.scope_3];
  const scopePercentages = [
    report.executive_summary.scope_1_percentage,
    report.executive_summary.scope_2_percentage,
    report.executive_summary.scope_3_percentage,
  ];

  const orgMeta: { label: string; value: React.ReactNode }[] = [
    { label: 'Organization', value: report.organization.name },
    ...(report.organization.country
      ? [{ label: 'Country', value: report.organization.country }]
      : []),
    ...(report.organization.industry
      ? [{ label: 'Industry', value: report.organization.industry }]
      : []),
    ...(report.organization.base_year
      ? [{ label: 'Base year', value: report.organization.base_year }]
      : []),
    { label: 'Consolidation', value: report.boundaries.consolidation_approach },
    { label: 'Facilities', value: report.boundaries.included_facilities },
    {
      label: 'Period',
      value: `${new Date(report.boundaries.reporting_period_start).toLocaleDateString()} – ${new Date(report.boundaries.reporting_period_end).toLocaleDateString()}`,
    },
  ];

  const comparison = report.base_year_comparison;

  return (
    <div className="space-y-4">
      {/* Header: what this report is + who it covers */}
      <Card padding="none" className="overflow-hidden">
        <div className="px-5 py-3 flex flex-wrap items-center justify-between gap-3 border-b border-border">
          <div>
            <h2 className="text-lg font-bold text-foreground">{report.report_title}</h2>
            <p className="text-sm text-foreground-muted">
              {report.reporting_period} · Report date{' '}
              {new Date(report.report_date).toLocaleDateString()}
            </p>
          </div>
          <Badge variant="primary">ISO 14064-1</Badge>
        </div>
        <div className="flex flex-wrap divide-x divide-border">
          {orgMeta.map((m) => (
            <div key={m.label} className="px-5 py-2">
              <p className="text-xs font-medium text-foreground-muted">{m.label}</p>
              <p className="text-sm font-semibold text-foreground">{m.value}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* The footprint in one strip */}
      <StatBand
        cells={[
          {
            label: 'Total emissions',
            value: `${formatNumber(report.executive_summary.total_emissions_tonnes, 1)} t CO2e`,
            sub: `${report.executive_summary.total_activities} activities`,
          },
          ...scopes.map((s, i) => ({
            label: (
              <>
                <span
                  className={cn(
                    'w-2 h-2 rounded-full shrink-0',
                    SCOPE_DOT[s.scope as 1 | 2 | 3]
                  )}
                />
                {s.scope_name}
              </>
            ),
            value: (
              <>
                {formatNumber(s.total_co2e_tonnes, 1)} t
                <span className="text-sm font-medium text-foreground-muted ml-1.5">
                  {scopePercentages[i].toFixed(0)}%
                </span>
              </>
            ),
            sub: `${s.activity_count} activities · DQ ${s.avg_data_quality.toFixed(1)}`,
          })),
          {
            label: 'Data quality',
            value: report.executive_summary.data_quality_score.toFixed(2),
            sub: (
              <DataQualityBadge
                score={Math.round(report.executive_summary.data_quality_score) as 1 | 2 | 3 | 4 | 5}
                size="sm"
              />
            ),
          },
        ]}
      />

      {/* Top sources + what the quality score means — one row */}
      <Card padding="none">
        <div className="px-5 py-3 space-y-1 text-sm">
          <p className="text-foreground">
            <span className="font-medium">Top sources:</span>{' '}
            {report.executive_summary.top_emission_sources
              .map((source, i) => `${i + 1}. ${source}`)
              .join(' · ')}
          </p>
          <p className="text-foreground-muted">{report.data_quality_interpretation}</p>
        </div>
      </Card>

      {/* Scope details — the tables carry the content */}
      {scopes.map((scopeData) => (
        <Card key={scopeData.scope} padding="none" className="overflow-hidden">
          <button
            type="button"
            className="w-full px-5 py-3 flex items-center justify-between hover:bg-background-muted/50 transition-colors"
            onClick={() => toggleScope(scopeData.scope)}
          >
            <span className="flex items-center gap-3">
              <ScopeBadge scope={scopeData.scope as 1 | 2 | 3} />
              <span className="font-medium text-foreground">{scopeData.scope_name}</span>
              <span className="text-xs text-foreground-muted">
                {scopeData.activity_count} activities
              </span>
            </span>
            {expandedScopes[scopeData.scope] ? (
              <ChevronUp className="w-4 h-4 text-foreground-muted" />
            ) : (
              <ChevronDown className="w-4 h-4 text-foreground-muted" />
            )}
          </button>
          {expandedScopes[scopeData.scope] && (
            <div className="px-5 pb-4 border-t border-border pt-2">
              {scopeData.sources.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Emission Source</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead className="text-right">Activities</TableHead>
                      <TableHead className="text-right">Quantity</TableHead>
                      <TableHead className="text-right">Emissions (t CO2e)</TableHead>
                      <TableHead className="text-center">Data Quality</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {scopeData.sources.map((source, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-medium">{source.display_name}</TableCell>
                        <TableCell className="text-foreground-muted">
                          {categoryNames[source.category_code] || source.category_code}
                        </TableCell>
                        <TableCell className="text-right">{source.activity_count}</TableCell>
                        <TableCell className="text-right">
                          {formatNumber(source.total_quantity, 1)} {source.unit}
                        </TableCell>
                        <TableCell className="text-right font-semibold">
                          {formatNumber(source.total_co2e_tonnes, 2)}
                        </TableCell>
                        <TableCell className="text-center">
                          <DataQualityBadge
                            score={Math.round(source.avg_data_quality) as 1 | 2 | 3 | 4 | 5}
                            size="sm"
                            showLabel={false}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-sm text-foreground-muted py-2">
                  No {scopeData.scope_name.toLowerCase()} emissions recorded
                </p>
              )}
            </div>
          )}
        </Card>
      ))}

      {/* Methodology — reference text, collapsed by default */}
      <Card padding="none" className="overflow-hidden">
        <button
          type="button"
          className="w-full px-5 py-3 flex items-center justify-between hover:bg-background-muted/50 transition-colors"
          onClick={() => setShowMethodology((v) => !v)}
        >
          <span className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <Info className="w-4 h-4 text-foreground-muted" />
            Methodology
          </span>
          {showMethodology ? (
            <ChevronUp className="w-4 h-4 text-foreground-muted" />
          ) : (
            <ChevronDown className="w-4 h-4 text-foreground-muted" />
          )}
        </button>
        {showMethodology && (
          <div className="px-5 pb-4 border-t border-border pt-3 space-y-3 text-sm">
            <div>
              <h4 className="font-semibold text-foreground mb-0.5">Calculation Approach</h4>
              <p className="text-foreground-muted">{report.methodology.calculation_approach}</p>
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-0.5">Global Warming Potentials</h4>
              <p className="text-foreground-muted">{report.methodology.gwp_values}</p>
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-0.5">Emission Factor Sources</h4>
              <ul className="list-disc list-inside text-foreground-muted">
                {report.methodology.emission_factor_sources.map((source, index) => (
                  <li key={index}>{source}</li>
                ))}
              </ul>
            </div>
            {report.methodology.exclusions.length > 0 && (
              <div>
                <h4 className="font-semibold text-foreground mb-0.5">Exclusions</h4>
                <ul className="list-disc list-inside text-foreground-muted">
                  {report.methodology.exclusions.map((exclusion, index) => (
                    <li key={index}>{exclusion}</li>
                  ))}
                </ul>
              </div>
            )}
            {report.methodology.assumptions.length > 0 && (
              <div>
                <h4 className="font-semibold text-foreground mb-0.5">Key Assumptions</h4>
                <ul className="list-disc list-inside text-foreground-muted">
                  {report.methodology.assumptions.map((assumption, index) => (
                    <li key={index}>{assumption}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Base year — one line */}
      {comparison && (
        <Card padding="none">
          <div className="px-5 py-3 flex flex-wrap items-center gap-x-6 gap-y-1 text-sm">
            <span className="font-medium text-foreground">
              Base year {comparison.base_year}
            </span>
            <span className="text-foreground-muted">
              {formatNumber(comparison.base_year_emissions_tonnes, 1)} t →{' '}
              {formatNumber(comparison.current_emissions_tonnes, 1)} t CO2e
            </span>
            <span
              className={cn(
                'flex items-center gap-1 font-semibold',
                comparison.percentage_change < 0 ? 'text-success' : 'text-error'
              )}
            >
              {comparison.percentage_change < 0 ? (
                <TrendingDown className="w-4 h-4" />
              ) : (
                <TrendingUp className="w-4 h-4" />
              )}
              {comparison.percentage_change > 0 ? '+' : ''}
              {comparison.percentage_change.toFixed(1)}%
            </span>
          </div>
        </Card>
      )}

      {/* Verification — the finish line */}
      <Card padding="none">
        <div className="px-5 py-3 flex flex-wrap items-center gap-3 text-sm">
          <FileCheck className="w-4 h-4 text-foreground-muted" />
          <span className="font-medium text-foreground">Verification</span>
          <Badge
            variant={
              report.verification.status === 'verified'
                ? 'success'
                : report.verification.status === 'audit'
                ? 'warning'
                : 'default'
            }
          >
            {report.verification.status.charAt(0).toUpperCase() +
              report.verification.status.slice(1)}
          </Badge>
          {report.verification.assurance_level && (
            <span className="text-foreground-muted">
              Assurance:{' '}
              <span className="font-medium capitalize">
                {report.verification.assurance_level}
              </span>
            </span>
          )}
          {report.verification.verified_by && (
            <span className="text-foreground-muted">
              by {report.verification.verified_by}
              {report.verification.verified_at &&
                ` on ${new Date(report.verification.verified_at).toLocaleDateString()}`}
            </span>
          )}
        </div>
        {report.verification.verification_statement && (
          <p className="px-5 pb-3 text-sm text-foreground-muted italic">
            &quot;{report.verification.verification_statement}&quot;
          </p>
        )}
      </Card>
    </div>
  );
}
