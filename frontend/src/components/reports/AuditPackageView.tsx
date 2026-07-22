'use client';

import { Fragment, useState } from 'react';
import {
  Surface,
  PanelLabel,
  StatCells,
  DataTable,
  CellValue,
  type CanopyColumn,
  type StatCell,
} from '@/components/canopy';
import { Badge, ScopeBadge, DataQualityBadge, Button } from '@/components/ui';
import { formatCO2e, formatNumber, formatDate, formatFactor, categoryNames} from '@/lib/utils';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { AuditPackage } from '@/lib/api';

interface AuditPackageViewProps {
  auditPackage: AuditPackage;
  onDownload?: () => void;
}

/** Quiet key–value row. */
function Kv({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-3.5 py-1.5 text-[12.5px]">
      <span className="min-w-[130px] shrink-0 text-cy-faint">{label}</span>
      <span className="font-semibold text-cy-ink">{children}</span>
    </div>
  );
}

/** Detail line inside an expanded activity row. */
function DetailKv({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-3 text-[12px]">
      <span className="w-36 shrink-0 text-cy-faint">{label}</span>
      <span className="text-cy-ink">{children}</span>
    </div>
  );
}

const thClass =
  'pb-2.5 text-[10.5px] font-bold tracking-[0.07em] uppercase text-cy-faint text-left';
const thRight = `${thClass} text-right`;
const tdClass = 'border-t border-cy-row py-[9px] text-[13px] text-cy-ink';
const tdRight = `${tdClass} text-right tabular-nums text-cy-muted`;

type EmissionFactorRow = AuditPackage['emission_factors'][number];
type ImportBatchRow = AuditPackage['import_batches'][number];

const factorColumns: CanopyColumn<EmissionFactorRow>[] = [
  {
    key: 'name',
    header: 'Factor',
    render: (factor) => <span className="font-semibold">{factor.display_name}</span>,
  },
  {
    key: 'source',
    header: 'Source',
    render: (factor) => (
      <span className="text-cy-muted">
        {factor.source} ({factor.region}, {factor.year})
      </span>
    ),
  },
  {
    key: 'scope',
    header: 'Scope',
    render: (factor) => <ScopeBadge scope={factor.scope as 1 | 2 | 3} size="sm" />,
  },
  {
    key: 'value',
    header: 'Value',
    align: 'right',
    render: (factor) => `${formatFactor(factor.co2e_factor)} ${factor.factor_unit}`,
  },
  {
    key: 'uses',
    header: 'Uses',
    align: 'right',
    render: (factor) => factor.usage_count,
  },
  {
    key: 'total',
    header: 'Total',
    align: 'right',
    render: (factor) => <CellValue>{formatCO2e(factor.total_co2e_kg)}</CellValue>,
  },
];

const importColumns: CanopyColumn<ImportBatchRow>[] = [
  {
    key: 'file',
    header: 'File',
    render: (batch) => <span className="font-semibold">{batch.file_name}</span>,
  },
  {
    key: 'type',
    header: 'Type',
    render: (batch) => <span className="text-[11px] uppercase text-cy-muted">{batch.file_type}</span>,
  },
  {
    key: 'status',
    header: 'Status',
    render: (batch) => (
      <Badge
        variant={
          batch.status === 'completed' ? 'success' : batch.status === 'failed' ? 'error' : 'warning'
        }
        size="sm"
      >
        {batch.status}
      </Badge>
    ),
  },
  { key: 'rows', header: 'Rows', align: 'right', render: (batch) => batch.total_rows },
  { key: 'ok', header: 'OK', align: 'right', render: (batch) => batch.successful_rows },
  { key: 'failed', header: 'Failed', align: 'right', render: (batch) => batch.failed_rows },
  {
    key: 'uploaded',
    header: 'Uploaded',
    align: 'right',
    render: (batch) => formatDate(batch.uploaded_at),
  },
];

