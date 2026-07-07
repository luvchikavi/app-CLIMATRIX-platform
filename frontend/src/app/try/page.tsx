'use client';

/**
 * Public "Try Climatrix" page (no login) — the trust-builder we share in forums.
 * Drop any spreadsheet → see it calculated live, WITH the methodology (factor,
 * source, formula) behind every number → CTA to sign up.
 */

import { useCallback, useRef, useState } from 'react';
import Link from 'next/link';
import { demoAnalyze, DemoResult } from '@/lib/api';
import { cn } from '@/lib/utils';
import {
  UploadCloud,
  Loader2,
  Leaf,
  ArrowRight,
  Info,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';

const SCOPE_COLOR: Record<number, string> = {
  1: 'text-rose-400',
  2: 'text-amber-400',
  3: 'text-emerald-400',
};

export default function TryPage() {
  const [result, setResult] = useState<DemoResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File) => {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(await demoAnalyze(file));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong.');
    } finally {
      setBusy(false);
    }
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files?.[0];
      if (f) handleFile(f);
    },
    [handleFile]
  );

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
            <Sparkles className="h-3.5 w-3.5" /> No login. Nothing saved. Just try it.
          </div>
          <h1 className="text-3xl font-bold sm:text-4xl">
            Drop your messiest emissions data.
            <br />
            <span className="text-emerald-400">Watch it calculate — and show its work.</span>
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-slate-400">
            Any spreadsheet, any layout. CLIMATRIX maps every line to a real emission factor,
            computes your footprint, and shows you exactly <em>how</em> each number was derived —
            the factor, its source, and the formula.
          </p>
        </div>

        {/* Dropzone */}
        {!result && (
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => fileRef.current?.click()}
            className={cn(
              'mt-10 flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 py-16 text-center transition-colors',
              dragOver ? 'border-emerald-400 bg-emerald-500/10' : 'border-slate-700 hover:border-emerald-500'
            )}
          >
            {busy ? (
              <>
                <Loader2 className="h-10 w-10 animate-spin text-emerald-400" />
                <p className="font-medium">Reading your file and calculating…</p>
                <p className="text-xs text-slate-500">A few seconds — we map, ground, and compute each line.</p>
              </>
            ) : (
              <>
                <UploadCloud className="h-10 w-10 text-emerald-400" />
                <p className="font-medium">Drag a spreadsheet here, or click to browse</p>
                <p className="text-xs text-slate-500">CSV or Excel · first 50 rows · nothing is stored</p>
              </>
            )}
            <input
              ref={fileRef}
              type="file"
              accept=".csv,.tsv,.xlsx,.xls"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
              }}
            />
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
            {result.notice && (
              <div className="flex items-start gap-2 rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-300">
                <Info className="mt-0.5 h-4 w-4 shrink-0" />
                {result.notice}
              </div>
            )}

            {/* Headline number */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 text-center">
              <p className="text-sm text-slate-400">Calculated footprint from {result.filename}</p>
              <p className="mt-1 text-4xl font-bold text-emerald-400">
                {result.total_tco2e.toLocaleString(undefined, { maximumFractionDigits: 1 })}
                <span className="ml-2 text-lg text-slate-400">tCO₂e</span>
              </p>
              <div className="mt-3 flex justify-center gap-6 text-sm">
                {result.by_scope.map((s) => (
                  <span key={s.scope} className={SCOPE_COLOR[s.scope] || 'text-slate-300'}>
                    Scope {s.scope}: {s.tco2e.toLocaleString(undefined, { maximumFractionDigits: 1 })} t
                  </span>
                ))}
              </div>
              <p className="mt-3 text-xs text-slate-500">
                {result.rows_calculated} of {result.rows_read} rows calculated
                {result.capped && ' · showing the first 50 rows'}
              </p>
            </div>

            {/* Rows with methodology — the trust builder */}
            <div className="overflow-hidden rounded-2xl border border-slate-800">
              <div className="flex items-center gap-2 border-b border-slate-800 bg-slate-900/60 px-4 py-3 text-sm font-medium">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                Every number, explained — factor, source &amp; formula
              </div>
              <div className="divide-y divide-slate-800">
                {result.rows.map((r, i) => (
                  <div key={i} className="px-4 py-3">
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <span className="font-medium text-slate-200">{r.source_description || '—'}</span>
                      {r.co2e_kg != null ? (
                        <span className="text-sm font-semibold text-emerald-400">
                          {(r.co2e_kg / 1000).toLocaleString(undefined, { maximumFractionDigits: 2 })} tCO₂e
                          {r.scope ? <span className="ml-2 text-xs text-slate-500">Scope {r.scope}</span> : null}
                        </span>
                      ) : (
                        <span className="text-xs italic text-amber-400">{r.note || 'needs review'}</span>
                      )}
                    </div>
                    {r.methodology?.formula && (
                      <p className="mt-1 font-mono text-xs text-slate-400">
                        {r.methodology.formula}
                        {r.methodology.factor_source && (
                          <span className="ml-2 rounded bg-slate-800 px-1.5 py-0.5 text-slate-300">
                            {r.methodology.factor_source}
                          </span>
                        )}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* CTA */}
            <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-6 text-center">
              <p className="text-lg font-semibold">That&apos;s your data — mapped, calculated, and defensible.</p>
              <p className="mt-1 text-sm text-slate-300">
                Sign up to keep it, run full Scope 1/2/3 reports, and build a decarbonization plan.
              </p>
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
                  Try another file
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
