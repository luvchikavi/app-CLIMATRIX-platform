'use client';

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
  DataQualityBadge,
} from '@/components/ui';
import { formatNumber, formatCO2e } from '@/lib/utils';
import { BarChart3, Info, CheckCircle, AlertCircle } from 'lucide-react';
import type { DataQualitySummary } from '@/lib/api';

interface DataQualityReportProps {
  report: DataQualitySummary;
}

export function DataQualityReport({ report }: DataQualityReportProps) {
  const getQualityLabel = (score: number): string => {
    switch (score) {
      case 1:
        return 'Verified Data';
      case 2:
        return 'Primary Data';
      case 3:
        return 'Activity Average';
      case 4:
        return 'Spend-Based';
      case 5:
        return 'Estimated';
      default:
        return 'Unknown';
    }
  };

  const getQualityDescription = (score: number): string => {
    switch (score) {
      case 1:
        return 'Audited/verified data from primary sources (e.g., audited energy bills)';
      case 2:
        return 'Non-audited data from primary sources (e.g., utility bills, invoices)';
      case 3:
        return 'Physical activity data with average emission factors';
      case 4:
        return 'Economic activity-based modeling (e.g., spend-based calculations)';
      case 5:
        return 'Estimated data with high uncertainty (e.g., industry averages)';
      default:
        return '';
    }
  };

  // Calculate totals for the bar chart visualization
  const maxCO2e = Math.max(...report.by_score.map((s) => s.total_co2e_kg), 1);

  return (
    <div className="space-y-6">
      {/* Overall Score Card */}
      <Card className="bg-gradient-to-r from-primary/5 to-primary/10 border-primary/20">
        <CardContent className="py-8">
          <div className="text-center">
            <p className="text-sm font-medium text-foreground-muted uppercase tracking-wide">
              Weighted Average Data Quality Score
            </p>
            <div className="mt-4 flex items-center justify-center gap-4">
              <div className="text-5xl font-bold text-primary">
                {report.weighted_average_score.toFixed(2)}
              </div>
              <div className="text-left">
                <DataQualityBadge
                  score={Math.round(report.weighted_average_score) as 1 | 2 | 3 | 4 | 5}
                />
                <p className="text-sm text-foreground-muted mt-1">out of 5 (1 = best)</p>
              </div>
            </div>
            <p className="text-foreground-muted mt-4 max-w-xl mx-auto">
              {report.score_interpretation}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card padding="lg">
          <div className="text-center">
            <p className="text-sm font-medium text-foreground-muted">Total Activities</p>
            <p className="text-3xl font-bold text-foreground mt-2">{report.total_activities}</p>
          </div>
        </Card>
        <Card padding="lg">
          <div className="text-center">
            <p className="text-sm font-medium text-foreground-muted">Reporting Period</p>
            <p className="text-xl font-bold text-foreground mt-2">{report.period_name}</p>
          </div>
        </Card>
        <Card padding="lg">
          <div className="text-center">
            <p className="text-sm font-medium text-foreground-muted">PCAF Standard</p>
            <Badge variant="primary" className="mt-2">
              Compliant
            </Badge>
          </div>
        </Card>
      </div>

      {/* Score Breakdown Visual */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-foreground-muted" />
            Score Distribution by Emissions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((score) => {
              const scoreData = report.by_score.find((s) => s.score === score);
              const percentage = scoreData ? (scoreData.total_co2e_kg / maxCO2e) * 100 : 0;
              const barColors = {
                1: 'bg-success',
                2: 'bg-info',
                3: 'bg-warning',
                4: 'bg-secondary',
                5: 'bg-error',
              };

              return (
                <div key={score} className="flex items-center gap-4">
                  <div className="w-24 flex items-center gap-2">
                    <span className="text-sm font-mono font-semibold">DQ{score}</span>
                    <DataQualityBadge score={score as 1 | 2 | 3 | 4 | 5} size="sm" showLabel={false} />
                  </div>
                  <div className="flex-1 h-8 bg-background-muted rounded-lg overflow-hidden">
                    <div
                      className={`h-full ${barColors[score as keyof typeof barColors]} transition-all duration-500`}
                      style={{ width: `${Math.max(percentage, 1)}%` }}
                    />
                  </div>
                  <div className="w-32 text-right">
                    <span className="text-sm font-semibold text-foreground">
                      {scoreData ? formatCO2e(scoreData.total_co2e_kg) : '0 kg CO2e'}
                    </span>
                  </div>
                  <div className="w-16 text-right">
                    <span className="text-sm text-foreground-muted">
                      {scoreData ? `${scoreData.percentage.toFixed(1)}%` : '0%'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Detailed Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Score Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Score</TableHead>
                <TableHead>Label</TableHead>
                <TableHead className="text-right">Activities</TableHead>
                <TableHead className="text-right">Total Emissions</TableHead>
                <TableHead className="text-right">% of Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {[1, 2, 3, 4, 5].map((score) => {
                const scoreData = report.by_score.find((s) => s.score === score);
                return (
                  <TableRow key={score}>
                    <TableCell>
                      <DataQualityBadge score={score as 1 | 2 | 3 | 4 | 5} showLabel={false} />
                    </TableCell>
                    <TableCell className="font-medium">{getQualityLabel(score)}</TableCell>
                    <TableCell className="text-right">
                      {scoreData ? scoreData.activity_count : 0}
                    </TableCell>
                    <TableCell className="text-right font-semibold">
                      {scoreData ? formatCO2e(scoreData.total_co2e_kg) : '0 kg CO2e'}
                    </TableCell>
                    <TableCell className="text-right text-foreground-muted">
                      {scoreData ? `${scoreData.percentage.toFixed(1)}%` : '0%'}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Quality Score Definitions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="w-5 h-5 text-foreground-muted" />
            PCAF Data Quality Score Definitions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((score) => (
              <div key={score} className="flex items-start gap-3">
                <DataQualityBadge score={score as 1 | 2 | 3 | 4 | 5} size="sm" />
                <div>
                  <p className="font-medium text-foreground">{getQualityLabel(score)}</p>
                  <p className="text-sm text-foreground-muted">{getQualityDescription(score)}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Improvement Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-foreground-muted" />
            Recommendations for Improving Data Quality
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {report.weighted_average_score > 3 && (
              <li className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-warning mt-0.5" />
                <span className="text-foreground-muted">
                  Consider requesting primary data (invoices, bills) from suppliers to reduce
                  reliance on estimated values.
                </span>
              </li>
            )}
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-success mt-0.5" />
              <span className="text-foreground-muted">
                Implement data collection processes for Scope 3 categories to improve coverage and
                accuracy.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-success mt-0.5" />
              <span className="text-foreground-muted">
                Consider third-party verification of emission data to achieve DQ1 status for key
                sources.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-success mt-0.5" />
              <span className="text-foreground-muted">
                Document data collection methods and maintain supporting evidence for audit trails.
              </span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
