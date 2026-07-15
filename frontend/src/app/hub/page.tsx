'use client';

/**
 * Data Hub — the living map of the inventory.
 *
 * One screen, two jobs: declare what's relevant (the profile — the expectation
 * a validator reads) and watch what has actually arrived against it (coverage,
 * on the measured/calculated/estimated/gap ladder). The full GHG category
 * matrix is always visible — nothing is hidden, including what you exclude.
 */

import { useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { AppShell } from '@/components/layout';
import { Surface, PanelLabel, PageHead, StatCells, type StatCell } from '@/components/canopy';
import { Button, toast } from '@/components/ui';
import { usePeriods, useSites } from '@/hooks/useEmissions';
import { useHubOverview, useSaveHubProfile } from '@/hooks/useHub';
import { usePeriodStore } from '@/stores/period';
import { CategoryDrawer } from '@/components/hub/CategoryDrawer';
import { api, HubCategory, HubRelevance } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

const SESSION_STATUS: Record<string, { label: string; chip: string }> = {
  needs_answers: { label: 'Questions waiting', chip: 'bg-cy-warn-soft text-cy-warn' },
  ready_for_review: { label: 'Ready to review', chip: 'bg-info-50 text-info' },
  committed: { label: 'In ledger', chip: 'bg-cy-accent-soft text-cy-accent' },
  analyzing: { label: 'Analyzing…', chip: 'bg-cy-row text-cy-muted' },
  failed: { label: 'Failed', chip: 'bg-error-50 text-error' },
};

// The data-quality ladder colours — same language as the import review grid.
const TIER_SEGMENT: Record<string, { bar: string; label: string }> = {
  measured: { bar: 'bg-cy-accent', label: 'Measured' },
  calculated: { bar: 'bg-cy-scope3', label: 'Calculated' },
  estimated: { bar: 'bg-cy-warn', label: 'Estimated' },
  gap: { bar: 'bg-cy-faint/40', label: 'Gap' },
};
const TIER_ORDER = ['measured', 'calculated', 'estimated', 'gap'] as const;
// "In ledger" = banked — ink, distinct from every ladder tier.
const LEDGER_BAR = 'bg-cy-ink/60';

const SCOPE_SECTIONS: { title: string; blurb: string; match: (c: HubCategory) => boolean }[] = [
  { title: 'Scope 1 — Direct emissions', blurb: 'Fuel you burn, vehicles you run, refrigerants you lose', match: (c) => c.scope === 1 },
  { title: 'Scope 2 — Purchased energy', blurb: 'Electricity, heat and steam you buy', match: (c) => c.scope === 2 },
  {
    title: 'Scope 3 — Value chain (upstream)',
    blurb: 'What happens before your operations',
    match: (c) => c.scope === 3 && parseFloat(c.code.split('.')[1]) <= 8,
  },
  {
    title: 'Scope 3 — Value chain (downstream)',
    blurb: 'What happens after your products leave',
    match: (c) => c.scope === 3 && parseFloat(c.code.split('.')[1]) >= 9,
  },
];

const RELEVANCE_OPTIONS: { value: HubRelevance; label: string; active: string }[] = [
  { value: 'relevant', label: 'Relevant', active: 'bg-cy-accent-soft text-cy-accent' },
  { value: 'not_relevant', label: 'Not relevant', active: 'bg-cy-surface text-cy-muted shadow-sm' },
  { value: 'not_sure', label: 'Not sure', active: 'bg-cy-warn-soft text-cy-warn' },
];

function CoverageBar({ category }: { category: HubCategory }) {
  const { coverage, profile } = category;
  const relevance = profile?.relevance ?? 'not_sure';
  const total = coverage.staged_count + coverage.committed_count;

  if (relevance === 'not_relevant') {
    return (
      <p className="truncate text-[12px] italic text-cy-faint">
        {profile?.exclusion_reason || 'Excluded'}
      </p>
    );
  }

  if (total === 0) {
    return (
      <div className="flex items-center gap-2">
        <div className="h-1.5 flex-1 rounded-full bg-cy-row" />
        <span
          className={cn(
            'shrink-0 text-[12px] font-semibold',
            relevance === 'relevant' ? 'text-cy-warn' : 'text-cy-faint'
          )}
        >
          {relevance === 'relevant' ? 'No data yet' : '—'}
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <div className="flex h-1.5 flex-1 overflow-hidden rounded-full bg-cy-row">
        {coverage.committed_count > 0 && (
          <div
            className={LEDGER_BAR}
            style={{ width: `${(coverage.committed_count / total) * 100}%` }}
            title={`${coverage.committed_count} in ledger`}
          />
        )}
        {TIER_ORDER.map((tier) => {
          const n = coverage.staged_by_tier[tier] ?? 0;
          if (!n) return null;
          return (
            <div
              key={tier}
              className={TIER_SEGMENT[tier].bar}
              style={{ width: `${(n / total) * 100}%` }}
              title={`${n} ${TIER_SEGMENT[tier].label.toLowerCase()}`}
            />
          );
        })}
      </div>
      <span className="shrink-0 text-[12px] tabular-nums text-cy-muted">
        {total} {total === 1 ? 'row' : 'rows'}
        {coverage.committed_count > 0 && ` · ${coverage.committed_count} in ledger`}
      </span>
    </div>
  );
}

function CategoryRow({
  category,
  onRelevance,
  onOpen,
  saving,
}: {
  category: HubCategory;
  onRelevance: (code: string, relevance: HubRelevance, reason?: string) => void;
  onOpen: (category: HubCategory) => void;
  saving: boolean;
}) {
  const relevance = category.profile?.relevance ?? 'not_sure';
  const [reasonDraft, setReasonDraft] = useState<string | null>(null);

  const pick = (value: HubRelevance) => {
    if (value === relevance && reasonDraft === null) return;
    if (value === 'not_relevant') {
      // an exclusion must carry its reason — that line is what an auditor reads
      setReasonDraft(category.profile?.exclusion_reason ?? '');
      return;
    }
    setReasonDraft(null);
    onRelevance(category.code, value);
  };

  const confirmExclusion = () => {
    if (!reasonDraft?.trim()) {
      toast.error('A short reason is required — it becomes your documented exclusion.');
      return;
    }
    onRelevance(category.code, 'not_relevant', reasonDraft.trim());
    setReasonDraft(null);
  };

  return (
    <div
      className={cn(
        'grid grid-cols-1 gap-2 py-3 sm:grid-cols-[minmax(0,2fr)_minmax(0,1.6fr)_auto] sm:items-center sm:gap-4',
        relevance === 'not_relevant' && 'opacity-60'
      )}
    >
      <button type="button" onClick={() => onOpen(category)} className="min-w-0 cursor-pointer text-left">
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-[11px] text-cy-faint">{category.code}</span>
          <span className="truncate text-[13px] font-semibold text-cy-ink hover:text-cy-accent">
            {category.name}
          </span>
          {category.profile?.data_owner && (
            <span className="hidden truncate text-[11.5px] text-cy-faint lg:inline">
              · {category.profile.data_owner}
            </span>
          )}
        </div>
        <p className="truncate text-[12px] text-cy-muted">{category.description}</p>
      </button>

      <CoverageBar category={category} />

      <div className="flex items-center gap-2">
        {category.coverage.open_questions > 0 && (
          <Link
            href="/ingest"
            className="shrink-0 rounded-full bg-cy-warn-soft px-2 py-0.5 text-[11px] font-bold text-cy-warn"
            title="Open questions from your uploads"
          >
            ? {category.coverage.open_questions}
          </Link>
        )}
        <div className="flex shrink-0 rounded-full bg-cy-row p-0.5">
          {RELEVANCE_OPTIONS.map((opt) => {
            const isActive = relevance === opt.value && reasonDraft === null;
            return (
              <button
                key={opt.value}
                type="button"
                disabled={saving}
                onClick={() => pick(opt.value)}
                title={opt.label}
                className={cn(
                  'cursor-pointer rounded-full px-2.5 py-1 text-[11.5px] font-semibold transition-colors',
                  isActive ? opt.active : 'text-cy-faint hover:text-cy-muted'
                )}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>

      {reasonDraft !== null && (
        <div className="flex items-center gap-2 sm:col-span-3">
          <input
            autoFocus
            value={reasonDraft}
            onChange={(e) => setReasonDraft(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && confirmExclusion()}
            placeholder="Why is this not relevant? e.g. “No district heating at any site”"
            className="flex-1 rounded-[10px] border-0 bg-cy-row px-3 py-2 text-[13px] font-semibold text-cy-ink placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent"
          />
          <Button size="sm" onClick={confirmExclusion} disabled={saving}>
            Exclude
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setReasonDraft(null)}>
            Cancel
          </Button>
        </div>
      )}
    </div>
  );
}

export default function HubPage() {
  const { data: periods } = usePeriods();
  const { selectedPeriodId } = usePeriodStore();
  const periodId = periods?.find((p) => p.id === selectedPeriodId)?.id ?? periods?.[0]?.id;
  const queryClient = useQueryClient();

  // Per-site profile layer: org-wide by default; large orgs override per site.
  const { data: sites } = useSites();
  const [siteId, setSiteId] = useState<string>('');

  const { data, isLoading } = useHubOverview(periodId, siteId || undefined);
  const saveProfile = useSaveHubProfile(siteId || undefined);
  const [drawer, setDrawer] = useState<HubCategory | null>(null);
  const { data: sessions } = useQuery({
    queryKey: ['ingest-sessions'],
    queryFn: () => api.listIngestSessions(),
    staleTime: 30 * 1000,
  });
  const recentSessions = (sessions ?? []).slice(0, 5);

  // Multi-file drop: each file becomes its own session; the list below tracks them.
  const [uploading, setUploading] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const uploadFiles = async (files: FileList | File[]) => {
    const list = Array.from(files);
    for (let i = 0; i < list.length; i++) {
      setUploading(`${list[i].name} (${i + 1}/${list.length})`);
      try {
        await api.ingestUpload(list[i], periodId);
      } catch (e) {
        toast.error(`${list[i].name}: ${e instanceof Error ? e.message : 'upload failed'}`);
      }
      queryClient.invalidateQueries({ queryKey: ['ingest-sessions'] });
      queryClient.invalidateQueries({ queryKey: ['hub-overview'] });
    }
    setUploading(null);
    toast.success(`${list.length} file${list.length > 1 ? 's' : ''} processed — review below`);
  };

  const setupMode = useMemo(
    () => !!data && data.stats.not_sure === data.stats.total_categories,
    [data]
  );

  const handleRelevance = (code: string, relevance: HubRelevance, reason?: string) => {
    saveProfile.mutate(
      [{ category_code: code, relevance, exclusion_reason: reason ?? null }],
      {
        onError: (e) =>
          toast.error(e instanceof Error ? e.message : 'Could not save — try again'),
      }
    );
  };

  const statCells: StatCell[] | null = data
    ? [
        {
          label: 'Categories relevant',
          value: String(data.stats.relevant),
          sub: `/ ${data.stats.total_categories}`,
        },
        {
          label: 'Relevant with data',
          value: String(data.stats.with_data),
          sub: data.stats.relevant ? `/ ${data.stats.relevant}` : undefined,
        },
        { label: 'Open questions', value: String(data.stats.open_questions) },
        { label: 'Still undecided', value: String(data.stats.not_sure) },
      ]
    : null;

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <PageHead
            title="Data hub"
            subtitle="Everything Climatrix knows comes through here — files in, verified numbers out."
          />
          <div className="mb-[22px] flex flex-wrap items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() =>
                api
                  .downloadPunchList(periodId)
                  .catch((e) =>
                    toast.error(e instanceof Error ? e.message : 'Export failed')
                  )
              }
              title="The auditor punch-list: what's solid, what's estimated, what's missing"
            >
              Verification pack
            </Button>
            {(sites?.length ?? 0) > 1 && (
              <select
                value={siteId}
                onChange={(e) => setSiteId(e.target.value)}
                className="cursor-pointer rounded-full border-0 bg-cy-row px-3 py-1.5 text-[12px] font-semibold text-cy-ink focus:outline-none focus:ring-2 focus:ring-cy-accent"
                title="Which profile layer to view/edit — coverage is org-wide"
              >
                <option value="">All sites (org profile)</option>
                {(sites ?? []).map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            )}
            <Link href="/activities?add=1">
              <Button variant="secondary" size="sm">
                Add manually
              </Button>
            </Link>
          </div>
        </div>

        {/* Drop several files at once — each becomes its own upload session */}
        <Surface
          padding="none"
          tint="soft"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (e.dataTransfer.files?.length) uploadFiles(e.dataTransfer.files);
          }}
          onClick={() => !uploading && fileRef.current?.click()}
          className="cursor-pointer px-6 py-7 text-center"
        >
          {uploading ? (
            <p className="flex items-center justify-center gap-2 text-[13px] font-semibold text-cy-accent">
              <Loader2 className="h-4 w-4 animate-spin" />
              Reading {uploading}…
            </p>
          ) : (
            <>
              <p className="text-[14px] font-bold text-cy-ink">Drop a file to import</p>
              <p className="mt-1 text-[12.5px] text-cy-muted">
                One or many — invoices export, fuel cards, the CLIMATRIX template. Climatrix reads
                it and asks only what it can&apos;t infer.
              </p>
            </>
          )}
          <input
            ref={fileRef}
            type="file"
            multiple
            hidden
            accept=".xlsx,.xlsm,.csv"
            onChange={(e) => e.target.files?.length && uploadFiles(e.target.files)}
          />
        </Surface>

        {statCells && (
          <Surface>
            <PanelLabel>Your inventory map</PanelLabel>
            <StatCells cells={statCells} />
          </Surface>
        )}

        {/* The chase list — relevant categories still waiting for data */}
        {data && (() => {
          const missing = data.categories.filter(
            (c) =>
              (c.profile?.relevance ?? 'not_sure') === 'relevant' &&
              c.coverage.committed_count === 0 &&
              c.coverage.staged_count === 0
          );
          if (missing.length === 0) return null;
          return (
            <Surface tint="warn">
              <PanelLabel className="text-cy-warn">Still missing — your chase list</PanelLabel>
              <div className="flex flex-wrap gap-1.5">
                {missing.map((c) => (
                  <button
                    key={c.code}
                    onClick={() => setDrawer(c)}
                    className="cursor-pointer rounded-full bg-cy-surface px-3 py-1 text-[12px] font-semibold text-cy-ink hover:text-cy-accent"
                  >
                    {c.code} {c.name}
                    {c.profile?.data_owner && ` → ask ${c.profile.data_owner}`}
                  </button>
                ))}
              </div>
            </Surface>
          );
        })()}

        {recentSessions.length > 0 && (
          <Surface>
            <PanelLabel>In review</PanelLabel>
            <div className="divide-y divide-cy-row">
              {recentSessions.map((s) => {
                const meta = SESSION_STATUS[s.status] ?? {
                  label: s.status,
                  chip: 'bg-cy-row text-cy-muted',
                };
                return (
                  <Link
                    key={s.id}
                    href={`/ingest?session=${s.id}`}
                    className="flex items-center gap-3 py-2.5 hover:bg-cy-row/40"
                  >
                    <span className="min-w-0 flex-1 truncate text-[13px] font-semibold text-cy-ink">
                      {s.filename}
                    </span>
                    <span className="hidden text-[12px] tabular-nums text-cy-muted sm:inline">
                      {s.total_rows} rows
                      {s.open_question_count > 0 && ` · ${s.open_question_count} open questions`}
                    </span>
                    <span className={cn('rounded-full px-2 py-0.5 text-[11px] font-bold', meta.chip)}>
                      {meta.label}
                    </span>
                    <span className="text-cy-faint" aria-hidden="true">→</span>
                  </Link>
                );
              })}
            </div>
          </Surface>
        )}

        {setupMode && (
          <Surface tint="soft">
            <p className="text-[13px] font-bold text-cy-ink">
              Start by mapping your inventory — two clicks per row.
            </p>
            <p className="mt-0.5 max-w-[62ch] text-[12.5px] text-cy-muted">
              Mark each category as relevant or not. This becomes your reporting boundary: it
              tells the parser what to expect and tells you what&apos;s still missing. You can
              change any answer later.
            </p>
          </Surface>
        )}

        {isLoading && (
          <div className="flex items-center justify-center gap-2 py-16 text-cy-faint">
            <Loader2 className="h-5 w-5 animate-spin" />
            Loading your inventory map…
          </div>
        )}

        {data &&
          SCOPE_SECTIONS.map((section) => {
            const cats = data.categories.filter(section.match);
            if (cats.length === 0) return null;
            return (
              <Surface key={section.title}>
                <PanelLabel>{section.title}</PanelLabel>
                <p className="-mt-2.5 mb-2 text-[12px] text-cy-muted">{section.blurb}</p>
                <div className="divide-y divide-cy-row">
                  {cats.map((c) => (
                    <CategoryRow
                      key={c.code}
                      category={c}
                      onRelevance={handleRelevance}
                      onOpen={setDrawer}
                      saving={saveProfile.isPending}
                    />
                  ))}
                </div>
              </Surface>
            );
          })}

        {data && (
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 px-1 text-[11.5px] text-cy-faint">
            <span className="flex items-center gap-1.5">
              <span className={cn('h-[7px] w-[7px] rounded-full', LEDGER_BAR)} /> In ledger
            </span>
            {TIER_ORDER.map((tier) => (
              <span key={tier} className="flex items-center gap-1.5">
                <span className={cn('h-[7px] w-[7px] rounded-full', TIER_SEGMENT[tier].bar)} />
                {TIER_SEGMENT[tier].label}
              </span>
            ))}
          </div>
        )}
      </div>

      {drawer && (
        <CategoryDrawer
          key={drawer.code}
          // keep the drawer in sync with fresh overview data after saves
          category={data?.categories.find((c) => c.code === drawer.code) ?? drawer}
          siteId={siteId || undefined}
          periodId={periodId}
          onClose={() => setDrawer(null)}
        />
      )}
    </AppShell>
  );
}
