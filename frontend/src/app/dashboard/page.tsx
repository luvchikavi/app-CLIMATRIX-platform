'use client';

/**
 * The Canopy dashboard (batch 2.2) — the locked template page, on real data:
 * greeting → ONE focus card (next-best-action) → footprint cells → largest
 * sources + what needs you. The journey lives in the rail; nothing here is
 * shown twice, and no number is the largest thing on screen.
 * (JourneyMap, the KPI band, the pie/site charts and the activities table
 * retired — Activities owns the ledger, Reports owns the breakdowns.)
 */

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import { usePeriods, useReportSummary, useSitesBreakdown } from '@/hooks/useEmissions';
import { useJourney } from '@/hooks/useJourney';
import { useLoadSampleData } from '@/hooks/useSampleData';
import { AppShell } from '@/components/layout';
import {
  BarList,
  CanopyButton,
  FocusCard,
  PageHead,
  PanelLabel,
  StatCells,
  Surface,
  TaskList,
  type StatCell,
} from '@/components/canopy';
import { api } from '@/lib/api';
import { categoryNames } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

/** tonnes, calm: integers once real, decimals only while tiny */
function tonnes(kg: number): string {
  const t = kg / 1000;
  if (t >= 100) return Math.round(t).toLocaleString();
  if (t >= 1) return t.toFixed(1);
  return t.toFixed(2);
}

