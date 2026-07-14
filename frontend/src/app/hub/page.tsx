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
import { Card, CardContent, Button, toast } from '@/components/ui';
import { usePeriods, useSites } from '@/hooks/useEmissions';
import { useHubOverview, useSaveHubProfile } from '@/hooks/useHub';
import { usePeriodStore } from '@/stores/period';
import { CategoryDrawer } from '@/components/hub/CategoryDrawer';
import { api, HubCategory, HubRelevance } from '@/lib/api';
import { cn } from '@/lib/utils';
import {
  UploadCloud,
  HelpCircle,
  CheckCircle2,
  XCircle,
  CircleDashed,
  Loader2,
  ArrowRight,
  Ban,
  FileSpreadsheet,
  PlusCircle,
  ChevronRight,
} from 'lucide-react';

const SESSION_STATUS: Record<string, { label: string; chip: string }> = {
  needs_answers: {
    label: 'Questions waiting',
    chip: 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300',
  },
  ready_for_review: {
    label: 'Ready to review',
    chip: 'bg-sky-100 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300',
  },
  committed: {
    label: 'In ledger',
    chip: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300',
  },
  analyzing: {
    label: 'Analyzing…',
    chip: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
  },
  failed: {
    label: 'Failed',
    chip: 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300',
  },
};

// The data-quality ladder colours — same language as the import review grid.
const TIER_SEGMENT: Record<string, { bar: string; label: string }> = {
  measured: { bar: 'bg-emerald-500', label: 'Measured' },
  calculated: { bar: 'bg-teal-500', label: 'Calculated' },
  estimated: { bar: 'bg-amber-500', label: 'Estimated' },
  gap: { bar: 'bg-slate-400', label: 'Gap' },
};
const TIER_ORDER = ['measured', 'calculated', 'estimated', 'gap'] as const;

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

const RELEVANCE_OPTIONS: {
  value: HubRelevance;
  label: string;
  icon: typeof CheckCircle2;
  active: string;
}[] = [
  {
    value: 'relevant',
    label: 'Relevant',
    icon: CheckCircle2,
    active: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300',
  },
  {
    value: 'not_relevant',
    label: 'Not relevant',
    icon: XCircle,
    active: 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  },
  {
    value: 'not_sure',
    label: 'Not sure',
    icon: CircleDashed,
    active: 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300',
  },
];

