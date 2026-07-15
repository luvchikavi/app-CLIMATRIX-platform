'use client';

import { useState, type ReactNode } from 'react';
import { notFound } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  BarList,
  CanopyButton,
  CellValue,
  Chip,
  ChipGroup,
  DataTable,
  FinishBar,
  FocusCard,
  PageHead,
  PanelLabel,
  PillTabs,
  ShareBar,
  Shell,
  StatCells,
  StepDoneText,
  StepLockedText,
  StepRow,
  StepValue,
  Surface,
  TaskList,
  canopyFont,
  type CanopyColumn,
  type RailProps,
} from '@/components/canopy';

/**
 * Canopy visual QA surface (DESIGN-REVISION-PLAN.md §2.4). Dev-only: the
 * production build serves 404 here. Recreates the three locked mockup pages
 * (Dashboard / Plan / Reports, Galil Steel numbers) with the real kit, in
 * light and dark, plus a primitives inventory.
 */

const journeySteps = [
  { title: 'Measure', status: '51 activities · complete', state: 'done' as const, href: '#' },
  { title: 'Plan', status: 'Set your 2030 target', state: 'now' as const, href: '#' },
  { title: 'Report', status: 'Opens after your plan', state: 'locked' as const, href: '#' },
];

function railFor(active: string): RailProps {
  return {
    steps: journeySteps,
    nav: [
      { label: 'Dashboard', href: '#', active: active === 'Dashboard' },
      { label: 'Data hub', href: '#', active: active === 'Data hub' },
      { label: 'Plan', href: '#', active: active === 'Plan' },
      { label: 'Reports', href: '#', active: active === 'Reports' },
      {
        label: 'Tools',
        items: [
          { label: 'CBAM check', href: '#' },
          { label: 'Modules', href: '#' },
        ],
      },
      { label: 'Settings', href: '#' },
    ],
  };
}

function DashboardMock() {
  return (
    <Shell rail={railFor('Dashboard')}>
      <PageHead
        title="Good morning, Avi"
        subtitle="Measurement is done. One step left before your first report."
      />
      <FocusCard
        progress={{ fraction: 1 / 3, label: '1/3' }}
        kicker="Next · Plan"
        title="Set your 2030 reduction target"
        body="Takes about 10 minutes. Climatrix suggests a science-based target from your FY2025 baseline, then drafts the measures to hit it."
        action={{ label: 'Set my target', href: '#' }}
        skip={{ label: 'Not now', href: '#' }}
      />
      <Surface className="mb-4">
        <PanelLabel>Footprint · FY2025</PanelLabel>
        <StatCells
          cells={[
            { label: 'Total', value: '64,468', sub: 't CO₂e' },
            { label: 'Scope 1', value: '18,052', sub: '28%', scope: 1 },
            { label: 'Scope 2', value: '38,383', sub: '60%', scope: 2 },
            { label: 'Scope 3', value: '8,034', sub: '12%', scope: 3 },
          ]}
        />
      </Surface>
      <div className="grid gap-4 md:grid-cols-2">
        <Surface>
          <PanelLabel>Largest sources</PanelLabel>
          <BarList
            items={[
              { label: 'Israel grid electricity', value: '38,383 t', pct: 100 },
              { label: 'Natural gas — furnaces', value: '14,830 t', pct: 39 },
              { label: 'Fuel & energy WTT', value: '7,556 t', pct: 20 },
              { label: 'Diesel — fleet', value: '3,221 t', pct: 8 },
            ]}
          />
        </Surface>
        <Surface>
          <PanelLabel>What needs you</PanelLabel>
          <TaskList
            items={[
              {
                state: 'open',
                text: 'Set a reduction target',
                hint: 'unlocks your plan',
                action: { label: 'Start →', href: '#' },
              },
              { state: 'open', text: '3 rows awaiting review in Data', hint: '2 min' },
              { state: 'done', text: 'FY2025 data complete', hint: 'imported 12 Jul' },
            ]}
          />
        </Surface>
      </div>
    </Shell>
  );
}