export function AuditPackageView({ auditPackage, onDownload }: AuditPackageViewProps) {
  const [expandedActivities, setExpandedActivities] = useState<Set<string>>(new Set());
  const [showAllActivities, setShowAllActivities] = useState(false);

  const toggleActivity = (activityId: string) => {
    setExpandedActivities((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(activityId)) {
        newSet.delete(activityId);
      } else {
        newSet.add(activityId);
      }
      return newSet;
    });
  };

  const displayedActivities = showAllActivities
    ? auditPackage.activities
    : auditPackage.activities.slice(0, 10);

  const handleDownload = () => {
    const jsonStr = JSON.stringify(auditPackage, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `audit-package-${auditPackage.summary.period_name.replace(/\s+/g, '-')}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    onDownload?.();
  };

  const summary = auditPackage.summary;

  const summaryCells: StatCell[] = [
    {
      label: 'Total',
      value: formatNumber(summary.total_emissions_tonnes, 1),
      sub: 't CO₂e',
    },
    { label: 'Scope 1', value: formatNumber(summary.scope_1_emissions_tonnes, 1), scope: 1 },
    { label: 'Scope 2', value: formatNumber(summary.scope_2_emissions_tonnes, 1), scope: 2 },
    { label: 'Scope 3', value: formatNumber(summary.scope_3_emissions_tonnes, 1), scope: 3 },
    {
      label: 'Data quality',
      value: summary.overall_data_quality_score.toFixed(2),
      sub: '/ 5',
    },
  ];

  return (
    <div className="space-y-4">
      {/* Pack summary */}
      <Surface>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <PanelLabel>Audit pack</PanelLabel>
          <div className="flex items-center gap-2">
            <Badge size="sm">v{auditPackage.package_version}</Badge>
            <Button variant="secondary" size="sm" onClick={handleDownload}>
              Download JSON
            </Button>
          </div>
        </div>
        <Kv label="Organization">{summary.organization_name}</Kv>
        <Kv label="Period">
          {summary.period_name} · {formatDate(summary.reporting_period_start)} –{' '}
          {formatDate(summary.reporting_period_end)}
        </Kv>
        <Kv label="Generated">{formatDate(summary.generated_at)}</Kv>
        <div className="mt-3.5">
          <StatCells cells={summaryCells} />
        </div>
        <p className="mt-3 flex items-center gap-2 text-[12px] text-cy-muted">
          <Badge
            variant={
              summary.verification_status === 'verified'
                ? 'success'
                : summary.verification_status === 'audit'
                ? 'warning'
                : 'default'
            }
            size="sm"
          >
            {summary.verification_status}
          </Badge>
          {summary.total_activities} activities · every row traces to its source below
        </p>
      </Surface>

      {/* Activity register (expandable rows) */}
      <Surface>
        <PanelLabel>Activity register · {auditPackage.activities.length}</PanelLabel>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className={`${thClass} w-8`} aria-label="Expand" />
                <th className={thClass}>Description</th>
                <th className={thClass}>Category</th>
                <th className={thClass}>Scope</th>
                <th className={thRight}>Quantity</th>
                <th className={thRight}>Emissions</th>
                <th className={thRight}>Quality</th>
              </tr>
            </thead>
            <tbody>
              {displayedActivities.map((activity) => (
                <Fragment key={activity.activity_id}>
                  <tr
                    className="cursor-pointer hover:bg-cy-row/40"
                    onClick={() => toggleActivity(activity.activity_id)}
                  >
                    <td className={tdClass}>
                      {expandedActivities.has(activity.activity_id) ? (
                        <ChevronUp className="h-3.5 w-3.5 text-cy-faint" />
                      ) : (
                        <ChevronDown className="h-3.5 w-3.5 text-cy-faint" />
                      )}
                    </td>
                    <td className={`${tdClass} font-semibold`}>{activity.description}</td>
                    <td className={`${tdClass} text-cy-muted`}>
                      {activity.category_name ||
                        categoryNames[activity.category_code] ||
                        activity.category_code}
                    </td>
                    <td className={tdClass}>
                      <ScopeBadge scope={activity.scope as 1 | 2 | 3} size="sm" />
                    </td>
                    <td className={tdRight}>
                      {formatNumber(activity.quantity, 2)} {activity.unit}
                    </td>
                    <td className={tdRight}>
                      <CellValue>{formatCO2e(activity.co2e_kg)}</CellValue>
                    </td>
                    <td className={`${tdRight}`}>
                      <DataQualityBadge
                        score={activity.data_quality_score as 1 | 2 | 3 | 4 | 5}
                        size="sm"
                        showLabel={false}
                      />
                    </td>
                  </tr>
                  {expandedActivities.has(activity.activity_id) && (
                    <tr>
                      <td colSpan={7} className="border-t border-cy-row">
                        <div className="my-2 grid grid-cols-1 gap-x-8 gap-y-1.5 rounded-[12px] bg-cy-row/40 p-4 md:grid-cols-2">
                          <div className="space-y-1.5">
                            <DetailKv label="Activity key">
                              <span className="font-mono text-[11px]">{activity.activity_key}</span>
                            </DetailKv>
                            <DetailKv label="Date">{formatDate(activity.activity_date)}</DetailKv>
                            <DetailKv label="Method">{activity.calculation_method}</DetailKv>
                            <DetailKv label="Data source">{activity.data_source}</DetailKv>
                            {activity.import_file_name && (
                              <DetailKv label="Import file">{activity.import_file_name}</DetailKv>
                            )}
                          </div>
                          <div className="space-y-1.5">
                            <DetailKv label="Emission factor">
                              {formatFactor(activity.emission_factor_value)} {activity.emission_factor_unit}
                            </DetailKv>
                            {activity.calculation_formula && (
                              <DetailKv label="Formula">
                                <span className="font-mono text-[11px]">
                                  {activity.calculation_formula}
                                </span>
                              </DetailKv>
                            )}
                            <DetailKv label="Confidence">
                              <Badge
                                variant={
                                  activity.confidence_level === 'high'
                                    ? 'success'
                                    : activity.confidence_level === 'medium'
                                    ? 'warning'
                                    : 'error'
                                }
                                size="sm"
                              >
                                {activity.confidence_level}
                              </Badge>
                            </DetailKv>
                            {activity.wtt_co2e_kg != null && activity.wtt_co2e_kg > 0 && (
                              <DetailKv label="WTT emissions">
                                {formatCO2e(activity.wtt_co2e_kg)}
                              </DetailKv>
                            )}
                          </div>
                          {activity.data_quality_justification && (
                            <p className="text-[12px] text-cy-muted md:col-span-2">
                              {activity.data_quality_justification}
                            </p>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>

        {auditPackage.activities.length > 10 && (
          <button
            type="button"
            onClick={() => setShowAllActivities(!showAllActivities)}
            className="mt-3 cursor-pointer text-[12.5px] font-semibold text-cy-accent"
          >
            {showAllActivities
              ? 'Show fewer'
              : `Show all ${auditPackage.activities.length} activities`}{' '}
            →
          </button>
        )}
      </Surface>

      {/* Emission factors */}
      <Surface>
        <PanelLabel>Emission factors · {auditPackage.emission_factors.length}</PanelLabel>
        <div className="overflow-x-auto">
          <DataTable
            columns={factorColumns}
            rows={auditPackage.emission_factors.slice(0, 15)}
            rowKey={(factor) => factor.factor_id}
          />
        </div>
        {auditPackage.emission_factors.length > 15 && (
          <p className="mt-3 text-[11.5px] text-cy-faint">
            Showing 15 of {auditPackage.emission_factors.length} — the downloaded pack has all of
            them.
          </p>
        )}
      </Surface>

      {/* Import history */}
      {auditPackage.import_batches.length > 0 && (
        <Surface>
          <PanelLabel>Import history · {auditPackage.import_batches.length}</PanelLabel>
          <div className="overflow-x-auto">
            <DataTable
              columns={importColumns}
              rows={auditPackage.import_batches}
              rowKey={(batch) => batch.batch_id}
            />
          </div>
        </Surface>
      )}

      {/* Methodology */}
      <Surface>
        <PanelLabel>Methodology</PanelLabel>
        <Kv label="Overview">{auditPackage.methodology.overview}</Kv>
        <Kv label="GHG Protocol">{auditPackage.methodology.ghg_protocol_alignment}</Kv>
        <Kv label="Calculation">{auditPackage.methodology.calculation_approach}</Kv>
        <Kv label="Validation rules">
          {auditPackage.methodology.data_validation_rules.join(' · ')}
        </Kv>
        <div className="mt-2 space-y-1.5">
          {Object.entries(auditPackage.methodology.confidence_level_criteria).map(
            ([level, criteria]) => (
              <div key={level} className="flex items-start gap-2 text-[12.5px] text-cy-muted">
                <Badge
                  variant={level === 'high' ? 'success' : level === 'medium' ? 'warning' : 'error'}
                  size="sm"
                >
                  {level}
                </Badge>
                <span>{criteria}</span>
              </div>
            )
          )}
        </div>
      </Surface>
    </div>
  );
}
