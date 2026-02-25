'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import { useAuthStore } from '@/stores/auth';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  useOrganization,
  useUpdateOrganization,
  useSupportedRegions,
  usePeriods,
  useCreatePeriod,
} from '@/hooks/useEmissions';
import { api, Invitation } from '@/lib/api';
import { COUNTRY_OPTIONS } from '@/lib/countries';
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
  toast,
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
  Edit2,
  Trash2,
  X,
  Lock,
  Unlock,
  Mail,
  RefreshCw,
  Send,
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
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [periodForm, setPeriodForm] = useState({
    name: '',
    start_date: '',
    end_date: '',
  });

  // Organization edit mode state (Task 2.2)
  const [isEditingOrg, setIsEditingOrg] = useState(false);
  const [orgForm, setOrgForm] = useState({
    name: '',
    country_code: '',
    industry_code: '',
  });
  const [orgSaving, setOrgSaving] = useState(false);

  // Invitation state (Task 2.3)
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteForm, setInviteForm] = useState({ email: '', role: 'editor' });
  const [inviteSending, setInviteSending] = useState(false);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [invitationsLoading, setInvitationsLoading] = useState(false);
  const [resendingId, setResendingId] = useState<string | null>(null);
  const [cancelingId, setCancelingId] = useState<string | null>(null);

  // Generate year options (current year and next 2 years, plus last 5 years)
  const currentYear = new Date().getFullYear();
  const yearOptions = Array.from({ length: 8 }, (_, i) => currentYear - 5 + i);

  // Handle year selection - auto-fill form with defaults
  const handleYearSelect = (year: number) => {
    setSelectedYear(year);
    setPeriodForm({
      name: `FY ${year}`,
      start_date: `${year}-01-01`,
      end_date: `${year}-12-31`,
    });
  };
  const [mounted, setMounted] = useState(false);

  // All data fetching hooks (must be before any conditional returns)
  const { data: org, isLoading: orgLoading } = useOrganization();
  const { data: regions } = useSupportedRegions();
  const { data: periods } = usePeriods();
  const updateOrg = useUpdateOrganization();
  const createPeriod = useCreatePeriod();

  // Invitation fetcher (useCallback must be before conditional returns)
  const fetchInvitations = useCallback(async () => {
    setInvitationsLoading(true);
    try {
      const data = await api.getInvitations();
      setInvitations(data);
    } catch {
      // silently fail - invitations list is supplementary
    } finally {
      setInvitationsLoading(false);
    }
  }, []);

  // All useEffect hooks
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isAuthenticated) {
      router.push('/');
    }
  }, [mounted, isAuthenticated, router]);

  // Fetch invitations when users tab is active
  useEffect(() => {
    if (activeTab === 'users' && mounted && isAuthenticated) {
      fetchInvitations();
    }
  }, [activeTab, mounted, isAuthenticated, fetchInvitations]);

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
      setSelectedYear(null);
      setPeriodForm({ name: '', start_date: '', end_date: '' });
    } catch (error) {
      console.error('Failed to create period:', error);
    }
  };

  const handleClosePeriodModal = () => {
    setShowPeriodModal(false);
    setSelectedYear(null);
    setPeriodForm({ name: '', start_date: '', end_date: '' });
  };

  // --- Organization Edit Handlers (Task 2.2) ---
  const handleStartEditOrg = () => {
    setOrgForm({
      name: org?.name || '',
      country_code: org?.country_code || '',
      industry_code: org?.industry_code || '',
    });
    setIsEditingOrg(true);
  };

  const handleCancelEditOrg = () => {
    setIsEditingOrg(false);
  };

  const handleSaveOrg = async () => {
    if (!orgForm.name.trim()) return;
    setOrgSaving(true);
    try {
      await updateOrg.mutateAsync({
        name: orgForm.name.trim(),
        country_code: orgForm.country_code || null,
        industry_code: orgForm.industry_code || null,
      });
      setIsEditingOrg(false);
      toast.success('Organization updated successfully');
    } catch (error) {
      toast.error('Failed to update organization');
    } finally {
      setOrgSaving(false);
    }
  };

  // --- Invitation Handlers (Task 2.3) ---
  const handleSendInvite = async () => {
    if (!inviteForm.email.trim()) return;
    setInviteSending(true);
    try {
      await api.inviteUser(inviteForm.email.trim(), inviteForm.role);
      toast.success(`Invitation sent to ${inviteForm.email}`);
      setShowInviteModal(false);
      setInviteForm({ email: '', role: 'editor' });
      fetchInvitations();
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Failed to send invitation';
      toast.error(message);
    } finally {
      setInviteSending(false);
    }
  };

  const handleResendInvitation = async (id: string) => {
    setResendingId(id);
    try {
      await api.resendInvitation(id);
      toast.success('Invitation resent');
      fetchInvitations();
    } catch {
      toast.error('Failed to resend invitation');
    } finally {
      setResendingId(null);
    }
  };

  const handleCancelInvitation = async (id: string) => {
    setCancelingId(id);
    try {
      await api.cancelInvitation(id);
      toast.success('Invitation canceled');
      fetchInvitations();
    } catch {
      toast.error('Failed to cancel invitation');
    } finally {
      setCancelingId(null);
    }
  };

  const handleCloseInviteModal = () => {
    setShowInviteModal(false);
    setInviteForm({ email: '', role: 'editor' });
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
                    <div className="flex items-center justify-between w-full">
                      <CardTitle className="flex items-center gap-2">
                        <Building2 className="w-5 h-5 text-foreground-muted" />
                        Organization Details
                      </CardTitle>
                      {!isEditingOrg && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleStartEditOrg}
                          leftIcon={<Edit2 className="w-4 h-4" />}
                        >
                          Edit
                        </Button>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    {isEditingOrg ? (
                      <div className="space-y-4">
                        <Input
                          label="Organization Name"
                          value={orgForm.name}
                          onChange={(e) => setOrgForm({ ...orgForm, name: e.target.value })}
                          placeholder="Enter organization name"
                        />
                        <Select
                          label="Country"
                          options={COUNTRY_OPTIONS}
                          value={orgForm.country_code}
                          onChange={(e) => setOrgForm({ ...orgForm, country_code: e.target.value })}
                        />
                        <Input
                          label="Industry Code"
                          value={orgForm.industry_code}
                          onChange={(e) => setOrgForm({ ...orgForm, industry_code: e.target.value })}
                          placeholder="e.g., NACE A01, SIC 2911"
                        />
                        <div className="flex items-center gap-3 pt-2">
                          <Button
                            variant="primary"
                            onClick={handleSaveOrg}
                            disabled={!orgForm.name.trim() || orgSaving}
                            isLoading={orgSaving}
                          >
                            Save Changes
                          </Button>
                          <Button
                            variant="outline"
                            onClick={handleCancelEditOrg}
                            disabled={orgSaving}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
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
                            <Badge variant="secondary">
                              {COUNTRY_OPTIONS.find((c) => c.value === org.country_code)?.label || org.country_code}
                            </Badge>
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
                    )}
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
                {/* Team Members Card */}
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
                        onClick={() => setShowInviteModal(true)}
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

                      {/* Accepted invitations (other team members) */}
                      {invitations
                        .filter((inv) => inv.status === 'accepted')
                        .map((inv) => (
                          <div
                            key={inv.id}
                            className="flex items-center justify-between p-4 border border-border rounded-xl"
                          >
                            <div className="flex items-center gap-4">
                              <div className="w-10 h-10 rounded-full bg-success/20 flex items-center justify-center text-success font-semibold">
                                {inv.email.charAt(0).toUpperCase()}
                              </div>
                              <div>
                                <h3 className="font-semibold text-foreground">{inv.email}</h3>
                                <p className="text-sm text-foreground-muted">
                                  Joined {new Date(inv.created_at).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            <Badge variant={inv.role === 'admin' ? 'primary' : 'secondary'}>
                              {inv.role}
                            </Badge>
                          </div>
                        ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Pending Invitations Card */}
                <Card padding="lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Mail className="w-5 h-5 text-foreground-muted" />
                      Pending Invitations
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {invitationsLoading ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="w-6 h-6 animate-spin text-primary" />
                        <span className="ml-2 text-foreground-muted text-sm">Loading invitations...</span>
                      </div>
                    ) : invitations.filter((inv) => inv.status === 'pending').length > 0 ? (
                      <div className="space-y-3">
                        {invitations
                          .filter((inv) => inv.status === 'pending')
                          .map((inv) => (
                            <div
                              key={inv.id}
                              className="flex items-center justify-between p-4 border border-border rounded-xl"
                            >
                              <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-full bg-warning/20 flex items-center justify-center">
                                  <Mail className="w-5 h-5 text-warning" />
                                </div>
                                <div>
                                  <h3 className="font-semibold text-foreground">{inv.email}</h3>
                                  <p className="text-sm text-foreground-muted">
                                    Sent {new Date(inv.created_at).toLocaleDateString()}
                                  </p>
                                </div>
                              </div>
                              <div className="flex items-center gap-3">
                                <Badge variant={inv.role === 'admin' ? 'primary' : 'secondary'}>
                                  {inv.role}
                                </Badge>
                                <Badge variant="warning">Pending</Badge>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleResendInvitation(inv.id)}
                                  disabled={resendingId === inv.id}
                                  isLoading={resendingId === inv.id}
                                  leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                                >
                                  Resend
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="text-error border-error/30 hover:bg-error/10"
                                  onClick={() => handleCancelInvitation(inv.id)}
                                  disabled={cancelingId === inv.id}
                                  isLoading={cancelingId === inv.id}
                                  leftIcon={<X className="w-3.5 h-3.5" />}
                                >
                                  Cancel
                                </Button>
                              </div>
                            </div>
                          ))}
                      </div>
                    ) : (
                      <EmptyState
                        variant="minimal"
                        title="No pending invitations"
                        description="Invite team members to collaborate on your organization's emissions data."
                        action={{
                          label: 'Invite User',
                          onClick: () => setShowInviteModal(true),
                        }}
                      />
                    )}
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
            onClick={handleClosePeriodModal}
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
                onClick={handleClosePeriodModal}
                className="p-2 rounded-lg hover:bg-background-muted transition-colors"
              >
                <X className="w-5 h-5 text-foreground-muted" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-4">
              {/* Year Selector - Primary */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Select Year
                </label>
                <div className="flex flex-wrap gap-2">
                  {yearOptions.map((year) => (
                    <button
                      key={year}
                      type="button"
                      onClick={() => handleYearSelect(year)}
                      className={cn(
                        'px-4 py-2 rounded-lg border-2 font-medium transition-all',
                        selectedYear === year
                          ? 'border-primary bg-primary text-white'
                          : 'border-border bg-background hover:border-primary/50 text-foreground'
                      )}
                    >
                      {year}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-foreground-muted mt-2">
                  Select a year to auto-fill dates (Jan 1 - Dec 31)
                </p>
              </div>

              {/* Period Name - Auto-filled but editable */}
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

              {/* Date Range - Auto-filled but editable */}
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

              {/* Info box showing what will be created */}
              {periodForm.name && periodForm.start_date && periodForm.end_date && (
                <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
                  <p className="text-sm text-primary">
                    <span className="font-medium">Creating:</span> {periodForm.name} ({new Date(periodForm.start_date).toLocaleDateString()} - {new Date(periodForm.end_date).toLocaleDateString()})
                  </p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border">
              <Button variant="outline" onClick={handleClosePeriodModal}>
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

      {/* Invite User Modal (Task 2.3) */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-neutral-950/50 backdrop-blur-sm"
            onClick={handleCloseInviteModal}
          />

          {/* Modal */}
          <div className="relative bg-background-elevated rounded-2xl shadow-2xl max-w-md w-full animate-fade-in-up">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <div>
                <h2 className="text-lg font-semibold text-foreground">Invite Team Member</h2>
                <p className="text-sm text-foreground-muted">Send an invitation to join your organization</p>
              </div>
              <button
                onClick={handleCloseInviteModal}
                className="p-2 rounded-lg hover:bg-background-muted transition-colors"
              >
                <X className="w-5 h-5 text-foreground-muted" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-4">
              <Input
                label="Email Address"
                type="email"
                placeholder="colleague@company.com"
                value={inviteForm.email}
                onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
              />
              <Select
                label="Role"
                value={inviteForm.role}
                onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
                options={[
                  { value: 'viewer', label: 'Viewer - Can view data and reports' },
                  { value: 'editor', label: 'Editor - Can add and edit data' },
                  { value: 'admin', label: 'Admin - Full access' },
                ]}
              />
              <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
                <p className="text-sm text-primary">
                  An email will be sent with a link to create an account and join your organization.
                </p>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border">
              <Button variant="outline" onClick={handleCloseInviteModal}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleSendInvite}
                disabled={!inviteForm.email.trim() || inviteSending}
                isLoading={inviteSending}
                leftIcon={<Send className="w-4 h-4" />}
              >
                Send Invitation
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