function PlanMock() {
  return (
    <Shell rail={railFor('Plan')}>
      <PageHead
        title="Your path to 2030"
        subtitle="Five steps from baseline to a tracked plan. You're on step 2."
      />
      <Surface padding="tight">
        <StepRow
          num={1}
          state="done"
          title="Baseline"
          description={
            <>
              FY2025 · <StepValue>64,468 t CO₂e</StepValue> across 51 activities. Largest source:
              grid electricity, 60%.
            </>
          }
          action={<StepDoneText />}
        />
        <StepRow
          num={2}
          state="now"
          title="Set your target"
          description={
            <>
              SBTi 1.5°C suggests <StepValue>−42% by 2030</StepValue> → 37,392 t. Adjust it or
              pick a custom path.
            </>
          }
          action={
            <CanopyButton href="#" className="px-3.5 py-2">
              Set target
            </CanopyButton>
          }
        />
        <StepRow
          num={3}
          title="Choose measures"
          description="Matched to your data — every number shows where it comes from."
          action={<StepLockedText>After target</StepLockedText>}
        >
          <div className="mt-2">
            {[
              {
                name: 'Renewable PPA — 30% of grid',
                chips: ['your data', 'IL price', 'IEA'],
                value: '−11,515 t',
                detail: '$0.4M · 3.1y payback',
              },
              {
                name: 'Furnace heat recovery',
                chips: ['your data', 'BAT BREF'],
                value: '−2,225 t',
                detail: '$1.1M · 4.8y',
              },
              {
                name: 'Fleet: 40% electric by 2028',
                chips: ['your data', 'AI assumption'],
                value: '−1,288 t',
                detail: '$0.9M · 6.2y',
              },
            ].map((m) => (
              <div
                key={m.name}
                className="flex items-baseline justify-between gap-4 py-[7px] text-[12.5px]"
              >
                <span className="text-cy-ink">
                  {m.name}
                  <ChipGroup>
                    {m.chips.map((chip) => (
                      <Chip key={chip} variant={chip === 'your data' ? 'you' : 'default'}>
                        {chip}
                      </Chip>
                    ))}
                  </ChipGroup>
                </span>
                <span className="whitespace-nowrap tabular-nums text-cy-muted">
                  <b className="font-semibold text-cy-ink">{m.value}</b> · {m.detail}
                </span>
              </div>
            ))}
          </div>
        </StepRow>
        <StepRow
          num={4}
          state="locked"
          title="Your plan"
          description="Reduction vs. target, investment, savings — one line per year."
          action={<StepLockedText />}
        />
        <StepRow
          num={5}
          state="locked"
          title="Track"
          description="Actual vs. planned, every reporting period."
          action={<StepLockedText />}
        />
      </Surface>
    </Shell>
  );
}

interface CategoryRow {
  category: string;
  scope: number;
  activities: number;
  tonnes: string;
  share: number;
}

const categoryRows: CategoryRow[] = [
  { category: 'Purchased electricity', scope: 2, activities: 12, tonnes: '38,383', share: 59.5 },
  { category: 'Stationary combustion', scope: 1, activities: 18, tonnes: '14,830', share: 23.0 },
  { category: 'Fuel & energy (WTT)', scope: 3, activities: 2, tonnes: '7,556', share: 11.7 },
  { category: 'Mobile combustion', scope: 1, activities: 17, tonnes: '3,221', share: 5.0 },
  { category: 'Business travel', scope: 3, activities: 2, tonnes: '478', share: 0.8 },
];

const categoryColumns: CanopyColumn<CategoryRow>[] = [
  { key: 'category', header: 'Category', render: (r) => r.category },
  { key: 'scope', header: 'Scope', render: (r) => r.scope },
  { key: 'activities', header: 'Activities', align: 'right', render: (r) => r.activities },
  {
    key: 'tonnes',
    header: 't CO₂e',
    align: 'right',
    render: (r) => <CellValue>{r.tonnes}</CellValue>,
  },
  { key: 'share', header: 'Share', align: 'right', render: (r) => <ShareBar pct={r.share} /> },
];

function ReportsMock() {
  const [tab, setTab] = useState('summary');
  return (
    <Shell rail={railFor('Reports')}>
      <PageHead
        title="Reports — FY2025"
        subtitle="Everything here updates live from your data. Verify when you're ready."
      />
      <PillTabs
        className="mb-5"
        value={tab}
        onChange={setTab}
        tabs={[
          { id: 'summary', label: 'Summary' },
          { id: 'scope', label: 'By scope' },
          { id: 'site', label: 'By site' },
          { id: 'iso', label: 'ISO 14064' },
          { id: 'quality', label: 'Data quality' },
          { id: 'audit', label: 'Audit' },
          { id: 'export', label: 'Export' },
        ]}
      />
      <Surface className="mb-4">
        <PanelLabel>Footprint</PanelLabel>
        <StatCells
          cells={[
            { label: 'Total', value: '64,468', sub: 't CO₂e' },
            { label: 'Scope 1', value: '18,052', sub: '28%', scope: 1 },
            { label: 'Scope 2', value: '38,383', sub: '60%', scope: 2 },
            { label: 'Scope 3', value: '8,034', sub: '12%', scope: 3 },
          ]}
        />
      </Surface>
      <Surface className="mb-4">
        <PanelLabel>By category</PanelLabel>
        <DataTable columns={categoryColumns} rows={categoryRows} rowKey={(r) => r.category} />
      </Surface>
      <FinishBar
        status={{ label: 'Draft', tone: 'warn' }}
        summary="Data quality 3.0 / 5 · ready for internal review"
        action={{ label: 'Start verification', href: '#' }}
        exports={[{ label: 'PDF', href: '#' }, { label: 'CSV', href: '#' }, { label: 'CDP JSON', href: '#' }]}
      />
    </Shell>
  );
}

