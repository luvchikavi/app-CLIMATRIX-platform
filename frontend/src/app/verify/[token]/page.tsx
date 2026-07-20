'use client';

/**
 * PUBLIC verifier read-only portal (magic link, no auth).
 *
 * An invited external verifier (VVB/auditor) opens this link and reviews ONE
 * reporting period's inventory — every line's source, factor, method and
 * result — plus the org's audit trail. Read-only, one period, nothing else.
 * This is the "audit-ready platform + verifier read-only role" build item
 * (docs/AUDIT-PARTNERS-RESEARCH.md): the per-line derivation trail no
 * competitor exposes, handed to the verifier in one place.
 */

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api, PublicApiError } from '@/lib/api';
import type { VerifierPeriod, VerifierLine, VerifierAuditEntry } from '@/lib/api';
import { Leaf, Loader2, ShieldCheck, Lock, AlertTriangle, FileCheck2 } from 'lucide-react';

const SCOPE_LABEL: Record<number, string> = {
  1: 'Scope 1 · Direct',
  2: 'Scope 2 · Energy',
  3: 'Scope 3 · Value chain',
};

function tonnes(kg: number | null): string {
  if (kg == null) return '—';
  const t = kg / 1000;
  if (t >= 100) return Math.round(t).toLocaleString();
  if (t >= 1) return t.toFixed(1);
  return t.toFixed(2);
}

type Tab = 'inventory' | 'audit';

