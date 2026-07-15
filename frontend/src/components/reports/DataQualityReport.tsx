'use client';

/**
 * PCAF data quality, density template: score band → ONE table (the old bar
 * chart, breakdown table and definitions card were three views of the same
 * five rows) → how to improve as the finish line.
 */

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
  DataQualityBadge,
} from '@/components/ui';
import { formatCO2e } from '@/lib/utils';
import { CheckCircle, AlertCircle } from 'lucide-react';
import type { DataQualitySummary } from '@/lib/api';

interface DataQualityReportProps {
  report: DataQualitySummary;
}

const QUALITY_LABELS: Record<number, { label: string; description: string }> = {
  1: {
    label: 'Verified Data',
    description: 'Audited/verified data from primary sources (e.g., audited energy bills)',
  },
  2: {
    label: 'Primary Data',
    description: 'Non-audited data from primary sources (e.g., utility bills, invoices)',
  },
  3: {
    label: 'Activity Average',
    description: 'Physical activity data with average emission factors',
  },
  4: {
    label: 'Spend-Based',
    description: 'Economic activity-based modeling (e.g., spend-based calculations)',
  },
  5: {
    label: 'Estimated',
    description: 'Estimated data with high uncertainty (e.g., industry averages)',
  },
};

const BAR_COLORS: Record<number, string> = {
  1: 'bg-success',
  2: 'bg-info',
  3: 'bg-warning',
  4: 'bg-secondary',
  5: 'bg-error',
};

export function DataQualityReport({ report }: DataQualityReportProps) {
  return (
    <div className="space-y-4">
      {/* Score band: the number, what it means, how much it covers */}
      <Card padding="none" className="overflow-hidden">
        <div className="flex flex-wrap divide-x divide-border">
          <div className="px-5 py-3 min-w-[180px]">
            <p className="text-xs font-medium text-foreground-muted whitespace-nowrap">
              Weighted score (PCAF)
            </p>
            <p className="text-2xl font-bold text-foreground mt-0.5 tracking-tight">
              {report.weighted_average_score.toFixed(2)}
              <span className="text-sm font-medium text-foreground-muted ml-1.5">
                / 5 · 1 = best
              </span>
            </p>
            <div className="mt-1">
              <DataQualityBadge
                score={Math.round(report.weighted_average_score) as 1 | 2 | 3 | 4 | 5}
                size="sm"
              />
            </div>
          </div>
          <div className="px-5 py-3 flex-1 min-w-[240px]">
            <p className="text-xs font-medium text-foreground-muted">What this means</p>
            <p className="text-sm text-foreground mt-1">{report.score_interpretation}</p>
          </div>
          <div className="px-5 py-3">
            <p className="text-xs font-medium text-foreground-muted">Activities</p>
            <p className="text-2xl font-bold text-foreground mt-0.5 tracking-tight">
              {report.total_activities}
            </p>
          </div>
        </div>
      </Card>

      {/* One table: score, meaning, coverage, emissions share */}
      <Card>
        <CardHeader>
          <CardTitle>Score Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Score</TableHead>
                <TableHead>Meaning</TableHead>
                <TableHead className="text-right">Activities</TableHead>
                <TableHead>Emissions</TableHead>
                <TableHead className="text-right">% of Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {[1, 2, 3, 4, 5].map((score) => {
                const scoreData = report.by_score.find((s) => s.score === score);
                const percentage = scoreData ? scoreData.percentage : 0;
                return (
                  <TableRow key={score}>
                    <TableCell>
                      <DataQualityBadge
                        score={score as 1 | 2 | 3 | 4 | 5}
                        showLabel={false}
                      />
                    </TableCell>
                    <TableCell>
                      <p className="font-medium text-foreground">
                        {QUALITY_LABELS[score].label}
                      </p>
                      <p className="text-xs text-foreground-muted">
                        {QUALITY_LABELS[score].description}
                      </p>
                    </TableCell>
                    <TableCell className="text-right">
                      {scoreData ? scoreData.activity_count : 0}
                    </TableCell>
                    <TableCell className="min-w-[200px]">
                      <div className="flex items-center gap-3">
                        <div className="flex-1 h-2 bg-background-muted rounded overflow-hidden">
                          <div
                            className={`h-full ${BAR_COLORS[score]}`}
                            style={{ width: `${Math.min(percentage, 100)}%` }}
                          />
                        </div>
                        <span className="w-28 text-right text-sm font-semibold text-foreground shrink-0">
                          {scoreData ? formatCO2e(scoreData.total_co2e_kg) : '0 kg CO2e'}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right text-foreground-muted">
                      {percentage.toFixed(1)}%
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Finish line: how to move the score */}
      <Card padding="none">
        <div className="px-5 py-3">
          <p className="text-sm font-semibold text-foreground mb-2">Improve your score</p>
          <ul className="space-y-1.5 text-sm">
            {report.weighted_average_score > 3 && (
              <li className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-warning mt-0.5 shrink-0" />
                <span className="text-foreground-muted">
                  Request primary data (invoices, bills) from suppliers to reduce reliance
                  on estimated values.
                </span>
              </li>
            )}
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-success mt-0.5 shrink-0" />
              <span className="text-foreground-muted">
                Implement data collection for Scope 3 categories to improve coverage and
                accuracy.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-success mt-0.5 shrink-0" />
              <span className="text-foreground-muted">
                Third-party verification of emission data achieves DQ1 status for key
                sources.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-success mt-0.5 shrink-0" />
              <span className="text-foreground-muted">
                Document data collection methods and keep supporting evidence for audit
                trails.
              </span>
            </li>
          </ul>
        </div>
      </Card>
    </div>
  );
}
