'use client';

import { useState } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  Badge,
  ScopeBadge,
  DataQualityBadge,
  Button,
} from '@/components/ui';
import { formatCO2e, formatNumber, formatDate, categoryNames } from '@/lib/utils';
import {
  Download,
  FileText,
  Database,
  Upload,
  ChevronDown,
  ChevronUp,
  BookOpen,
} from 'lucide-react';
import type { AuditPackage } from '@/lib/api';

interface AuditPackageViewProps {
  auditPackage: AuditPackage;
  onDownload?: () => void;
}

export function AuditPackageView({ auditPackage, onDownload }: AuditPackageViewProps) {
  const [expandedActivities, setExpandedActivities] = useState<Set<string>>(new Set());
  const [showAllActivities, setShowAllActivities] = useState(false);
  const [showMethodology, setShowMethodology] = useState(false);

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

  return (
    <div className="space-y-4">
      {/* Header + summary in one card: what, when, the numbers, the action */}
      <Card padding="none" className="overflow-hidden">
        <div className="px-5 py-3 flex flex-wrap items-center justify-between gap-3 border-b border-border">
          <div>
            <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
              Audit Package
              <Badge variant="secondary">v{auditPackage.package_version}</Badge>
            </h2>
            <p className="text-sm text-foreground-muted">
              {auditPackage.summary.organization_name} · {auditPackage.summary.period_name} (
              {formatDate(auditPackage.summary.reporting_period_start)} –{' '}
              {formatDate(auditPackage.summary.reporting_period_end)}) · Generated{' '}
              {formatDate(auditPackage.summary.generated_at)}
            </p>
          </div>
          <Button variant="primary" leftIcon={<Download className="w-4 h-4" />} onClick={handleDownload}>
            Download JSON
          </Button>
        </div>
        <div className="flex flex-wrap divide-x divide-border">
          <div className="px-5 py-3 min-w-[160px]">
            <p className="text-xs font-medium text-foreground-muted">Total emissions</p>
            <p className="text-xl font-bold text-foreground mt-0.5 tracking-tight">
              {formatNumber(auditPackage.summary.total_emissions_tonnes, 2)} t CO2e
            </p>
            <p className="text-xs text-foreground-muted mt-0.5">
              {auditPackage.summary.total_activities} activities
            </p>
          </div>
          {(
            [
              [1, auditPackage.summary.scope_1_emissions_tonnes, 'bg-scope1'],
              [2, auditPackage.summary.scope_2_emissions_tonnes, 'bg-scope2'],
              [3, auditPackage.summary.scope_3_emissions_tonnes, 'bg-scope3'],
            ] as const
          ).map(([scope, tonnes, dot]) => (
            <div key={scope} className="px-5 py-3 min-w-[120px]">
              <p className="flex items-center gap-1.5 text-xs font-medium text-foreground-muted">
                <span className={`w-2 h-2 rounded-full shrink-0 ${dot}`} />
                Scope {scope}
              </p>
              <p className="text-xl font-bold text-foreground mt-0.5 tracking-tight">
                {formatNumber(tonnes, 2)} t
              </p>
            </div>
          ))}
          <div className="px-5 py-3 min-w-[120px]">
            <p className="text-xs font-medium text-foreground-muted">Data quality</p>
            <p className="text-xl font-bold text-foreground mt-0.5 tracking-tight">
              {auditPackage.summary.overall_data_quality_score.toFixed(2)}
            </p>
          </div>
          <div className="px-5 py-3 min-w-[130px]">
            <p className="text-xs font-medium text-foreground-muted">Verification</p>
            <Badge
              variant={
                auditPackage.summary.verification_status === 'verified'
                  ? 'success'
                  : auditPackage.summary.verification_status === 'audit'
                  ? 'warning'
                  : 'default'
              }
              className="mt-1"
            >
              {auditPackage.summary.verification_status}
            </Badge>
          </div>
        </div>
      </Card>

      {/* Activities Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-foreground-muted" />
              Activities ({auditPackage.activities.length})
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10"></TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Scope</TableHead>
                <TableHead className="text-right">Quantity</TableHead>
                <TableHead className="text-right">Emissions</TableHead>
                <TableHead className="text-center">DQ</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {displayedActivities.map((activity) => (
                <>
                  <TableRow
                    key={activity.activity_id}
                    className="cursor-pointer hover:bg-background-muted/50"
                    onClick={() => toggleActivity(activity.activity_id)}
                  >
                    <TableCell>
                      {expandedActivities.has(activity.activity_id) ? (
                        <ChevronUp className="w-4 h-4 text-foreground-muted" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-foreground-muted" />
                      )}
                    </TableCell>
                    <TableCell className="font-medium">{activity.description}</TableCell>
                    <TableCell className="text-foreground-muted">
                      {activity.category_name || categoryNames[activity.category_code] || activity.category_code}
                    </TableCell>
                    <TableCell>
                      <ScopeBadge scope={activity.scope as 1 | 2 | 3} size="sm" />
                    </TableCell>
                    <TableCell className="text-right">
                      {formatNumber(activity.quantity, 2)} {activity.unit}
                    </TableCell>
                    <TableCell className="text-right font-semibold">
                      {formatCO2e(activity.co2e_kg)}
                    </TableCell>
                    <TableCell className="text-center">
                      <DataQualityBadge
                        score={activity.data_quality_score as 1 | 2 | 3 | 4 | 5}
                        size="sm"
                        showLabel={false}
                      />
                    </TableCell>
                  </TableRow>
                  {expandedActivities.has(activity.activity_id) && (
                    <TableRow key={`${activity.activity_id}-details`}>
                      <TableCell colSpan={7} className="bg-background-muted/30 p-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="font-semibold text-foreground mb-2">Activity Details</p>
                            <dl className="space-y-1">
                              <div className="flex">
                                <dt className="w-40 text-foreground-muted">Activity Key:</dt>
                                <dd className="font-mono text-xs">{activity.activity_key}</dd>
                              </div>
                              <div className="flex">
                                <dt className="w-40 text-foreground-muted">Activity Date:</dt>
                                <dd>{formatDate(activity.activity_date)}</dd>
                              </div>
                              <div className="flex">
                                <dt className="w-40 text-foreground-muted">Calculation Method:</dt>
                                <dd>{activity.calculation_method}</dd>
                              </div>
                              <div className="flex">
                                <dt className="w-40 text-foreground-muted">Data Source:</dt>
                                <dd>{activity.data_source}</dd>
                              </div>
                              {activity.import_file_name && (
                                <div className="flex">
                                  <dt className="w-40 text-foreground-muted">Import File:</dt>
                                  <dd>{activity.import_file_name}</dd>
                                </div>
                              )}
                            </dl>
                          </div>
                          <div>
                            <p className="font-semibold text-foreground mb-2">Emission Calculation</p>
                            <dl className="space-y-1">
                              <div className="flex">
                                <dt className="w-40 text-foreground-muted">Emission Factor:</dt>
                                <dd>
                                  {activity.emission_factor_value} {activity.emission_factor_unit}
                                </dd>
                              </div>
                              {activity.calculation_formula && (
                                <div className="flex">
                                  <dt className="w-40 text-foreground-muted">Formula:</dt>
                                  <dd className="font-mono text-xs">{activity.calculation_formula}</dd>
                                </div>
                              )}
                              <div className="flex">
                                <dt className="w-40 text-foreground-muted">Confidence:</dt>
                                <dd>
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
                                </dd>
                              </div>
                              {activity.wtt_co2e_kg != null && activity.wtt_co2e_kg > 0 && (
                                <div className="flex">
                                  <dt className="w-40 text-foreground-muted">WTT Emissions:</dt>
                                  <dd>{formatCO2e(activity.wtt_co2e_kg)}</dd>
                                </div>
                              )}
                            </dl>
                          </div>
                          {activity.data_quality_justification && (
                            <div className="col-span-2">
                              <p className="font-semibold text-foreground mb-1">Data Quality Justification</p>
                              <p className="text-foreground-muted">{activity.data_quality_justification}</p>
                            </div>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </>
              ))}
            </TableBody>
          </Table>

          {auditPackage.activities.length > 10 && (
            <div className="mt-4 text-center">
              <Button variant="outline" onClick={() => setShowAllActivities(!showAllActivities)}>
                {showAllActivities
                  ? 'Show Less'
                  : `Show All ${auditPackage.activities.length} Activities`}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Emission Factors Used */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5 text-foreground-muted" />
            Emission Factors Used ({auditPackage.emission_factors.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Factor Name</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Scope</TableHead>
                <TableHead className="text-right">Factor Value</TableHead>
                <TableHead className="text-right">Usage Count</TableHead>
                <TableHead className="text-right">Total CO2e</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {auditPackage.emission_factors.slice(0, 15).map((factor) => (
                <TableRow key={factor.factor_id}>
                  <TableCell className="font-medium">{factor.display_name}</TableCell>
                  <TableCell className="text-foreground-muted">
                    {factor.source} ({factor.region}, {factor.year})
                  </TableCell>
                  <TableCell>
                    <ScopeBadge scope={factor.scope as 1 | 2 | 3} size="sm" />
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {factor.co2e_factor.toFixed(4)} {factor.factor_unit}
                  </TableCell>
                  <TableCell className="text-right">{factor.usage_count}</TableCell>
                  <TableCell className="text-right font-semibold">
                    {formatCO2e(factor.total_co2e_kg)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {auditPackage.emission_factors.length > 15 && (
            <p className="text-sm text-foreground-muted text-center mt-4">
              Showing 15 of {auditPackage.emission_factors.length} emission factors. Download the
              full package for complete data.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Import History */}
      {auditPackage.import_batches.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="w-5 h-5 text-foreground-muted" />
              Import History ({auditPackage.import_batches.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>File Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Total Rows</TableHead>
                  <TableHead className="text-right">Successful</TableHead>
                  <TableHead className="text-right">Failed</TableHead>
                  <TableHead>Uploaded</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {auditPackage.import_batches.map((batch) => (
                  <TableRow key={batch.batch_id}>
                    <TableCell className="font-medium">{batch.file_name}</TableCell>
                    <TableCell className="text-foreground-muted uppercase text-xs">
                      {batch.file_type}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          batch.status === 'completed'
                            ? 'success'
                            : batch.status === 'failed'
                            ? 'error'
                            : 'warning'
                        }
                        size="sm"
                      >
                        {batch.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">{batch.total_rows}</TableCell>
                    <TableCell className="text-right text-success">{batch.successful_rows}</TableCell>
                    <TableCell className="text-right text-error">{batch.failed_rows}</TableCell>
                    <TableCell className="text-foreground-muted">{formatDate(batch.uploaded_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Methodology — reference text, collapsed by default */}
      <Card padding="none" className="overflow-hidden">
        <button
          type="button"
          className="w-full px-5 py-3 flex items-center justify-between hover:bg-background-muted/50 transition-colors"
          onClick={() => setShowMethodology((v) => !v)}
        >
          <span className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <BookOpen className="w-4 h-4 text-foreground-muted" />
            Methodology Documentation
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
              <h4 className="font-semibold text-foreground mb-0.5">Overview</h4>
              <p className="text-foreground-muted">{auditPackage.methodology.overview}</p>
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-0.5">GHG Protocol Alignment</h4>
              <p className="text-foreground-muted">{auditPackage.methodology.ghg_protocol_alignment}</p>
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-0.5">Calculation Approach</h4>
              <p className="text-foreground-muted">{auditPackage.methodology.calculation_approach}</p>
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-0.5">Data Validation Rules</h4>
              <ul className="list-disc list-inside text-foreground-muted">
                {auditPackage.methodology.data_validation_rules.map((rule, index) => (
                  <li key={index}>{rule}</li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-0.5">Confidence Level Criteria</h4>
              <div className="space-y-1.5">
                {Object.entries(auditPackage.methodology.confidence_level_criteria).map(([level, criteria]) => (
                  <div key={level} className="flex items-start gap-2">
                    <Badge
                      variant={level === 'high' ? 'success' : level === 'medium' ? 'warning' : 'error'}
                      size="sm"
                    >
                      {level}
                    </Badge>
                    <span className="text-foreground-muted">{criteria}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
