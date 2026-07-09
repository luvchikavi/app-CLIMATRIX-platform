'use client';

/**
 * PUBLIC CBAM supplier data form (magic link, no auth).
 *
 * A non-EU installation operator opens this link from the data-request
 * email and submits actual specific embedded emissions (SEE) per CN code.
 * Submitted values become "actual (supplier)" intensities in the
 * importer's imports register and annual declaration — replacing penalised
 * default values. Styled like the other public pages (/try, /cbam-check).
 */

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api, PublicApiError } from '@/lib/api';
import type { CBAMSupplierRequestContext, CBAMSupplierEmissionRowInput } from '@/lib/types';
import {
  Leaf,
  Loader2,
  Plus,
  Trash2,
  Factory,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Info,
} from 'lucide-react';

interface FormRow {
  cnCode: string;
  directSee: string;
  indirectSee: string;
  periodStart: string;
  periodEnd: string;
  verifierName: string;
  verified: boolean;
}

const EMPTY_ROW: FormRow = {
  cnCode: '',
  directSee: '',
  indirectSee: '',
  periodStart: '',
  periodEnd: '',
  verifierName: '',
  verified: false,
};

type LinkState = 'loading' | 'ok' | 'not_found' | 'expired' | 'error';

const inputClass =
  'w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-white placeholder:text-slate-600';

