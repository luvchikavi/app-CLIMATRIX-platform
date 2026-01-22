'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { useSites, useCreateSite, useDeleteSite, useSupportedRegions } from '@/hooks/useEmissions';
import { Site } from '@/lib/api';
import { AppShell } from '@/components/layout';
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
  Input,
  Select,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  EmptyState,
  Badge,
} from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  Plus,
  MapPin,
  Building2,
  Globe,
  Trash2,
  Edit,
  Loader2,
  X,
  AlertCircle,
  Zap,
  Factory,
} from 'lucide-react';

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
  const createSite = useCreateSite();
  const deleteSite = useDeleteSite();

  // All useEffect hooks
  useEffect(() => {
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
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
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

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Sites & Locations</h1>
          <p className="text-foreground-muted mt-1">
            Manage your organization's facilities and locations
          </p>
        </div>
        <Button
          variant="primary"
          onClick={openAddModal}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          Add Site
        </Button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-foreground-muted">Loading sites...</span>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && sites && sites.length === 0 && (
        <Card padding="lg">
          <EmptyState
            icon={<Building2 className="w-12 h-12" />}
            title="No sites yet"
            description="Add your first site to track emissions by location. Sites help you organize activities by facility or office."
            action={{
              label: 'Add Site',
              onClick: openAddModal,
            }}
          />
        </Card>
      )}

      {/* Sites Grid */}
      {!isLoading && sites && sites.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sites.map((site) => (
            <Card key={site.id} padding="lg" className="hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-xl bg-primary-light">
                  <Building2 className="w-6 h-6 text-primary" />
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
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
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDeleteConfirm(site.id)}
                    className="text-error hover:bg-error/10"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              <h3 className="text-lg font-semibold text-foreground">{site.name}</h3>

              {site.address && (
                <div className="flex items-start gap-2 mt-2">
                  <MapPin className="w-4 h-4 text-foreground-muted flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-foreground-muted">{site.address}</span>
                </div>
              )}

              <div className="flex items-center gap-4 mt-4 pt-4 border-t border-border-muted">
                {site.country_code && (
                  <div className="flex items-center gap-1.5">
                    <Globe className="w-4 h-4 text-foreground-muted" />
                    <span className="text-sm text-foreground-muted">{site.country_code}</span>
                  </div>
                )}
                {site.grid_region && (
                  <div className="flex items-center gap-1.5">
                    <Zap className="w-4 h-4 text-foreground-muted" />
                    <span className="text-sm text-foreground-muted">{site.grid_region}</span>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add/Edit Site Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-neutral-950/50 backdrop-blur-sm"
            onClick={() => setShowAddModal(false)}
          />

          {/* Modal */}
          <div className="relative bg-background-elevated rounded-2xl shadow-2xl max-w-md w-full animate-fade-in-up">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <div>
                <h2 className="text-lg font-semibold text-foreground">
                  {editingSite ? 'Edit Site' : 'Add New Site'}
                </h2>
                <p className="text-sm text-foreground-muted">
                  {editingSite ? 'Update site details' : 'Create a new facility or location'}
                </p>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-2 rounded-lg hover:bg-background-muted transition-colors"
              >
                <X className="w-5 h-5 text-foreground-muted" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Site Name *
                </label>
                <Input
                  placeholder="e.g., Headquarters, Factory A"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Country
                </label>
                <Select
                  value={formData.country_code}
                  onChange={(e) => setFormData({ ...formData, country_code: e.target.value })}
                  options={[
                    { value: '', label: 'Select country...' },
                    { value: 'IL', label: 'Israel' },
                    { value: 'US', label: 'United States' },
                    { value: 'GB', label: 'United Kingdom' },
                    { value: 'DE', label: 'Germany' },
                    { value: 'FR', label: 'France' },
                    { value: 'NL', label: 'Netherlands' },
                    { value: 'CN', label: 'China' },
                    { value: 'IN', label: 'India' },
                  ]}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Address
                </label>
                <Input
                  placeholder="Street address, city"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Grid Region
                </label>
                <Select
                  value={formData.grid_region}
                  onChange={(e) => setFormData({ ...formData, grid_region: e.target.value })}
                  options={[
                    { value: '', label: 'Auto-detect from country...' },
                    ...(regions?.map((r) => ({ value: r.code, label: r.name })) || []),
                  ]}
                />
                <p className="text-xs text-foreground-muted mt-1">
                  Used for Scope 2 electricity emission factors
                </p>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border">
              <Button variant="outline" onClick={() => setShowAddModal(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleSubmit}
                disabled={!formData.name.trim() || createSite.isPending}
                isLoading={createSite.isPending}
              >
                {editingSite ? 'Save Changes' : 'Add Site'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-neutral-950/50 backdrop-blur-sm"
            onClick={() => setDeleteConfirm(null)}
          />

          {/* Modal */}
          <div className="relative bg-background-elevated rounded-2xl shadow-2xl max-w-sm w-full animate-fade-in-up">
            <div className="p-6 text-center">
              <div className="w-12 h-12 rounded-full bg-error/10 flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-6 h-6 text-error" />
              </div>
              <h2 className="text-lg font-semibold text-foreground">Delete Site?</h2>
              <p className="text-sm text-foreground-muted mt-2">
                This will permanently delete this site. Activities associated with this site will be unassigned.
              </p>
            </div>

            <div className="flex items-center justify-center gap-3 px-6 py-4 border-t border-border">
              <Button variant="outline" onClick={() => setDeleteConfirm(null)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={() => handleDelete(deleteConfirm)}
                isLoading={deleteSite.isPending}
              >
                Delete Site
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
      <Loader2 className="w-8 h-8 text-primary animate-spin" />
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
