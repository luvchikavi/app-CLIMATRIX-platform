'use client';

import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import { AppShell } from '@/components/layout';
import { CanopyButton, PageHead, PanelLabel, StatCells, Surface } from '@/components/canopy';
import { Badge, EmptyState } from '@/components/ui';
import { cn, formatMoney } from '@/lib/utils';
import { Loader2, Target, CheckCircle2, Circle, Flag } from 'lucide-react';

export default function RoadmapPage() {
  const { user } = useAuthStore();
  const router = useRouter();

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
    <AppShell>
      <CanopyButton href="/decarbonization" variant="quiet" className="mb-2 inline-block">
        ← Back to plan
      </CanopyButton>
      <PageHead title="Decarbonization roadmap" subtitle="Your path to net zero" />

      {isLoading ? (
        <div className="flex items-center justify-center py-12" role="status" aria-live="polite">
          <Loader2 className="w-6 h-6 text-cy-accent animate-spin" aria-hidden="true" />
        </div>
      ) : !activeTarget ? (
        <Surface>
          <EmptyState
            icon={<Target className="w-8 h-8" strokeWidth={1.5} />}
            title="No active target"
            description="Set a decarbonization target to view your roadmap."
            action={{ label: 'Set target', onClick: () => router.push('/decarbonization'), icon: <></> }}
          />
        </Surface>
      ) : (
        <div className="grid gap-4">
          {/* Target summary */}
          <Surface>
            <PanelLabel>Active target</PanelLabel>
            <h3 className="text-[16px] font-[650] tracking-[-0.01em] text-cy-ink mb-4">
              {activeTarget.name}
            </h3>
            <StatCells
              cells={[
                { label: 'Base year', value: String(activeTarget.base_year) },
                { label: 'Target year', value: String(activeTarget.target_year) },
                {
                  label: 'Base emissions',
                  value: Number(activeTarget.base_year_emissions_tco2e || 0).toLocaleString(),
                  sub: 't CO₂e',
                },
                {
                  label: 'Target emissions',
                  value: Number(activeTarget.target_emissions_tco2e || 0).toLocaleString(),
                  sub: 't CO₂e',
                },
              ]}
            />
          </Surface>

          {/* Timeline */}
          <Surface>
            <PanelLabel>Timeline</PanelLabel>
            <div className="relative">
              {/* Timeline line — a quiet row-tint spine, no border */}
              <div className="absolute left-4 top-8 bottom-8 w-0.5 bg-cy-row" aria-hidden="true" />

              <div className="space-y-7">
                {milestoneYears.map((year) => {
                  const isPast = year < currentYear;
                  const isCurrent = year === currentYear;
                  const isTarget = year === activeTarget.target_year;
                  const isBase = year === activeTarget.base_year;

                  // Calculate expected emissions for this year (linear interpolation).
                  // base_year_emissions_tco2e / target_reduction_percent arrive as strings
                  // (Decimal serialized) — coerce with Number() or the math yields NaN.
                  const baseEmissions = Number(activeTarget.base_year_emissions_tco2e || 0);
                  const reductionPct = Number(activeTarget.target_reduction_percent || 0);
                  const progress = (year - activeTarget.base_year) / (activeTarget.target_year - activeTarget.base_year);
                  const expectedEmissions = baseEmissions * (1 - progress * (reductionPct / 100));

                  return (
                    <div key={year} className="flex items-start gap-4 relative">
                      <div
                        className={cn(
                          'w-8 h-8 rounded-full flex items-center justify-center z-10',
                          isPast || isCurrent
                            ? 'bg-cy-accent text-white'
                            : isTarget
                              ? 'bg-cy-warn-soft text-cy-warn'
                              : 'bg-cy-row text-cy-faint'
                        )}
                      >
                        {isPast ? (
                          <CheckCircle2 className="w-4 h-4" />
                        ) : isCurrent ? (
                          <Circle className="w-4 h-4 fill-current" />
                        ) : isTarget ? (
                          <Flag className="w-4 h-4" />
                        ) : (
                          <Circle className="w-4 h-4" />
                        )}
                      </div>

                      <div className="flex-1 pb-3">
                        <div className="flex items-center justify-between gap-4">
                          <h4
                            className={cn(
                              'text-[13.5px] font-semibold tabular-nums',
                              isCurrent ? 'text-cy-accent' : isTarget ? 'text-cy-warn' : 'text-cy-ink'
                            )}
                          >
                            {year}
                            {isBase && (
                              <span className="ml-2 text-[11.5px] font-normal text-cy-muted">Base year</span>
                            )}
                            {isTarget && (
                              <span className="ml-2 text-[11.5px] font-normal text-cy-muted">Target year</span>
                            )}
                            {isCurrent && (
                              <Badge variant="success" size="sm" className="ml-2">
                                Current
                              </Badge>
                            )}
                          </h4>
                          <div className="text-right">
                            <p className="text-[13.5px] font-semibold tabular-nums text-cy-ink">
                              {expectedEmissions.toLocaleString(undefined, { maximumFractionDigits: 0 })} t CO₂e
                            </p>
                            <p className="text-[11.5px] tabular-nums text-cy-muted">
                              Target: −{(progress * Number(activeTarget.target_reduction_percent)).toFixed(0)}%
                            </p>
                          </div>
                        </div>

                        {/* Progress bar for this year */}
                        <div className="mt-2">
                          <div className="w-full h-2 bg-cy-row rounded-full overflow-hidden">
                            <div
                              className={cn(
                                'h-full rounded-full transition-all',
                                isPast || isCurrent ? 'bg-cy-accent' : 'bg-cy-warn-soft'
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
          </Surface>

          {/* Active scenario summary */}
          {activeScenario && (
            <Surface>
              <div className="flex items-center justify-between mb-3.5">
                <PanelLabel className="mb-0">Active scenario</PanelLabel>
                <Badge variant="primary">{activeScenario.name}</Badge>
              </div>
              <StatCells
                cells={[
                  {
                    label: 'Total initiatives',
                    value: String(activeScenario.initiatives_count || 0),
                  },
                  {
                    label: 'Expected reduction',
                    value: `−${Number(activeScenario.total_reduction_tco2e || 0).toLocaleString()}`,
                    sub: 't CO₂e',
                  },
                  {
                    label: 'Total investment',
                    value: formatMoney(activeScenario.total_investment || 0),
                  },
                ]}
              />
              {activeScenario.description && (
                <p className="text-[13px] text-cy-muted mt-4">{activeScenario.description}</p>
              )}
            </Surface>
          )}
        </div>
      )}
    </AppShell>
  );
}
