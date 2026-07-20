'use client';

/**
 * Methodology — the rules every number in Climatrix is computed under, served
 * from the backend's single source of truth (GET /reference/methodology) so
 * this page can never drift from what the calculation engine actually does.
 * This is the page a practitioner shows their verifier.
 */

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { AppShell } from '@/components/layout';
import { Surface, PanelLabel } from '@/components/canopy';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';
import { ArrowLeft, Loader2 } from 'lucide-react';

const TIER_TONE: Record<string, string> = {
  measured: 'bg-cy-accent-soft text-cy-accent',
  calculated: 'bg-cy-row text-cy-ink',
  estimated: 'bg-cy-warn-soft text-cy-warn',
  gap: 'bg-cy-row text-cy-muted',
};

export default function MethodologyPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['reference-methodology'],
    queryFn: () => api.getMethodology(),
    staleTime: 24 * 60 * 60 * 1000,
  });

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl">
        <Link
          href="/reports"
          className="mb-4 inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-cy-muted hover:text-cy-ink"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Reports
        </Link>
        <h1 className="text-[22px] font-bold text-cy-ink">Methodology</h1>
        <p className="mt-1 mb-6 text-[13.5px] text-cy-muted">
          The rules every number on this platform is computed under — served from the same
          source the calculation engine uses, so this page cannot drift from what actually
          runs. Show it to your verifier.
        </p>

        {isLoading || !data ? (
          <div className="flex items-center gap-2 py-10 text-cy-muted">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading…
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <Surface>
              <PanelLabel>Accounting standard</PanelLabel>
              <p className="text-[13.5px] font-semibold text-cy-ink">
                {data.ghg_accounting_standard}
              </p>
              <p className="mt-1 text-[13px] text-cy-muted">{data.calculation_approach}</p>
              <p className="mt-2 text-[13px] text-cy-muted">
                <span className="font-semibold text-cy-ink">Global warming potentials:</span>{' '}
                {data.gwp_statement}
              </p>
            </Surface>

            <Surface>
              <PanelLabel>Data-quality ladder</PanelLabel>
              <p className="mb-3 text-[13px] text-cy-muted">
                Every line in your inventory sits on this ladder — estimates are labelled,
                never hidden. The PCAF score (1 best – 5 worst) is what a validator will
                scrutinise.
              </p>
              <div className="flex flex-col gap-2">
                {data.data_quality_tiers.map((t) => (
                  <div key={t.tier} className="flex items-baseline gap-3">
                    <span
                      className={cn(
                        'w-24 shrink-0 rounded-full px-2.5 py-1 text-center text-[11px] font-bold capitalize',
                        TIER_TONE[t.tier] ?? TIER_TONE.gap
                      )}
                    >
                      {t.tier}
                    </span>
                    <span className="text-[13px] text-cy-ink">
                      {t.description}
                      <span className="ml-2 text-[11.5px] text-cy-faint">
                        PCAF {t.scores.join('–')}
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </Surface>

            <Surface>
              <PanelLabel>Method hierarchy</PanelLabel>
              <p className="mb-3 text-[13px] text-cy-muted">
                When several calculation methods are possible, the highest available method
                wins — and the method actually used is recorded on every line.
              </p>
              <ol className="flex flex-col gap-2">
                {data.method_hierarchy.map((m, i) => (
                  <li key={m.method} className="flex items-baseline gap-3">
                    <span className="w-5 shrink-0 text-right text-[12px] font-bold tabular-nums text-cy-faint">
                      {i + 1}.
                    </span>
                    <span className="text-[13px] text-cy-ink">
                      <span className="font-semibold">{m.label}</span>
                      <span className="text-cy-muted"> — {m.description}</span>
                    </span>
                  </li>
                ))}
              </ol>
            </Surface>

            <Surface>
              <PanelLabel>Consolidation approach</PanelLabel>
              <p className="text-[13px] text-cy-muted">
                Your organization reports under one of the GHG Protocol consolidation
                approaches — set in Settings, and stated as-is in every report:
              </p>
              <div className="mt-2.5 flex flex-wrap gap-1.5">
                {data.consolidation_approaches.map((c) => (
                  <span
                    key={c.value}
                    className="rounded-full bg-cy-row px-3 py-1 text-[12px] font-semibold text-cy-ink"
                  >
                    {c.label}
                  </span>
                ))}
              </div>
            </Surface>

            <Surface>
              <PanelLabel>Biogenic CO₂</PanelLabel>
              <p className="text-[13px] leading-relaxed text-cy-ink">{data.biogenic_policy}</p>
            </Surface>

            <Surface>
              <PanelLabel>Factor provenance</PanelLabel>
              <p className="text-[13px] leading-relaxed text-cy-ink">
                Every calculated line stores the emission factor it used — source, year and
                region — plus the method, the data-quality score and any assumptions made
                (including derived quantities such as flight distances, with the full
                derivation recorded). The audit package export contains this trail
                end-to-end, so a third-party verifier can trace any figure back to its
                source row.
              </p>
            </Surface>
          </div>
        )}
      </div>
    </AppShell>
  );
}
