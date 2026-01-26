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
} from '@/components/ui';
import { cn, formatCO2e, formatNumber, categoryNames } from '@/lib/utils';
import {
  Building2,
  Globe,
  Target,
  TrendingDown,
  TrendingUp,
  FileCheck,
  ChevronDown,
  ChevronUp,
  Info,
  Leaf,
  Factory,
  Zap,
  Truck,
} from 'lucide-react';
import type { GHGInventoryReport as GHGInventoryReportType } from '@/lib/api';

interface GHGInventoryReportProps {
  report: GHGInventoryReportType;
}

export function GHGInventoryReport({ report }: GHGInventoryReportProps) {
  const [expandedScopes, setExpandedScopes] = useState<Record<number, boolean>>({
    1: true,
    2: true,
    3: false,
  });

  const toggleScope = (scope: number) => {
    setExpandedScopes(prev => ({ ...prev, [scope]: !prev[scope] }));
  };

  const getScopeIcon = (scope: number) => {
    switch (scope) {
      case 1:
        return <Factory className="w-5 h-5" />;
      case 2:
        return <Zap className="w-5 h-5" />;
      case 3:
        return <Truck className="w-5 h-5" />;
      default:
        return <Leaf className="w-5 h-5" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Report Header */}
      <Card className="bg-gradient-to-r from-primary/5 to-primary/10 border-primary/20">
        <CardContent className="py-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-bold text-foreground">{report.report_title}</h2>
              <p className="text-foreground-muted mt-1">
                Reporting Period: {report.reporting_period}
              </p>
              <p className="text-sm text-foreground-muted mt-0.5">
                Report Date: {new Date(report.report_date).toLocaleDateString()}
              </p>
            </div>
            <Badge variant="primary">ISO 14064-1</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Organization Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="w-5 h-5 text-foreground-muted" />
            Organization Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div>
              <p className="text-sm font-medium text-foreground-muted">Organization</p>
              <p className="text-foreground font-semibold mt-1">{report.organization.name}</p>
            </div>
            {report.organization.country && (
              <div>
                <p className="text-sm font-medium text-foreground-muted">Country</p>
                <p className="text-foreground font-semibold mt-1">{report.organization.country}</p>
              </div>
            )}
            {report.organization.industry && (
              <div>
                <p className="text-sm font-medium text-foreground-muted">Industry</p>
                <p className="text-foreground font-semibold mt-1">{report.organization.industry}</p>
              </div>
            )}
            {report.organization.base_year && (
              <div>
                <p className="text-sm font-medium text-foreground-muted">Base Year</p>
                <p className="text-foreground font-semibold mt-1">{report.organization.base_year}</p>
              </div>
            )}
          </div>

          <div className="mt-6 pt-6 border-t border-border">
            <h4 className="text-sm font-semibold text-foreground mb-3">Reporting Boundary</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-foreground-muted">Consolidation Approach</p>
                <p className="text-foreground">{report.boundaries.consolidation_approach}</p>
              </div>
              <div>
                <p className="text-sm text-foreground-muted">Included Facilities</p>
                <p className="text-foreground">{report.boundaries.included_facilities}</p>
              </div>
              <div>
                <p className="text-sm text-foreground-muted">Period</p>
                <p className="text-foreground">
                  {new Date(report.boundaries.reporting_period_start).toLocaleDateString()} -{' '}
                  {new Date(report.boundaries.reporting_period_end).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Executive Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5 text-foreground-muted" />
            Executive Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Total Emissions */}
          <div className="text-center mb-8">
            <p className="text-sm font-medium text-foreground-muted uppercase tracking-wide">
              Total GHG Emissions
            </p>
            <p className="text-4xl font-bold text-primary mt-2">
              {formatNumber(report.executive_summary.total_emissions_tonnes, 1)} t CO2e
            </p>
            <p className="text-foreground-muted mt-1">
              {report.executive_summary.total_activities} activities recorded
            </p>
          </div>

          {/* Scope Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-scope1/10 rounded-lg p-4 text-center border border-scope1/20">
              <p className="text-sm font-medium text-scope1">Scope 1 - Direct</p>
              <p className="text-2xl font-bold text-foreground mt-1">
                {formatNumber(report.executive_summary.scope_1_tonnes, 1)} t
              </p>
              <p className="text-sm text-foreground-muted">
                {report.executive_summary.scope_1_percentage.toFixed(1)}%
              </p>
            </div>
            <div className="bg-scope2/10 rounded-lg p-4 text-center border border-scope2/20">
              <p className="text-sm font-medium text-scope2">Scope 2 - Indirect</p>
              <p className="text-2xl font-bold text-foreground mt-1">
                {formatNumber(report.executive_summary.scope_2_tonnes, 1)} t
              </p>
              <p className="text-sm text-foreground-muted">
                {report.executive_summary.scope_2_percentage.toFixed(1)}%
              </p>
            </div>
            <div className="bg-scope3/10 rounded-lg p-4 text-center border border-scope3/20">
              <p className="text-sm font-medium text-scope3">Scope 3 - Value Chain</p>
              <p className="text-2xl font-bold text-foreground mt-1">
                {formatNumber(report.executive_summary.scope_3_tonnes, 1)} t
              </p>
              <p className="text-sm text-foreground-muted">
                {report.executive_summary.scope_3_percentage.toFixed(1)}%
              </p>
            </div>
          </div>

          {/* Top Sources & Data Quality */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-3">Top Emission Sources</h4>
              <ul className="space-y-2">
                {report.executive_summary.top_emission_sources.map((source, index) => (
                  <li key={index} className="flex items-center gap-2 text-sm text-foreground-muted">
                    <span className="w-5 h-5 rounded-full bg-primary/10 text-primary text-xs flex items-center justify-center font-medium">
                      {index + 1}
                    </span>
                    {source}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-3">Data Quality</h4>
              <div className="flex items-center gap-3">
                <DataQualityBadge
                  score={Math.round(report.executive_summary.data_quality_score) as 1 | 2 | 3 | 4 | 5}
                />
                <span className="text-sm text-foreground-muted">
                  Weighted average: {report.executive_summary.data_quality_score.toFixed(2)}
                </span>
              </div>
              <p className="text-sm text-foreground-muted mt-2">
                {report.data_quality_interpretation}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Scope Details */}
      {[report.scope_1, report.scope_2, report.scope_3].map((scopeData) => (
        <Card key={scopeData.scope}>
          <CardHeader
            className="cursor-pointer hover:bg-background-muted/50 transition-colors"
            onClick={() => toggleScope(scopeData.scope)}
          >
            <div className="flex items-center justify-between w-full">
              <CardTitle className="flex items-center gap-3">
                {getScopeIcon(scopeData.scope)}
                <ScopeBadge scope={scopeData.scope as 1 | 2 | 3} />
                <span className="ml-2">{scopeData.scope_name}</span>
              </CardTitle>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="font-bold text-foreground">
                    {formatNumber(scopeData.total_co2e_tonnes, 1)} t CO2e
                  </p>
                  <p className="text-sm text-foreground-muted">
                    {scopeData.percentage_of_total.toFixed(1)}% of total
                  </p>
                </div>
                {expandedScopes[scopeData.scope] ? (
                  <ChevronUp className="w-5 h-5 text-foreground-muted" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-foreground-muted" />
                )}
              </div>
            </div>
          </CardHeader>
          {expandedScopes[scopeData.scope] && (
            <CardContent>
              <div className="flex items-center gap-4 mb-4 text-sm text-foreground-muted">
                <span>{scopeData.activity_count} activities</span>
                <span>|</span>
                <span>
                  Avg. data quality:{' '}
                  <DataQualityBadge
                    score={Math.round(scopeData.avg_data_quality) as 1 | 2 | 3 | 4 | 5}
                    size="sm"
                  />
                </span>
              </div>

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
                <p className="text-center text-foreground-muted py-4">
                  No {scopeData.scope_name.toLowerCase()} emissions recorded
                </p>
              )}
            </CardContent>
          )}
        </Card>
      ))}

      {/* Methodology */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="w-5 h-5 text-foreground-muted" />
            Methodology
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-foreground mb-1">Calculation Approach</h4>
              <p className="text-foreground-muted">{report.methodology.calculation_approach}</p>
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-1">Global Warming Potentials</h4>
              <p className="text-foreground-muted">{report.methodology.gwp_values}</p>
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-1">Emission Factor Sources</h4>
              <ul className="list-disc list-inside text-foreground-muted">
                {report.methodology.emission_factor_sources.map((source, index) => (
                  <li key={index}>{source}</li>
                ))}
              </ul>
            </div>
            {report.methodology.exclusions.length > 0 && (
              <div>
                <h4 className="font-semibold text-foreground mb-1">Exclusions</h4>
                <ul className="list-disc list-inside text-foreground-muted">
                  {report.methodology.exclusions.map((exclusion, index) => (
                    <li key={index}>{exclusion}</li>
                  ))}
                </ul>
              </div>
            )}
            {report.methodology.assumptions.length > 0 && (
              <div>
                <h4 className="font-semibold text-foreground mb-1">Key Assumptions</h4>
                <ul className="list-disc list-inside text-foreground-muted">
                  {report.methodology.assumptions.map((assumption, index) => (
                    <li key={index}>{assumption}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Base Year Comparison */}
      {report.base_year_comparison && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {report.base_year_comparison.percentage_change < 0 ? (
                <TrendingDown className="w-5 h-5 text-success" />
              ) : (
                <TrendingUp className="w-5 h-5 text-error" />
              )}
              Base Year Comparison
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 text-center">
              <div>
                <p className="text-sm text-foreground-muted">Base Year</p>
                <p className="text-xl font-bold text-foreground">
                  {report.base_year_comparison.base_year}
                </p>
              </div>
              <div>
                <p className="text-sm text-foreground-muted">Base Year Emissions</p>
                <p className="text-xl font-bold text-foreground">
                  {formatNumber(report.base_year_comparison.base_year_emissions_tonnes, 1)} t
                </p>
              </div>
              <div>
                <p className="text-sm text-foreground-muted">Current Emissions</p>
                <p className="text-xl font-bold text-foreground">
                  {formatNumber(report.base_year_comparison.current_emissions_tonnes, 1)} t
                </p>
              </div>
              <div>
                <p className="text-sm text-foreground-muted">Change</p>
                <p
                  className={cn(
                    'text-xl font-bold',
                    report.base_year_comparison.percentage_change < 0 ? 'text-success' : 'text-error'
                  )}
                >
                  {report.base_year_comparison.percentage_change > 0 ? '+' : ''}
                  {report.base_year_comparison.percentage_change.toFixed(1)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Verification Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileCheck className="w-5 h-5 text-foreground-muted" />
            Verification Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Badge
              variant={
                report.verification.status === 'verified'
                  ? 'success'
                  : report.verification.status === 'audit'
                  ? 'warning'
                  : 'default'
              }
            >
              {report.verification.status.charAt(0).toUpperCase() + report.verification.status.slice(1)}
            </Badge>
            {report.verification.assurance_level && (
              <span className="text-foreground-muted">
                Assurance Level: <span className="font-medium capitalize">{report.verification.assurance_level}</span>
              </span>
            )}
          </div>
          {report.verification.verified_by && (
            <p className="text-sm text-foreground-muted mt-3">
              Verified by: {report.verification.verified_by}
              {report.verification.verified_at &&
                ` on ${new Date(report.verification.verified_at).toLocaleDateString()}`}
            </p>
          )}
          {report.verification.verification_statement && (
            <p className="text-sm text-foreground-muted mt-2 italic">
              "{report.verification.verification_statement}"
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
