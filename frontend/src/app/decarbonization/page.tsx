'use client';

/**
 * Decarbonization as a journey with a start, middle, and end:
 * 1 Baseline → 2 Set target → 3 Choose measures → 4 Your plan → Track.
 *
 * Each step is one slim row: its state, the few numbers that matter, one
 * action. Nothing the dashboard already shows is repeated here; progress
 * numbers come from the server (targets/{id}/progress), never recomputed.
 */

import { useState, useEffect, Suspense, Fragment } from 'react';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { AppShell } from '@/components/layout';
import { Button, Card, Badge } from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  Loader2,
  Check,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { SetTargetModal } from '@/components/decarbonization/SetTargetModal';

const FRAMEWORK_LABELS: Record<string, string> = {
  sbti_1_5c: 'SBTi 1.5°C',
  sbti_wb2c: 'SBTi Well-Below 2°C',
  net_zero: 'Net Zero',
  custom: 'Custom',
};

const STEP_TITLES = ['Baseline', 'Set target', 'Choose measures', 'Your plan'];

// API Decimal fields arrive as strings — always coerce before formatting.
const fmtT = (n: number | string) =>
  Number(n).toLocaleString(undefined, { maximumFractionDigits: 1 });

const fmtMoney = (n: number) =>
  n >= 1_000_000
    ? `$${(n / 1_000_000).toFixed(1)}M`
    : n >= 1_000
      ? `$${(n / 1_000).toFixed(0)}K`
      : `$${n.toFixed(0)}`;

function StepRow({
  n,
  title,
  done,
  current,
  action,
  children,
}: {
  n: number;
  title: string;
  done: boolean;
  current: boolean;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        'flex flex-col md:flex-row md:items-center gap-2 md:gap-4 px-4 py-3',
        current && 'bg-primary/5'
      )}
    >
      <div className="flex items-center gap-3 md:w-44 shrink-0">
        <span
          className={cn(
            'flex items-center justify-center w-6 h-6 rounded-full text-xs font-semibold shrink-0',
            done
              ? 'bg-success text-white'
              : current
                ? 'bg-primary text-white'
                : 'bg-background-muted text-foreground-muted'
          )}
        >
          {done ? <Check className="w-3.5 h-3.5" /> : n}
        </span>
        <span
          className={cn(
            'text-sm font-semibold',
            done || current ? 'text-foreground' : 'text-foreground-muted'
          )}
        >
          {title}
        </span>
      </div>
      <div className="flex-1 min-w-0 text-sm text-foreground-muted md:truncate">
        {children}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

