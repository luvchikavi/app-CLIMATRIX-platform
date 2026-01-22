'use client';

import { useState, useEffect, Suspense } from 'react';
import { useAuthStore } from '@/stores/auth';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  useOrganization,
  useUpdateOrganization,
  useSupportedRegions,
  usePeriods,
  useCreatePeriod,
} from '@/hooks/useEmissions';
import { AppShell } from '@/components/layout';
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Input,
  Select,
  Badge,
  EmptyState,
} from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  Building2,
  Globe,
  Calendar,
  Users,
  Shield,
  Loader2,
  Check,
  Plus,
  Edit,
  Trash2,
  X,
  Lock,
  Unlock,
} from 'lucide-react';

type SettingsTab = 'organization' | 'region' | 'periods' | 'users';

function SettingsPageContent() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialTab = (searchParams.get('tab') as SettingsTab) || 'organization';

  // All useState hooks
  const [activeTab, setActiveTab] = useState<SettingsTab>(initialTab);
  const [showPeriodModal, setShowPeriodModal] = useState(false);
  const [periodForm, setPeriodForm] = useState({
    name: '',
    start_date: '',
    end_date: '',
  });
  const [mounted, setMounted] = useState(false);

  // All data fetching hooks (must be before any conditional returns)
  const { data: org, isLoading: orgLoading } = useOrganization();
  const { data: regions } = useSupportedRegions();
  const { data: periods } = usePeriods();
  const updateOrg = useUpdateOrganization();
  const createPeriod = useCreatePeriod();

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

  const handleRegionChange = async (region: string) => {
    await updateOrg.mutateAsync({ default_region: region });
  };

  const handleCreatePeriod = async () => {
    if (!periodForm.name || !periodForm.start_date || !periodForm.end_date) return;

    try {
      await createPeriod.mutateAsync({
        name: periodForm.name,
        start_date: periodForm.start_date,
        end_date: periodForm.end_date,
      });
      setShowPeriodModal(false);
      setPeriodForm({ name: '', start_date: '', end_date: '' });
    } catch (error) {
      console.error('Failed to create period:', error);
    }
  };

  const tabs: { id: SettingsTab; label: string; icon: React.ElementType }[] = [
    { id: 'organization', label: 'Organization', icon: Building2 },
    { id: 'region', label: 'Region', icon: Globe },
    { id: 'periods', label: 'Periods', icon: Calendar },
    { id: 'users', label: 'Users', icon: Users },
  ];

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Settings</h1>
          <p className="text-foreground-muted mt-1">
            Manage your organization's settings and preferences
          </p>
        </div>
      </div>

      {/* Loading State */}
      {orgLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-foreground-muted">Loading settings...</span>
        </div>
      )}

      {/* Settings Content */}
      {!orgLoading && (
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Tab Navigation (Sidebar style on desktop) */}
          <div className="lg:w-64 flex-shrink-0">
            <nav className="space-y-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={cn(
                      'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-left',
                      activeTab === tab.id
                        ? 'bg-primary text-white'
                        : 'text-foreground hover:bg-background-muted'
                    )}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="font-medium">{tab.label}</span>
                  </button>
                );
              })}
            </nav>

            {/* Logout Button */}
            <div className="mt-8 pt-8 border-t border-border">
              <Button
                variant="outline"
                className="w-full text-error border-error/30 hover:bg-error/10"
                onClick={() => {
                  logout();
                  router.push('/');
                }}
              >
                Sign Out
              </Button>
            </div>
          </div>

          {/* Tab Content */}
          <div className="flex-1 min-w-0">
            {/* Organization Tab */}
            {activeTab === 'organization' && (
              <div className="space-y-6 animate-fade-in">
                <Card padding="lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Building2 className="w-5 h-5 text-foreground-muted" />
                      Organization Details
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      <div>
                        <label className="block text-sm font-medium text-foreground-muted mb-1">
                          Organization Name
                        </label>
                        <p className="text-lg font-semibold text-foreground">{org?.name}</p>
                      </div>

                      {org?.country_code && (
                        <div>
                          <label className="block text-sm font-medium text-foreground-muted mb-1">
                            Country
                          </label>
                          <Badge variant="secondary">{org.country_code}</Badge>
                        </div>
                      )}

                      {org?.industry_code && (
                        <div>
                          <label className="block text-sm font-medium text-foreground-muted mb-1">
                            Industry
                          </label>
                          <p className="text-foreground">{org.industry_code}</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Current User Card */}
                <Card padding="lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="w-5 h-5 text-foreground-muted" />
                      Your Account
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-foreground-muted mb-1">
                          Email
                        </label>
                        <p className="text-foreground">{user?.email}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-foreground-muted mb-1">
                          Role
                        </label>
                        <Badge variant={user?.role === 'admin' ? 'primary' : 'secondary'}>
                          {user?.role}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Region Tab */}
            {activeTab === 'region' && (
              <div className="space-y-6 animate-fade-in">
                <Card padding="lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Globe className="w-5 h-5 text-foreground-muted" />
                      Default Region
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-foreground-muted mb-6">
                      Select your region to use region-specific emission factors for electricity and other location-based calculations.
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {regions?.map((region) => (
                        <button
                          key={region.code}
                          onClick={() => handleRegionChange(region.code)}
                          disabled={updateOrg.isPending}
                          className={cn(
                            'p-4 rounded-xl border-2 text-left transition-all',
                            org?.default_region === region.code
                              ? 'border-primary bg-primary-light'
                              : 'border-border hover:border-primary/50 hover:bg-primary-light/50'
                          )}
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <h3 className="font-semibold text-foreground">{region.name}</h3>
                              <p className="text-sm text-foreground-muted mt-1">{region.description}</p>
                            </div>
                            {org?.default_region === region.code && (
                              <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                                <Check className="w-4 h-4 text-white" />
                              </div>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>

                    {updateOrg.isPending && (
                      <div className="mt-4 flex items-center gap-2 text-sm text-foreground-muted">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Saving...
                      </div>
                    )}

                    {updateOrg.isSuccess && !updateOrg.isPending && (
                      <div className="mt-4 flex items-center gap-2 text-sm text-success">
                        <Check className="w-4 h-4" />
                        Region updated successfully
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Periods Tab */}
            {activeTab === 'periods' && (
              <div className="space-y-6 animate-fade-in">
                <Card padding="lg">
                  <CardHeader>
                    <div className="flex items-center justify-between w-full">
                      <CardTitle className="flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-foreground-muted" />
                        Reporting Periods
                      </CardTitle>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => setShowPeriodModal(true)}
                        leftIcon={<Plus className="w-4 h-4" />}
                      >
                        Add Period
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {periods && periods.length > 0 ? (
                      <div className="space-y-3">
                        {periods.map((period) => (
                          <div
                            key={period.id}
                            className="flex items-center justify-between p-4 border border-border rounded-xl"
                          >
                            <div className="flex items-center gap-4">
                              <div className="p-2 rounded-lg bg-background-muted">
                                <Calendar className="w-5 h-5 text-foreground-muted" />
                              </div>
                              <div>
                                <h3 className="font-semibold text-foreground">{period.name}</h3>
                                <p className="text-sm text-foreground-muted">
                                  {new Date(period.start_date).toLocaleDateString()} - {new Date(period.end_date).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {period.is_locked ? (
                                <Badge variant="secondary">
                                  <Lock className="w-3 h-3 mr-1" />
                                  Locked
                                </Badge>
                              ) : (
                                <Badge variant="success">
                                  <Unlock className="w-3 h-3 mr-1" />
                                  Active
                                </Badge>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <EmptyState
                        variant="minimal"
                        title="No reporting periods"
                        description="Create your first reporting period to start tracking emissions."
                        action={{
                          label: 'Create Period',
                          onClick: () => setShowPeriodModal(true),
                        }}
                      />
                    )}
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Users Tab */}
            {activeTab === 'users' && (
              <div className="space-y-6 animate-fade-in">
                <Card padding="lg">
                  <CardHeader>
                    <div className="flex items-center justify-between w-full">
                      <CardTitle className="flex items-center gap-2">
                        <Users className="w-5 h-5 text-foreground-muted" />
                        Team Members
                      </CardTitle>
                      <Button
                        variant="primary"
                        size="sm"
                        leftIcon={<Plus className="w-4 h-4" />}
                        disabled
                      >
                        Invite User
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {/* Current user */}
                      <div className="flex items-center justify-between p-4 border border-border rounded-xl">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-white font-semibold">
                            {user?.email?.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <h3 className="font-semibold text-foreground">{user?.email}</h3>
                            <p className="text-sm text-foreground-muted">You</p>
                          </div>
                        </div>
                        <Badge variant={user?.role === 'admin' ? 'primary' : 'secondary'}>
                          {user?.role}
                        </Badge>
                      </div>
                    </div>

                    <div className="mt-6 p-4 bg-background-muted rounded-xl">
                      <p className="text-sm text-foreground-muted text-center">
                        Team management coming soon. Contact support to add more users.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create Period Modal */}
      {showPeriodModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-neutral-950/50 backdrop-blur-sm"
            onClick={() => setShowPeriodModal(false)}
          />

          {/* Modal */}
          <div className="relative bg-background-elevated rounded-2xl shadow-2xl max-w-md w-full animate-fade-in-up">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <div>
                <h2 className="text-lg font-semibold text-foreground">Create Reporting Period</h2>
                <p className="text-sm text-foreground-muted">Define a new reporting period</p>
              </div>
              <button
                onClick={() => setShowPeriodModal(false)}
                className="p-2 rounded-lg hover:bg-background-muted transition-colors"
              >
                <X className="w-5 h-5 text-foreground-muted" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Period Name *
                </label>
                <Input
                  placeholder="e.g., FY 2024, Q1 2024"
                  value={periodForm.name}
                  onChange={(e) => setPeriodForm({ ...periodForm, name: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1.5">
                    Start Date *
                  </label>
                  <Input
                    type="date"
                    value={periodForm.start_date}
                    onChange={(e) => setPeriodForm({ ...periodForm, start_date: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1.5">
                    End Date *
                  </label>
                  <Input
                    type="date"
                    value={periodForm.end_date}
                    onChange={(e) => setPeriodForm({ ...periodForm, end_date: e.target.value })}
                  />
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border">
              <Button variant="outline" onClick={() => setShowPeriodModal(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleCreatePeriod}
                disabled={!periodForm.name || !periodForm.start_date || !periodForm.end_date || createPeriod.isPending}
                isLoading={createPeriod.isPending}
              >
                Create Period
              </Button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

// Loading fallback for Suspense
function SettingsLoading() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-primary animate-spin" />
    </div>
  );
}

// Main export with Suspense boundary
export default function SettingsPage() {
  return (
    <Suspense fallback={<SettingsLoading />}>
      <SettingsPageContent />
    </Suspense>
  );
}
