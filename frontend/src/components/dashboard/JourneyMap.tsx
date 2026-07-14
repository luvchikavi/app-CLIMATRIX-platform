'use client';

/**
 * The dashboard's journey map: Measure → Plan → Report.
 *
 * One compact strip answering "where am I and what's next" for each of the
 * three journeys. Every number is server state the journey pages themselves
 * use (hub overview, targets, scenarios, target progress) — the map never
 * derives its own version of progress.
 */

import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useHubOverview } from '@/hooks/useHub';
import { Card } from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  Database,
  Target,
  FileText,
  ArrowRight,
  CheckCircle2,
  Lock,
  type LucideIcon,
} from 'lucide-react';

interface JourneyMapProps {
  /** The top-bar (global) period — journeys are read against it. */
  periodId?: string;
}

interface Journey {
  key: string;
  label: string;
  icon: LucideIcon;
  progressPercent: number;
  done: boolean;
  blocked: boolean;
  statusLine: string;
  nextLabel: string;
  nextHref: string;
}

export function JourneyMap({ periodId }: JourneyMapProps) {
  const router = useRouter();

  const { data: hub } = useHubOverview(periodId);
  const { data: targets } = useQuery({
    queryKey: ['decarbonization-targets'],
    queryFn: () => api.getDecarbonizationTargets(),
  });
  const { data: scenarios } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => api.getScenarios(),
  });

  const activeTarget = targets?.find((t) => t.is_active);
  const activeScenario = scenarios?.find((s) => s.is_active);

  const { data: targetProgress } = useQuery({
    queryKey: ['target-progress', activeTarget?.id, periodId],
    queryFn: () => api.getTargetProgress(activeTarget!.id, periodId!),
    enabled: !!activeTarget && !!periodId,
  });

  const stats = hub?.stats;
  const relevant = stats?.relevant ?? 0;
  const covered = stats?.with_data ?? 0;
  const openQuestions = stats?.open_questions ?? 0;
  const gaps = Math.max(relevant - covered, 0);
  const hasData = covered > 0;

  // — Measure: profile set → data in → questions answered —
  const measureDone = relevant > 0 && gaps === 0 && openQuestions === 0;
  const measure: Journey = {
    key: 'measure',
    label: 'Measure',
    icon: Database,
    progressPercent: relevant > 0 ? Math.min((covered / relevant) * 100, 100) : 0,
    done: measureDone,
    blocked: false,
    statusLine:
      relevant === 0
        ? 'No categories marked relevant yet'
        : `${covered} of ${relevant} relevant categories have data`,
    ...(relevant === 0
      ? { nextLabel: 'Set up your category profile', nextHref: '/hub' }
      : openQuestions > 0
        ? {
            nextLabel: `Answer ${openQuestions} open question${openQuestions === 1 ? '' : 's'}`,
            nextHref: '/hub',
          }
        : gaps > 0
          ? {
              nextLabel: `Bring data for ${gaps} categor${gaps === 1 ? 'y' : 'ies'}`,
              nextHref: '/hub',
            }
          : { nextLabel: 'Review your coverage', nextHref: '/hub' }),
  };

  // — Plan: target set → measures picked → plan reaches the target —
  const achievement = activeScenario
    ? Number(activeScenario.target_achievement_percent)
    : 0;
  const planStepsDone = (activeTarget ? 1 : 0) + (activeScenario ? 1 : 0) + (achievement >= 100 ? 1 : 0);
  const planDone = planStepsDone === 3;
  const plan: Journey = {
    key: 'plan',
    label: 'Plan',
    icon: Target,
    progressPercent: (planStepsDone / 3) * 100,
    done: planDone,
    blocked: !hasData,
    statusLine: !activeTarget
      ? 'No reduction target yet'
      : !activeScenario
        ? `Target −${Number(activeTarget.target_reduction_percent).toFixed(0)}% by ${activeTarget.target_year} — no scenario yet`
        : `Plan covers ${achievement.toFixed(0)}% of your target`,
    ...(!hasData
      ? { nextLabel: 'Complete Measure first', nextHref: '/hub' }
      : !activeTarget
        ? { nextLabel: 'Set your reduction target', nextHref: '/decarbonization' }
        : !activeScenario
          ? { nextLabel: 'Pick reduction measures', nextHref: '/decarbonization/recommendations' }
          : achievement < 100
            ? { nextLabel: 'Add measures to close the gap', nextHref: '/decarbonization/recommendations' }
            : targetProgress && !targetProgress.on_track
              ? { nextLabel: 'Behind trajectory — review plan', nextHref: '/decarbonization' }
              : { nextLabel: 'Track your progress', nextHref: '/decarbonization' }),
  };

  // — Report: data in → gaps and questions cleared → generate —
  const reportReady = hasData && gaps === 0 && openQuestions === 0;
  const blockers = gaps + openQuestions;
  const report: Journey = {
    key: 'report',
    label: 'Report',
    icon: FileText,
    progressPercent: !hasData ? 0 : reportReady ? 100 : 50,
    done: false, // "done" would be an exported report — not tracked yet
    blocked: !hasData,
    statusLine: !hasData
      ? 'Waiting for data'
      : reportReady
        ? 'Inventory is report-ready'
        : `${blockers} item${blockers === 1 ? '' : 's'} to resolve for an audit-ready report`,
    ...(!hasData
      ? { nextLabel: 'Complete Measure first', nextHref: '/hub' }
      : reportReady
        ? { nextLabel: 'Generate your report', nextHref: '/reports' }
        : { nextLabel: 'Close the gaps in Data Hub', nextHref: '/hub' }),
  };

  const journeys = [measure, plan, report];

  return (
    <Card padding="none" className="overflow-hidden">
      <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-border">
        {journeys.map((j, i) => {
          const Icon = j.icon;
          return (
            <div key={j.key} className={cn('p-4', j.blocked && 'opacity-60')}>
              <div className="flex items-center gap-2 mb-2">
                <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary/10 text-primary text-xs font-semibold">
                  {i + 1}
                </span>
                <Icon className="w-4 h-4 text-foreground-muted" />
                <span className="text-sm font-semibold text-foreground">{j.label}</span>
                {j.done && <CheckCircle2 className="w-4 h-4 text-success ml-auto" />}
                {j.blocked && <Lock className="w-3.5 h-3.5 text-foreground-muted ml-auto" />}
              </div>

              <div className="w-full h-1.5 bg-background-muted rounded-full overflow-hidden mb-2">
                <div
                  className={cn(
                    'h-full rounded-full transition-all',
                    j.done ? 'bg-success' : 'bg-primary'
                  )}
                  style={{ width: `${Math.max(j.progressPercent, 2)}%` }}
                />
              </div>

              <p className="text-xs text-foreground-muted mb-2 truncate" title={j.statusLine}>
                {j.statusLine}
              </p>

              <button
                type="button"
                onClick={() => router.push(j.nextHref)}
                className={cn(
                  'inline-flex items-center gap-1 text-xs font-medium transition-colors',
                  j.blocked
                    ? 'text-foreground-muted hover:text-foreground'
                    : 'text-primary hover:text-primary/80'
                )}
              >
                {j.nextLabel}
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
