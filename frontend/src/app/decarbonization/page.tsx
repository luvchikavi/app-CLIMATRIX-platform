'use client';

/**
 * Plan (batch 2.4) — the locked template page: five steps from baseline to a
 * tracked plan, as soft rows inside ONE surface. The open step sits on the
 * accent-soft pill; measures show what's known about them. Progress numbers
 * come from the server (targets/{id}/progress), never recomputed.
 */

import { useState } from 'react';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { AppShell } from '@/components/layout';
import {
  CanopyButton,
  PageHead,
  StepDoneText,
  StepLockedText,
  StepRow,
  StepValue,
  Surface,
} from '@/components/canopy';
import { num, formatMoney as fmtMoney } from '@/lib/utils';
import { Loader2 } from 'lucide-react';
import { SetTargetModal } from '@/components/decarbonization/SetTargetModal';

const FRAMEWORK_LABELS: Record<string, string> = {
  sbti_1_5c: 'SBTi 1.5°C',
  sbti_wb2c: 'SBTi Well-Below 2°C',
  net_zero: 'Net Zero',
  custom: 'Custom',
};

// API Decimal fields arrive as strings — always coerce before formatting.
const fmtT = (n: number | string) =>
  Number(n).toLocaleString(undefined, { maximumFractionDigits: 1 });

