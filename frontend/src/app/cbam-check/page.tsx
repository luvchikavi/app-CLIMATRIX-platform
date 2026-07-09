'use client';

/**
 * Public "Am I in CBAM scope?" checker (no login) — the 50 t exemption
 * question every EU importer of steel/aluminium/cement/fertilisers is asking
 * now that the definitive regime is live. Lead-before-results, like /try.
 */

import { useCallback, useState } from 'react';
import Link from 'next/link';
import { api, CBAMScreenItemInput, CBAMScreenResult } from '@/lib/api';
import {
  Leaf,
  Scale,
  Loader2,
  Plus,
  Trash2,
  Info,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';

const SECTOR_OPTIONS = [
  { value: 'cement', label: 'Cement' },
  { value: 'iron_steel', label: 'Iron & steel' },
  { value: 'aluminium', label: 'Aluminium' },
  { value: 'fertiliser', label: 'Fertilisers' },
  { value: 'hydrogen', label: 'Hydrogen' },
  { value: 'electricity', label: 'Electricity' },
];

// Common CN codes per sector — suggested defaults so the visitor doesn't need
// to know the nomenclature (any code still overrides the sector pick).
const CN_SUGGESTIONS: Record<string, { code: string; label: string }[]> = {
  cement: [
    { code: '2523 29', label: 'Portland cement' },
    { code: '2523 10', label: 'Cement clinker' },
  ],
  iron_steel: [
    { code: '7208', label: 'Hot-rolled flat steel' },
    { code: '7210', label: 'Coated flat steel' },
    { code: '7308', label: 'Steel structures' },
  ],
  aluminium: [
    { code: '7601', label: 'Unwrought aluminium' },
    { code: '7604', label: 'Aluminium bars & profiles' },
  ],
  fertiliser: [
    { code: '3102 10', label: 'Urea' },
    { code: '2814', label: 'Ammonia' },
    { code: '3105', label: 'NPK fertilisers' },
  ],
  hydrogen: [{ code: '2804 10', label: 'Hydrogen' }],
  electricity: [{ code: '2716 00', label: 'Electrical energy' }],
};

interface Line {
  sector: string;
  cnCode: string;
  massKg: string;
  origin: string;
}

const EMPTY_LINE: Line = { sector: 'iron_steel', cnCode: '', massKg: '', origin: '' };

const fmt = (n: number, digits = 1) =>
  n.toLocaleString(undefined, { maximumFractionDigits: digits });

export default function CBAMCheckPage() {
  const [lines, setLines] = useState<Line[]>([{ ...EMPTY_LINE }]);
  const [result, setResult] = useState<CBAMScreenResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Lead-before-results: the computed basket is held until the prospect
  // leaves contact details — every check becomes a trackable lead.
  const [pendingItems, setPendingItems] = useState<CBAMScreenItemInput[] | null>(null);
  const [captured, setCaptured] = useState(false);
  const [email, setEmail] = useState('');
  const [leadName, setLeadName] = useState('');
  const [leadOrg, setLeadOrg] = useState('');

  const setLine = (i: number, patch: Partial<Line>) =>
    setLines((prev) => prev.map((l, idx) => (idx === i ? { ...l, ...patch } : l)));

  const buildItems = (): CBAMScreenItemInput[] =>
    lines
      .filter((l) => (l.cnCode.trim() || l.sector) && Number(l.massKg) > 0)
      .map((l) => ({
        cn_code_or_sector: l.cnCode.trim() || l.sector,
        mass_kg: Number(l.massKg),
        origin_country: l.origin.trim() || undefined,
      }));

  const runScreen = useCallback(async (items: CBAMScreenItemInput[]) => {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(await api.cbamScreen({ items }));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong.');
    } finally {
      setBusy(false);
    }
  }, []);

  const onCheck = useCallback(() => {
    const items = buildItems();
    if (items.length === 0) {
      setError('Add at least one line with a sector (or CN code) and an annual quantity.');
      return;
    }
    setError(null);
    if (!captured) {
      setPendingItems(items);
      return;
    }
    runScreen(items);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lines, captured, runScreen]);

  const submitLeadAndScreen = useCallback(async () => {
    const value = email.trim();
    if (!value || !value.includes('@') || !pendingItems) return;
    try {
      await api.captureLead({
        email: value,
        name: leadName.trim() || undefined,
        organization_name: leadOrg.trim() || undefined,
        source: 'website_demo',
        what_tried: 'cbam-check',
      });
    } catch {
      // non-blocking — never let capture failure interrupt the prospect
    }
    setCaptured(true);
    const items = pendingItems;
    setPendingItems(null);
    await runScreen(items);
  }, [email, leadName, leadOrg, pendingItems, runScreen]);

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
        <Link
          href="/"
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-400"
        >
          Sign in / Sign up
        </Link>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-12">
        {/* Hero */}
        <div className="text-center">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
            <Scale className="h-3.5 w-3.5" /> Free 60-second check. No account needed.
          </div>
          <h1 className="text-3xl font-bold sm:text-4xl">
            Am I in <span className="text-emerald-400">CBAM</span> scope?
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-slate-400">
            The EU&apos;s carbon border tax entered its definitive regime on 1 January 2026. If you
            import less than <strong className="text-slate-200">50 tonnes a year</strong> of iron
            &amp; steel, aluminium, fertilisers and cement combined, you&apos;re exempt — hydrogen
            and electricity are always in scope. Enter your expected annual imports to see where
            you stand and what certificates could cost.
          </p>
        </div>

        {/* Import lines */}
        <div className="mt-10 overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
          <table className="w-full min-w-[560px] text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3 font-medium">Product (sector or CN code)</th>
                <th className="px-4 py-3 font-medium">Annual quantity (kg)</th>
                <th className="px-4 py-3 font-medium">Origin (optional)</th>
                <th className="px-2 py-3" />
              </tr>
            </thead>
            <tbody>
              {lines.map((line, i) => (
                <tr key={i} className="border-b border-slate-800/60 last:border-0">
                  <td className="px-4 py-2">
                    <div className="flex flex-wrap gap-2">
                      <select
                        value={line.sector}
                        onChange={(e) => setLine(i, { sector: e.target.value })}
                        className="rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-white"
                      >
                        {SECTOR_OPTIONS.map((o) => (
                          <option key={o.value} value={o.value}>
                            {o.label}
                          </option>
                        ))}
                      </select>
                      <input
                        value={line.cnCode}
                        onChange={(e) => setLine(i, { cnCode: e.target.value })}
                        list={`cn-suggestions-${line.sector}`}
                        placeholder={
                          CN_SUGGESTIONS[line.sector]?.[0]
                            ? `e.g. ${CN_SUGGESTIONS[line.sector][0].code} (${CN_SUGGESTIONS[line.sector][0].label})`
                            : 'CN code (optional)'
                        }
                        className="w-56 rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-white placeholder:text-slate-600"
                      />
                      <datalist id={`cn-suggestions-${line.sector}`}>
                        {(CN_SUGGESTIONS[line.sector] ?? []).map((s) => (
                          <option key={s.code} value={s.code}>
                            {s.label}
                          </option>
                        ))}
                      </datalist>
                    </div>
                  </td>
                  <td className="px-4 py-2">
                    <input
                      type="number"
                      min="0"
                      value={line.massKg}
                      onChange={(e) => setLine(i, { massKg: e.target.value })}
                      placeholder={line.sector === 'electricity' ? 'kWh per year' : 'kg per year'}
                      className="w-32 rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-white placeholder:text-slate-600"
                    />
                  </td>
                  <td className="px-4 py-2">
                    <input
                      value={line.origin}
                      onChange={(e) => setLine(i, { origin: e.target.value })}
                      placeholder="e.g. TR"
                      className="w-24 rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-white placeholder:text-slate-600"
                    />
                  </td>
                  <td className="px-2 py-2 text-right">
                    <button
                      onClick={() => setLines((prev) => prev.filter((_, idx) => idx !== i))}
                      disabled={lines.length === 1}
                      className="rounded-lg p-2 text-slate-500 hover:text-rose-400 disabled:opacity-30"
                      aria-label="Remove line"
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
              onClick={() => setLines((prev) => [...prev, { ...EMPTY_LINE }])}
              className="inline-flex items-center gap-1.5 text-sm text-emerald-400 hover:text-emerald-300"
            >
              <Plus className="h-4 w-4" /> Add line
            </button>
            <button
              onClick={onCheck}
              disabled={busy}
              className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-400 disabled:opacity-40"
            >
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Scale className="h-4 w-4" />}
              Check my exposure
            </button>
          </div>
        </div>

        {/* Lead gate — who are we showing this verdict to? */}
        {pendingItems && !captured && (
          <div className="mx-auto mt-8 max-w-md rounded-2xl border border-emerald-500/30 bg-slate-900 p-6">
            <p className="font-medium text-white">Your CBAM verdict is ready</p>
            <p className="mt-1 text-sm text-slate-400">
              Tell us where to send the full exposure breakdown and we&apos;ll show it right now.
            </p>
            <div className="mt-4 space-y-2">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Work email (required)"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white placeholder:text-slate-500"
              />
              <input
                value={leadName}
                onChange={(e) => setLeadName(e.target.value)}
                placeholder="Your name (optional)"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white placeholder:text-slate-500"
              />
              <input
                value={leadOrg}
                onChange={(e) => setLeadOrg(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && submitLeadAndScreen()}
                placeholder="Organization (optional)"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white placeholder:text-slate-500"
              />
              <button
                onClick={submitLeadAndScreen}
                disabled={!email.includes('@')}
                className="w-full rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-400 disabled:opacity-40"
              >
                Show my verdict
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-6 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
            {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="mt-10 space-y-6">
            {/* Verdict */}
            {result.exempt ? (
              <div className="rounded-2xl border border-emerald-500/40 bg-emerald-500/10 p-6 text-center">
                <div className="inline-flex items-center gap-2 text-emerald-300">
                  <ShieldCheck className="h-6 w-6" />
                  <span className="text-2xl font-bold">EXEMPT</span>
                </div>
                <p className="mt-2 text-sm text-slate-300">
                  Your {fmt(result.in_threshold_mass_kg / 1000)} t of threshold goods is below the
                  50 t de minimis — you have{' '}
                  <strong className="text-emerald-300">
                    {fmt(result.headroom_kg / 1000)} t of headroom
                  </strong>{' '}
                  before CBAM obligations apply. Monitor your cumulative imports: the flag is
                  raised at 90% of the threshold, and artificially splitting imports is prohibited.
                </p>
              </div>
            ) : (
              <div className="rounded-2xl border border-amber-500/40 bg-amber-500/10 p-6 text-center">
                <div className="inline-flex items-center gap-2 text-amber-300">
                  <AlertTriangle className="h-6 w-6" />
                  <span className="text-2xl font-bold">IN SCOPE</span>
                </div>
                <p className="mt-2 text-sm text-slate-300">
                  {result.in_threshold_mass_kg >= result.threshold_kg ? (
                    <>
                      Your {fmt(result.in_threshold_mass_kg / 1000)} t of threshold goods exceeds
                      the 50 t de minimis.
                    </>
                  ) : (
                    <>Hydrogen and electricity imports are always in CBAM scope — no threshold.</>
                  )}{' '}
                  You must hold (or have applied for) authorised CBAM declarant status, track every
                  import, and surrender certificates for 2026 imports by 30 September 2027.
                </p>
              </div>
            )}

            {/* Per-line table */}
            <div className="overflow-hidden rounded-2xl border border-slate-800">
              <div className="flex items-center gap-2 border-b border-slate-800 bg-slate-900/60 px-4 py-3 text-sm font-medium">
                <Scale className="h-4 w-4 text-emerald-400" />
                Line-by-line estimate (default values + {fmt(result.default_value_markup_pct, 0)}%
                2026 markup, ETS €{fmt(result.ets_price_eur, 2)}/tCO₂e)
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[520px] text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 text-left text-xs uppercase tracking-wide text-slate-500">
                      <th className="px-4 py-2 font-medium">Line</th>
                      <th className="px-4 py-2 font-medium">Sector</th>
                      <th className="px-4 py-2 font-medium">Covered</th>
                      <th className="px-4 py-2 text-right font-medium">tCO₂e est.</th>
                      <th className="px-4 py-2 text-right font-medium">Certificate cost €</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {result.items.map((item, i) => (
                      <tr key={i}>
                        <td className="px-4 py-2 text-slate-300">{item.cn_code_or_sector}</td>
                        <td className="px-4 py-2 text-slate-300">
                          {item.sector_label || <span className="italic text-slate-500">not a CBAM good</span>}
                        </td>
                        <td className="px-4 py-2">
                          {item.covered ? (
                            <span className="text-amber-300">Yes</span>
                          ) : (
                            <span className="text-slate-500">No</span>
                          )}
                        </td>
                        <td className="px-4 py-2 text-right text-slate-200">
                          {item.sector ? fmt(item.estimated_emissions_tco2e, 2) : '—'}
                        </td>
                        <td className="px-4 py-2 text-right text-slate-200">
                          {item.covered ? `€${fmt(item.estimated_certificate_cost_eur, 0)}` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex items-baseline justify-between border-t border-slate-800 bg-slate-900/60 px-4 py-3">
                <span className="text-sm text-slate-400">
                  Estimated 2026–27 certificate liability
                </span>
                <span className="text-xl font-bold text-emerald-400">
                  €{fmt(result.total_estimated_certificate_cost_eur, 0)}
                  <span className="ml-2 text-sm font-normal text-slate-400">
                    ({fmt(result.total_estimated_emissions_tco2e, 1)} tCO₂e)
                  </span>
                </span>
              </div>
            </div>

            {/* Assumptions — say what we simplified, always */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
              <div className="mb-2 flex items-center gap-2 text-xs font-medium text-slate-400">
                <Info className="h-3.5 w-3.5" /> Assumptions behind this estimate
              </div>
              <ul className="list-disc space-y-1 pl-5 text-xs text-slate-500">
                {result.assumptions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>

            {/* CTA */}
            <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-6 text-center">
              <p className="text-lg font-semibold">
                {result.exempt
                  ? 'Stay exempt — and prove it with a tracked import register.'
                  : 'In scope? Cut the bill with actual supplier data instead of penalised defaults.'}
              </p>
              <p className="mt-1 text-sm text-slate-300">
                The CLIMATRIX CBAM module tracks your imports against the 50 t threshold, chases
                supplier emissions data, and forecasts your certificate cash-out.
              </p>
              {captured && (
                <p className="mt-3 text-sm text-emerald-300">
                  We&apos;ll send the full breakdown to {email.trim()}.
                </p>
              )}
              <div className="mt-4 flex justify-center gap-3">
                <Link
                  href="/"
                  className="inline-flex items-center gap-1 rounded-lg bg-emerald-500 px-5 py-2.5 font-medium text-white hover:bg-emerald-400"
                >
                  Get started free <ArrowRight className="h-4 w-4" />
                </Link>
                <button
                  onClick={() => {
                    setResult(null);
                    setError(null);
                  }}
                  className="rounded-lg border border-slate-700 px-5 py-2.5 text-slate-300 hover:border-slate-500"
                >
                  Adjust my imports
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Footer note */}
        <p className="mt-10 text-center text-xs text-slate-600">
          Screening estimate only — not legal advice. EU Reg. 2023/956 as amended by Reg. (EU)
          2025/2083 (Omnibus). Definitive regime since 1 Jan 2026; certificate sales open 1 Feb
          2027.
        </p>
      </main>
    </div>
  );
}
