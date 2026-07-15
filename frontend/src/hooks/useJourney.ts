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
import type { RailJourneyStep, TaskItem } from '@/components/canopy';

/** The one next-best-action (plan §4): exactly one action wins. */
export interface JourneyFocus {
  step: 'Measure' | 'Plan' | 'Report';
  title: string;
  body: string;
  action: { label: string; href: string };
}

export interface JourneyState {
  steps: RailJourneyStep[];
  focus: JourneyFocus;
  /** journey position for the FocusCard ring, e.g. { fraction: 1/3, label: '1/3' } */
  progress: { fraction: number; label: string };
  /** one guiding line for the dashboard greeting */
  statusLine: string;
  /** "What needs you" rows for the dashboard TaskList (max 4) */
  tasks: TaskItem[];
  hasData: boolean;
  relevant: number;
}

export function useJourney(): JourneyState {
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

  // The next-best-action selector (plan §4): exactly one action wins.
  const focus: JourneyFocus =
    relevant === 0
      ? {
          step: 'Measure',
          title: 'Set up your data profile',
          body: 'Tell Climatrix which activity categories apply to you — about five minutes, and it shapes everything that follows.',
          action: { label: 'Open the Data hub', href: '/hub' },
        }
      : !hasData
        ? {
            step: 'Measure',
            title: 'Bring your first data in',
            body: 'Upload a spreadsheet or your energy records — Smart Import reads them and only asks what it can’t infer.',
            action: { label: 'Open the Data hub', href: '/hub' },
          }
        : openQuestions > 0
          ? {
              step: 'Measure',
              title: `Answer ${openQuestions} open question${openQuestions === 1 ? '' : 's'}`,
              body: 'Smart Import needs a few answers to finish classifying your rows — about two minutes.',
              action: { label: 'Review questions', href: '/hub' },
            }
          : gaps > 0
            ? {
                step: 'Measure',
                title: `Bring data for ${gaps} more categor${gaps === 1 ? 'y' : 'ies'}`,
                body: 'A few relevant categories still have no data. Close them and your inventory is complete.',
                action: { label: 'Open the Data hub', href: '/hub' },
              }
            : !activeTarget
              ? {
                  step: 'Plan',
                  title: 'Set your 2030 reduction target',
                  body: 'Takes about 10 minutes. Climatrix suggests a science-based target from your baseline, then drafts the measures to hit it.',
                  action: { label: 'Set my target', href: '/decarbonization' },
                }
              : !activeScenario
                ? {
                    step: 'Plan',
                    title: 'Choose your reduction measures',
                    body: 'Measures matched to your data — every number shows where it comes from.',
                    action: { label: 'Choose measures', href: '/decarbonization/recommendations' },
                  }
                : achievement < 100
                  ? {
                      step: 'Plan',
                      title: 'Close the gap to your target',
                      body: `Your plan covers ${achievement.toFixed(0)}% of the target. Add or scale measures to reach 100%.`,
                      action: { label: 'Adjust the plan', href: '/decarbonization/recommendations' },
                    }
                  : {
                      step: 'Report',
                      title: 'Verify and share your report',
                      body: 'Your inventory is complete and your plan reaches the target. Run verification and export.',
                      action: { label: 'Open Reports', href: '/reports' },
                    };

  // "What needs you": open items first, then what's already standing.
  const tasks: TaskItem[] = [];
  if (openQuestions > 0)
    tasks.push({
      state: 'open',
      text: `Answer ${openQuestions} open question${openQuestions === 1 ? '' : 's'}`,
      hint: 'about 2 min',
      action: { label: 'Start →', href: '/hub' },
    });
  if (gaps > 0)
    tasks.push({
      state: 'open',
      text: `Bring data for ${gaps} categor${gaps === 1 ? 'y' : 'ies'}`,
      action: { label: 'Data hub →', href: '/hub' },
    });
  if (hasData && !activeTarget)
    tasks.push({
      state: 'open',
      text: 'Set a reduction target',
      hint: 'unlocks your plan',
      action: { label: 'Start →', href: '/decarbonization' },
    });
  if (activeTarget && !activeScenario)
    tasks.push({
      state: 'open',
      text: 'Pick your reduction measures',
      action: { label: 'Choose →', href: '/decarbonization/recommendations' },
    });
  if (activeTarget && activeScenario && achievement < 100)
    tasks.push({
      state: 'open',
      text: 'Your plan doesn’t reach the target yet',
      hint: `${achievement.toFixed(0)}% covered`,
      action: { label: 'Adjust →', href: '/decarbonization/recommendations' },
    });
  if (measureDone)
    tasks.push({ state: 'done', text: 'Data complete', hint: `${covered} categories covered` });
  if (activeTarget)
    tasks.push({
      state: 'done',
      text: `Target set — −${Number(activeTarget.target_reduction_percent).toFixed(0)}% by ${activeTarget.target_year}`,
    });
  if (planDone) tasks.push({ state: 'done', text: 'Plan reaches your target' });

  const doneCount = (measureDone ? 1 : 0) + (planDone ? 1 : 0);
  const statusLine =
    doneCount === 0
      ? relevant === 0
        ? 'Welcome — your journey starts with a little data.'
        : 'You’re measuring. Your footprint builds as data comes in.'
      : doneCount === 1
        ? 'Measurement is done. One step left before your first report.'
        : 'Your plan reaches the target — reporting is open.';

  return {
    steps: [
      { title: 'Measure', status: measureStatus, state: state(0), href: '/hub' },
      { title: 'Plan', status: planStatus, state: state(1), href: '/decarbonization' },
      { title: 'Report', status: reportStatus, state: state(2), href: '/reports' },
    ],
    focus,
    progress: { fraction: doneCount / 3, label: `${doneCount}/3` },
    statusLine,
    tasks: tasks.slice(0, 4),
    hasData,
    relevant,
  };
}
