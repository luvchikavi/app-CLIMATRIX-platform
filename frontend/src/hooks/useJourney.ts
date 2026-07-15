'use client';

/**
 * The journey rail's single data source: Measure → Plan → Report states from
 * the same server queries the journey pages themselves use (hub overview,
 * targets, scenarios) — the rail never derives its own version of progress.
 * Extracted from dashboard/JourneyMap (which retires in batch 2.2); Phase 3
 * consolidates this into one backend endpoint.
 */

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useHubOverview } from '@/hooks/useHub';
import { usePeriodStore } from '@/stores/period';
import type { RailJourneyStep } from '@/components/canopy';

export function useJourney(): { steps: RailJourneyStep[] } {
  const { selectedPeriodId } = usePeriodStore();

  const { data: hub } = useHubOverview(selectedPeriodId ?? undefined);
  const { data: targets } = useQuery({
    queryKey: ['decarbonization-targets'],
    queryFn: () => api.getDecarbonizationTargets(),
  });
  const { data: scenarios } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => api.getScenarios(),
  });

  const stats = hub?.stats;
  const relevant = stats?.relevant ?? 0;
  const covered = stats?.with_data ?? 0;
  const openQuestions = stats?.open_questions ?? 0;
  const gaps = Math.max(relevant - covered, 0);
  const hasData = covered > 0;

  const activeTarget = targets?.find((t) => t.is_active);
  const activeScenario = scenarios?.find((s) => s.is_active);
  const achievement = activeScenario ? Number(activeScenario.target_achievement_percent) : 0;

  const measureDone = relevant > 0 && gaps === 0 && openQuestions === 0;
  const planDone = !!activeTarget && !!activeScenario && achievement >= 100;
  const reportReady = hasData && gaps === 0 && openQuestions === 0;
  const blockers = gaps + openQuestions;

  const measureStatus =
    relevant === 0
      ? 'Set up your profile'
      : measureDone
        ? `${covered} categories · complete`
        : openQuestions > 0
          ? `${openQuestions} question${openQuestions === 1 ? '' : 's'} open`
          : `${covered} of ${relevant} categories covered`;

  const planStatus = !hasData
    ? 'Opens after Measure'
    : planDone
      ? 'Plan reaches target ✓'
      : !activeTarget
        ? 'Set your reduction target'
        : !activeScenario
          ? `Target −${Number(activeTarget.target_reduction_percent).toFixed(0)}% · pick measures`
          : `Plan covers ${achievement.toFixed(0)}% of target`;

  const reportStatus = !hasData
    ? 'Opens after your data'
    : reportReady
      ? 'Ready to generate'
      : `${blockers} item${blockers === 1 ? '' : 's'} to resolve`;

  // Soft-locks (decision #3): every step keeps its href — a "locked" state
  // only changes how the rail paints it, never whether it navigates.
  const doneOrLocked = [
    { done: measureDone, locked: false },
    { done: planDone, locked: !hasData },
    { done: false, locked: !hasData },
  ];
  // Exactly one "now": the first step that is neither done nor locked.
  const nowIndex = doneOrLocked.findIndex((s) => !s.done && !s.locked);

  const state = (i: number): RailJourneyStep['state'] =>
    doneOrLocked[i].done ? 'done' : doneOrLocked[i].locked ? 'locked' : i === nowIndex ? 'now' : 'todo';

  return {
    steps: [
      { title: 'Measure', status: measureStatus, state: state(0), href: '/hub' },
      { title: 'Plan', status: planStatus, state: state(1), href: '/decarbonization' },
      { title: 'Report', status: reportStatus, state: state(2), href: '/reports' },
    ],
  };
}