export default function SupplierDataPage() {
  const params = useParams<{ token: string }>();
  const token = params?.token ?? '';

  const [linkState, setLinkState] = useState<LinkState>('loading');
  const [context, setContext] = useState<CBAMSupplierRequestContext | null>(null);
  const [rows, setRows] = useState<FormRow[]>([{ ...EMPTY_ROW }]);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const ctx = await api.getCBAMSupplierRequest(token);
        if (cancelled) return;
        setContext(ctx);
        setLinkState('ok');
        if (ctx.rows.length > 0) {
          // Revision: prefill with the previously submitted rows
          setRows(
            ctx.rows.map((r) => ({
              cnCode: r.cn_code,
              directSee: String(r.direct_see_tco2e_per_t),
              indirectSee: r.indirect_see_tco2e_per_t != null ? String(r.indirect_see_tco2e_per_t) : '',
              periodStart: r.production_period_start,
              periodEnd: r.production_period_end,
              verifierName: r.verifier_name ?? '',
              verified: r.verified,
            }))
          );
        }
      } catch (e) {
        if (cancelled) return;
        if (e instanceof PublicApiError && e.status === 404) setLinkState('not_found');
        else if (e instanceof PublicApiError && e.status === 410) setLinkState('expired');
        else setLinkState('error');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const setRow = (i: number, patch: Partial<FormRow>) =>
    setRows((prev) => prev.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));

  const validate = (): string | null => {
    const filled = rows.filter((r) => r.cnCode.trim() !== '' || r.directSee !== '');
    if (filled.length === 0) return 'Add at least one product row.';
    for (const r of filled) {
      if (r.cnCode.trim().length < 4) return 'Each row needs a CN code (at least 4 digits).';
      const direct = Number(r.directSee);
      if (r.directSee === '' || Number.isNaN(direct) || direct < 0)
        return `Row CN ${r.cnCode}: direct SEE must be a number ≥ 0.`;
      if (r.indirectSee !== '' && (Number.isNaN(Number(r.indirectSee)) || Number(r.indirectSee) < 0))
        return `Row CN ${r.cnCode}: indirect SEE must be a number ≥ 0.`;
      if (!r.periodStart || !r.periodEnd) return `Row CN ${r.cnCode}: production period is required.`;
      if (r.periodEnd < r.periodStart)
        return `Row CN ${r.cnCode}: production period end is before its start.`;
    }
    return null;
  };

  const submit = useCallback(async () => {
    const problem = validate();
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const payload: CBAMSupplierEmissionRowInput[] = rows
        .filter((r) => r.cnCode.trim() !== '' || r.directSee !== '')
        .map((r) => ({
          cn_code: r.cnCode.trim(),
          direct_see_tco2e_per_t: Number(r.directSee),
          indirect_see_tco2e_per_t: r.indirectSee === '' ? null : Number(r.indirectSee),
          production_period_start: r.periodStart,
          production_period_end: r.periodEnd,
          verifier_name: r.verifierName.trim() || null,
          verified: r.verified,
        }));
      const ctx = await api.submitCBAMSupplierData(token, payload);
      setContext(ctx);
      setSubmitted(true);
    } catch (e) {
      if (e instanceof PublicApiError && e.status === 410) setLinkState('expired');
      else setError(e instanceof Error ? e.message : 'Something went wrong — please try again.');
    } finally {
      setSubmitting(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows, token]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600">
            <Leaf className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-semibold">CLIMATRIX</span>
        </Link>
        <span className="text-xs text-slate-500">CBAM supplier data portal</span>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-12">
        {linkState === 'loading' && (
          <div className="flex justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
          </div>
        )}

        {linkState === 'not_found' && (
          <div className="mx-auto max-w-md rounded-2xl border border-rose-500/40 bg-rose-500/10 p-8 text-center">
            <AlertTriangle className="mx-auto h-8 w-8 text-rose-300" />
            <h1 className="mt-3 text-xl font-bold">Link not found</h1>
            <p className="mt-2 text-sm text-slate-300">
              This data-request link is unknown or has been revoked. Please check the link in your
              email, or ask the importer to send a new request.
            </p>
          </div>
        )}

        {linkState === 'expired' && (
          <div className="mx-auto max-w-md rounded-2xl border border-amber-500/40 bg-amber-500/10 p-8 text-center">
            <Clock className="mx-auto h-8 w-8 text-amber-300" />
            <h1 className="mt-3 text-xl font-bold">This request has expired</h1>
            <p className="mt-2 text-sm text-slate-300">
              Data-request links are valid for 60 days. Ask the importer to send a new request if
              you still need to provide emissions data.
            </p>
          </div>
        )}

        {linkState === 'error' && (
          <div className="mx-auto max-w-md rounded-2xl border border-rose-500/40 bg-rose-500/10 p-8 text-center">
            <AlertTriangle className="mx-auto h-8 w-8 text-rose-300" />
            <h1 className="mt-3 text-xl font-bold">Something went wrong</h1>
            <p className="mt-2 text-sm text-slate-300">
              We could not load this request. Please try again in a moment.
            </p>
          </div>
        )}

        {linkState === 'ok' && context && submitted && (
          <div className="mx-auto max-w-md rounded-2xl border border-emerald-500/40 bg-emerald-500/10 p-8 text-center">
            <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-300" />
            <h1 className="mt-3 text-2xl font-bold">Data submitted</h1>
            <p className="mt-2 text-sm text-slate-300">
              Thank you — your emissions data for{' '}
              <strong className="text-white">{context.installation_name}</strong> has been sent to{' '}
              <strong className="text-white">{context.importer_org_name}</strong>. It will replace
              default values in their CBAM declaration.
            </p>
            <p className="mt-3 text-xs text-slate-400">
              Need to correct something? Reopen this link any time before it expires and submit
              again — the new values replace the old ones.
            </p>
            <button
              onClick={() => setSubmitted(false)}
              className="mt-5 rounded-lg border border-slate-700 px-5 py-2.5 text-sm text-slate-300 hover:border-slate-500"
            >
              Revise my submission
            </button>
          </div>
        )}

        {linkState === 'ok' && context && !submitted && (
          <>
            {/* Who is asking */}
            <div className="text-center">
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
                <Factory className="h-3.5 w-3.5" /> CBAM embedded-emissions data request
              </div>
              <h1 className="text-3xl font-bold">
                <span className="text-emerald-400">{context.importer_org_name}</span> requests your
                emissions data
              </h1>
              <p className="mx-auto mt-4 max-w-2xl text-slate-400">
                As an EU importer of goods produced at{' '}
                <strong className="text-slate-200">
                  {context.installation_name} ({context.installation_country})
                </strong>
                , they need the actual specific embedded emissions (SEE) per CN code under EU
                Regulation 2023/956. Providing actual data replaces penalised default values in
                their declaration. No account is needed.
              </p>
              {context.message && (
                <p className="mx-auto mt-4 max-w-xl rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3 text-sm text-slate-300">
                  &ldquo;{context.message}&rdquo;
                </p>
              )}
              {context.status === 'submitted' && (
                <p className="mx-auto mt-4 max-w-xl text-sm text-emerald-300">
                  You already submitted data for this request — submitting again replaces the
                  previous values.
                </p>
              )}
            </div>

            {/* Rows */}
            <div className="mt-10 overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
              <table className="w-full min-w-[880px] text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-left text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-4 py-3 font-medium">CN code</th>
                    <th className="px-4 py-3 font-medium">Direct SEE (tCO₂e/t)</th>
                    <th className="px-4 py-3 font-medium">Indirect SEE (optional)</th>
                    <th className="px-4 py-3 font-medium">Production period</th>
                    <th className="px-4 py-3 font-medium">Verifier (optional)</th>
                    <th className="px-4 py-3 font-medium">Verified</th>
                    <th className="px-2 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, i) => (
                    <tr key={i} className="border-b border-slate-800/60 last:border-0 align-top">
                      <td className="px-4 py-2">
                        <input
                          value={row.cnCode}
                          onChange={(e) => setRow(i, { cnCode: e.target.value })}
                          placeholder="e.g. 7208"
                          className={`${inputClass} w-28`}
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          min="0"
                          step="any"
                          value={row.directSee}
                          onChange={(e) => setRow(i, { directSee: e.target.value })}
                          placeholder="e.g. 1.85"
                          className={`${inputClass} w-28`}
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          min="0"
                          step="any"
                          value={row.indirectSee}
                          onChange={(e) => setRow(i, { indirectSee: e.target.value })}
                          placeholder="—"
                          className={`${inputClass} w-28`}
                        />
                      </td>
                      <td className="px-4 py-2">
                        <div className="flex flex-col gap-1.5">
                          <input
                            type="date"
                            value={row.periodStart}
                            onChange={(e) => setRow(i, { periodStart: e.target.value })}
                            className={`${inputClass} w-40`}
                            aria-label="Production period start"
                          />
                          <input
                            type="date"
                            value={row.periodEnd}
                            onChange={(e) => setRow(i, { periodEnd: e.target.value })}
                            className={`${inputClass} w-40`}
                            aria-label="Production period end"
                          />
                        </div>
                      </td>
                      <td className="px-4 py-2">
                        <input
                          value={row.verifierName}
                          onChange={(e) => setRow(i, { verifierName: e.target.value })}
                          placeholder="Verifier name"
                          className={`${inputClass} w-36`}
                        />
                      </td>
                      <td className="px-4 py-2">
                        <label className="inline-flex items-center gap-1.5 pt-1.5 text-xs text-slate-400">
                          <input
                            type="checkbox"
                            checked={row.verified}
                            onChange={(e) => setRow(i, { verified: e.target.checked })}
                            className="h-4 w-4 rounded border-slate-700 bg-slate-950 accent-emerald-500"
                          />
                          <ShieldCheck className="h-3.5 w-3.5" />
                        </label>
                      </td>
                      <td className="px-2 py-2 text-right">
                        <button
                          onClick={() => setRows((prev) => prev.filter((_, idx) => idx !== i))}
                          disabled={rows.length === 1}
                          className="rounded-lg p-2 text-slate-500 hover:text-rose-400 disabled:opacity-30"
                          aria-label="Remove row"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="flex items-center justify-between border-t border-slate-800 px-4 py-3">
                <button
                  onClick={() => setRows((prev) => [...prev, { ...EMPTY_ROW }])}
                  className="inline-flex items-center gap-1.5 text-sm text-emerald-400 hover:text-emerald-300"
                >
                  <Plus className="h-4 w-4" /> Add product
                </button>
                <button
                  onClick={submit}
                  disabled={submitting}
                  className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-400 disabled:opacity-40"
                >
                  {submitting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <CheckCircle2 className="h-4 w-4" />
                  )}
                  Submit emissions data
                </button>
              </div>
            </div>

            {error && (
              <div className="mt-6 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
                {error}
              </div>
            )}

            {/* Guidance */}
            <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
              <div className="mb-2 flex items-center gap-2 text-xs font-medium text-slate-400">
                <Info className="h-3.5 w-3.5" /> What to enter
              </div>
              <ul className="list-disc space-y-1 pl-5 text-xs text-slate-500">
                <li>
                  Direct SEE: tonnes of CO₂e emitted at the installation per tonne of product
                  (Regulation (EU) 2023/956 monitoring rules).
                </li>
                <li>
                  Indirect SEE: emissions from purchased electricity per tonne of product — leave
                  blank if not determined.
                </li>
                <li>The production period is the period the emissions data was monitored over.</li>
                <li>
                  Tick &ldquo;verified&rdquo; only if an accredited verifier has verified the data;
                  name the verifier.
                </li>
              </ul>
            </div>
          </>
        )}

        <p className="mt-10 text-center text-xs text-slate-600">
          Data is transmitted to the requesting importer only and used for their CBAM compliance.
          Powered by CLIMATRIX.
        </p>
      </main>
    </div>
  );
}