function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 18) return 'Good afternoon';
  return 'Good evening';
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { selectedPeriodId } = usePeriodStore();
  const journey = useJourney();
  const loadSample = useLoadSampleData();

  const { data: periods, isLoading: periodsLoading } = usePeriods();
  // Only trust the persisted period if it belongs to THIS org's list.
  const globalPeriodId = periods?.find((p) => p.id === selectedPeriodId)?.id ?? periods?.[0]?.id;

  const {
    data: summary,
    isLoading: summaryLoading,
    isError: summaryError,
    refetch: refetchSummary,
  } = useReportSummary(globalPeriodId || '');

  const isLoading = periodsLoading || (summaryLoading && !!globalPeriodId);
  const firstName = user?.full_name?.split(' ')[0] || user?.email?.split('@')[0] || 'there';

  const total = summary?.total_co2e_kg ?? 0;
  const scopes = [
    { n: 1 as const, kg: summary?.scope_1_co2e_kg ?? 0 },
    { n: 2 as const, kg: summary?.scope_2_co2e_kg ?? 0 },
    { n: 3 as const, kg: summary?.scope_3_co2e_kg ?? 0 },
  ];
  const pct = (kg: number) => (total > 0 ? `${Math.round((kg / total) * 100)}%` : '0%');

  const topSources = [...(summary?.by_category ?? [])]
    .sort((a, b) => b.total_co2e_kg - a.total_co2e_kg)
    .slice(0, 4);
  const maxSource = topSources[0]?.total_co2e_kg ?? 1;

  const isEmpty = !!summary && total === 0;

  // More data on the glance line — still one quiet row, numbers ≤16px.
  const activityCount = (summary?.by_scope ?? []).reduce((n, s) => n + s.activity_count, 0);
  const { data: dq } = useQuery({
    queryKey: ['data-quality', globalPeriodId],
    queryFn: () => api.getDataQualitySummary(globalPeriodId!),
    enabled: !!globalPeriodId && total > 0,
    staleTime: 2 * 60 * 1000,
  });
  const { data: sitesBreakdown } = useSitesBreakdown(globalPeriodId);
  const topSites = [...(sitesBreakdown ?? [])]
    .sort((a, b) => b.total_co2e_kg - a.total_co2e_kg)
    .slice(0, 4);
  const maxSite = topSites[0]?.total_co2e_kg ?? 1;

  const footprintCells: StatCell[] = [
    { label: 'Total', value: tonnes(total), sub: 't CO₂e' },
    ...scopes.map((s) => ({
      label: `Scope ${s.n}`,
      value: tonnes(s.kg),
      sub: pct(s.kg),
      scope: s.n,
    })),
    ...(activityCount > 0
      ? [{ label: 'Activities', value: activityCount.toLocaleString() }]
      : []),
    ...(dq
      ? [
          {
            label: 'Data quality · 1 = best',
            value: dq.weighted_average_score.toFixed(1),
            sub: '/ 5',
          },
        ]
      : []),
  ];

  return (
    <AppShell>
      <PageHead title={`${greeting()}, ${firstName}`} subtitle={journey.statusLine} />

      {isLoading && (
        <div className="flex items-center justify-center py-20" role="status" aria-live="polite">
          <Loader2 className="h-6 w-6 animate-spin text-cy-accent" aria-hidden="true" />
          <span className="ml-3 text-[13px] text-cy-muted">Loading your footprint…</span>
        </div>
      )}

      {!isLoading && summaryError && (
        <Surface tint="warn" className="max-w-[560px]">
          <p className="mb-3 text-[13.5px] text-cy-ink">
            Your emissions data didn’t load — this is usually temporary.
          </p>
          <CanopyButton onClick={() => refetchSummary()}>Try again</CanopyButton>
        </Surface>
      )}

      {!isLoading && periods && periods.length === 0 && (
        <FocusCard
          kicker="Start here"
          title="Create your first reporting period"
          body="A reporting period (usually your fiscal year) is the container everything else lives in — data, reports and plans."
          action={{ label: 'Create a period', href: '/settings?tab=periods' }}
          progress={{ fraction: 0, label: '0/3' }}
        />
      )}

      {!isLoading && !summaryError && summary && (
        <>
          {isEmpty ? (
            <FocusCard
              kicker="Start here"
              title="See Climatrix in action"
              body="Load a realistic sample dataset — a full year of an industrial company’s energy data. Dashboard, report and reduction scenarios come alive; one click removes it all again."
              action={{
                label: loadSample.isPending ? 'Loading…' : 'Load sample data',
                onClick: () => !loadSample.isPending && loadSample.mutate(),
              }}
              skip={{ label: 'or bring your own data', href: '/hub' }}
              progress={journey.progress}
            />
          ) : (
            <FocusCard
              kicker={`Next · ${journey.focus.step}`}
              title={journey.focus.title}
              body={journey.focus.body}
              action={journey.focus.action}
              progress={journey.progress}
            />
          )}

          <Surface className="mb-4">
            <PanelLabel>Footprint · {summary.period_name}</PanelLabel>
            <StatCells cells={footprintCells} />
          </Surface>

          <div className="mb-4 grid gap-4 md:grid-cols-2">
            <Surface>
              <PanelLabel>Largest sources</PanelLabel>
              {topSources.length > 0 ? (
                <BarList
                  items={topSources.map((c) => ({
                    label: categoryNames[c.category_code] || c.category_code,
                    value: `${tonnes(c.total_co2e_kg)} t`,
                    pct: (c.total_co2e_kg / maxSource) * 100,
                  }))}
                />
              ) : (
                <p className="text-[12.5px] text-cy-muted">
                  Your biggest emission sources appear here as data comes in.
                </p>
              )}
            </Surface>
            <Surface>
              <PanelLabel>What needs you</PanelLabel>
              {journey.tasks.length > 0 ? (
                <TaskList items={journey.tasks} />
              ) : (
                <p className="text-[12.5px] text-cy-muted">Nothing right now — you’re ahead.</p>
              )}
            </Surface>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Surface>
              <PanelLabel>By site</PanelLabel>
              {topSites.length > 0 ? (
                <>
                  <BarList
                    items={topSites.map((s) => ({
                      label: s.site_name,
                      value: `${tonnes(s.total_co2e_kg)} t`,
                      pct: (s.total_co2e_kg / maxSite) * 100,
                    }))}
                  />
                  {(sitesBreakdown?.length ?? 0) > 4 && (
                    <Link
                      href="/sites"
                      className="mt-2.5 inline-block text-[12px] font-semibold text-cy-accent"
                    >
                      All {sitesBreakdown!.length} sites →
                    </Link>
                  )}
                </>
              ) : (
                <p className="text-[12.5px] text-cy-muted">
                  Assign activities to sites and the split appears here.{' '}
                  <Link href="/sites" className="font-semibold text-cy-accent">
                    Manage sites →
                  </Link>
                </p>
              )}
            </Surface>
            <Surface>
              <PanelLabel>Your plan</PanelLabel>
              {journey.plan.hasTarget ? (
                <>
                  <p className="text-[13px] text-cy-ink">
                    <b className="font-semibold tabular-nums">
                      −{journey.plan.targetPct?.toFixed(0)}% by {journey.plan.targetYear}
                    </b>{' '}
                    <span className="text-cy-muted">· your reduction target</span>
                  </p>
                  <div className="mt-2.5 flex items-center gap-3">
                    <div className="h-1.5 max-w-[240px] flex-1 overflow-hidden rounded-[3px] bg-cy-row" aria-hidden="true">
                      <div
                        className="h-full rounded-[3px] bg-cy-accent"
                        style={{ width: `${Math.min(100, journey.plan.achievementPct)}%` }}
                      />
                    </div>
                    <span className="text-[12px] tabular-nums text-cy-muted">
                      {journey.plan.hasScenario
                        ? `plan covers ${journey.plan.achievementPct.toFixed(0)}%`
                        : 'no measures picked yet'}
                    </span>
                  </div>
                  <Link
                    href="/decarbonization"
                    className="mt-3 inline-block text-[12px] font-semibold text-cy-accent"
                  >
                    Open the plan →
                  </Link>
                </>
              ) : (
                <p className="text-[12.5px] text-cy-muted">
                  No reduction target yet — setting one unlocks measures matched to your data.{' '}
                  <Link href="/decarbonization" className="font-semibold text-cy-accent">
                    Set your target →
                  </Link>
                </p>
              )}
            </Surface>
          </div>
        </>
      )}
    </AppShell>
  );
}
