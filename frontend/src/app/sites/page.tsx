'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import { useSites, useCreateSite, useDeleteSite, useSupportedRegions, usePeriods, useSitesBreakdown } from '@/hooks/useEmissions';
import { Site } from '@/lib/api';
import { AppShell } from '@/components/layout';
import { Surface, PanelLabel, PageHead } from '@/components/canopy';
import { Button, Input, Select, EmptyState } from '@/components/ui';
import { COUNTRY_OPTIONS } from '@/lib/countries';
import { formatCO2e } from '@/lib/utils';
import { Trash2, Edit, Loader2, X } from 'lucide-react';

function SitesPageContent() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  // All useState hooks
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingSite, setEditingSite] = useState<Site | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    country_code: '',
    address: '',
    grid_region: '',
  });
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  // All data fetching hooks (must be before any conditional returns)
  const { data: sites, isLoading } = useSites();
  const { data: regions } = useSupportedRegions();
  const { data: periods } = usePeriods();
  const { selectedPeriodId } = usePeriodStore();
  // Only trust the persisted period if it belongs to THIS org's list — a stale
  // localStorage value from another session/org would 404 every query.
  const activePeriodId = periods?.find((p) => p.id === selectedPeriodId)?.id ?? periods?.[0]?.id;
  const { data: sitesBreakdown } = useSitesBreakdown(activePeriodId);
  const createSite = useCreateSite();
  const deleteSite = useDeleteSite();

  // All useEffect hooks
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- pre-existing intentional state sync on mount/deps change; no behavior change
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isAuthenticated) {
      router.push('/');
    }
  }, [mounted, isAuthenticated, router]);

  // Conditional return AFTER all hooks
  if (!mounted || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-cy-accent animate-spin" />
      </div>
    );
  }

  const handleSubmit = async () => {
    if (!formData.name.trim()) return;

    try {
      await createSite.mutateAsync(formData);
      setShowAddModal(false);
      setFormData({ name: '', country_code: '', address: '', grid_region: '' });
    } catch (error) {
      console.error('Failed to create site:', error);
    }
  };

  const handleDelete = async (siteId: string) => {
    try {
      await deleteSite.mutateAsync(siteId);
      setDeleteConfirm(null);
    } catch (error) {
      console.error('Failed to delete site:', error);
    }
  };

  const openAddModal = () => {
    setEditingSite(null);
    setFormData({ name: '', country_code: '', address: '', grid_region: '' });
    setShowAddModal(true);
  };

  // Total across sites, for the quiet share bars.
  const grandTotal =
    sitesBreakdown?.reduce((sum, s) => sum + (s.total_co2e_kg || 0), 0) || 0;

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <PageHead
          title="Sites"
          subtitle="Your facilities and locations — one boundary, one profile each"
        />
        <Button variant="primary" onClick={openAddModal}>
          + Add site
        </Button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 animate-spin text-cy-accent" />
          <span className="ml-3 text-[13px] text-cy-muted">Loading sites…</span>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && sites && sites.length === 0 && (
        <Surface>
          <EmptyState
            title="No sites yet"
            description="Add your first site to track emissions by location. Sites help you organize activities by facility or office."
            action={{
              label: 'Add site',
              onClick: openAddModal,
            }}
          />
        </Surface>
      )}

      {/* Sites — one surface, quiet rows */}
      {!isLoading && sites && sites.length > 0 && (
        <Surface>
          <PanelLabel>Your sites</PanelLabel>
          <div className="divide-y divide-cy-row">
            {sites.map((site) => {
              const stats = sitesBreakdown?.find((s) => s.site_id === site.id);
              const pct = stats && grandTotal > 0 ? (stats.total_co2e_kg / grandTotal) * 100 : 0;
              const subParts = [
                site.address,
                site.country_code,
                site.grid_region,
                stats ? `${stats.activity_count} activities` : null,
              ].filter(Boolean);
              return (
                <div
                  key={site.id}
                  className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 py-3"
                >
                  <div className="min-w-0 flex-1">
                    <Link
                      href={`/sites/${site.id}`}
                      className="text-[13px] font-semibold text-cy-ink hover:text-cy-accent"
                    >
                      {site.name}
                    </Link>
                    <p className="mt-0.5 truncate text-[12px] text-cy-muted">
                      {subParts.join(' · ') || 'No details yet'}
                    </p>
                    {stats && (
                      <p className="mt-0.5 text-[11.5px] tabular-nums text-cy-faint">
                        S1 {formatCO2e(stats.scope_1_co2e_kg)} · S2 {formatCO2e(stats.scope_2_co2e_kg)} · S3{' '}
                        {formatCO2e(stats.scope_3_co2e_kg)}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="whitespace-nowrap text-[12.5px] tabular-nums text-cy-muted">
                      {stats ? (
                        <>
                          <span
                            aria-hidden="true"
                            className="mr-2 inline-block h-1 rounded-[2px] bg-cy-accent align-[2px]"
                            style={{ width: `${Math.max(2, (pct / 100) * 60)}px` }}
                          />
                          <b className="font-semibold text-cy-ink">{formatCO2e(stats.total_co2e_kg)}</b>
                          {grandTotal > 0 && ` · ${pct.toFixed(1)}%`}
                        </>
                      ) : (
                        <span className="text-cy-faint">no data yet</span>
                      )}
                    </span>
                    <span className="flex items-center gap-0.5">
                      <button
                        type="button"
                        onClick={() => {
                          setEditingSite(site);
                          setFormData({
                            name: site.name,
                            country_code: site.country_code || '',
                            address: site.address || '',
                            grid_region: site.grid_region || '',
                          });
                          setShowAddModal(true);
                        }}
                        className="cursor-pointer rounded-md p-1.5 text-cy-faint transition-colors hover:bg-cy-row hover:text-cy-ink"
                        title="Edit site"
                      >
                        <Edit className="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeleteConfirm(site.id)}
                        className="cursor-pointer rounded-md p-1.5 text-cy-faint transition-colors hover:bg-error-50 hover:text-error"
                        title="Delete site"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
          <button
            type="button"
            onClick={openAddModal}
            className="mt-3 cursor-pointer text-[12.5px] font-semibold text-cy-muted transition-colors hover:text-cy-accent"
          >
            + Add site
          </button>
        </Surface>
      )}

      {/* Add/Edit Site Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label="Site details">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setShowAddModal(false)}
          />

          {/* Modal */}
          <div className="relative w-full max-w-md rounded-cy bg-background-elevated shadow-xl animate-fade-in-up">
            {/* Modal Header */}
            <div className="flex items-start justify-between px-6 pb-2 pt-6">
              <div>
                <h2 className="text-[16px] font-bold tracking-[-0.01em] text-foreground">
                  {editingSite ? 'Edit site' : 'Add a site'}
                </h2>
                <p className="text-[12.5px] text-cy-muted">
                  {editingSite ? 'Update site details' : 'A facility or location emissions belong to'}
                </p>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="rounded-md p-1.5 text-cy-muted transition-colors hover:bg-cy-row hover:text-foreground"
                aria-label="Close"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="space-y-4 p-6">
              <Input
                label="Site name *"
                placeholder="e.g., Headquarters, Factory A"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
              <Select
                label="Country"
                value={formData.country_code}
                onChange={(e) => setFormData({ ...formData, country_code: e.target.value })}
                options={COUNTRY_OPTIONS}
              />
              <Input
                label="Address"
                placeholder="Street address, city"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              />
              <Select
                label="Grid region"
                value={formData.grid_region}
                onChange={(e) => setFormData({ ...formData, grid_region: e.target.value })}
                options={[
                  { value: '', label: 'Auto-detect from country…' },
                  ...(regions?.map((r) => ({ value: r.code, label: r.name })) || []),
                ]}
                hint="Used for Scope 2 electricity emission factors"
              />
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-2 px-6 pb-6">
              <Button variant="ghost" onClick={() => setShowAddModal(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleSubmit}
                disabled={!formData.name.trim() || createSite.isPending}
                isLoading={createSite.isPending}
              >
                {editingSite ? 'Save changes' : 'Add site'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label="Delete site">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setDeleteConfirm(null)}
          />

          {/* Modal */}
          <div className="relative w-full max-w-sm rounded-cy bg-background-elevated shadow-xl animate-fade-in-up">
            <div className="p-6 text-center">
              <h2 className="text-[16px] font-bold tracking-[-0.01em] text-foreground">Delete this site?</h2>
              <p className="mt-2 text-[12.5px] text-cy-muted">
                This permanently deletes the site. Its activities stay in the ledger, unassigned.
              </p>
            </div>

            <div className="flex items-center justify-center gap-2 px-6 pb-6">
              <Button variant="ghost" onClick={() => setDeleteConfirm(null)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={() => handleDelete(deleteConfirm)}
                isLoading={deleteSite.isPending}
              >
                Delete site
              </Button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

// Loading fallback for Suspense
function SitesLoading() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-cy-accent animate-spin" />
    </div>
  );
}

// Main export with Suspense boundary
export default function SitesPage() {
  return (
    <Suspense fallback={<SitesLoading />}>
      <SitesPageContent />
    </Suspense>
  );
}
