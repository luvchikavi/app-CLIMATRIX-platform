'use client';

/**
 * Org EPD registry — every declaration project with its workflow status and
 * validity countdown. EPDs are created from a product page (the wizard
 * needs a product + pinned footprint); this page is the overview.
 */

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout';
import { Surface, PageHead } from '@/components/canopy';
import { EmptyState } from '@/components/ui';
import { LoadSampleDataButton } from '@/components/LoadSampleDataButton';
import { useEpds } from '@/hooks/useEpd';
import { EPD_STATUS_META } from '@/lib/epd';
import { cn } from '@/lib/utils';
import { FileStack, Loader2 } from 'lucide-react';

function ValidityCell({
  validUntil,
  days,
}: {
  validUntil: string | null;
  days: number | null;
}) {
  if (!validUntil || days == null) {
    return <span className="text-cy-faint">—</span>;
  }
  const warn = days < 180;
  return (
    <span className={cn('tabular-nums', warn ? 'font-semibold text-cy-warn' : 'text-cy-muted')}>
      {validUntil.slice(0, 10)}
      <span className="ml-1.5 text-[11px] text-cy-faint">
        {days < 0 ? `${-days}d overdue` : `${days}d left`}
      </span>
    </span>
  );
}

function EpdRegistryContent() {
  const router = useRouter();
  const { data: epds, isLoading } = useEpds();

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-cy-accent" />
      </div>
    );
  }

  return (
    <>
      <PageHead
        title="EPD registry"
        subtitle="Environmental Product Declarations in preparation — ISO 14025 / EN 15804+A2, verified through the verifier portal, published by your program operator"
      />

      {!epds?.length ? (
        <>
          <EmptyState
            icon={<FileStack className="h-8 w-8" />}
            title="No EPD projects yet"
            description="Open a product, compute + finalize its footprint, then hit “Prepare EPD” — the declaration pins that snapshot and walks the ISO 14025 workflow from there."
            action={{ label: 'Go to products', onClick: () => router.push('/products') }}
          />
          <div className="mt-4 flex flex-col items-center text-center">
            <LoadSampleDataButton caption="Or load sample data — it includes a ready EPD draft pinned to a finalized steel-coil footprint, so you can walk the whole ISO 14025 flow." />
          </div>
        </>
      ) : (
        <Surface padding="panel">
          <table className="w-full text-[13px]">
            <thead>
              <tr>
                {['Declaration', 'Product', 'Program operator', 'Status', 'Valid until', ''].map((h, i) => (
                  <th
                    key={i}
                    className="py-2 pr-3 text-left text-[10.5px] font-bold uppercase tracking-[0.07em] text-cy-faint"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {epds.map((e) => {
                const meta = EPD_STATUS_META[e.status];
                return (
                  <tr key={e.id} className="border-t border-cy-row">
                    <td className="py-2.5 pr-3">
                      <Link href={`/epd/${e.id}`} className="font-semibold text-cy-ink hover:text-cy-accent">
                        {e.name}
                      </Link>
                      <div className="text-[11px] text-cy-faint">
                        {e.pcr} · v{e.version}
                        {e.registration_number ? ` · ${e.registration_number}` : ''}
                      </div>
                    </td>
                    <td className="py-2.5 pr-3 text-cy-muted">{e.product_name}</td>
                    <td className="py-2.5 pr-3 text-cy-muted">{e.program_operator ?? '—'}</td>
                    <td className="py-2.5 pr-3">
                      <span className={cn('rounded-full px-2 py-0.5 text-[11px] font-semibold', meta.className)}>
                        {meta.label}
                      </span>
                    </td>
                    <td className="py-2.5 pr-3">
                      <ValidityCell validUntil={e.valid_until} days={e.days_until_expiry} />
                    </td>
                    <td className="py-2.5 text-right">
                      <Link href={`/epd/${e.id}`} className="text-[12.5px] font-semibold text-cy-accent hover:underline">
                        Open →
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Surface>
      )}
    </>
  );
}

export default function EpdRegistryPage() {
  return (
    <AppShell>
      <EpdRegistryContent />
    </AppShell>
  );
}
