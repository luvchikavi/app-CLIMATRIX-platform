'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  Loader2,
  ArrowLeft,
  Target,
  Calendar,
  CheckCircle2,
  Circle,
  TrendingDown,
  Flag,
  Milestone,
} from 'lucide-react';
import Link from 'next/link';

export default function RoadmapPage() {
  const { user } = useAuthStore();

  const { data: targets, isLoading: targetsLoading } = useQuery({
    queryKey: ['decarbonization-targets'],
    queryFn: () => api.getDecarbonizationTargets(),
    enabled: !!user?.organization_id,
  });

  const { data: scenarios, isLoading: scenariosLoading } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => api.getScenarios(),
    enabled: !!user?.organization_id,
  });

  const activeTarget = targets?.find(t => t.is_active);
  const activeScenario = scenarios?.find(s => s.is_active);

  const isLoading = targetsLoading || scenariosLoading;

  // Generate milestone years from base year to target year
  const milestoneYears = activeTarget
    ? Array.from(
        { length: activeTarget.target_year - activeTarget.base_year + 1 },
        (_, i) => activeTarget.base_year + i
      )
    : [];

  const currentYear = new Date().getFullYear();

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/decarbonization">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Decarbonization Roadmap</h1>
            <p className="text-foreground-muted">Your path to net zero</p>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      ) : !activeTarget ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Target className="w-16 h-16 mx-auto mb-4 text-foreground-muted opacity-50" />
              <h3 className="text-lg font-medium text-foreground mb-2">No Active Target</h3>
              <p className="text-foreground-muted mb-4">
                Set a decarbonization target to view your roadmap
              </p>
              <Link href="/decarbonization">
                <Button>Set Target</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Target Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Flag className="w-5 h-5 text-primary" />
                {activeTarget.name}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <p className="text-sm text-foreground-muted">Base Year</p>
                  <p className="text-xl font-bold text-foreground">{activeTarget.base_year}</p>
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Target Year</p>
                  <p className="text-xl font-bold text-foreground">{activeTarget.target_year}</p>
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Base Emissions</p>
                  <p className="text-xl font-bold text-foreground">
                    {Number(activeTarget.base_year_emissions_tco2e || 0).toLocaleString()} tCO2e
                  </p>
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Target Emissions</p>
                  <p className="text-xl font-bold text-success">
                    {Number(activeTarget.target_emissions_tco2e || 0).toLocaleString()} tCO2e
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Timeline */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Milestone className="w-5 h-5 text-foreground-muted" />
                Timeline
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative">
                {/* Timeline line */}
                <div className="absolute left-4 top-8 bottom-8 w-0.5 bg-border" />

                <div className="space-y-8">
                  {milestoneYears.map((year, index) => {
                    const isPast = year < currentYear;
                    const isCurrent = year === currentYear;
                    const isTarget = year === activeTarget.target_year;
                    const isBase = year === activeTarget.base_year;

                    // Calculate expected emissions for this year (linear interpolation)
                    const progress = (year - activeTarget.base_year) / (activeTarget.target_year - activeTarget.base_year);
                    const expectedEmissions = activeTarget.base_year_emissions_tco2e * (1 - progress * (activeTarget.target_reduction_percent / 100));

                    return (
                      <div key={year} className="flex items-start gap-4 relative">
                        <div className={cn(
                          "w-8 h-8 rounded-full flex items-center justify-center z-10",
                          isPast ? 'bg-success' :
                          isCurrent ? 'bg-primary' :
                          isTarget ? 'bg-warning' :
                          'bg-background-muted border-2 border-border'
                        )}>
                          {isPast ? (
                            <CheckCircle2 className="w-4 h-4 text-white" />
                          ) : isCurrent ? (
                            <Circle className="w-4 h-4 text-white fill-white" />
                          ) : isTarget ? (
                            <Flag className="w-4 h-4 text-white" />
                          ) : (
                            <Circle className="w-4 h-4 text-foreground-muted" />
                          )}
                        </div>

                        <div className="flex-1 pb-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <h4 className={cn(
                                "font-semibold",
                                isCurrent ? 'text-primary' :
                                isTarget ? 'text-warning' :
                                'text-foreground'
                              )}>
                                {year}
                                {isBase && <span className="ml-2 text-sm font-normal text-foreground-muted">(Base Year)</span>}
                                {isTarget && <span className="ml-2 text-sm font-normal text-foreground-muted">(Target Year)</span>}
                                {isCurrent && <Badge variant="success" className="ml-2">Current</Badge>}
                              </h4>
                            </div>
                            <div className="text-right">
                              <p className="font-medium text-foreground">
                                {expectedEmissions.toLocaleString(undefined, { maximumFractionDigits: 0 })} tCO2e
                              </p>
                              <p className="text-sm text-foreground-muted">
                                Target: -{(progress * activeTarget.target_reduction_percent).toFixed(0)}%
                              </p>
                            </div>
                          </div>

                          {/* Progress bar for this year */}
                          <div className="mt-2">
                            <div className="w-full h-2 bg-background-muted rounded-full overflow-hidden">
                              <div
                                className={cn(
                                  "h-full rounded-full transition-all",
                                  isPast || isCurrent ? 'bg-success' : 'bg-border'
                                )}
                                style={{ width: `${(1 - progress) * 100}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Active Scenario Initiatives */}
          {activeScenario && activeScenario.initiatives && activeScenario.initiatives.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <TrendingDown className="w-5 h-5 text-success" />
                    Planned Initiatives
                  </div>
                  <Badge variant="secondary">{activeScenario.name}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {activeScenario.initiatives.map((init, index) => (
                    <div
                      key={init.id || index}
                      className="flex items-center justify-between p-4 rounded-lg border border-border"
                    >
                      <div>
                        <h4 className="font-medium text-foreground">{init.initiative?.name || 'Initiative'}</h4>
                        <p className="text-sm text-foreground-muted">
                          Year {init.planned_start_year || 'TBD'} - {init.planned_end_year || 'TBD'}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-success">
                          -{Number(init.expected_reduction_tco2e || 0).toLocaleString()} tCO2e
                        </p>
                        <Badge variant={init.status === 'completed' ? 'success' : init.status === 'in_progress' ? 'warning' : 'secondary'}>
                          {init.status || 'planned'}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