export default function DecarbonizationPage() {
  const { isAuthenticated } = useAuthStore();
  const globalPeriodId = usePeriodStore((s) => s.selectedPeriodId);
  const [showTargetModal, setShowTargetModal] = useState(false);

  const { data: periods } = useQuery({
    queryKey: ['periods'],
    queryFn: () => api.getPeriods(),
    enabled: isAuthenticated,
  });

  // Follow the top-bar (global) period when valid; otherwise the latest
  // non-locked period, or the first.
  const selectedPeriodId =
    periods?.find((p) => p.id === globalPeriodId)?.id ??
    periods?.find((p) => !p.is_locked)?.id ??
    periods?.[0]?.id;

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

  const activeTarget = targets?.find((t) => t.is_active);
  const activeScenario = scenarios?.find((s) => s.is_active);

  // Step states — the journey's spine
  const hasBaseline = !!profile && num(profile.total_co2e_tonnes) > 0;
  const hasTarget = !!activeTarget;
  const hasMeasures = !!activeScenario && (activeScenario.initiatives_count ?? 0) > 0;
  const achievement = activeScenario ? Number(activeScenario.target_achievement_percent) : 0;
  const planReaches = hasMeasures && achievement >= 100;
  const stepDone = [hasBaseline, hasTarget, hasMeasures, planReaches];
  const firstOpen = stepDone.findIndex((d) => !d);
  const currentStep = firstOpen === -1 ? 5 : firstOpen + 1; // 5 = tracking mode

  const state = (n: number, done: boolean, locked: boolean) =>
    done ? ('done' as const) : locked ? ('locked' as const) : currentStep === n ? ('now' as const) : ('todo' as const);

  const topSources = (profile?.top_sources ?? [])
    .slice(0, 3)
    .map((s) => `${s.display_name} ${Number(s.percentage_of_total).toFixed(0)}%`)
    .join(' · ');

  if (profileLoading && !profile) {
    return (
      <AppShell>
        <div className="flex items-center justify-center py-20" role="status" aria-live="polite">
          <Loader2 className="h-6 w-6 animate-spin text-cy-accent" aria-hidden="true" />
          <span className="ml-3 text-[13px] text-cy-muted">Loading your plan…</span>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHead
        title={`Your path to ${activeTarget?.target_year ?? 2030}`}
        subtitle={
          currentStep === 5
            ? 'Your plan reaches the target — now it tracks itself, period by period.'
            : `Five steps from baseline to a tracked plan. You're on step ${currentStep}.`
        }
      />

      <Surface padding="tight">
        {/* 1 — Baseline */}
        <StepRow
          num={1}
          title="Baseline"
          state={state(1, hasBaseline, false)}
          description={
            hasBaseline ? (
              <>
                {profile!.period_name} · <StepValue>{fmtT(profile!.total_co2e_tonnes)} t CO₂e</StepValue>
                {topSources && <> — top: {topSources}</>}
              </>
            ) : (
              'No emissions data for this period yet — bring data in through the Data hub.'
            )
          }
          action={
            hasBaseline ? (
              <StepDoneText />
            ) : (
              <CanopyButton href="/hub" className="px-3.5 py-2">
                Open Data hub
              </CanopyButton>
            )
          }
        />

        {/* 2 — Set target */}
        <StepRow
          num={2}
          title="Set your target"
          state={state(2, hasTarget, !hasBaseline)}
          description={
            hasTarget ? (
              <>
                {FRAMEWORK_LABELS[activeTarget!.framework] || activeTarget!.framework} ·{' '}
                <StepValue>
                  −{Number(activeTarget!.target_reduction_percent).toFixed(1)}% by{' '}
                  {activeTarget!.target_year}
                </StepValue>{' '}
                → {fmtT(Number(activeTarget!.target_emissions_tco2e))} t (from{' '}
                {fmtT(Number(activeTarget!.base_year_emissions_tco2e))} in {activeTarget!.base_year})
              </>
            ) : hasBaseline ? (
              'Pick a framework — SBTi 1.5°C, Net Zero or custom — and the reduction math is done for you.'
            ) : (
              'Opens after your baseline — the target math starts from it.'
            )
          }
          action={
            hasTarget ? (
              <button
                type="button"
                onClick={() => setShowTargetModal(true)}
                className="cursor-pointer text-[12.5px] font-semibold text-cy-accent"
              >
                Edit
              </button>
            ) : !hasBaseline ? (
              <StepLockedText>After baseline</StepLockedText>
            ) : (
              <CanopyButton onClick={() => setShowTargetModal(true)} className="px-3.5 py-2">
                Set target
              </CanopyButton>
            )
          }
        />

        {/* 3 — Choose measures */}
        <StepRow
          num={3}
          title="Choose measures"
          state={state(3, hasMeasures, !hasBaseline)}
          description={
            hasMeasures ? (
              <>
                <StepValue>{activeScenario!.initiatives_count} measures</StepValue> selected in
                “{activeScenario!.name}”
              </>
            ) : (
              'Matched to your data — every number shows where it comes from.'
            )
          }
          action={
            !hasBaseline ? (
              <StepLockedText>After baseline</StepLockedText>
            ) : !hasTarget ? (
              <StepLockedText>After target</StepLockedText>
            ) : (
              <CanopyButton
                href="/decarbonization/recommendations"
                variant={currentStep === 3 ? 'primary' : 'pill'}
                className={currentStep === 3 ? 'px-3.5 py-2' : ''}
              >
                Choose measures
              </CanopyButton>
            )
          }
        >
          {!hasMeasures && hasBaseline && (recommendations?.length ?? 0) > 0 && (
            <div className="mt-2">
              {recommendations!.slice(0, 3).map((r) => (
                <div
                  key={r.initiative_name}
                  className="flex items-baseline justify-between gap-4 py-[7px] text-[12.5px]"
                >
                  <span className="min-w-0 truncate text-cy-ink">{r.initiative_name}</span>
                  <span className="whitespace-nowrap tabular-nums text-cy-muted">
                    <b className="font-semibold text-cy-ink">
                      −{fmtT(Number(r.potential_reduction_tco2e))} t
                    </b>
                    {r.estimated_capex != null && <> · {fmtMoney(Number(r.estimated_capex))}</>}
                  </span>
                </div>
              ))}
            </div>
          )}
        </StepRow>

        {/* 4 — Your plan */}
        <StepRow
          num={4}
          title="Your plan"
          state={state(4, planReaches, !hasMeasures && !hasTarget)}
          description={
            activeScenario ? (
              <>
                “{activeScenario.name}” covers <StepValue>{achievement.toFixed(0)}% of the target</StepValue>{' '}
                · −{fmtT(Number(activeScenario.total_reduction_tco2e))} t ·{' '}
                {fmtMoney(Number(activeScenario.total_investment))} investment
              </>
            ) : (
              'Reduction vs. target, investment, savings — one line per year.'
            )
          }
          action={
            activeScenario ? (
              <CanopyButton
                href="/decarbonization/scenarios"
                variant={currentStep === 4 ? 'primary' : 'pill'}
                className={currentStep === 4 ? 'px-3.5 py-2' : ''}
              >
                View plan
              </CanopyButton>
            ) : hasTarget ? (
              <CanopyButton href="/decarbonization/scenarios" variant="pill">
                Build scenario
              </CanopyButton>
            ) : (
              <StepLockedText />
            )
          }
        />

        {/* 5 — Track */}
        <StepRow
          num={5}
          title="Track"
          state={hasTarget && activeScenario ? (currentStep === 5 ? 'now' : 'todo') : 'locked'}
          description={
            hasTarget && activeScenario && targetProgress ? (
              <>
                <StepValue>{targetProgress.on_track ? 'On track' : 'Behind trajectory'}</StepValue> ·{' '}
                {targetProgress.checkpoint_year}: actual{' '}
                {fmtT(Number(targetProgress.actual_emissions_tco2e))} vs plan{' '}
                {fmtT(Number(targetProgress.planned_emissions_tco2e))} t CO₂e
              </>
            ) : (
              'Actual vs. planned, every reporting period.'
            )
          }
          action={
            hasTarget && activeScenario ? (
              <CanopyButton href="/decarbonization/roadmap" variant="pill">
                Roadmap
              </CanopyButton>
            ) : (
              <StepLockedText />
            )
          }
        />
      </Surface>

      {/* Set Target Modal */}
      {showTargetModal && (
        <SetTargetModal
          isOpen={showTargetModal}
          onClose={() => setShowTargetModal(false)}
          existingTarget={activeTarget}
          baselineEmissions={profile ? num(profile.total_co2e_tonnes) : undefined}
          baseYear={
            profile ? new Date(profile.analysis_date).getFullYear() : new Date().getFullYear()
          }
          basePeriodId={selectedPeriodId || undefined}
        />
      )}
    </AppShell>
  );
}
