'use client';

import { useSites } from '@/hooks/useEmissions';
import { useSiteStore } from '@/stores/site';
import { Building2, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SiteSelectorProps {
  className?: string;
  compact?: boolean;
}

export function SiteSelector({ className, compact = false }: SiteSelectorProps) {
  const { data: sites } = useSites();
  const { selectedSiteId, setSelectedSiteId } = useSiteStore();

  if (!sites || sites.length === 0) return null;

  const selectedSite = sites.find((s) => s.id === selectedSiteId);

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Building2 className="w-4 h-4 text-foreground-muted flex-shrink-0" />
      <select
        value={selectedSiteId || ''}
        onChange={(e) => setSelectedSiteId(e.target.value || null)}
        className={cn(
          'px-2 py-1.5 rounded-lg border border-border bg-background-elevated',
          'text-sm text-foreground appearance-none cursor-pointer',
          'hover:border-neutral-300 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary',
          compact ? 'max-w-[180px]' : 'min-w-[200px]'
        )}
      >
        <option value="">All Sites</option>
        {sites.map((site) => (
          <option key={site.id} value={site.id}>
            {site.name}
          </option>
        ))}
      </select>
      {selectedSiteId && (
        <button
          onClick={() => setSelectedSiteId(null)}
          className="p-1 rounded hover:bg-background-muted text-foreground-muted hover:text-foreground transition-colors"
          title="Clear site filter"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}
