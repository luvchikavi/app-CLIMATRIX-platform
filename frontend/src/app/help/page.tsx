'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/layout';
import { Surface, PanelLabel, PageHead } from '@/components/canopy';
import {
  BookOpen,
  ChevronDown,
  FileText,
  LifeBuoy,
  Mail,
  Package,
  Scale,
  Search,
  ShieldCheck,
  Sparkles,
  Upload,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const SUPPORT_EMAIL = 'support@climatrix.co';

/** In-app quick guides: where to click, in journey order. */
const GUIDES = [
  {
    icon: Upload,
    title: 'Import your data',
    body: 'Drop any file — invoices, fuel cards, travel exports — on the Data hub. The AI parser maps every row to an emission factor and asks only the questions that matter.',
    href: '/hub',
    cta: 'Open Data hub',
  },
  {
    icon: Sparkles,
    title: 'Review with confidence bands',
    body: 'Green rows are grounded, amber were calculated with assumptions (expand any row to see exactly how), red need your input. Nothing enters your inventory unreviewed.',
    href: '/ingest',
    cta: 'Go to Smart Import',
  },
  {
    icon: FileText,
    title: 'Generate reports & exports',
    body: 'ISO 14064-1 report, VSME, ESRS E1 and CDP exports, CSV/PDF — all from the Reports page, with the methodology and recalculation policy stated inside the report.',
    href: '/reports',
    cta: 'Open Reports',
  },
  {
    icon: ShieldCheck,
    title: 'Invite your verifier',
    body: 'From the Reports → Verification tab, send your auditor a read-only, token-gated portal with the full inventory, provenance and audit log. No account needed on their side.',
    href: '/reports',
    cta: 'Verification tab',
  },
  {
    icon: Package,
    title: 'Product footprints (PCF)',
    body: 'Model a product and its bill of materials on the Products page — Climatrix computes the cradle-to-gate footprint and exports PACT v3 JSON your customers can ingest.',
    href: '/products',
    cta: 'Open Products',
  },
  {
    icon: Scale,
    title: 'CBAM compliance',
    body: 'Check the 50-tonne exemption for free, then manage embedded emissions, CN codes and quarterly reports in the CBAM module.',
    href: '/modules/cbam',
    cta: 'Open CBAM',
  },
];

const FAQS: { q: string; a: string; tags: string }[] = [
  {
    q: 'Where do my emission factors come from?',
    a: 'The factor library carries DEFRA, EPA, IEA and EEIO factors with source, region and year on every factor. Resolution prefers your row/site region, then your organization default, then a Global fallback — and every calculated number keeps its full derivation story (open any row to see the formula and the factor used). The Methodology page documents the whole approach.',
    tags: 'factors defra epa methodology region calculation',
  },
  {
    q: 'Why is a row amber or red in Smart Import?',
    a: 'Amber means the number was calculated with an assumption (e.g. a round-trip was inferred, or a global factor was used instead of a country-specific one) — expand the row to see exactly which. Red means we could not ground the row and need your input. Approving amber rows is normal; the assumption stays disclosed in your audit trail.',
    tags: 'smart import confidence bands amber red review grid',
  },
  {
    q: 'What is the difference between location-based and market-based Scope 2?',
    a: 'Location-based uses your grid’s average factor; market-based uses your electricity supplier’s specific factor (or contract). Per the GHG Protocol Scope 2 Guidance, Climatrix computes and discloses both when you provide a supplier factor.',
    tags: 'scope 2 electricity market location dual reporting',
  },
  {
    q: 'My total changed after a recalculation — why?',
    a: 'Recalculation re-resolves every activity against the current factor library. If factors were updated (new DEFRA year, region fix), stored results move to match. Your organization’s recalculation policy (Settings → GHG policy) states the threshold that triggers a base-year recalculation, and the report discloses it.',
    tags: 'recalculation base year policy totals changed',
  },
  {
    q: 'What can my auditor see in the verifier portal?',
    a: 'Exactly what you granted: a read-only view of one reporting period — summary, the full inventory with per-row provenance, and the audit log. Access is token-gated, revocable, and every visit is logged. Verifiers never see other periods or billing.',
    tags: 'verifier auditor portal iso 14064 verification',
  },
  {
    q: 'What does the PCF module export?',
    a: 'A PACT (WBCSD) Data Exchange v3 ProductFootprint JSON — the machine-readable format buyer procurement systems ingest — plus the on-screen breakdown by EN 15804 lifecycle stage with a per-line derivation story. Supplier PCFs you upload count as primary data and raise your primary-data share.',
    tags: 'pcf pact product footprint export bom supplier',
  },
  {
    q: 'Why are exports locked on my account?',
    a: 'During the free trial all results stay on screen — exports (PDF, CSV, VSME/ESRS/CDP, PACT) unlock on a paid plan. If you bought a Report Pass, exports are licensed to the reporting year the pass covers.',
    tags: 'trial exports locked 402 report pass billing',
  },
  {
    q: 'How do I add sites, users or another reporting period?',
    a: 'Sites live in Workspace → Sites (each site can carry its own grid region for factor resolution). Users are invited from Settings. Reporting periods are created from the period selector in the top bar or Settings → Periods. Plan caps apply; add-on packs extend them.',
    tags: 'sites users seats periods settings grid region',
  },
  {
    q: 'Is my data secure? Who can see it?',
    a: 'Data is encrypted in transit and at rest, and every query is scoped to your organization. Verifier access is read-only and token-gated. The Security page documents the practices, and the audit trail records changes to your inventory.',
    tags: 'security privacy encryption tenant isolation audit',
  },
  {
    q: 'Can Climatrix handle CBAM?',
    a: 'Yes — the CBAM module covers the free 50-tonne exemption checker, embedded-emissions calculation by CN code, supplier data requests, and quarterly report preparation. It shares the factor engine and your product CN codes with the PCF module.',
    tags: 'cbam eu carbon border cn code embedded emissions',
  },
];

function FaqRow({ q, a, open, onToggle }: { q: string; a: string; open: boolean; onToggle: () => void }) {
  return (
    <div className="border-t border-cy-row first:border-t-0">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="flex w-full cursor-pointer items-center justify-between gap-3 py-3.5 text-left"
      >
        <span className="text-[14px] font-semibold text-cy-ink">{q}</span>
        <ChevronDown className={cn('h-4 w-4 shrink-0 text-cy-faint transition-transform', open && 'rotate-180')} />
      </button>
      {open && <p className="pb-4 pr-8 text-[13px] leading-relaxed text-cy-muted">{a}</p>}
    </div>
  );
}

export default function HelpPage() {
  const [query, setQuery] = useState('');
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const filteredFaqs = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return FAQS;
    return FAQS.filter(
      (f) => f.q.toLowerCase().includes(q) || f.a.toLowerCase().includes(q) || f.tags.includes(q)
    );
  }, [query]);

  return (
    <AppShell>
      <PageHead
        title="Help & support"
        subtitle="Quick guides, answers, and a direct line to the team"
      />

      {/* Quick guides */}
      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {GUIDES.map((g) => (
          <Surface key={g.title} padding="panel" className="flex flex-col">
            <g.icon className="mb-2 h-5 w-5 text-cy-accent" strokeWidth={1.75} />
            <h3 className="text-[14px] font-[650] text-cy-ink">{g.title}</h3>
            <p className="mt-1 flex-1 text-[12.5px] leading-relaxed text-cy-muted">{g.body}</p>
            <Link
              href={g.href}
              className="mt-2 text-[12.5px] font-semibold text-cy-accent hover:underline"
            >
              {g.cta} →
            </Link>
          </Surface>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        {/* FAQ */}
        <Surface padding="panel">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <PanelLabel>Frequently asked questions</PanelLabel>
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-cy-faint" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search answers…"
                className="w-56 rounded-full bg-cy-row py-1.5 pl-8 pr-3 text-[12.5px] text-cy-ink placeholder:text-cy-faint focus:outline-none focus:ring-1 focus:ring-cy-accent"
              />
            </div>
          </div>
          {filteredFaqs.length === 0 ? (
            <p className="py-6 text-center text-[13px] text-cy-faint">
              No matches — try a different word, or email us below.
            </p>
          ) : (
            filteredFaqs.map((f, i) => (
              <FaqRow
                key={f.q}
                q={f.q}
                a={f.a}
                open={openFaq === i}
                onToggle={() => setOpenFaq(openFaq === i ? null : i)}
              />
            ))
          )}
        </Surface>

        {/* Technical assistance */}
        <div className="flex flex-col gap-3">
          <Surface padding="panel">
            <LifeBuoy className="mb-2 h-5 w-5 text-cy-accent" strokeWidth={1.75} />
            <h3 className="text-[14px] font-[650] text-cy-ink">Technical assistance</h3>
            <p className="mt-1 text-[12.5px] leading-relaxed text-cy-muted">
              Stuck on an import, a number that looks wrong, or an export? Email us with the page
              you were on and (if it&rsquo;s about a file) the file — a human answers, typically
              within one business day.
            </p>
            <a
              href={`mailto:${SUPPORT_EMAIL}?subject=Support%20request`}
              className="mt-3 inline-flex items-center gap-1.5 rounded-[10px] bg-cy-accent px-3.5 py-2 text-[12.5px] font-semibold text-white hover:opacity-90"
            >
              <Mail className="h-3.5 w-3.5" />
              {SUPPORT_EMAIL}
            </a>
          </Surface>
          <Surface padding="panel">
            <BookOpen className="mb-2 h-5 w-5 text-cy-accent" strokeWidth={1.75} />
            <h3 className="text-[14px] font-[650] text-cy-ink">Methodology & references</h3>
            <ul className="mt-1.5 space-y-1.5 text-[12.5px]">
              <li>
                <Link href="/methodology" className="text-cy-accent hover:underline">
                  Calculation methodology
                </Link>
                <span className="text-cy-faint"> — factors, hierarchy, WTT, dual Scope 2</span>
              </li>
              <li>
                <Link href="/security" className="text-cy-accent hover:underline">
                  Security practices
                </Link>
              </li>
              <li>
                <Link href="/roadmap" className="text-cy-accent hover:underline">
                  Product roadmap
                </Link>
                <span className="text-cy-faint"> — what ships next (LCA, EPD, PCAF)</span>
              </li>
              <li>
                <Link href="/billing" className="text-cy-accent hover:underline">
                  Plans & billing
                </Link>
              </li>
            </ul>
          </Surface>
        </div>
      </div>
    </AppShell>
  );
}