export default function VerifierPortalPage() {
  const params = useParams();
  const token = String(params.token || '');

  const [period, setPeriod] = useState<VerifierPeriod | null>(null);
  const [lines, setLines] = useState<VerifierLine[]>([]);
  const [auditLog, setAuditLog] = useState<VerifierAuditEntry[]>([]);
  const [tab, setTab] = useState<Tab>('inventory');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [p, inv, log] = await Promise.all([
        api.getVerifierPeriod(token),
        api.getVerifierInventory(token),
        api.getVerifierAuditLog(token),
      ]);
      setPeriod(p);
      setLines(inv);
      setAuditLog(log);
    } catch (e) {
      if (e instanceof PublicApiError && e.status === 403) {
        setError('This verifier link has expired. Ask your client to send a fresh one.');
      } else {
        setError('This verifier link is not valid. It may have been revoked.');
      }
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F4F7F5]">
        <Loader2 className="h-7 w-7 animate-spin text-[#1F7A5C]" />
      </div>
    );
  }

  if (error || !period) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F4F7F5] p-6">
        <div className="max-w-md rounded-2xl border border-[#EDF2EE] bg-white p-8 text-center shadow-sm">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#F6EEDC]">
            <AlertTriangle className="h-5 w-5 text-[#A97614]" />
          </div>
          <h1 className="text-[17px] font-bold text-[#212724]">Link unavailable</h1>
          <p className="mt-2 text-[13px] text-[#67716B]">{error}</p>
        </div>
      </div>
    );
  }

  const scopeTotals = [
    { s: 1, v: period.scope_1_co2e_kg },
    { s: 2, v: period.scope_2_co2e_kg },
    { s: 3, v: period.scope_3_co2e_kg },
  ];

  return (
    <div className="min-h-screen bg-[#F4F7F5] text-[#212724]">
      {/* Header */}
      <header className="border-b border-[#EDF2EE] bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-5 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#1F7A5C]">
              <Leaf className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="text-[14px] font-bold leading-tight">CLIMATRIX</p>
              <p className="text-[11px] leading-tight text-[#67716B]">Verifier portal</p>
            </div>
          </div>
          <div className="flex items-center gap-2 rounded-full bg-[#E4F1EB] px-3 py-1.5 text-[12px] font-semibold text-[#1F7A5C]">
            <Lock className="h-3.5 w-3.5" />
            Read-only verifier view
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 py-8">
        {/* Period summary */}
        <div className="rounded-2xl border border-[#EDF2EE] bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-[12px] font-semibold uppercase tracking-[0.06em] text-[#939C96]">
                {period.organization_name}
              </p>
              <h1 className="mt-0.5 text-[22px] font-bold tracking-[-0.01em]">
                {period.period_name}
              </h1>
              <p className="mt-1 text-[12.5px] text-[#67716B]">
                {period.period_start?.slice(0, 10)} — {period.period_end?.slice(0, 10)}
                {period.verifier_name ? ` · prepared for ${period.verifier_name}` : ''}
              </p>
            </div>
            <div className="flex flex-col items-end gap-1.5">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-[#EDF2EE] px-3 py-1 text-[12px] font-semibold capitalize">
                <FileCheck2 className="h-3.5 w-3.5 text-[#1F7A5C]" />
                {period.status}
              </span>
              {period.assurance_level && (
                <span className="text-[11.5px] text-[#67716B]">
                  Assurance: {period.assurance_level}
                </span>
              )}
              {period.verified_by && (
                <span className="text-[11.5px] text-[#67716B]">
                  Verified by {period.verified_by}
                </span>
              )}
            </div>
          </div>

          <div className="mt-5 flex flex-wrap gap-x-10 gap-y-3 border-t border-[#EDF2EE] pt-5">
            <div>
              <p className="text-[24px] font-bold tabular-nums">{tonnes(period.total_co2e_kg)}</p>
              <p className="text-[11.5px] text-[#67716B]">Total t CO₂e · {period.line_count} lines</p>
            </div>
            {scopeTotals.map(({ s, v }) => (
              <div key={s}>
                <p className="text-[18px] font-semibold tabular-nums">{tonnes(v)}</p>
                <p className="text-[11.5px] text-[#67716B]">{SCOPE_LABEL[s]}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Tabs */}
        <div className="mt-6 flex gap-2">
          {(['inventory', 'audit'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded-full px-4 py-1.5 text-[12.5px] font-semibold transition-colors ${
                tab === t
                  ? 'bg-[#1F7A5C] text-white'
                  : 'bg-white text-[#67716B] hover:text-[#212724]'
              }`}
            >
              {t === 'inventory' ? `Inventory (${lines.length})` : `Audit trail (${auditLog.length})`}
            </button>
          ))}
        </div>

        {/* Inventory — the per-line derivation trail */}
        {tab === 'inventory' && (
          <div className="mt-4 overflow-x-auto rounded-2xl border border-[#EDF2EE] bg-white shadow-sm">
            <table className="w-full border-collapse text-[12.5px]">
              <thead>
                <tr className="border-b border-[#EDF2EE]">
                  {['Scope', 'Activity', 'Quantity', 'Factor', 'Method', 'DQ', 't CO₂e'].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-[0.06em] text-[#939C96]"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {lines.map((l) => (
                  <tr key={l.id} className="border-b border-[#EDF2EE] align-top last:border-0">
                    <td className="px-4 py-3">
                      <span className="whitespace-nowrap text-[11.5px] font-semibold text-[#1F7A5C]">
                        {SCOPE_LABEL[l.scope] ?? `Scope ${l.scope}`}
                      </span>
                      <div className="text-[11px] text-[#939C96]">{l.category_code}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium">{l.description || l.activity_key}</div>
                      <div className="font-mono text-[11px] text-[#939C96]">{l.activity_key}</div>
                      {l.site && <div className="text-[11px] text-[#939C96]">{l.site}</div>}
                    </td>
                    <td className="px-4 py-3 tabular-nums text-[#67716B]">
                      {l.quantity.toLocaleString()} {l.unit}
                    </td>
                    <td className="px-4 py-3 text-[#67716B]">
                      {l.factor_region || '—'}
                      {l.factor_source_year ? ` · ${l.factor_source_year}` : ''}
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-[#67716B]">{l.method || '—'}</div>
                      {l.formula && (
                        <div className="mt-0.5 font-mono text-[10.5px] text-[#939C96]">{l.formula}</div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className="text-[#67716B]"
                        title={l.data_quality_justification || undefined}
                      >
                        {l.data_quality_score != null ? `PCAF ${l.data_quality_score}/5` : '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-semibold tabular-nums">
                      {tonnes(l.co2e_kg)}
                    </td>
                  </tr>
                ))}
                {lines.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-[13px] text-[#939C96]">
                      No inventory lines in this period yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Audit trail */}
        {tab === 'audit' && (
          <div className="mt-4 overflow-hidden rounded-2xl border border-[#EDF2EE] bg-white shadow-sm">
            {auditLog.length === 0 ? (
              <p className="px-4 py-8 text-center text-[13px] text-[#939C96]">
                No audit entries recorded.
              </p>
            ) : (
              <ul className="divide-y divide-[#EDF2EE]">
                {auditLog.map((e, i) => (
                  <li key={i} className="flex items-start justify-between gap-4 px-4 py-3">
                    <div>
                      <p className="text-[12.5px]">{e.description}</p>
                      <p className="text-[11px] text-[#939C96]">
                        {e.action} · {e.resource_type}
                        {e.user_email ? ` · ${e.user_email}` : ''}
                      </p>
                    </div>
                    <span className="whitespace-nowrap text-[11px] tabular-nums text-[#939C96]">
                      {e.created_at.slice(0, 16).replace('T', ' ')}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        <footer className="mt-8 flex items-center justify-center gap-2 text-[11.5px] text-[#939C96]">
          <ShieldCheck className="h-3.5 w-3.5" />
          Every line traces to its source, factor, method and result — verification-ready by construction.
        </footer>
      </main>
    </div>
  );
}