function CoverageBar({ category }: { category: HubCategory }) {
  const { coverage, profile } = category;
  const relevance = profile?.relevance ?? 'not_sure';
  const total = coverage.staged_count + coverage.committed_count;

  if (relevance === 'not_relevant') {
    return (
      <div className="flex items-center gap-1.5 text-xs text-slate-400 dark:text-slate-500">
        <Ban className="h-3.5 w-3.5 shrink-0" />
        <span className="truncate italic">{profile?.exclusion_reason || 'Excluded'}</span>
      </div>
    );
  }

  if (total === 0) {
    return (
      <div className="flex items-center gap-2">
        <div className="h-2 flex-1 rounded-full bg-slate-100 dark:bg-slate-800" />
        <span
          className={cn(
            'shrink-0 text-xs font-medium',
            relevance === 'relevant'
              ? 'text-rose-500 dark:text-rose-400'
              : 'text-slate-400 dark:text-slate-500'
          )}
        >
          {relevance === 'relevant' ? 'No data yet' : '—'}
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <div className="flex h-2 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
        {coverage.committed_count > 0 && (
          <div
            className="bg-indigo-500"
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
      <span className="shrink-0 text-xs text-slate-500 dark:text-slate-400">
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
        'grid grid-cols-1 gap-2 px-4 py-3 sm:grid-cols-[minmax(0,2fr)_minmax(0,1.6fr)_auto] sm:items-center sm:gap-4',
        relevance === 'not_relevant' && 'opacity-60'
      )}
    >
      <button type="button" onClick={() => onOpen(category)} className="min-w-0 text-left">
        <div className="flex items-baseline gap-2">
          <span className="text-xs font-mono text-slate-400 dark:text-slate-500">{category.code}</span>
          <span className="truncate text-sm font-medium text-slate-800 hover:text-emerald-600 dark:text-slate-100 dark:hover:text-emerald-400">
            {category.name}
          </span>
          {category.profile?.data_owner && (
            <span className="hidden truncate text-xs text-slate-400 lg:inline">
              · {category.profile.data_owner}
            </span>
          )}
        </div>
        <p className="truncate text-xs text-slate-500 dark:text-slate-400">{category.description}</p>
      </button>

      <CoverageBar category={category} />

      <div className="flex items-center gap-2">
        {category.coverage.open_questions > 0 && (
          <Link
            href="/ingest"
            className="flex shrink-0 items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700 hover:bg-amber-200 dark:bg-amber-950/60 dark:text-amber-300"
            title="Open questions from your uploads"
          >
            <HelpCircle className="h-3 w-3" />
            {category.coverage.open_questions}
          </Link>
        )}
        <div className="flex shrink-0 rounded-lg border border-slate-200 p-0.5 dark:border-slate-700">
          {RELEVANCE_OPTIONS.map((opt) => {
            const Icon = opt.icon;
            const isActive = relevance === opt.value && reasonDraft === null;
            return (
              <button
                key={opt.value}
                type="button"
                disabled={saving}
                onClick={() => pick(opt.value)}
                title={opt.label}
                className={cn(
                  'flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors',
                  isActive
                    ? opt.active
                    : 'text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300'
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                <span className="hidden lg:inline">{opt.label}</span>
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
            className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
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

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">Data Hub</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Your whole inventory in one place — what&apos;s relevant, what&apos;s arrived, what&apos;s
              still missing.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              onClick={() =>
                api
                  .downloadPunchList(periodId)
                  .catch((e) =>
                    toast.error(e instanceof Error ? e.message : 'Export failed')
                  )
              }
              title="The auditor punch-list: what's solid, what's estimated, what's missing"
            >
              <FileSpreadsheet className="mr-2 h-4 w-4" />
              Verification pack
            </Button>
            {(sites?.length ?? 0) > 1 && (
              <select
                value={siteId}
                onChange={(e) => setSiteId(e.target.value)}
                className="rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                title="Which profile layer to view/edit — coverage is org-wide"
              >
                <option value="">All sites (org profile)</option>
                {(sites ?? []).map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            )}
            <Link href="/activities?add=1">
              <Button variant="outline">
                <PlusCircle className="mr-2 h-4 w-4" />
                Add manually
              </Button>
            </Link>
            <Link href="/ingest">
              <Button>
                <UploadCloud className="mr-2 h-4 w-4" />
                Upload data
              </Button>
            </Link>
          </div>
        </div>

        {/* Drop several files at once — each becomes its own upload session */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (e.dataTransfer.files?.length) uploadFiles(e.dataTransfer.files);
          }}
          onClick={() => !uploading && fileRef.current?.click()}
          className={cn(
            'flex cursor-pointer items-center justify-center gap-2 rounded-xl border-2 border-dashed px-4 py-3 text-sm transition-colors',
            uploading
              ? 'border-emerald-400 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300'
              : 'border-slate-300 text-slate-500 hover:border-emerald-400 dark:border-slate-700 dark:text-slate-400'
          )}
        >
          {uploading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Reading {uploading}…
            </>
          ) : (
            <>
              <UploadCloud className="h-4 w-4" />
              Drop one or many files here — invoices export, fuel cards, the CLIMATRIX template…
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
        </div>

        {data && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Card>
              <CardContent className="p-4">
                <p className="text-2xl font-semibold text-slate-900 dark:text-white">
                  {data.stats.relevant}
                  <span className="text-sm font-normal text-slate-400"> / {data.stats.total_categories}</span>
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">Categories relevant</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-2xl font-semibold text-slate-900 dark:text-white">
                  {data.stats.with_data}
                  <span className="text-sm font-normal text-slate-400">
                    {' '}/ {data.stats.relevant || '—'}
                  </span>
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">Relevant with data</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-2xl font-semibold text-amber-600 dark:text-amber-400">
                  {data.stats.open_questions}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">Open questions</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-2xl font-semibold text-slate-900 dark:text-white">
                  {data.stats.not_sure}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">Still undecided</p>
              </CardContent>
            </Card>
          </div>
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
            <Card className="border-amber-200 bg-amber-50/40 dark:border-amber-900 dark:bg-amber-950/20">
              <CardContent className="p-4">
                <p className="mb-2 text-sm font-semibold text-slate-900 dark:text-white">
                  Still missing — your chase list
                </p>
                <div className="flex flex-wrap gap-2">
                  {missing.map((c) => (
                    <button
                      key={c.code}
                      onClick={() => setDrawer(c)}
                      className="rounded-full border border-amber-300 bg-white px-3 py-1 text-xs font-medium text-amber-800 hover:bg-amber-100 dark:border-amber-800 dark:bg-transparent dark:text-amber-300"
                    >
                      {c.code} {c.name}
                      {c.profile?.data_owner && ` → ask ${c.profile.data_owner}`}
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          );
        })()}

        {recentSessions.length > 0 && (
          <Card>
            <CardContent className="p-0">
              <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3 dark:border-slate-800">
                <div>
                  <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
                    Recent uploads
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Every file lands here — answer its questions, review, commit.
                  </p>
                </div>
              </div>
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {recentSessions.map((s) => {
                  const meta = SESSION_STATUS[s.status] ?? {
                    label: s.status,
                    chip: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
                  };
                  return (
                    <Link
                      key={s.id}
                      href={`/ingest?session=${s.id}`}
                      className="flex items-center gap-3 px-4 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-900/50"
                    >
                      <FileSpreadsheet className="h-4 w-4 shrink-0 text-slate-400" />
                      <span className="min-w-0 flex-1 truncate text-sm text-slate-800 dark:text-slate-200">
                        {s.filename}
                      </span>
                      <span className="hidden text-xs text-slate-400 sm:inline">
                        {s.total_rows} rows
                        {s.open_question_count > 0 && ` · ${s.open_question_count} open questions`}
                      </span>
                      <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', meta.chip)}>
                        {meta.label}
                      </span>
                      <ChevronRight className="h-4 w-4 shrink-0 text-slate-300" />
                    </Link>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {setupMode && (
          <Card className="border-emerald-200 bg-emerald-50/50 dark:border-emerald-900 dark:bg-emerald-950/20">
            <CardContent className="flex items-start gap-3 p-4">
              <ArrowRight className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600 dark:text-emerald-400" />
              <div className="text-sm text-slate-700 dark:text-slate-300">
                <p className="font-medium text-slate-900 dark:text-white">
                  Start by mapping your inventory — two clicks per row.
                </p>
                <p className="mt-0.5 text-slate-500 dark:text-slate-400">
                  Mark each category as relevant or not. This becomes your reporting boundary: it
                  tells the parser what to expect and tells you what&apos;s still missing. You can
                  change any answer later.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {isLoading && (
          <div className="flex items-center justify-center gap-2 py-16 text-slate-400">
            <Loader2 className="h-5 w-5 animate-spin" />
            Loading your inventory map…
          </div>
        )}

        {data &&
          SCOPE_SECTIONS.map((section) => {
            const cats = data.categories.filter(section.match);
            if (cats.length === 0) return null;
            return (
              <Card key={section.title}>
                <CardContent className="p-0">
                  <div className="border-b border-slate-100 px-4 py-3 dark:border-slate-800">
                    <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
                      {section.title}
                    </h2>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{section.blurb}</p>
                  </div>
                  <div className="divide-y divide-slate-100 dark:divide-slate-800">
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
                </CardContent>
              </Card>
            );
          })}

        {data && (
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 px-1 text-xs text-slate-400 dark:text-slate-500">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-indigo-500" /> In ledger
            </span>
            {TIER_ORDER.map((tier) => (
              <span key={tier} className="flex items-center gap-1.5">
                <span className={cn('h-2 w-2 rounded-full', TIER_SEGMENT[tier].bar)} />
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