function DecarbonizationPageContent() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  const [mounted, setMounted] = useState(false);
  const [selectedPeriodId, setSelectedPeriodId] = useState<string | null>(null);
  const [showTargetModal, setShowTargetModal] = useState(false);

  const { data: periods } = useQuery({
    queryKey: ['periods'],
    queryFn: () => api.getPeriods(),
    enabled: isAuthenticated,
  });

  // Default period: follow the top-bar (global) selection when valid,
  // otherwise the latest non-locked period, or the first
  const globalPeriodId = usePeriodStore((s) => s.selectedPeriodId);
  useEffect(() => {
    if (periods && periods.length > 0 && !selectedPeriodId) {
      const activePeriod =
        periods.find((p) => p.id === globalPeriodId) ||
        periods.find((p) => !p.is_locked) ||
        periods[0];
      // eslint-disable-next-line react-hooks/set-state-in-effect -- pre-existing intentional state sync on mount/deps change; no behavior change
      setSelectedPeriodId(activePeriod.id);
    }
  }, [periods, selectedPeriodId, globalPeriodId]);

  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ['emission-profile', selectedPeriodId],
    queryFn: () => api.getEmissionProfile(selectedPeriodId!),
    enabled: !!selectedPeriodId,
  });

  const { data: recommendations } = useQuery({
    queryKey: ['recommendations', selectedPeriodId],
    queryFn: () => api.getRecommendations(selectedPeriodId!, { limit: 5 }),
    enabled: !!selectedPeriodId,
  });

  const { data: targets } = useQuery({
    queryKey: ['decarbonization-targets'],
    queryFn: () => api.getDecarbonizationTargets(),
    enabled: isAuthenticated,
  });

  const { data: scenarios } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => api.getScenarios(),
    enabled: isAuthenticated,
  });

  // Server-computed progress vs target — the single source of truth
  const activeTargetId = targets?.find((t) => t.is_active)?.id;
  const { data: targetProgress } = useQuery({
    queryKey: ['target-progress', activeTargetId, selectedPeriodId],
    queryFn: () => api.getTargetProgress(activeTargetId!, selectedPeriodId!),
    enabled: !!activeTargetId && !!selectedPeriodId,
  });

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- pre-existing intentional state sync on mount/deps change; no behavior change
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isAuthenticated) {
      router.push('/');
    }
  }, [mounted, isAuthenticated, router]);

  if (!mounted || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  const activeTarget = targets?.find((t) => t.is_active);
  const activeScenario = scenarios?.find((s) => s.is_active);

  // Step states — the journey's spine
  const hasBaseline = !!profile && profile.total_co2e_tonnes > 0;
  const hasTarget = !!activeTarget;
  const hasMeasures = !!activeScenario && (activeScenario.initiatives_count ?? 0) > 0;
  const achievement = activeScenario
    ? Number(activeScenario.target_achievement_percent)
    : 0;
  const planReaches = hasMeasures && achievement >= 100;
  const stepDone = [hasBaseline, hasTarget, hasMeasures, planReaches];
  const firstOpen = stepDone.findIndex((d) => !d);
  const currentStep = firstOpen === -1 ? 5 : firstOpen + 1; // 5 = tracking mode

  const topSources = (profile?.top_sources ?? [])
    .slice(0, 3)
    .map((s) => `${s.display_name} ${Number(s.percentage_of_total).toFixed(0)}%`)
    .join(' · ');

  return (
    <AppShell>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Decarbonization</h1>
          <p className="text-foreground-muted mt-1">
            From baseline to a plan that reaches your target
          </p>
        </div>
        {periods && periods.length > 0 && (
          <select
            value={selectedPeriodId || ''}
            onChange={(e) => setSelectedPeriodId(e.target.value)}
            className="px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm"
          >
            {periods.map((period) => (
              <option key={period.id} value={period.id}>
                {period.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* The spine: where you are between start and finish */}
      <div className="flex items-center mb-6" aria-label="Journey progress">
        {STEP_TITLES.map((title, i) => (
          <Fragment key={title}>
            {i > 0 && (
              <div
                className={cn(
                  'flex-1 h-0.5 mx-2',
                  stepDone[i - 1] ? 'bg-success' : 'bg-border'
                )}
              />
            )}
            <div className="flex items-center gap-2 shrink-0">
              <span
                className={cn(
                  'flex items-center justify-center w-6 h-6 rounded-full text-xs font-semibold',
                  stepDone[i]
                    ? 'bg-success text-white'
                    : currentStep === i + 1
                      ? 'bg-primary text-white ring-4 ring-primary/20'
                      : 'bg-background-muted text-foreground-muted'
                )}
              >
                {stepDone[i] ? <Check className="w-3.5 h-3.5" /> : i + 1}
              </span>
              <span
                className={cn(
                  'text-xs font-medium hidden sm:inline',
                  stepDone[i] || currentStep === i + 1
                    ? 'text-foreground'
                    : 'text-foreground-muted'
                )}
              >
                {title}
              </span>
            </div>
          </Fragment>
        ))}
      </div>

      {/* The steps — one slim row each */}
      <Card padding="none" className="overflow-hidden">
        <div className="divide-y divide-border">
          {/* 1 — Baseline */}
          <StepRow
            n={1}
            title="Baseline"
            done={hasBaseline}
            current={currentStep === 1}
            action={
              !hasBaseline ? (
                <Button size="sm" onClick={() => router.push('/hub')}>
                  Open Data Hub
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              ) : (
                <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard')}>
                  Breakdown
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              )
            }
          >
            {profileLoading ? (
              '…'
            ) : hasBaseline ? (
              <>
                <span className="font-semibold text-foreground">
                  {fmtT(profile!.total_co2e_tonnes)} tCO2e
                </span>{' '}
                in {profile!.period_name} — top: {topSources}
              </>
            ) : (
              'No emissions data for this period yet — bring data in through the Data Hub.'
            )}
          </StepRow>

          {/* 2 — Set target */}
          <StepRow
            n={2}
            title="Set target"
            done={hasTarget}
            current={currentStep === 2}
            action={
              hasBaseline && (
                <Button
                  variant={hasTarget ? 'outline' : 'primary'}
                  size="sm"
                  onClick={() => setShowTargetModal(true)}
                >
                  {hasTarget ? 'Edit' : 'Set target'}
                </Button>
              )
            }
          >
            {hasTarget ? (
              <>
                {FRAMEWORK_LABELS[activeTarget!.framework] || activeTarget!.framework} ·{' '}
                <span className="font-semibold text-foreground">
                  −{Number(activeTarget!.target_reduction_percent).toFixed(1)}% by{' '}
                  {activeTarget!.target_year}
                </span>{' '}
                · {fmtT(Number(activeTarget!.target_emissions_tco2e))} tCO2e (from{' '}
                {fmtT(Number(activeTarget!.base_year_emissions_tco2e))} in{' '}
                {activeTarget!.base_year})
              </>
            ) : hasBaseline ? (
              'Pick a framework — SBTi 1.5°C, Net Zero or custom — and the reduction math is done for you.'
            ) : (
              'Complete your baseline first — the target math starts from it.'
            )}
          </StepRow>

          {/* 3 — Choose measures */}
          <StepRow
            n={3}
            title="Choose measures"
            done={hasMeasures}
            current={currentStep === 3}
            action={
              hasBaseline && (
                <Button
                  variant={currentStep === 3 ? 'primary' : 'outline'}
                  size="sm"
                  onClick={() => router.push('/decarbonization/recommendations')}
                >
                  Choose measures
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              )
            }
          >
            {hasMeasures ? (
              <>
                <span className="font-semibold text-foreground">
                  {activeScenario!.initiatives_count} measures
                </span>{' '}
                selected in &ldquo;{activeScenario!.name}&rdquo;
              </>
            ) : recommendations && recommendations.length > 0 ? (
              <>
                <span className="font-semibold text-foreground">
                  {recommendations.length} recommendations
                </span>{' '}
                matched to your profile — e.g.{' '}
                {recommendations
                  .slice(0, 2)
                  .map((r) => r.initiative_name)
                  .join(', ')}
              </>
            ) : hasBaseline ? (
              'Reduction measures matched to your emission profile.'
            ) : (
              'Measures are matched to your baseline once data is in.'
            )}
          </StepRow>

          {/* 4 — Your plan */}
          <StepRow
            n={4}
            title="Your plan"
            done={planReaches}
            current={currentStep === 4}
            action={
              (hasMeasures || hasTarget) && (
                <Button
                  variant={currentStep === 4 ? 'primary' : 'outline'}
                  size="sm"
                  onClick={() => router.push('/decarbonization/scenarios')}
                >
                  {activeScenario ? 'View plan' : 'Build scenario'}
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              )
            }
          >
            {activeScenario ? (
              <>
                &ldquo;{activeScenario.name}&rdquo; covers{' '}
                <span
                  className={cn(
                    'font-semibold',
                    achievement >= 100 ? 'text-success' : 'text-foreground'
                  )}
                >
                  {achievement.toFixed(0)}% of the target
                </span>{' '}
                · −{fmtT(Number(activeScenario.total_reduction_tco2e))} tCO2e ·{' '}
                {fmtMoney(Number(activeScenario.total_investment))} investment
              </>
            ) : (
              'Bundle your chosen measures into a scenario and see whether it reaches the target.'
            )}
          </StepRow>

          {/* Track — appears once there is a plan to track */}
          {hasTarget && activeScenario && (
            <StepRow
              n={5}
              title="Track"
              done={false}
              current={currentStep === 5}
              action={
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push('/decarbonization/roadmap')}
                >
                  Roadmap
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              }
            >
              {targetProgress ? (
                <span className="flex items-center gap-2 flex-wrap">
                  {targetProgress.on_track ? (
                    <Badge variant="success" className="inline-flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> On track
                    </Badge>
                  ) : (
                    <Badge variant="warning" className="inline-flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" /> Behind trajectory
                    </Badge>
                  )}
                  <span>
                    {targetProgress.checkpoint_year}: actual{' '}
                    {fmtT(Number(targetProgress.actual_emissions_tco2e))} vs plan{' '}
                    {fmtT(Number(targetProgress.planned_emissions_tco2e))} tCO2e
                  </span>
                </span>
              ) : (
                '…'
              )}
            </StepRow>
          )}
        </div>
      </Card>

      {/* Set Target Modal */}
      {showTargetModal && (
        <SetTargetModal
          isOpen={showTargetModal}
          onClose={() => setShowTargetModal(false)}
          existingTarget={activeTarget}
          baselineEmissions={profile?.total_co2e_tonnes}
          baseYear={
            profile
              ? new Date(profile.analysis_date).getFullYear()
              : new Date().getFullYear()
          }
          basePeriodId={selectedPeriodId || undefined}
        />
      )}
    </AppShell>
  );
}

function DecarbonizationLoading() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-primary animate-spin" />
    </div>
  );
}

export default function DecarbonizationPage() {
  return (
    <Suspense fallback={<DecarbonizationLoading />}>
      <DecarbonizationPageContent />
    </Suspense>
  );
}
