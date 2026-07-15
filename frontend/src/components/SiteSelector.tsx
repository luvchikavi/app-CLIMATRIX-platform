'use client';

import { useSites } from '@/hooks/useEmissions';
import { useSiteStore } from '@/stores/site';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SiteSelectorProps {
  className?: string;
  compact?: boolean;
}

export function SiteSelector({ className, compact = false }: SiteSelectorProps) {
  const { data: sites } = useSites();
  const { selectedSiteId, setSelectedSiteId } = useSiteStore();

  if (!sites || sites.length === 0) return null;

  return (
    <div className={cn('flex items-center gap-1.5', className)}>
      <select
        value={selectedSiteId || ''}
        onChange={(e) => setSelectedSiteId(e.target.value || null)}
        className={cn(
          'rounded-full border-0 px-3.5 py-1.5',
          'cursor-pointer appearance-none text-[12.5px] font-semibold',
          'focus:outline-none focus:ring-2 focus:ring-cy-accent',
          selectedSiteId ? 'bg-cy-accent-soft text-cy-accent' : 'bg-transparent text-cy-muted hover:bg-cy-row',
          compact ? 'max-w-[180px]' : 'min-w-[200px]'
        )}
      >
        <option value="">All sites</option>
        {sites.map((site) => (
          <option key={site.id} value={site.id}>
            {site.name}
          </option>
        ))}
      </select>
      {selectedSiteId && (
        <button
          onClick={() => setSelectedSiteId(null)}
          className="rounded-md p-1 text-cy-muted transition-colors hover:bg-cy-row hover:text-foreground"
          title="Clear site filter"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}
