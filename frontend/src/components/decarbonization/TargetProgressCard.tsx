'use client';

import { DecarbonizationTarget } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  Target,
  TrendingDown,
  CheckCircle2,
  AlertTriangle,
  Calendar,
  Plus,
} from 'lucide-react';

interface TargetProgressCardProps {
  target?: DecarbonizationTarget;
  currentEmissions?: number;
  onSetTarget?: () => void;
}

const frameworkLabels: Record<string, string> = {
  sbti_1_5c: 'SBTi 1.5°C',
  sbti_wb2c: 'SBTi Well-Below 2°C',
  net_zero: 'Net Zero',
  custom: 'Custom',
};

export function TargetProgressCard({
  target,
  currentEmissions,
  onSetTarget,
}: TargetProgressCardProps) {
  if (!target) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5 text-foreground-muted" />
            Decarbonization Target
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6">
            <div className="w-16 h-16 rounded-full bg-background-muted flex items-center justify-center mx-auto mb-4">
              <Target className="w-8 h-8 text-foreground-muted" />
            </div>
            <p className="text-foreground-muted mb-4">
              Set a decarbonization target to track your progress
            </p>
            <Button onClick={onSetTarget}>
              <Plus className="w-4 h-4 mr-2" />
              Set Target
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Calculate progress
  const requiredReduction = target.base_year_emissions_tco2e - target.target_emissions_tco2e;
  const actualReduction = currentEmissions !== undefined
    ? target.base_year_emissions_tco2e - currentEmissions
    : 0;
  const progressPercent = requiredReduction > 0
    ? Math.min((actualReduction / requiredReduction) * 100, 100)
    : 0;

  // Calculate trajectory
  const yearsTotal = target.target_year - target.base_year;
  const yearsElapsed = new Date().getFullYear() - target.base_year;
  const expectedProgressPercent = yearsTotal > 0 ? (yearsElapsed / yearsTotal) * 100 : 0;

  const onTrack = progressPercent >= expectedProgressPercent * 0.9; // Within 10% of expected

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-foreground-muted" />
            Target Progress
          </div>
          <Badge variant={target.is_sbti_validated ? 'success' : 'secondary'}>
            {frameworkLabels[target.framework] || target.framework}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Target Name */}
          <div>
            <h4 className="font-medium text-foreground">{target.name}</h4>
            <div className="flex items-center gap-2 text-sm text-foreground-muted mt-1">
              <Calendar className="w-4 h-4" />
              <span>{target.base_year} → {target.target_year}</span>
            </div>
          </div>

          {/* Progress Bar */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-foreground-muted">Progress to Target</span>
              <span className="font-medium text-foreground">{progressPercent.toFixed(0)}%</span>
            </div>
            <div className="relative w-full h-3 bg-background-muted rounded-full overflow-hidden">
              {/* Expected progress marker */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-foreground-muted z-10"
                style={{ left: `${expectedProgressPercent}%` }}
              />
              {/* Actual progress */}
              <div
                className={cn(
                  "h-full rounded-full transition-all",
                  onTrack ? 'bg-success' : 'bg-warning'
                )}
                style={{ width: `${Math.max(progressPercent, 0)}%` }}
              />
            </div>
            <div className="flex items-center justify-between mt-2 text-xs text-foreground-muted">
              <span>0%</span>
              <span className="text-center">
                {onTrack ? (
                  <span className="flex items-center gap-1 text-success">
                    <CheckCircle2 className="w-3 h-3" />
                    On Track
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-warning">
                    <AlertTriangle className="w-3 h-3" />
                    Behind Schedule
                  </span>
                )}
              </span>
              <span>100%</span>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
            <div>
              <p className="text-sm text-foreground-muted">Current</p>
              <p className="text-lg font-bold text-foreground">
                {currentEmissions?.toLocaleString() || '—'} tCO2e
              </p>
            </div>
            <div>
              <p className="text-sm text-foreground-muted">Target ({target.target_year})</p>
              <p className="text-lg font-bold text-foreground">
                {Number(target.target_emissions_tco2e || 0).toLocaleString()} tCO2e
              </p>
            </div>
          </div>

          {/* Reduction Goal */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-success/10">
            <div className="flex items-center gap-2">
              <TrendingDown className="w-5 h-5 text-success" />
              <span className="text-sm font-medium text-success">Reduction Goal</span>
            </div>
            <span className="font-bold text-success">-{Number(target.target_reduction_percent || 0).toFixed(1)}%</span>
          </div>

          {/* Scope Coverage */}
          <div className="flex flex-wrap gap-2">
            {target.includes_scope1 && <Badge variant="secondary">Scope 1</Badge>}
            {target.includes_scope2 && <Badge variant="secondary">Scope 2</Badge>}
            {target.includes_scope3 && <Badge variant="secondary">Scope 3</Badge>}
          </div>

          {/* Edit Button */}
          <Button variant="outline" className="w-full" onClick={onSetTarget}>
            Edit Target
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
