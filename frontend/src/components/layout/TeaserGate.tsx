'use client';

/**
 * Teaser phase-2 UX — the trial "show the capability, withhold the deliverable"
 * layer, rendered on top of the server-side entitlement gates.
 *
 * - TrialWatermark: wraps on-screen results while trialing so they read as a
 *   preview (faint diagonal watermark + a quiet "subscribe to export" band),
 *   never a clean exportable artifact.
 * - ExpiredPaywall: the day-15 gate — trial over, data preserved, subscribe.
 * - ReportTeaserGate: picks the right treatment for a report surface.
 */

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Lock, Sparkles } from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui';

export function useEntitlementFlags() {
  const { data } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => api.getSubscription(),
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
  return {
    isTrialing: !!data?.is_trialing,
    isExpired: !!data?.is_expired,
    plan: data?.plan ?? 'free',
    limits: data?.plan_limits,
    loaded: !!data,
  };
}

/** Faint, tiled, rotated wordmark — reads as a watermark without hiding data. */
function WatermarkLayer({ label }: { label: string }) {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 z-10 overflow-hidden select-none"
    >
      <div className="absolute inset-0 flex flex-col justify-around opacity-[0.05]">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="whitespace-nowrap text-center text-[34px] font-extrabold uppercase tracking-[0.35em] text-cy-ink"
            style={{ transform: 'rotate(-24deg)' }}
          >
            {`${label} ${label} ${label} ${label}`}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Wrap on-screen results during a trial. Paid/non-trial users get the children
 * untouched (zero cost). The watermark is non-interactive; the data underneath
 * stays fully readable — the point is "you can see it, you can't take it".
 */
export function TrialWatermark({
  children,
  label = 'Trial preview',
}: {
  children: React.ReactNode;
  label?: string;
}) {
  const { isTrialing } = useEntitlementFlags();
  if (!isTrialing) return <>{children}</>;
  return (
    <div className="relative">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-cy border border-cy-accent/25 bg-cy-accent-soft px-4 py-2.5">
        <span className="flex items-center gap-2 text-[12.5px] font-semibold text-cy-accent">
          <Sparkles className="h-4 w-4" strokeWidth={1.75} aria-hidden="true" />
          Trial preview — the numbers are real, exports unlock on a plan
        </span>
        <Link href="/pricing">
          <Button size="sm">Subscribe to export</Button>
        </Link>
      </div>
      <div className="relative">
        <WatermarkLayer label={label} />
        {children}
      </div>
    </div>
  );
}

/**
 * The day-15 paywall: the trial ended (is_expired). Data is preserved; the
 * value EXTRACTION is what's gated. Shown in place of a gated surface.
 */
export function ExpiredPaywall({
  title = 'Your trial has ended',
  blurb = 'Everything you built is safe and still here. Subscribe to view and export audit-ready reports again.',
}: {
  title?: string;
  blurb?: string;
}) {
  return (
    <div className="mx-auto max-w-lg rounded-cy border border-cy-row bg-background-elevated p-8 text-center shadow-sm">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-cy-accent-soft">
        <Lock className="h-5 w-5 text-cy-accent" strokeWidth={1.75} aria-hidden="true" />
      </div>
      <h3 className="text-[17px] font-bold tracking-[-0.01em] text-foreground">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-[13px] text-cy-muted">{blurb}</p>
      <div className="mt-6 flex items-center justify-center gap-3">
        <Link href="/pricing">
          <Button>See plans</Button>
        </Link>
        <Link href="/pricing#report-pass">
          <Button variant="outline">Report once a year?</Button>
        </Link>
      </div>
      <p className="mt-4 text-[11.5px] text-cy-faint">
        Your data, sites and audit trail are retained on the Free plan.
      </p>
    </div>
  );
}

/**
 * Report-surface gate: expired → paywall (blocks); trialing → watermark(children);
 * paid → children. Keeps the report page declarative.
 */
export function ReportTeaserGate({ children }: { children: React.ReactNode }) {
  const { isExpired } = useEntitlementFlags();
  if (isExpired) return <ExpiredPaywall />;
  return <TrialWatermark>{children}</TrialWatermark>;
}
