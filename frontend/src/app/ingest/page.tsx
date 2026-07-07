'use client';

/**
 * AI Ingestion Funnel — the "drop any file" experience.
 *
 * Drop → Analyzing → Answer questions → Review grid → Commit. The client never
 * reshapes their data to fit the app: they upload whatever they have, confirm a
 * few targeted questions, and the rows land in the ledger.
 */

import { useCallback, useEffect, useRef, useState, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { AppShell } from '@/components/layout';
import { Card, CardContent, Button, toast } from '@/components/ui';
import { usePeriods } from '@/hooks/useEmissions';
import { usePeriodStore } from '@/stores/period';
import {
  api,
  IngestionSessionDetail,
  StagedRow,
  ClarificationQuestion,
} from '@/lib/api';
import { cn } from '@/lib/utils';
import {
  UploadCloud,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  FileSpreadsheet,
} from 'lucide-react';

const BAND: Record<string, { dot: string; text: string; label: string }> = {
  green: { dot: 'bg-emerald-500', text: 'text-emerald-600 dark:text-emerald-400', label: 'High confidence' },
  amber: { dot: 'bg-amber-500', text: 'text-amber-600 dark:text-amber-400', label: 'Review suggested' },
  red: { dot: 'bg-red-500', text: 'text-red-600 dark:text-red-400', label: 'Needs attention' },
};

// The data-quality ladder — the client-friendly view of what they can stand behind.
const TIER: Record<string, { label: string; chip: string; dot: string; blurb: string }> = {
  measured: {
    label: 'Measured',
    chip: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300',
    dot: 'bg-emerald-500',
    blurb: 'Primary / supplier data — highest quality',
  },
  calculated: {
    label: 'Calculated',
    chip: 'bg-teal-100 text-teal-700 dark:bg-teal-950/50 dark:text-teal-300',
    dot: 'bg-teal-500',
    blurb: 'Real activity data × a standard factor',
  },
  estimated: {
    label: 'Estimated',
    chip: 'bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300',
    dot: 'bg-amber-500',
    blurb: 'From spend/proxy — an estimate you can upgrade',
  },
  gap: {
    label: 'Gap',
    chip: 'bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
    dot: 'bg-slate-400',
    blurb: 'Not yet measurable — needs the right data',
  },
};
const TIER_ORDER = ['measured', 'calculated', 'estimated', 'gap'] as const;

// Scope is the classification a validator (and the client) cares about most —
// keep it unmistakable and colour-coded throughout.
const SCOPE: Record<number, { label: string; blurb: string; chip: string; dot: string }> = {
  1: {
    label: 'Scope 1',
    blurb: 'Direct emissions',
    chip: 'bg-rose-100 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300',
    dot: 'bg-rose-500',
  },
  2: {
    label: 'Scope 2',
    blurb: 'Purchased energy',
    chip: 'bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300',
    dot: 'bg-amber-500',
  },
  3: {
    label: 'Scope 3',
    blurb: 'Value chain',
    chip: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300',
    dot: 'bg-emerald-500',
  },
};

const CATEGORY_NAMES: Record<string, string> = {
  '1.1': 'Stationary combustion',
  '1.2': 'Mobile combustion',
  '1.3': 'Fugitive emissions',
  '2': 'Purchased electricity',
  '2.1': 'Purchased electricity',
  '2.2': 'Purchased heat & steam',
  '2.3': 'Purchased cooling',
  '3.1': 'Purchased goods & services',
  '3.2': 'Capital goods',
  '3.3': 'Fuel & energy (WTT/T&D)',
  '3.4': 'Upstream transport',
  '3.5': 'Waste',
  '3.6': 'Business travel',
  '3.7': 'Employee commuting',
  '3.8': 'Upstream leased assets',
  '3.9': 'Downstream transport',
  '3.10': 'Processing of sold products',
  '3.11': 'Use of sold products',
  '3.12': 'End-of-life treatment',
  '3.13': 'Downstream leased assets',
  '3.14': 'Franchises',
  '3.15': 'Investments',
};


function IngestContent() {
  const { data: periods } = usePeriods();
  const searchParams = useSearchParams();
  const { selectedPeriodId, setSelectedPeriodId } = usePeriodStore();
  const [session, setSession] = useState<IngestionSessionDetail | null>(null);
  const [busy, setBusy] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const fileRef = useRef<HTMLInputElement>(null);

  // Deep link from the Data Hub's "Recent uploads": /ingest?session=<id>
  const linkedSessionId = searchParams.get('session');
  useEffect(() => {
    if (!linkedSessionId) return;
    let cancelled = false;
    api
      .getIngestSession(linkedSessionId)
      .then((s) => {
        if (!cancelled) setSession(s);
      })
      .catch(() => {
        if (!cancelled) toast.error('Could not load that upload session.');
      });
    return () => {
      cancelled = true;
    };
  }, [linkedSessionId]);

  // Only trust the saved period if it actually belongs to the current org's list —
  // a stale localStorage value from another session/org would 404 on upload.
  const periodId =
    periods?.find((p) => p.id === selectedPeriodId)?.id ?? periods?.[0]?.id;

  const handleFile = useCallback(
    async (file: File) => {
      setBusy(true);
      setSession(null);
      try {
        let result = await api.ingestUpload(file, periodId || undefined);
        setSession(result);
        // In production the parse runs on the worker — poll until it's ready.
        let tries = 0;
        while (
          (result.status === 'analyzing' || result.status === 'uploaded') &&
          tries < 150
        ) {
          await new Promise((r) => setTimeout(r, 2000));
          result = await api.getIngestSession(result.id);
          setSession(result);
          tries += 1;
        }
        if (result.status === 'failed') {
          toast.error(result.error_message || 'We could not read that file.');
        }
      } catch (e) {
        toast.error(e instanceof Error ? e.message : 'Upload failed');
      } finally {
        setBusy(false);
      }
    },
    [periodId]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const openQuestions = session?.questions.filter((q) => !q.answered) ?? [];

  const submitAnswers = async () => {
    if (!session) return;
    // '__unanswered__' is the dropdown placeholder — treat it as "not answered".
    const payload = openQuestions
      .map((q) => ({ question_id: q.id, answer: (answers[q.id] ?? '').trim() }))
      .filter((a) => a.answer.length > 0 && a.answer !== '__unanswered__');
    if (payload.length === 0) {
      toast.error('Answer at least one question first.');
      return;
    }
    setBusy(true);
    try {
      const updated = await api.answerIngestQuestions(session.id, payload);
      setSession(updated);
      setAnswers({});
      toast.success('Thanks — re-checked those rows.');
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Could not save answers');
    } finally {
      setBusy(false);
    }
  };

  const patchRow = async (row: StagedRow, status: string) => {
    if (!session) return;
    try {
      await api.patchIngestRow(session.id, row.id, { status });
      setSession({
        ...session,
        rows: session.rows.map((r) => (r.id === row.id ? { ...r, status: status as StagedRow['status'] } : r)),
      });
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Update failed');
    }
  };

  const approveAllReady = async () => {
    if (!session) return;
    const targets = session.rows.filter((r) => ['ready', 'needs_review'].includes(r.status));
    setBusy(true);
    try {
      await Promise.all(
        targets.map((r) => api.patchIngestRow(session.id, r.id, { status: 'approved' }))
      );
      setSession({
        ...session,
        rows: session.rows.map((r) =>
          targets.some((t) => t.id === r.id) ? { ...r, status: 'approved' } : r
        ),
      });
      toast.success(`Approved ${targets.length} rows`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Bulk approve failed');
    } finally {
      setBusy(false);
    }
  };

  const commit = async () => {
    if (!session) return;
    if (!periodId) {
      toast.error('Choose a reporting period first.');
      return;
    }
    setBusy(true);
    try {
      const done = await api.commitIngestSession(session.id, periodId);
      setSession(done);
      toast.success(`${done.committed_count} rows added to your inventory`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Commit failed');
    } finally {
      setBusy(false);
    }
  };

  const approvedCount = session?.rows.filter((r) => r.status === 'approved').length ?? 0;
  const isCommitted = session?.status === 'committed';
  const isAnalyzing =
    session?.status === 'analyzing' || session?.status === 'uploaded';

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-6 py-2">
        {/* Header */}
        <div>
          <Link
            href="/hub"
            className="mb-1 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
          >
            ← Data Hub
          </Link>
          <h1 className="flex items-center gap-2 text-2xl font-semibold text-slate-900 dark:text-white">
            <Sparkles className="h-6 w-6 text-emerald-500" />
            Drop your data — we&apos;ll do the rest
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Any spreadsheet, any layout. We read it, map every line to the right scope &amp;
            category, ask only where we&apos;re unsure, and show you everything before anything
            is saved.
          </p>
        </div>

        {/* Period selector */}
        <div className="flex items-center gap-3 text-sm">
          <span className="text-slate-500 dark:text-slate-400">Reporting period:</span>
          <select
            value={periodId || ''}
            onChange={(e) => setSelectedPeriodId(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-white"
          >
            {(periods ?? []).map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {/* Dropzone */}
        {!session && (
          <Card>
            <CardContent className="p-0">
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={onDrop}
                onClick={() => fileRef.current?.click()}
                className={cn(
                  'flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-16 text-center transition-colors',
                  dragOver
                    ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-950/30'
                    : 'border-slate-300 hover:border-emerald-400 dark:border-slate-700'
                )}
              >
                {busy ? (
                  <>
                    <Loader2 className="h-10 w-10 animate-spin text-emerald-500" />
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-200">
                      Reading your file and mapping every line…
                    </p>
                    <p className="text-xs text-slate-400">This can take up to a minute for large workbooks.</p>
                  </>
                ) : (
                  <>
                    <UploadCloud className="h-10 w-10 text-emerald-500" />
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-200">
                      Drag a file here, or click to browse
                    </p>
                    <p className="text-xs text-slate-400">
                      CSV, Excel (.xlsx/.xls), or PDF — up to 50&nbsp;MB
                    </p>
                  </>
                )}
                <input
                  ref={fileRef}
                  type="file"
                  className="hidden"
                  accept=".csv,.tsv,.xlsx,.xls,.pdf,.png,.jpg,.jpeg,.txt"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) handleFile(f);
                  }}
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Analyzing (worker is parsing the file) */}
        {isAnalyzing && (
          <Card>
            <CardContent className="flex flex-col items-center gap-3 py-16 text-center">
              <Loader2 className="h-10 w-10 animate-spin text-emerald-500" />
              <p className="text-sm font-medium text-slate-700 dark:text-slate-200">
                Reading {session?.filename} and mapping every line…
              </p>
              <p className="text-xs text-slate-400">
                Large workbooks can take up to a minute — this keeps running even if you
                switch tabs.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Failed */}
        {session?.status === 'failed' && (
          <Card>
            <CardContent className="flex items-start gap-3 py-6">
              <AlertTriangle className="mt-0.5 h-5 w-5 text-red-500" />
              <div>
                <p className="font-medium text-slate-800 dark:text-slate-100">
                  We couldn&apos;t process this file
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400">{session.error_message}</p>
                <Button variant="secondary" className="mt-3" onClick={() => setSession(null)}>
                  Try another file
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* No data found — explain instead of a silent "0 rows read" */}
        {session && !isAnalyzing && session.total_rows === 0 && session.summary?.notice && (
          <Card>
            <CardContent className="flex items-start gap-3 py-6">
              <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-500" />
              <div>
                <p className="font-medium text-slate-800 dark:text-slate-100">
                  No data rows to import from {session.filename}
                </p>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                  {session.summary.notice}
                </p>
                <Button variant="secondary" className="mt-3" onClick={() => setSession(null)}>
                  Upload a different file
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Summary bar */}
        {session &&
          session.status !== 'failed' &&
          !isAnalyzing &&
          session.total_rows > 0 && <SummaryBar session={session} />}

        {/* Inventory quality — measure / estimate / gap (the spine) */}
        {session &&
          session.status !== 'failed' &&
          !isAnalyzing &&
          session.total_rows > 0 &&
          session.summary?.by_tier && <InventoryQuality byTier={session.summary.by_tier} />}

        {/* Scope split — the classification a validator cares about most */}
        {session &&
          session.status !== 'failed' &&
          !isAnalyzing &&
          session.total_rows > 0 &&
          session.summary?.by_scope && <ScopeBreakdown byScope={session.summary.by_scope} />}

        {/* Duplicate-import warning */}
        {session?.summary?.duplicate_warning && !isCommitted && (
          <div className="flex items-start gap-2 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{session.summary.duplicate_warning}</span>
          </div>
        )}

        {/* Questions */}
        {session && openQuestions.length > 0 && !isCommitted && (
          <Card>
            <CardContent className="space-y-4 py-5">
              <div className="flex items-center gap-2">
                <HelpCircle className="h-5 w-5 text-amber-500" />
                <h2 className="font-semibold text-slate-800 dark:text-slate-100">
                  A few quick questions ({openQuestions.length})
                </h2>
              </div>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                We only ask where getting it wrong would change your numbers. Everything else is
                already mapped.
              </p>
              <div className="space-y-3">
                {openQuestions.map((q) => (
                  <QuestionRow
                    key={q.id}
                    q={q}
                    value={answers[q.id] ?? ''}
                    onChange={(v) => setAnswers((a) => ({ ...a, [q.id]: v }))}
                  />
                ))}
              </div>
              <Button onClick={submitAnswers} disabled={busy}>
                {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Submit answers
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Review grid */}
        {session && session.rows.length > 0 && session.status !== 'failed' && (
          <Card>
            <CardContent className="py-5">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-semibold text-slate-800 dark:text-slate-100">
                  Review {session.rows.length} rows
                </h2>
                {!isCommitted && (
                  <div className="flex gap-2">
                    <Button variant="secondary" size="sm" onClick={approveAllReady} disabled={busy}>
                      Approve all mapped
                    </Button>
                    <Button size="sm" onClick={commit} disabled={busy || approvedCount === 0}>
                      {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                      Add {approvedCount || ''} to inventory
                    </Button>
                  </div>
                )}
              </div>
              <ReviewGrid session={session} onPatch={patchRow} readOnly={isCommitted} />
            </CardContent>
          </Card>
        )}

        {/* Committed */}
        {isCommitted && (
          <Card>
            <CardContent className="flex flex-col items-center gap-3 py-8 text-center">
              <CheckCircle2 className="h-10 w-10 text-emerald-500" />
              <p className="text-lg font-semibold text-slate-800 dark:text-slate-100">
                {session.committed_count} rows added to your inventory
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                They&apos;re now calculated and included in your dashboard totals.
              </p>
              <div className="mt-2 flex gap-3">
                <Link href="/hub">
                  <Button>
                    Back to Data Hub <ArrowRight className="ml-1 h-4 w-4" />
                  </Button>
                </Link>
                <Link href="/dashboard">
                  <Button variant="secondary">View dashboard</Button>
                </Link>
                <Button variant="secondary" onClick={() => setSession(null)}>
                  Import another file
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AppShell>
  );
}

export default function IngestPage() {
  return (
    <Suspense fallback={null}>
      <IngestContent />
    </Suspense>
  );
}

function InventoryQuality({
  byTier,
}: {
  byTier: { measured: number; calculated: number; estimated: number; gap: number };
}) {
  const total = TIER_ORDER.reduce((n, t) => n + (byTier[t] || 0), 0) || 1;
  const solid = (byTier.measured || 0) + (byTier.calculated || 0);
  const pct = Math.round((solid / total) * 100);
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/50">
      <div className="mb-2 flex items-baseline justify-between">
        <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
          Inventory quality
        </p>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          <span className="font-semibold text-emerald-600 dark:text-emerald-400">{pct}%</span> you
          can stand behind (measured + calculated)
        </p>
      </div>
      {/* stacked bar */}
      <div className="flex h-2.5 w-full overflow-hidden rounded-full">
        {TIER_ORDER.map((t) =>
          byTier[t] ? (
            <div
              key={t}
              className={cn('h-full', TIER[t].dot)}
              style={{ width: `${((byTier[t] || 0) / total) * 100}%` }}
              title={`${TIER[t].label}: ${byTier[t]}`}
            />
          ) : null
        )}
      </div>
      <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs">
        {TIER_ORDER.map((t) => (
          <span key={t} className="flex items-center gap-1.5">
            <span className={cn('h-2 w-2 rounded-full', TIER[t].dot)} />
            <span className="font-medium text-slate-700 dark:text-slate-200">{TIER[t].label}</span>
            <span className="text-slate-400">{byTier[t] || 0}</span>
            <span className="text-slate-400 dark:text-slate-500">· {TIER[t].blurb}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

function ScopeBreakdown({ byScope }: { byScope: Record<string, number> }) {
  const rows = [1, 2, 3].map((s) => ({ scope: s, count: byScope[`scope_${s}`] || 0 }));
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900/50">
      <span className="text-sm font-semibold text-slate-800 dark:text-slate-100">Scope split</span>
      {rows.map(({ scope, count }) => (
        <span
          key={scope}
          className={cn(
            'inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-sm',
            SCOPE[scope].chip
          )}
          title={SCOPE[scope].blurb}
        >
          <span className="font-semibold">{SCOPE[scope].label}</span>
          <span className="opacity-70">·</span>
          <span>{count}</span>
          <span className="hidden text-xs opacity-70 sm:inline">{SCOPE[scope].blurb}</span>
        </span>
      ))}
    </div>
  );
}

function SummaryBar({ session }: { session: IngestionSessionDetail }) {
  const band = session.summary?.by_band ?? {};
  const security = session.summary?.security;
  return (
    <div className="flex flex-wrap items-center gap-4 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-900/50">
      <span className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
        <FileSpreadsheet className="h-4 w-4" /> {session.filename}
      </span>
      <span className="text-slate-400">·</span>
      <span className="text-slate-600 dark:text-slate-300">{session.total_rows} rows read</span>
      {(['green', 'amber', 'red'] as const).map((b) =>
        band[b] ? (
          <span key={b} className="flex items-center gap-1.5">
            <span className={cn('h-2 w-2 rounded-full', BAND[b].dot)} />
            <span className={BAND[b].text}>{band[b]}</span>
          </span>
        ) : null
      )}
      {security && (security.formula_cells_sanitised > 0 || security.injection_flags > 0) && (
        <span className="ml-auto flex items-center gap-1.5 text-xs text-slate-500">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
          {security.formula_cells_sanitised + security.injection_flags} unsafe cells neutralised
        </span>
      )}
    </div>
  );
}

function QuestionRow({
  q,
  value,
  onChange,
}: {
  q: ClarificationQuestion;
  value: string;
  onChange: (v: string) => void;
}) {
  const choices = q.choices ?? [];
  const selected = choices.find((c) => c.value === value);
  return (
    <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
      <div className="mb-2 flex items-start justify-between gap-3">
        <p className="text-sm text-slate-700 dark:text-slate-200">{q.question}</p>
        {q.applies_count > 1 && (
          <span className="whitespace-nowrap rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-medium text-amber-700 dark:bg-amber-500/15 dark:text-amber-300">
            {q.applies_count} rows
          </span>
        )}
      </div>
      {choices.length === 0 ? (
        // No preset options — free text as a last resort.
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Type your answer…"
          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-white"
        />
      ) : choices.length <= 4 ? (
        // A few options — show them as pick-one buttons.
        <div className="flex flex-wrap gap-2">
          {choices.map((c) => (
            <button
              key={c.value || '__gap__'}
              onClick={() => onChange(c.value)}
              className={cn(
                'rounded-full border px-3 py-1 text-xs transition-colors',
                selected?.value === c.value
                  ? 'border-emerald-500 bg-emerald-500 text-white'
                  : 'border-slate-300 text-slate-600 hover:border-emerald-400 dark:border-slate-700 dark:text-slate-300'
              )}
            >
              {c.label}
            </button>
          ))}
        </div>
      ) : (
        // Many options — a dropdown keeps it compact.
        <select
          value={value || '__unanswered__'}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-white"
        >
          <option value="__unanswered__">Choose the right activity…</option>
          {choices.map((c) => (
            <option key={c.value || '__gap__'} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}

function ReviewGrid({
  session,
  onPatch,
  readOnly,
}: {
  session: IngestionSessionDetail;
  onPatch: (row: StagedRow, status: string) => void;
  readOnly: boolean;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-400 dark:border-slate-800">
            <th className="py-2 pr-3 font-medium"> </th>
            <th className="py-2 pr-3 font-medium">Source</th>
            <th className="py-2 pr-3 font-medium">Mapped to</th>
            <th className="py-2 pr-3 font-medium">Scope</th>
            <th className="py-2 pr-3 font-medium">Quantity</th>
            <th className="py-2 pr-3 font-medium">Confidence</th>
            <th className="py-2 pr-3 font-medium">Data quality</th>
            {!readOnly && <th className="py-2 pr-3 font-medium">Action</th>}
          </tr>
        </thead>
        <tbody>
          {session.rows.map((r) => {
            const b = BAND[r.band] ?? BAND.red;
            return (
              <tr
                key={r.id}
                className={cn(
                  'border-b border-slate-100 align-top dark:border-slate-800/60',
                  r.status === 'rejected' && 'opacity-40'
                )}
              >
                <td className="py-2 pr-3">
                  <span className={cn('inline-block h-2.5 w-2.5 rounded-full', b.dot)} title={b.label} />
                </td>
                <td className="max-w-[16rem] py-2 pr-3 text-slate-600 dark:text-slate-300">
                  <div className="truncate">{r.description || '—'}</div>
                  {r.reasons && r.reasons.length > 0 && (
                    <div className="mt-0.5 truncate text-xs text-slate-400" title={r.reasons.join(' · ')}>
                      {r.reasons[0]}
                    </div>
                  )}
                </td>
                <td className="py-2 pr-3">
                  {r.activity_key ? (
                    <>
                      <span className="font-mono text-xs text-slate-700 dark:text-slate-200">
                        {r.activity_key}
                      </span>
                      {r.provenance?.factor_source && (
                        <div
                          className="mt-0.5 text-xs text-slate-400"
                          title={r.provenance.method_label || undefined}
                        >
                          {r.provenance.factor_source}
                          {r.provenance.factor_region ? ` · ${r.provenance.factor_region}` : ''}
                          {r.provenance.factor_year ? ` · ${r.provenance.factor_year}` : ''}
                        </div>
                      )}
                    </>
                  ) : (
                    <span className="text-xs italic text-amber-500">unmapped</span>
                  )}
                </td>
                <td className="py-2 pr-3">
                  {r.scope && SCOPE[r.scope] ? (
                    <div>
                      <span
                        className={cn(
                          'inline-flex items-center rounded px-1.5 py-0.5 text-xs font-semibold',
                          SCOPE[r.scope].chip
                        )}
                      >
                        {SCOPE[r.scope].label}
                      </span>
                      {r.category_code && CATEGORY_NAMES[r.category_code] && (
                        <div className="mt-0.5 text-xs text-slate-500">
                          {r.category_code} · {CATEGORY_NAMES[r.category_code]}
                        </div>
                      )}
                    </div>
                  ) : (
                    <span className="text-xs text-slate-400">—</span>
                  )}
                </td>
                <td className="py-2 pr-3 text-slate-600 dark:text-slate-300">
                  {r.quantity != null ? `${r.quantity} ${r.unit ?? ''}` : '—'}
                </td>
                <td className="py-2 pr-3">
                  <span className={cn('text-xs font-medium', b.text)}>
                    {Math.round(r.confidence * 100)}%
                  </span>
                  {r.commit_error && (
                    <div className="text-xs text-red-500" title={r.commit_error}>
                      not added
                    </div>
                  )}
                </td>
                <td className="py-2 pr-3">
                  {r.measurement_tier && TIER[r.measurement_tier] ? (
                    <span
                      className={cn(
                        'inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium',
                        TIER[r.measurement_tier].chip
                      )}
                      title={
                        `${TIER[r.measurement_tier].blurb}` +
                        (r.pcaf_data_quality ? ` · PCAF ${r.pcaf_data_quality}/5` : '')
                      }
                    >
                      {TIER[r.measurement_tier].label}
                    </span>
                  ) : (
                    <span className="text-xs text-slate-400">—</span>
                  )}
                </td>
                {!readOnly && (
                  <td className="py-2 pr-3">
                    {r.status === 'committed' ? (
                      <span className="text-xs text-emerald-500">added</span>
                    ) : (
                      <div className="flex gap-1">
                        <button
                          onClick={() => onPatch(r, 'approved')}
                          className={cn(
                            'rounded px-2 py-0.5 text-xs',
                            r.status === 'approved'
                              ? 'bg-emerald-500 text-white'
                              : 'border border-slate-300 text-slate-500 hover:border-emerald-400 dark:border-slate-700'
                          )}
                        >
                          Keep
                        </button>
                        <button
                          onClick={() => onPatch(r, 'rejected')}
                          className={cn(
                            'rounded px-2 py-0.5 text-xs',
                            r.status === 'rejected'
                              ? 'bg-red-500 text-white'
                              : 'border border-slate-300 text-slate-500 hover:border-red-400 dark:border-slate-700'
                          )}
                        >
                          Drop
                        </button>
                      </div>
                    )}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