function PrimitivesMock() {
  return (
    <div
      className={cn(
        canopyFont.variable,
        'bg-cy-canvas p-6 font-cy text-[13.5px] leading-[1.55] text-cy-ink antialiased'
      )}
    >
      <div className="grid gap-4 md:grid-cols-2">
        <Surface>
          <PanelLabel>Buttons</PanelLabel>
          <div className="flex flex-wrap items-center gap-4">
            <CanopyButton>Primary action</CanopyButton>
            <CanopyButton variant="pill">Pill</CanopyButton>
            <CanopyButton variant="quiet">Quiet / skip</CanopyButton>
          </div>
        </Surface>
        <Surface>
          <PanelLabel>Chips — provenance</PanelLabel>
          <div className="flex flex-wrap items-center gap-1.5">
            <Chip variant="you">your data</Chip>
            <Chip>IL price</Chip>
            <Chip>IEA</Chip>
            <Chip>standard range</Chip>
            <Chip>AI assumption</Chip>
          </div>
        </Surface>
        <Surface tint="soft">
          <PanelLabel className="text-cy-accent">Surface · soft tint</PanelLabel>
          <p className="text-[13px] text-cy-muted">Marks anything active or current.</p>
        </Surface>
        <Surface tint="warn">
          <PanelLabel className="text-cy-warn">Surface · warn tint</PanelLabel>
          <p className="text-[13px] text-cy-muted">
            Soft-lock banners and gentle notices — the only other functional color.
          </p>
        </Surface>
      </div>
      <FinishBar
        className="mt-4"
        status={{ label: 'Verified ✓', tone: 'done' }}
        summary="The finish bar in its done state."
        exports={[{ label: 'PDF', href: '#' }]}
      />
    </div>
  );
}

function Section({
  title,
  mode,
  children,
}: {
  title: string;
  mode: 'light' | 'dark';
  children: ReactNode;
}) {
  return (
    <section className="mb-10">
      <h2 className="mb-3 text-sm font-semibold text-neutral-500">
        {title} · {mode}
      </h2>
      <div className={cn(mode, 'overflow-hidden rounded-xl shadow-lg')}>{children}</div>
    </section>
  );
}

export default function DesignPreviewPage() {
  if (process.env.NODE_ENV === 'production') {
    notFound();
  }
  return (
    <div className="min-h-screen bg-[#E9ECE8] px-4 py-8 lg:px-10">
      <div className="mx-auto max-w-[1200px]">
        <header className="mb-8">
          <p className="text-[11px] font-bold tracking-[0.09em] uppercase text-[#1F7A5C]">
            Canopy · design preview (dev only)
          </p>
          <h1 className="mt-1 text-xl font-semibold text-neutral-800">
            Console × Guide — Phase 1 component kit
          </h1>
          <p className="mt-1 max-w-[70ch] text-sm text-neutral-600">
            The three locked mockup pages rebuilt with the real kit (Galil Steel numbers), light
            and dark, plus the primitives. Nothing user-visible changes until batch 2.1.
          </p>
        </header>
        <Section title="Dashboard" mode="light">
          <DashboardMock />
        </Section>
        <Section title="Dashboard" mode="dark">
          <DashboardMock />
        </Section>
        <Section title="Plan" mode="light">
          <PlanMock />
        </Section>
        <Section title="Plan" mode="dark">
          <PlanMock />
        </Section>
        <Section title="Reports" mode="light">
          <ReportsMock />
        </Section>
        <Section title="Reports" mode="dark">
          <ReportsMock />
        </Section>
        <Section title="Primitives" mode="light">
          <PrimitivesMock />
        </Section>
        <Section title="Primitives" mode="dark">
          <PrimitivesMock />
        </Section>
      </div>
    </div>
  );
}
