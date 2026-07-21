'use client';

/**
 * AI Ingestion Funnel — the "drop any file" experience.
 *
 * Drop → Analyzing → Answer questions → Review grid → Commit. The client never
 * reshapes their data to fit the app: they upload whatever they have, confirm a
 * few targeted questions, and the rows land in the ledger.
 */

import { Fragment, useCallback, useEffect, useRef, useState, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { AppShell } from '@/components/layout';
import { Surface, PanelLabel, PageHead } from '@/components/canopy';
import { Button, ScopeBadge, toast } from '@/components/ui';
import { usePeriods, useSites } from '@/hooks/useEmissions';
import { useEntitlementFlags } from '@/components/layout/TeaserGate';
import { usePeriodStore } from '@/stores/period';
import {
  api,
  IngestionSessionDetail,
  StagedRow,
  ClarificationQuestion,
} from '@/lib/api';
import { cn, formatQty } from '@/lib/utils';
import { Loader2, Lock } from 'lucide-react';

const BAND: Record<string, { dot: string; text: string; label: string }> = {
  green: { dot: 'bg-cy-accent', text: 'text-cy-accent', label: 'High confidence' },
  amber: { dot: 'bg-cy-warn', text: 'text-cy-warn', label: 'Review suggested' },
  red: { dot: 'bg-error', text: 'text-error', label: 'Needs attention' },
};

// The data-quality ladder — the client-friendly view of what they can stand behind.
const TIER: Record<string, { label: string; chip: string; dot: string; blurb: string }> = {
  measured: {
    label: 'Measured',
    chip: 'bg-cy-accent-soft text-cy-accent',
    dot: 'bg-cy-accent',
    blurb: 'Primary / supplier data — highest quality',
  },
  calculated: {
    label: 'Calculated',
    chip: 'bg-info-50 text-info',
    dot: 'bg-cy-scope3',
    blurb: 'Real activity data × a standard factor',
  },
  estimated: {
    label: 'Estimated',
    chip: 'bg-cy-warn-soft text-cy-warn',
    dot: 'bg-cy-warn',
    blurb: 'From spend/proxy — an estimate you can upgrade',
  },
  gap: {
    label: 'Gap',
    chip: 'bg-cy-row text-cy-muted',
    dot: 'bg-cy-faint/40',
    blurb: 'Not yet measurable — needs the right data',
  },
};
const TIER_ORDER = ['measured', 'calculated', 'estimated', 'gap'] as const;

// Scope is the classification a validator (and the client) cares about most.
const SCOPE_BLURB: Record<number, string> = {
  1: 'Direct emissions',
  2: 'Purchased energy',
  3: 'Value chain',
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
  const { data: sites } = useSites();
  const [siteId, setSiteId] = useState<string>('');
  // Which scopes this plan can COMMIT via Smart Import (Starter = 1 & 2; Scope 3
  // is parsed and shown but commit-locked — the value-chain upsell).
  const { limits } = useEntitlementFlags();
  const allowedScopes = (limits?.smart_import_scopes as number[] | undefined) ?? [1, 2, 3];
  const searchParams = useSearchParams();
  const { selectedPeriodId } = usePeriodStore();
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
        if (!cancelled) {
          setSession(s);
          setSiteId(s.site_id ?? '');
        }
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
        let result = await api.ingestUpload(file, periodId || undefined, siteId || undefined);
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
    [periodId, siteId]
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
      const done = await api.commitIngestSession(session.id, periodId, siteId || undefined);
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
      <div className="mx-auto max-w-5xl space-y-4 py-2">
        {/* Header */}
        <div>
          <div className="mb-2 flex items-center justify-between">
            <Link
              href="/hub"
              className="inline-flex items-center gap-1 text-[12.5px] font-semibold text-cy-muted hover:text-cy-ink"
            >
              ← Measure
            </Link>
            {session && !busy && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setSession(null);
                  setAnswers({});
                }}
              >
                New upload
              </Button>
            )}
          </div>
          <PageHead
            title={session ? session.filename : 'Drop your data — we’ll do the rest'}
            subtitle={
              session
                ? undefined
                : 'Any spreadsheet, any layout. We read it, map every line to the right scope & category, ask only where we’re unsure, and show you everything before anything is saved.'
            }
          />
        </div>

        {/* The period is chosen once, in the top bar — pages only display it.
            The site is chosen here: it decides which country's factors apply. */}
        <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[12.5px] text-cy-muted">
          Reporting period:{' '}
          <span className="font-semibold text-cy-ink">
            {periods?.find((p) => p.id === periodId)?.name || '…'}
          </span>
          {(sites?.length ?? 0) > 0 && (
            <>
              <span aria-hidden="true">·</span>
              <span>Site:</span>
              <select
                value={siteId}
                onChange={(e) => setSiteId(e.target.value)}
                disabled={busy || isCommitted}
                className="cursor-pointer rounded-full border-0 bg-cy-row px-2.5 py-1 text-[12px] font-semibold text-cy-ink focus:outline-none focus:ring-2 focus:ring-cy-accent disabled:cursor-default disabled:opacity-60"
                title="Which site this upload belongs to — its grid region drives factor choice"
              >
                <option value="">No specific site</option>
                {(sites ?? []).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                    {s.grid_region ? ` (${s.grid_region})` : ''}
                  </option>
                ))}
              </select>
            </>
          )}
        </p>

        {/* Dropzone */}
        {!session && (
          <Surface
            padding="none"
            tint="soft"
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => fileRef.current?.click()}
            className={cn(
              'flex cursor-pointer flex-col items-center justify-center gap-2 px-6 py-16 text-center transition-shadow',
              dragOver && 'ring-2 ring-cy-accent'
            )}
          >
            {busy ? (
              <>
                <Loader2 className="h-7 w-7 animate-spin text-cy-accent" />
                <p className="text-[14px] font-bold text-cy-ink">
                  Reading your file and mapping every line…
                </p>
                <p className="text-[12px] text-cy-muted">This can take up to a minute for large workbooks.</p>
              </>
            ) : (
              <>
                <p className="text-[14px] font-bold text-cy-ink">
                  Drag a file here, or click to browse
                </p>
                <p className="text-[12.5px] text-cy-muted">
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
          </Surface>
        )}

        {/* Analyzing (worker is parsing the file) */}
        {isAnalyzing && (
          <Surface className="flex flex-col items-center gap-2 py-16 text-center">
            <Loader2 className="h-7 w-7 animate-spin text-cy-accent" />
            <p className="text-[14px] font-bold text-cy-ink">
              Reading {session?.filename} and mapping every line…
            </p>
            <p className="text-[12px] text-cy-muted">
              Large workbooks can take up to a minute — this keeps running even if you
              switch tabs.
            </p>
          </Surface>
        )}

        {/* Failed */}
        {session?.status === 'failed' && (
          <Surface>
            <p className="flex items-center gap-2 text-[13.5px] font-bold text-cy-ink">
              <span className="h-[7px] w-[7px] rounded-full bg-error" aria-hidden="true" />
              We couldn&apos;t process this file
            </p>
            <p className="mt-1 text-[12.5px] text-cy-muted">{session.error_message}</p>
            <Button variant="secondary" size="sm" className="mt-3" onClick={() => setSession(null)}>
              Try another file
            </Button>
          </Surface>
        )}

        {/* No data found — explain instead of a silent "0 rows read" */}
        {session && !isAnalyzing && session.total_rows === 0 && session.summary?.notice && (
          <Surface>
            <p className="flex items-center gap-2 text-[13.5px] font-bold text-cy-ink">
              <span className="h-[7px] w-[7px] rounded-full bg-cy-warn" aria-hidden="true" />
              No data rows to import from {session.filename}
            </p>
            <p className="mt-1 text-[12.5px] text-cy-muted">{session.summary.notice}</p>
            <Button variant="secondary" size="sm" className="mt-3" onClick={() => setSession(null)}>
              Upload a different file
            </Button>
          </Surface>
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
          <Surface tint="warn" padding="none" className="px-4 py-3">
            <p className="text-[12.5px] text-cy-warn">{session.summary.duplicate_warning}</p>
          </Surface>
        )}

        {/* Sheets skipped as non-data — nothing vanishes silently */}
        {session?.summary?.skipped_sheets && session.summary.skipped_sheets.length > 0 && (
          <p className="px-1 text-[12px] text-cy-muted">
            Skipped as non-data: {session.summary.skipped_sheets.join(', ')} — tell us if one of
            these holds data.
          </p>
        )}

        {/* Questions */}
        {session && openQuestions.length > 0 && !isCommitted && (
          <Surface>
            <PanelLabel>Needs you · {openQuestions.length}</PanelLabel>
            <p className="-mt-2 mb-3 text-[12.5px] text-cy-muted">
              We only ask where getting it wrong would change your numbers. Everything else is
              already mapped.
            </p>
            <div className="space-y-1">
              {openQuestions.map((q) => (
                <QuestionRow
                  key={q.id}
                  q={q}
                  value={answers[q.id] ?? ''}
                  onChange={(v) => setAnswers((a) => ({ ...a, [q.id]: v }))}
                />
              ))}
            </div>
            <Button className="mt-4" onClick={submitAnswers} disabled={busy}>
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              Submit answers
            </Button>
          </Surface>
        )}

        {/* Review grid */}
        {session && session.rows.length > 0 && session.status !== 'failed' && (
          <Surface>
            <div className="mb-3.5 flex flex-wrap items-center justify-between gap-2">
              <PanelLabel className="mb-0">Ready to review · {session.rows.length} rows</PanelLabel>
              {!isCommitted && (
                <div className="flex gap-2">
                  <Button variant="secondary" size="sm" onClick={approveAllReady} disabled={busy}>
                    Approve all mapped
                  </Button>
                  <Button size="sm" onClick={commit} disabled={busy || approvedCount === 0}>
                    {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                    Add {approvedCount || ''} to inventory
                  </Button>
                </div>
              )}
            </div>
            <ReviewGrid
              session={session}
              onPatch={patchRow}
              readOnly={isCommitted}
              allowedScopes={allowedScopes}
            />
          </Surface>
        )}

        {/* Committed */}
        {isCommitted && (
          <Surface className="flex flex-col items-center gap-2 py-8 text-center">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-cy-accent-soft text-[16px] font-bold text-cy-accent" aria-hidden="true">
              ✓
            </span>
            <p className="text-[15px] font-bold text-cy-ink">
              {session.committed_count} rows added to your inventory
            </p>
            <p className="text-[12.5px] text-cy-muted">
              They&apos;re now calculated and included in your dashboard totals.
            </p>
            <div className="mt-2 flex flex-wrap justify-center gap-2">
              <Link href="/hub">
                <Button>Back to Measure →</Button>
              </Link>
              <Link href="/dashboard">
                <Button variant="secondary">View dashboard</Button>
              </Link>
              <Button variant="secondary" onClick={() => setSession(null)}>
                Import another file
              </Button>
            </div>
          </Surface>
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
    <Surface>
      <div className="mb-2.5 flex flex-wrap items-baseline justify-between gap-2">
        <PanelLabel className="mb-0">Inventory quality</PanelLabel>
        <p className="text-[12.5px] text-cy-muted">
          <span className="font-bold text-cy-accent">{pct}%</span> you can stand behind
          (measured + calculated)
        </p>
      </div>
      {/* stacked bar */}
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-cy-row">
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
      <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-[11.5px]">
        {TIER_ORDER.map((t) => (
          <span key={t} className="flex items-center gap-1.5">
            <span className={cn('h-[7px] w-[7px] rounded-full', TIER[t].dot)} />
            <span className="font-semibold text-cy-ink">{TIER[t].label}</span>
            <span className="tabular-nums text-cy-muted">{byTier[t] || 0}</span>
            <span className="text-cy-faint">· {TIER[t].blurb}</span>
          </span>
        ))}
      </div>
    </Surface>
  );
}

function ScopeBreakdown({ byScope }: { byScope: Record<string, number> }) {
  const rows = [1, 2, 3].map((s) => ({ scope: s, count: byScope[`scope_${s}`] || 0 }));
  return (
    <Surface padding="none" className="flex flex-wrap items-center gap-x-5 gap-y-2 px-6 py-3.5">
      <span className="text-[11px] font-bold uppercase tracking-[0.08em] text-cy-faint">
        Scope split
      </span>
      {rows.map(({ scope, count }) => (
        <span key={scope} className="flex items-center gap-1.5 text-[12.5px]" title={SCOPE_BLURB[scope]}>
          <ScopeBadge scope={scope as 1 | 2 | 3} size="sm" />
          <span className="font-semibold tabular-nums text-cy-ink">{count}</span>
          <span className="hidden text-cy-faint sm:inline">{SCOPE_BLURB[scope]}</span>
        </span>
      ))}
    </Surface>
  );
}

function SummaryBar({ session }: { session: IngestionSessionDetail }) {
  const band = session.summary?.by_band ?? {};
  const security = session.summary?.security;
  return (
    <Surface padding="none" className="flex flex-wrap items-center gap-x-4 gap-y-1.5 px-6 py-3.5 text-[12.5px]">
      <span className="font-semibold text-cy-ink">{session.filename}</span>
      <span className="text-cy-faint" aria-hidden="true">·</span>
      <span className="tabular-nums text-cy-muted">{session.total_rows} rows read</span>
      {(['green', 'amber', 'red'] as const).map((b) =>
        band[b] ? (
          <span key={b} className="flex items-center gap-1.5">
            <span className={cn('h-[7px] w-[7px] rounded-full', BAND[b].dot)} />
            <span className={cn('tabular-nums font-semibold', BAND[b].text)}>{band[b]}</span>
          </span>
        ) : null
      )}
      {security && (security.formula_cells_sanitised > 0 || security.injection_flags > 0) && (
        <span className="ml-auto text-[11.5px] text-cy-faint">
          {security.formula_cells_sanitised + security.injection_flags} unsafe cells neutralised
        </span>
      )}
    </Surface>
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
    <div className="flex items-baseline gap-2.5 py-2.5">
      <span className="relative top-px h-2 w-2 shrink-0 rounded-full border-[1.5px] border-cy-warn" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-3">
          <p className="text-[13px] text-cy-ink">{q.question}</p>
          {q.applies_count > 1 && (
            <span className="whitespace-nowrap rounded-full bg-cy-warn-soft px-2 py-0.5 text-[11px] font-bold text-cy-warn">
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
            className="mt-2 w-full rounded-[10px] border-0 bg-cy-row px-3 py-2 text-[13px] font-semibold text-cy-ink placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent"
          />
        ) : choices.length <= 4 ? (
          // A few options — show them as pick-one pills.
          <div className="mt-2 flex flex-wrap gap-1.5">
            {choices.map((c) => (
              <button
                key={c.value || '__gap__'}
                onClick={() => onChange(c.value)}
                className={cn(
                  'cursor-pointer rounded-full px-3 py-1.5 text-[12px] font-semibold transition-colors',
                  selected?.value === c.value
                    ? 'bg-cy-accent text-white'
                    : 'bg-cy-row text-cy-muted hover:text-cy-ink'
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
            className="mt-2 w-full cursor-pointer rounded-[10px] border-0 bg-cy-row px-3 py-2 text-[13px] font-semibold text-cy-ink focus:outline-none focus:ring-2 focus:ring-cy-accent"
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
    </div>
  );
}

/** The full "why" behind one staged row — every assumption and, for derived
 *  quantities (flight km, hotel nights, tonne-km), the computation itself. */
function RowStory({ row }: { row: StagedRow }) {
  const d = row.provenance?.derivation;
  return (
    <div className="rounded-[10px] bg-cy-row px-4 py-3">
      {d && (
        <div className="mb-2 flex flex-wrap gap-1.5">
          {d.origin && d.destination && (
            <span className="rounded-full bg-cy-accent-soft px-2.5 py-0.5 text-[11px] font-bold text-cy-accent">
              {d.origin} → {d.destination}
            </span>
          )}
          {d.gcd_km != null && d.uplift != null && (
            <span className="rounded-full bg-cy-surface px-2.5 py-0.5 text-[11px] font-semibold text-cy-muted">
              {Math.round(d.gcd_km).toLocaleString()} km great-circle × {formatQty(d.uplift)} uplift
            </span>
          )}
          {d.round_trip != null && (
            <span className="rounded-full bg-cy-surface px-2.5 py-0.5 text-[11px] font-semibold text-cy-muted">
              {d.round_trip ? 'round trip ×2' : 'one-way'}
              {d.rt_assumed ? ' (assumed)' : ''}
            </span>
          )}
          {(d.travelers ?? 1) > 1 && (
            <span className="rounded-full bg-cy-surface px-2.5 py-0.5 text-[11px] font-semibold text-cy-muted">
              × {d.travelers} travelers
            </span>
          )}
          {d.cabin && (
            <span className="rounded-full bg-cy-surface px-2.5 py-0.5 text-[11px] font-semibold text-cy-muted">
              {d.cabin}
              {d.cabin_assumed ? ' (assumed)' : ''}
            </span>
          )}
          {d.stay_country && (
            <span className="rounded-full bg-cy-surface px-2.5 py-0.5 text-[11px] font-semibold text-cy-muted">
              stay: {d.stay_country}
            </span>
          )}
          {d.route_km != null && (
            <span className="rounded-full bg-cy-surface px-2.5 py-0.5 text-[11px] font-semibold text-cy-muted">
              route {Math.round(d.route_km).toLocaleString()} km ({d.mode})
            </span>
          )}
          {d.gazetteer && (
            <span className="rounded-full bg-cy-surface px-2.5 py-0.5 text-[11px] font-semibold text-cy-faint">
              {d.gazetteer}
            </span>
          )}
        </div>
      )}
      {row.reasons && row.reasons.length > 0 ? (
        <ul className="flex flex-col gap-1">
          {row.reasons.map((reason, i) => (
            <li key={i} className="flex gap-2 text-[12px] leading-relaxed text-cy-muted">
              <span aria-hidden="true" className="text-cy-faint">
                ·
              </span>
              {reason}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-[12px] text-cy-faint">No notes on this row.</p>
      )}
    </div>
  );
}

function ReviewGrid({
  session,
  onPatch,
  readOnly,
  allowedScopes = [1, 2, 3],
}: {
  session: IngestionSessionDetail;
  onPatch: (row: StagedRow, status: string) => void;
  readOnly: boolean;
  allowedScopes?: number[];
}) {
  const lockedCount = session.rows.filter(
    (r) => r.scope != null && !allowedScopes.includes(r.scope)
  ).length;
  const [openRow, setOpenRow] = useState<string | null>(null);
  const th = 'py-2 pr-3 text-left text-[10.5px] font-bold uppercase tracking-[0.07em] text-cy-faint';
  return (
    <div className="overflow-x-auto">
      {!readOnly && lockedCount > 0 && (
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-cy border border-cy-warn/25 bg-cy-warn-soft px-4 py-2.5">
          <span className="flex items-center gap-2 text-[12.5px] font-semibold text-cy-warn">
            <Lock className="h-4 w-4" strokeWidth={1.75} aria-hidden="true" />
            {lockedCount} value-chain (Scope 3) {lockedCount === 1 ? 'row is' : 'rows are'} parsed and ready — commit them on Professional
          </span>
          <Link href="/pricing">
            <Button size="sm">Upgrade to commit Scope 3</Button>
          </Link>
        </div>
      )}
      <table className="w-full border-collapse text-[13px]">
        <thead>
          <tr>
            <th className={th}> </th>
            <th className={th}>Source</th>
            <th className={th}>Mapped to</th>
            <th className={th}>Scope</th>
            <th className={th}>Quantity</th>
            <th className={th}>Confidence</th>
            <th className={th}>Data quality</th>
            {!readOnly && <th className={th}>Action</th>}
          </tr>
        </thead>
        <tbody>
          {session.rows.map((r) => {
            const b = BAND[r.band] ?? BAND.red;
            const isOpen = openRow === r.id;
            const hasStory =
              (r.reasons && r.reasons.length > 0) || !!r.provenance?.derivation;
            return (
              <Fragment key={r.id}>
              <tr
                className={cn(
                  'border-t border-cy-row align-top',
                  r.status === 'rejected' && 'opacity-40'
                )}
              >
                <td className="py-2.5 pr-3">
                  <span className={cn('inline-block h-2 w-2 rounded-full', b.dot)} title={b.label} />
                </td>
                <td className="max-w-[16rem] py-2.5 pr-3 text-cy-ink">
                  <div className="truncate font-semibold">{r.description || '—'}</div>
                  {hasStory && (
                    <button
                      type="button"
                      onClick={() => setOpenRow(isOpen ? null : r.id)}
                      aria-expanded={isOpen}
                      className="mt-0.5 block max-w-full cursor-pointer truncate text-left text-[11.5px] text-cy-faint hover:text-cy-ink"
                      title={r.reasons?.join(' · ')}
                    >
                      <span aria-hidden="true" className="mr-1 inline-block text-[9px]">
                        {isOpen ? '▾' : '▸'}
                      </span>
                      {r.provenance?.derivation
                        ? isOpen
                          ? 'How this number was derived'
                          : `Derived quantity — how? · ${r.reasons?.[0] ?? ''}`
                        : (r.reasons?.[0] ?? 'Why?')}
                    </button>
                  )}
                </td>
                <td className="py-2.5 pr-3">
                  {r.activity_key ? (
                    <>
                      <span className="font-mono text-[11.5px] text-cy-ink">
                        {r.activity_key}
                      </span>
                      {r.provenance?.factor_source && (
                        <div
                          className="mt-0.5 text-[11.5px] text-cy-faint"
                          title={r.provenance.method_label || undefined}
                        >
                          {r.provenance.factor_source}
                          {r.provenance.factor_region ? ` · ${r.provenance.factor_region}` : ''}
                          {r.provenance.factor_year ? ` · ${r.provenance.factor_year}` : ''}
                        </div>
                      )}
                    </>
                  ) : (
                    <span className="text-[11.5px] italic text-cy-warn">unmapped</span>
                  )}
                </td>
                <td className="py-2.5 pr-3">
                  {r.scope ? (
                    <div>
                      <ScopeBadge scope={r.scope as 1 | 2 | 3} size="sm" />
                      {r.category_code && CATEGORY_NAMES[r.category_code] && (
                        <div className="mt-0.5 text-[11.5px] text-cy-muted">
                          {r.category_code} · {CATEGORY_NAMES[r.category_code]}
                        </div>
                      )}
                    </div>
                  ) : (
                    <span className="text-[11.5px] text-cy-faint">—</span>
                  )}
                </td>
                <td className="py-2.5 pr-3 tabular-nums text-cy-muted">
                  {r.quantity != null ? `${formatQty(r.quantity)} ${r.unit ?? ''}` : '—'}
                </td>
                <td className="py-2.5 pr-3">
                  <span className={cn('text-[12px] font-semibold tabular-nums', b.text)}>
                    {Math.round(r.confidence * 100)}%
                  </span>
                  {r.commit_error && (
                    <div className="text-[11.5px] text-error" title={r.commit_error}>
                      not added
                    </div>
                  )}
                </td>
                <td className="py-2.5 pr-3">
                  {r.measurement_tier && TIER[r.measurement_tier] ? (
                    <span
                      className={cn(
                        'inline-flex items-center rounded-full px-2 py-[2.5px] text-[10px] font-semibold tracking-[0.03em]',
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
                    <span className="text-[11.5px] text-cy-faint">—</span>
                  )}
                </td>
                {!readOnly && (
                  <td className="py-2.5 pr-3">
                    {r.status === 'committed' ? (
                      <span className="text-[11.5px] font-semibold text-cy-accent">added</span>
                    ) : r.scope != null && !allowedScopes.includes(r.scope) ? (
                      // Plan-gated scope (Starter can't commit Scope 3): parsed
                      // and shown, but the commit is the Professional upsell.
                      <Link
                        href="/pricing"
                        title="Scope 3 is parsed and ready — upgrade to Professional to commit value-chain rows"
                        className="inline-flex items-center gap-1 rounded-full bg-cy-warn-soft px-2.5 py-1 text-[11px] font-semibold text-cy-warn hover:brightness-95"
                      >
                        <Lock className="h-3 w-3" strokeWidth={2} aria-hidden="true" />
                        Upgrade to commit
                      </Link>
                    ) : (
                      <div className="flex gap-1">
                        <button
                          onClick={() => onPatch(r, 'approved')}
                          className={cn(
                            'cursor-pointer rounded-full px-2.5 py-1 text-[11.5px] font-semibold transition-colors',
                            r.status === 'approved'
                              ? 'bg-cy-accent text-white'
                              : 'bg-cy-row text-cy-muted hover:text-cy-ink'
                          )}
                        >
                          Keep
                        </button>
                        <button
                          onClick={() => onPatch(r, 'rejected')}
                          className={cn(
                            'cursor-pointer rounded-full px-2.5 py-1 text-[11.5px] font-semibold transition-colors',
                            r.status === 'rejected'
                              ? 'bg-error text-white'
                              : 'bg-cy-row text-cy-muted hover:text-cy-ink'
                          )}
                        >
                          Drop
                        </button>
                      </div>
                    )}
                  </td>
                )}
              </tr>
              {isOpen && (
                <tr className="border-t border-cy-row/50">
                  <td />
                  <td colSpan={readOnly ? 6 : 7} className="pt-0 pb-3 pr-3">
                    <RowStory row={r} />
                  </td>
                </tr>
              )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
