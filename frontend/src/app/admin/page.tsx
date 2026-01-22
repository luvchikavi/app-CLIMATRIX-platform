'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { api, AdminStats, AdminOrganization, AdminUser, AdminActivity, AdminOrgReport } from '@/lib/api';
import { AppShell } from '@/components/layout';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  ScopeBadge,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui';
import { formatCO2e } from '@/lib/utils';
import {
  Loader2,
  Building2,
  Users,
  Activity,
  TrendingUp,
  RefreshCw,
  ChevronRight,
  ArrowLeft,
  Shield,
  Calendar,
  Globe,
  BarChart3,
} from 'lucide-react';

type TabType = 'overview' | 'organizations' | 'users' | 'activities';

export default function AdminDashboard() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [organizations, setOrganizations] = useState<AdminOrganization[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [activities, setActivities] = useState<AdminActivity[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<string | null>(null);
  const [orgReport, setOrgReport] = useState<AdminOrgReport | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isAuthenticated) {
      router.push('/');
      return;
    }

    // Check if user is super admin
    if (mounted && isAuthenticated && user?.role !== 'super_admin') {
      router.push('/dashboard');
      return;
    }
  }, [mounted, isAuthenticated, user, router]);

  // Load data when authenticated
  useEffect(() => {
    if (mounted && isAuthenticated && user?.role === 'super_admin') {
      loadData();
    }
  }, [mounted, isAuthenticated, user]);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [statsData, orgsData, usersData, activitiesData] = await Promise.all([
        api.getAdminStats(),
        api.getAdminOrganizations(),
        api.getAdminUsers(),
        api.getAdminActivities(0, 50),
      ]);
      setStats(statsData);
      setOrganizations(orgsData);
      setUsers(usersData);
      setActivities(activitiesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load admin data');
    } finally {
      setIsLoading(false);
    }
  };

  const loadOrgReport = async (orgId: string) => {
    try {
      const report = await api.getAdminOrgReport(orgId);
      setOrgReport(report);
      setSelectedOrg(orgId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load organization report');
    }
  };

  if (!mounted || !isAuthenticated || user?.role !== 'super_admin') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  // Organization detail view
  if (selectedOrg && orgReport) {
    const org = organizations.find(o => o.id === selectedOrg);
    return (
      <AppShell>
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="ghost"
            onClick={() => {
              setSelectedOrg(null);
              setOrgReport(null);
            }}
            leftIcon={<ArrowLeft className="w-4 h-4" />}
          >
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
              <Building2 className="w-6 h-6" />
              {orgReport.organization.name}
            </h1>
            <p className="text-foreground-muted mt-1">
              {orgReport.organization.country_code || 'Global'} • {formatCO2e(orgReport.total_co2e_kg)} total emissions
            </p>
          </div>
        </div>

        {/* Scope Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card padding="lg" className="bg-scope-1/10 border-scope-1/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-scope-1">Scope 1</p>
                <p className="text-2xl font-bold text-foreground mt-1">
                  {formatCO2e(orgReport.by_scope.scope_1.total_co2e_kg)}
                </p>
              </div>
              <span className="text-sm text-foreground-muted">
                {orgReport.by_scope.scope_1.activity_count} activities
              </span>
            </div>
          </Card>
          <Card padding="lg" className="bg-scope-2/10 border-scope-2/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-scope-2">Scope 2</p>
                <p className="text-2xl font-bold text-foreground mt-1">
                  {formatCO2e(orgReport.by_scope.scope_2.total_co2e_kg)}
                </p>
              </div>
              <span className="text-sm text-foreground-muted">
                {orgReport.by_scope.scope_2.activity_count} activities
              </span>
            </div>
          </Card>
          <Card padding="lg" className="bg-scope-3/10 border-scope-3/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-scope-3">Scope 3</p>
                <p className="text-2xl font-bold text-foreground mt-1">
                  {formatCO2e(orgReport.by_scope.scope_3.total_co2e_kg)}
                </p>
              </div>
              <span className="text-sm text-foreground-muted">
                {orgReport.by_scope.scope_3.activity_count} activities
              </span>
            </div>
          </Card>
        </div>

        {/* Activities Table */}
        <Card>
          <CardHeader>
            <CardTitle>All Activities</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Scope</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Quantity</TableHead>
                  <TableHead className="text-right">CO2e</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[
                  ...orgReport.by_scope.scope_1.activities,
                  ...orgReport.by_scope.scope_2.activities,
                  ...orgReport.by_scope.scope_3.activities,
                ].map((act: any) => (
                  <TableRow key={act.id}>
                    <TableCell>
                      <ScopeBadge scope={parseInt(act.category_code.split('.')[0]) as 1 | 2 | 3 || 1} />
                    </TableCell>
                    <TableCell className="text-foreground-muted">{act.category_code}</TableCell>
                    <TableCell className="font-medium">{act.description}</TableCell>
                    <TableCell>{act.quantity} {act.unit}</TableCell>
                    <TableCell className="text-right font-semibold">
                      {act.co2e_kg?.toLocaleString(undefined, { maximumFractionDigits: 2 })} kg
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </AppShell>
    );
  }

  return (
    <AppShell>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Shield className="w-6 h-6 text-primary" />
            Admin Dashboard
          </h1>
          <p className="text-foreground-muted mt-1">
            View all organizations, users, and activity logs
          </p>
        </div>
        <Button
          variant="ghost"
          onClick={loadData}
          leftIcon={<RefreshCw className="w-4 h-4" />}
          disabled={isLoading}
        >
          Refresh
        </Button>
      </div>

      {/* Error State */}
      {error && (
        <Card padding="lg" className="mb-6 bg-error-50 border-error/20">
          <p className="text-error">{error}</p>
        </Card>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-foreground-muted">Loading admin data...</span>
        </div>
      )}

      {!isLoading && stats && (
        <>
          {/* Stats Overview */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary-light">
                  <Building2 className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Organizations</p>
                  <p className="text-2xl font-bold">{stats.total_organizations}</p>
                </div>
              </div>
            </Card>
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-info-light">
                  <Users className="w-5 h-5 text-info" />
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Users</p>
                  <p className="text-2xl font-bold">{stats.total_users}</p>
                </div>
              </div>
            </Card>
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-success-light">
                  <Activity className="w-5 h-5 text-success" />
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Activities</p>
                  <p className="text-2xl font-bold">{stats.total_activities}</p>
                </div>
              </div>
            </Card>
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-warning-light">
                  <TrendingUp className="w-5 h-5 text-warning" />
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Total CO2e</p>
                  <p className="text-2xl font-bold">{stats.total_co2e_tonnes.toFixed(1)}t</p>
                </div>
              </div>
            </Card>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-6 border-b border-border pb-2">
            {[
              { key: 'overview', label: 'Overview', icon: BarChart3 },
              { key: 'organizations', label: 'Organizations', icon: Building2 },
              { key: 'users', label: 'Users', icon: Users },
              { key: 'activities', label: 'Activity Log', icon: Activity },
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key as TabType)}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  activeTab === key
                    ? 'bg-primary text-white'
                    : 'text-foreground-muted hover:bg-background-muted'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recent Organizations */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-foreground-muted" />
                    Recent Organizations
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {organizations.slice(0, 5).map((org) => (
                      <div
                        key={org.id}
                        className="flex items-center justify-between p-3 rounded-lg bg-background-muted hover:bg-background-elevated cursor-pointer transition-colors"
                        onClick={() => loadOrgReport(org.id)}
                      >
                        <div>
                          <p className="font-medium">{org.name}</p>
                          <p className="text-sm text-foreground-muted">
                            {org.user_count} users • {org.activity_count} activities
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold">
                            {formatCO2e(org.total_co2e_kg)}
                          </span>
                          <ChevronRight className="w-4 h-4 text-foreground-muted" />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Recent Activity */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-foreground-muted" />
                    Recent Activity
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {activities.slice(0, 5).map((act) => (
                      <div key={act.id} className="p-3 rounded-lg bg-background-muted">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-medium text-primary">
                            {act.organization_name}
                          </span>
                          <ScopeBadge scope={act.scope as 1 | 2 | 3} />
                        </div>
                        <p className="font-medium text-sm truncate">{act.description}</p>
                        <p className="text-xs text-foreground-muted mt-1">
                          {act.quantity} {act.unit} • {act.co2e_kg?.toFixed(2)} kg CO2e
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === 'organizations' && (
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Organization</TableHead>
                      <TableHead>Country</TableHead>
                      <TableHead>Users</TableHead>
                      <TableHead>Activities</TableHead>
                      <TableHead className="text-right">Total CO2e</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {organizations.map((org) => (
                      <TableRow key={org.id} clickable onClick={() => loadOrgReport(org.id)}>
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            <Building2 className="w-4 h-4 text-foreground-muted" />
                            {org.name}
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="flex items-center gap-1 text-foreground-muted">
                            <Globe className="w-3 h-3" />
                            {org.country_code || org.default_region}
                          </span>
                        </TableCell>
                        <TableCell>{org.user_count}</TableCell>
                        <TableCell>{org.activity_count}</TableCell>
                        <TableCell className="text-right font-semibold">
                          {formatCO2e(org.total_co2e_kg)}
                        </TableCell>
                        <TableCell>
                          <ChevronRight className="w-4 h-4 text-foreground-muted" />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {activeTab === 'users' && (
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>User</TableHead>
                      <TableHead>Organization</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Last Login</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{user.full_name || 'Unnamed'}</p>
                            <p className="text-sm text-foreground-muted">{user.email}</p>
                          </div>
                        </TableCell>
                        <TableCell>{user.organization_name}</TableCell>
                        <TableCell>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            user.role === 'super_admin' ? 'bg-primary/10 text-primary' :
                            user.role === 'admin' ? 'bg-warning/10 text-warning' :
                            'bg-background-muted text-foreground-muted'
                          }`}>
                            {user.role}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className={`px-2 py-1 rounded text-xs ${
                            user.is_active ? 'bg-success/10 text-success' : 'bg-error/10 text-error'
                          }`}>
                            {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </TableCell>
                        <TableCell className="text-foreground-muted">
                          {user.last_login
                            ? new Date(user.last_login).toLocaleDateString()
                            : 'Never'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {activeTab === 'activities' && (
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Organization</TableHead>
                      <TableHead>Scope</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Quantity</TableHead>
                      <TableHead className="text-right">CO2e</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {activities.map((act) => (
                      <TableRow key={act.id}>
                        <TableCell className="font-medium text-primary">
                          {act.organization_name}
                        </TableCell>
                        <TableCell>
                          <ScopeBadge scope={act.scope as 1 | 2 | 3} />
                        </TableCell>
                        <TableCell className="max-w-xs truncate">{act.description}</TableCell>
                        <TableCell className="text-foreground-muted">
                          {act.quantity} {act.unit}
                        </TableCell>
                        <TableCell className="text-right font-semibold">
                          {act.co2e_kg?.toLocaleString(undefined, { maximumFractionDigits: 2 })} kg
                        </TableCell>
                        <TableCell className="text-foreground-muted text-sm">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {act.activity_date}
                          </span>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </AppShell>
  );
}
