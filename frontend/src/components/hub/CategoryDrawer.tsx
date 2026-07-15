'use client';

/**
 * Category drawer — one hub row, in depth (Layer 2 of the profile).
 * Who owns this data, what form it arrives in, the method question where it
 * matters, this category's open questions across every upload, and gap actions.
 */

import { useState } from 'react';
import Link from 'next/link';
import { Button, toast } from '@/components/ui';
import { useHubQuestions, useSaveHubProfile } from '@/hooks/useHub';
import { HubCategory, HubProfileEntry } from '@/lib/api';
import { X, Loader2 } from 'lucide-react';

const drawerLabel =
  'mb-1.5 block text-[11px] font-bold tracking-[0.06em] uppercase text-cy-faint';
const drawerField =
  'w-full rounded-[10px] border-0 bg-cy-row px-3 py-2.5 text-[13px] font-semibold text-cy-ink placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent';

const FORM_OPTIONS = [
  { value: 'meters', label: 'Meter readings (primary data)' },
  { value: 'invoices', label: 'Invoices / bills' },
  { value: 'spend', label: 'Spend from ERP (money only)' },
  { value: 'supplier_reports', label: 'Supplier / contractor reports' },
  { value: 'none_yet', label: 'No data source yet — needs chasing' },
];

export function CategoryDrawer({
  category,
  siteId,
  periodId,
  onClose,
}: {
  category: HubCategory;
  siteId?: string;
  periodId?: string;
  onClose: () => void;
}) {
  const save = useSaveHubProfile(siteId);
  const { data: questions, isLoading: questionsLoading } = useHubQuestions(
    category.code,
    periodId
  );

  // The parent passes key={category.code}, so state re-initializes per category.
  const [owner, setOwner] = useState(category.profile?.data_owner ?? '');
  const [form, setForm] = useState(category.profile?.expected_form ?? '');
  const [details, setDetails] = useState<Record<string, unknown>>(
    (category.profile?.details as Record<string, unknown>) ?? {}
  );

  const relevance = category.profile?.relevance ?? 'not_sure';
  const cov = category.coverage;

  const persist = (extra?: Partial<HubProfileEntry>) => {
    save.mutate(
      [
        {
          category_code: category.code,
          relevance: relevance === 'not_sure' ? 'relevant' : relevance,
          exclusion_reason: category.profile?.exclusion_reason ?? null,
          data_owner: owner || null,
          expected_form: form || null,
          details,
          ...extra,
        },
      ],
      {
        onSuccess: () => toast.success('Saved'),
        onError: (e) => toast.error(e instanceof Error ? e.message : 'Save failed'),
      }
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-neutral-950/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative flex h-full w-full max-w-md flex-col overflow-y-auto bg-background-elevated shadow-2xl animate-fade-in">
        <div className="flex items-start justify-between px-5 pb-2 pt-5">
          <div>
            <p className="font-mono text-[11px] text-cy-faint">{category.code}</p>
            <h2 className="text-[16px] font-bold tracking-[-0.01em] text-foreground">{category.name}</h2>
            <p className="text-[12.5px] text-cy-muted">{category.description}</p>
          </div>
          <button onClick={onClose} className="rounded-md p-1.5 text-cy-muted hover:bg-cy-row hover:text-foreground" aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 space-y-6 px-5 py-5">
          {/* Coverage snapshot */}
          <div className="rounded-[12px] bg-cy-row/50 p-4">
            <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.08em] text-cy-faint">Coverage</p>
            <div className="grid grid-cols-2 gap-2 text-[12.5px] text-cy-muted">
              <span>In ledger: <strong className="font-semibold text-foreground tabular-nums">{cov.committed_count}</strong></span>
              <span>CO2e: <strong className="font-semibold text-foreground tabular-nums">{(cov.total_co2e_kg / 1000).toFixed(1)} t</strong></span>
              <span>Staged: <strong className="font-semibold text-foreground tabular-nums">{cov.staged_count}</strong></span>
              <span>Open questions: <strong className="font-semibold text-foreground tabular-nums">{cov.open_questions}</strong></span>
            </div>
          </div>

          {/* Layer 2 — where the data comes from */}
          <div className="space-y-4">
            <div>
              <label className={drawerLabel}>Who owns this data?</label>
              <input
                value={owner}
                onChange={(e) => setOwner(e.target.value)}
                placeholder="e.g. Facilities, Finance, the travel agency…"
                className={drawerField}
              />
              <p className="mt-1 text-[11.5px] text-cy-faint">
                This becomes your chase list — who to ask when data is missing.
              </p>
            </div>
            <div>
              <label className={drawerLabel}>What form does it arrive in?</label>
              <select
                value={form}
                onChange={(e) => setForm(e.target.value)}
                className={drawerField}
              >
                <option value="">Not declared yet</option>
                {FORM_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
              <p className="mt-1 text-[11.5px] text-cy-faint">
                Sets the honest quality expectation (meters → measured, spend → estimated).
              </p>
            </div>

            {/* Method questions only where they matter */}
            {category.code === '2.1' && (
              <div>
                <label className={drawerLabel}>Scope 2 method</label>
                <select
                  value={(details.scope2_method as string) ?? ''}
                  onChange={(e) => setDetails({ ...details, scope2_method: e.target.value })}
                  className={drawerField}
                >
                  <option value="">Not decided</option>
                  <option value="location">Location-based (grid average)</option>
                  <option value="market">Market-based (supplier factors / RECs / PPAs)</option>
                  <option value="both">Both (dual reporting)</option>
                </select>
              </div>
            )}
            {category.code === '1.3' && (
              <div>
                <label className={drawerLabel}>Which refrigerant gases (if known)?</label>
                <input
                  value={(details.refrigerant_gases as string) ?? ''}
                  onChange={(e) => setDetails({ ...details, refrigerant_gases: e.target.value })}
                  placeholder="e.g. R-410A, R-134a — GWP differs hugely"
                  className={drawerField}
                />
              </div>
            )}

            <Button onClick={() => persist()} disabled={save.isPending} className="w-full">
              {save.isPending ? 'Saving…' : 'Save'}
            </Button>
          </div>

          {/* Open questions across all uploads */}
          <div>
            <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.08em] text-cy-faint">
              Open questions
            </p>
            {questionsLoading && (
              <p className="flex items-center gap-2 text-[12.5px] text-cy-muted">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading…
              </p>
            )}
            {!questionsLoading && (questions?.length ?? 0) === 0 && (
              <p className="text-[12.5px] text-cy-muted">None — nothing blocked here.</p>
            )}
            <div className="space-y-1.5">
              {(questions ?? []).map((q) => (
                <Link
                  key={q.id}
                  href={`/ingest?session=${q.session_id}`}
                  className="block rounded-[12px] bg-cy-warn-soft/60 p-3 hover:bg-cy-warn-soft"
                >
                  <p className="text-[13px] text-foreground">{q.question}</p>
                  <p className="mt-1 text-[11.5px] text-cy-muted">
                    {q.filename}
                    {q.applies_count > 1 && ` · one answer fixes ${q.applies_count} rows`}
                  </p>
                </Link>
              ))}
            </div>
          </div>
        </div>

        <div className="sticky bottom-0 bg-background-elevated px-5 py-4 shadow-[0_-1px_0_var(--cy-row)]">
          <Link href="/ingest">
            <Button variant="secondary" className="w-full">
              Upload data for this category
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
