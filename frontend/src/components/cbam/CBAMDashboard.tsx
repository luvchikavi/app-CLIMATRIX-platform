'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { api } from '@/lib/api';
import type { CBAMDashboard as CBAMDashboardType } from '@/lib/types';
import { Loader2 } from 'lucide-react';

interface CBAMDashboardProps {
  onNavigate: (
    view: 'installations' | 'imports' | 'declaration' | 'reports' | 'calculator'
  ) => void;
}

export function CBAMDashboard({ onNavigate }: CBAMDashboardProps) {
  const [dashboard, setDashboard] = useState<CBAMDashboardType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await api.getCBAMDashboard();
      setDashboard(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-cy-accent" />
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="flex items-center gap-3 py-4">
          <span className="h-[7px] w-[7px] shrink-0 rounded-full bg-error" aria-hidden="true" />
          <span className="text-[12.5px] text-error">{error}</span>
          <Button variant="secondary" size="sm" onClick={loadDashboard}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Year at a glance — one surface, quiet cells */}
      <Card>
        <div className="mb-3.5 flex flex-wrap items-center justify-between gap-2">
          <p className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.08em] text-cy-faint">
            Your CBAM year · {dashboard?.year}
            <span className="rounded-full bg-info-50 px-2 py-0.5 text-[10px] font-bold normal-case tracking-normal text-info">
              {dashboard?.phase === 'transitional' ? 'Transitional phase' : 'Definitive phase'}
            </span>
          </p>
          <Button size="sm" onClick={() => onNavigate('calculator')}>
            Calculate emissions
          </Button>
        </div>
        <div className="flex flex-wrap gap-x-11 gap-y-2.5">
          <button
            type="button"
            onClick={() => onNavigate('installations')}
            className="cursor-pointer text-left"
          >
            <p className="text-[16px] font-[650] tabular-nums text-cy-ink">
              {dashboard?.installations.total || 0}
            </p>
            <p className="mt-0.5 text-[11.5px] text-cy-muted hover:text-cy-accent">Installations →</p>
          </button>
          <button
            type="button"
            onClick={() => onNavigate('imports')}
            className="cursor-pointer text-left"
          >
            <p className="text-[16px] font-[650] tabular-nums text-cy-ink">
              {dashboard?.imports.total_count || 0}
            </p>
            <p className="mt-0.5 text-[11.5px] text-cy-muted hover:text-cy-accent">Imports YTD →</p>
          </button>
          <div>
            <p className="text-[16px] font-[650] tabular-nums text-cy-ink">
              {(dashboard?.imports.total_mass_tonnes || 0).toFixed(1)}
              <small className="ml-1 text-[11.5px] font-medium text-cy-muted">t</small>
            </p>
            <p className="mt-0.5 text-[11.5px] text-cy-muted">Covered mass</p>
          </div>
          <div>
            <p className="text-[16px] font-[650] tabular-nums text-cy-ink">
              {(dashboard?.imports.total_emissions_tco2e || 0).toFixed(1)}
              <small className="ml-1 text-[11.5px] font-medium text-cy-muted">t CO₂e</small>
            </p>
            <p className="mt-0.5 text-[11.5px] text-cy-muted">Embedded emissions</p>
          </div>
        </div>
      </Card>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Emissions by Sector */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Emissions by Sector</CardTitle>
          </CardHeader>
          <CardContent>
            {dashboard?.by_sector && dashboard.by_sector.length > 0 ? (
              <div className="space-y-4">
                {dashboard.by_sector.map((sector) => {
                  const maxEmissions = Math.max(...dashboard.by_sector.map((s) => s.total_emissions_tco2e));
                  const percentage = maxEmissions > 0 ? (sector.total_emissions_tco2e / maxEmissions) * 100 : 0;

                  return (
                    <div key={sector.sector} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium capitalize">{sector.sector.replace('_', ' ')}</span>
                        <span className="text-foreground-muted">
                          {sector.total_emissions_tco2e.toFixed(1)} tCO2e ({sector.import_count} imports)
                        </span>
                      </div>
                      <div className="h-2 bg-background-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-cy-scope3 rounded-full transition-all"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 text-foreground-muted">
                <p className="text-[13px] font-semibold text-cy-ink">No imports recorded yet</p>
                <p className="mt-0.5 text-[12.5px] text-cy-muted">Your covered goods land here as you register them.</p>
                <Button variant="secondary" size="sm" className="mt-3" onClick={() => onNavigate('imports')}>
                  Add first import
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Annual declaration (definitive regime) */}
        <Card>
          <CardHeader>
            <CardTitle>Annual declaration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2.5">
              <p className="flex items-baseline gap-2.5 text-[12.5px] text-cy-muted">
                <span className="relative top-px h-2 w-2 shrink-0 rounded-full border-[1.5px] border-cy-warn" aria-hidden="true" />
                <span>
                  One annual declaration per year —{' '}
                  <span className="font-semibold text-foreground">2026 is due 30 September 2027</span>{' '}
                  with certificate surrender.
                </span>
              </p>
              <p className="flex items-baseline gap-2.5 text-[12.5px] text-cy-muted">
                <span className="relative top-px h-2 w-2 shrink-0 rounded-full bg-cy-accent" aria-hidden="true" />
                <span>
                  Transitional quarterly reporting ended 31 Dec 2025 — historical reports stay
                  read-only.
                </span>
              </p>
            </div>
            <Button className="w-full mt-4" onClick={() => onNavigate('declaration')}>
              Open annual declaration
            </Button>
            <Button variant="secondary" className="w-full mt-2" onClick={() => onNavigate('reports')}>
              View quarterly history
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Installations by Country */}
      {dashboard?.installations.by_country && Object.keys(dashboard.installations.by_country).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Installations by Country</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {Object.entries(dashboard.installations.by_country).map(([country, count]) => (
                <div
                  key={country}
                  className="flex items-center gap-1.5 rounded-full bg-cy-row px-3 py-1.5 text-[12px]"
                >
                  <span className="font-semibold">{country}</span>
                  <span className="text-cy-muted">({count})</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
