'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import {
  api,
  AdminStats,
  AdminOrganization,
  AdminUser,
  AdminActivity,
  AdminOrgReport,
  CockpitData,
} from '@/lib/api';
import { AppShell } from '@/components/layout';
import { LeadsPanel } from '@/components/admin/LeadsPanel';
import { Surface, PanelLabel, StatCells, BarList } from '@/components/canopy';
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
import { formatCO2e, formatQty } from '@/lib/utils';
import {
  Loader2,
  Building2,
  Users,
  Activity,
  RefreshCw,
  ChevronRight,
  ArrowLeft,
  Shield,
  Calendar,
  Globe,
  BarChart3,
} from 'lucide-react';

type TabType = 'overview' | 'clients' | 'leads' | 'organizations' | 'users' | 'activities';

export default function AdminDashboard() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [cockpit, setCockpit] = useState<CockpitData | null>(null);
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
      const [statsData, cockpitData, orgsData, usersData, activitiesData] = await Promise.all([
        api.getAdminStats(),
        api.getAdminCockpit(),
        api.getAdminOrganizations(),
        api.getAdminUsers(),
        api.getAdminActivities(0, 50),
      ]);
      setStats(statsData);
      setCockpit(cockpitData);
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
            <h1 className="text-[20px] font-[650] tracking-[-0.01em] text-foreground flex items-center gap-2">
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
                <p className="text-[16px] font-[650] tabular-nums text-foreground mt-1">
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
                <p className="text-[16px] font-[650] tabular-nums text-foreground mt-1">
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
                <p className="text-[16px] font-[650] tabular-nums text-foreground mt-1">
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
                ].map((act) => (
                  <TableRow key={act.id}>
                    <TableCell>
                      <ScopeBadge scope={parseInt(act.category_code.split('.')[0]) as 1 | 2 | 3 || 1} />
                    </TableCell>
                    <TableCell className="text-foreground-muted">{act.category_code}</TableCell>
                    <TableCell className="font-medium">{act.description}</TableCell>
                    <TableCell>{formatQty(act.quantity)} {act.unit}</TableCell>
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
          <h1 className="text-[20px] font-[650] tracking-[-0.01em] text-foreground flex items-center gap-2">
            <Shield className="w-6 h-6 text-primary" />
            Super admin
          </h1>
          <p className="text-foreground-muted mt-1">
            The company cockpit — platform, revenue and pipeline at a glance.
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
          {/* Company glance: platform + revenue + pipeline in one quiet band */}
          <Surface className="mb-8">
            <PanelLabel>Company · at a glance</PanelLabel>
            <StatCells
              cells={[
                {
                  label: 'Organizations',
                  value: String(cockpit?.organizations_total ?? stats.total_organizations),
                  sub: `${cockpit?.organizations_active ?? '—'} active`,
                },
                { label: 'Users', value: String(stats.total_users) },
                {
                  label: 'MRR (list-price est.)',
                  value: `$${formatQty(cockpit?.mrr_usd ?? 0)}`,
                  sub: `${cockpit?.paying_orgs ?? 0} paying`,
                },
                { label: 'Active trials', value: String(cockpit?.trialing_orgs ?? 0) },
                {
                  label: 'Open leads',
                  value: String(cockpit?.leads_open ?? 0),
                  sub: `of ${cockpit?.leads_total ?? 0}`,
                },
                { label: 'Activities', value: stats.total_activities.toLocaleString() },
                {
                  label: 'Tracked emissions',
                  value: stats.total_co2e_tonnes.toLocaleString(undefined, {
                    maximumFractionDigits: 0,
                  }),
                  sub: 't CO₂e',
                },
              ]}
            />
          </Surface>

          {/* Tabs */}
          <div className="flex gap-2 mb-6 border-b border-cy-row pb-2">
            {[
              { key: 'overview', label: 'Overview', icon: BarChart3 },
              { key: 'clients', label: 'Clients', icon: Building2 },
              { key: 'leads', label: 'Leads', icon: Users },
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
          {activeTab === 'overview' && cockpit && (
            <>
            {(cockpit.attention.trials_expiring_7d.length > 0 ||
              cockpit.attention.stuck_orgs.length > 0 ||
              cockpit.attention.failed_ingests_7d.length > 0) && (
              <Surface tint="warn" className="mb-6">
                <PanelLabel>Needs you</PanelLabel>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <div>
                    <p className="mb-1.5 text-[11.5px] font-bold text-cy-warn">
                      Trials expiring · 7 days
                    </p>
                    {cockpit.attention.trials_expiring_7d.length === 0 ? (
                      <p className="text-[12px] text-cy-muted">None.</p>
                    ) : (
                      cockpit.attention.trials_expiring_7d.map((t) => (
                        <p key={t.organization_id} className="text-[12.5px] text-cy-ink">
                          {t.name}{' '}
                          <span className="text-cy-muted">
                            · {t.days_left}d left · {t.contact_email ?? '—'}
                          </span>
                        </p>
                      ))
                    )}
                  </div>
                  <div>
                    <p className="mb-1.5 text-[11.5px] font-bold text-cy-warn">
                      Signed up, no data yet
                    </p>
                    {cockpit.attention.stuck_orgs.length === 0 ? (
                      <p className="text-[12px] text-cy-muted">None.</p>
                    ) : (
                      cockpit.attention.stuck_orgs.slice(0, 5).map((s) => (
                        <p key={s.organization_id} className="text-[12.5px] text-cy-ink">
                          {s.name}{' '}
                          <span className="text-cy-muted">
                            · {s.days_since_signup}d · {s.contact_email ?? '—'}
                          </span>
                        </p>
                      ))
                    )}
                  </div>
                  <div>
                    <p className="mb-1.5 text-[11.5px] font-bold text-cy-warn">
                      Failed imports · 7 days
                    </p>
                    {cockpit.attention.failed_ingests_7d.length === 0 ? (
                      <p className="text-[12px] text-cy-muted">None.</p>
                    ) : (
                      cockpit.attention.failed_ingests_7d.slice(0, 5).map((f, i) => (
                        <p key={i} className="text-[12.5px] text-cy-ink">
                          {f.organization_name}{' '}
                          <span className="text-cy-muted">· {f.filename}</span>
                        </p>
                      ))
                    )}
                  </div>
                </div>
              </Surface>
            )}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Signups — last 14 days */}
              <Surface>
                <PanelLabel>Signups · last 14 days</PanelLabel>
                {(() => {
                  const max = Math.max(1, ...cockpit.signups_14d.map((d) => d.signups));
                  return (
                    <BarList
                      items={cockpit.signups_14d.slice(-7).map((d) => ({
                        label: new Date(d.day).toLocaleDateString(undefined, {
                          weekday: 'short',
                          day: 'numeric',
                        }),
                        value: String(d.signups),
                        pct: (d.signups / max) * 100,
                      }))}
                    />
                  );
                })()}
                <p className="mt-4 text-[11.5px] text-cy-muted">
                  {cockpit.signups_14d.reduce((sum, d) => sum + d.signups, 0)} signups in 14
                  days
                </p>
              </Surface>

              {/* Lead pipeline + plans */}
              <Surface>
                <PanelLabel>Lead pipeline</PanelLabel>
                {(() => {
                  const max = Math.max(1, ...cockpit.lead_pipeline.map((s) => s.count));
                  return (
                    <BarList
                      items={cockpit.lead_pipeline.map((s) => ({
                        label: s.status,
                        value: String(s.count),
                        pct: (s.count / max) * 100,
                      }))}
                    />
                  );
                })()}
                <div className="mt-5">
                  <PanelLabel>Plans</PanelLabel>
                  <StatCells
                    cells={cockpit.plans.map((p) => ({
                      label: p.plan,
                      value: String(p.orgs),
                      sub: p.mrr_usd > 0 ? `$${formatQty(p.mrr_usd)}/mo` : undefined,
                    }))}
                  />
                </div>
              </Surface>

              {/* Recent leads */}
              <Surface>
                <PanelLabel>Recent leads</PanelLabel>
                {cockpit.recent_leads.length === 0 ? (
                  <p className="text-[12.5px] text-cy-muted">
                    No leads yet — the website forms and the CBAM checker feed this list.
                  </p>
                ) : (
                  <div className="space-y-2.5">
                    {cockpit.recent_leads.map((lead) => (
                      <div
                        key={`${lead.email}-${lead.created_at}`}
                        className="flex items-center justify-between gap-3 text-[12.5px]"
                      >
                        <span className="min-w-0 truncate text-cy-ink">{lead.email}</span>
                        <span className="whitespace-nowrap text-cy-muted">
                          {lead.source} · {lead.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
                <button
                  onClick={() => setActiveTab('leads')}
                  className="mt-4 text-[12.5px] font-bold text-cy-accent"
                >
                  Open the lead CRM →
                </button>
              </Surface>

              {/* Recent signups */}
              <Surface>
                <PanelLabel>Recent signups</PanelLabel>
                {cockpit.recent_signups.length === 0 ? (
                  <p className="text-[12.5px] text-cy-muted">No signups yet.</p>
                ) : (
                  <div className="space-y-2.5">
                    {cockpit.recent_signups.map((signup) => (
                      <div
                        key={`${signup.email}-${signup.created_at}`}
                        className="flex items-center justify-between gap-3 text-[12.5px]"
                      >
                        <span className="min-w-0 truncate text-cy-ink">{signup.email}</span>
                        <span className="whitespace-nowrap text-cy-muted">
                          {signup.organization_name} ·{' '}
                          {new Date(signup.created_at).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                          })}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </Surface>
            </div>
            </>
          )}

          {activeTab === 'clients' && cockpit && (
            <div className="space-y-6">
              <Surface>
                <PanelLabel>
                  Clients · {cockpit.clients.length} — every number is live data
                </PanelLabel>
                <p className="mb-3 text-[11.5px] text-cy-muted">{cockpit.revenue_note}</p>
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse text-[12.5px]">
                    <thead>
                      <tr>
                        {['Organization', 'Contact', 'Plan', 'Status', 'Trial ends', 'Users', 'Rows', 'Last active', 't CO₂e'].map(
                          (h) => (
                            <th
                              key={h}
                              className="py-2 pr-3 text-left text-[10.5px] font-bold uppercase tracking-[0.07em] text-cy-faint"
                            >
                              {h}
                            </th>
                          )
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {cockpit.clients.map((c) => (
                        <tr key={c.id} className="border-t border-cy-row align-top">
                          <td className="py-2.5 pr-3 font-semibold text-cy-ink">
                            {c.name}
                            <div className="text-[11px] font-normal text-cy-faint">
                              since{' '}
                              {new Date(c.created_at).toLocaleDateString(undefined, {
                                month: 'short',
                                day: 'numeric',
                                year: '2-digit',
                              })}
                            </div>
                          </td>
                          <td className="py-2.5 pr-3 text-cy-muted">{c.contact_email ?? '—'}</td>
                          <td className="py-2.5 pr-3">
                            <span
                              className={
                                c.plan === 'professional' || c.plan === 'starter'
                                  ? 'rounded-full bg-cy-accent-soft px-2 py-0.5 text-[11px] font-bold text-cy-accent'
                                  : 'rounded-full bg-cy-row px-2 py-0.5 text-[11px] font-semibold text-cy-muted'
                              }
                            >
                              {c.plan}
                            </span>
                          </td>
                          <td className="py-2.5 pr-3 text-cy-muted">{c.status}</td>
                          <td className="py-2.5 pr-3 text-cy-muted">
                            {c.trial_ends_at
                              ? new Date(c.trial_ends_at).toLocaleDateString(undefined, {
                                  month: 'short',
                                  day: 'numeric',
                                })
                              : '—'}
                          </td>
                          <td className="py-2.5 pr-3 tabular-nums text-cy-muted">{c.users}</td>
                          <td className="py-2.5 pr-3 tabular-nums text-cy-muted">
                            {c.activities.toLocaleString()}
                          </td>
                          <td className="py-2.5 pr-3 text-cy-muted">
                            {c.last_activity_at
                              ? new Date(c.last_activity_at).toLocaleDateString(undefined, {
                                  month: 'short',
                                  day: 'numeric',
                                })
                              : 'never'}
                          </td>
                          <td className="py-2.5 pr-3 tabular-nums text-cy-ink">
                            {formatQty(c.total_co2e_tonnes)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Surface>

              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <Surface>
                  <PanelLabel>Finance — live</PanelLabel>
                  <StatCells
                    cells={[
                      {
                        label: 'MRR (list-price est.)',
                        value: `$${formatQty(cockpit.mrr_usd)}`,
                      },
                      { label: 'ARR run-rate', value: `$${formatQty(cockpit.arr_usd)}` },
                      { label: 'Paying orgs', value: String(cockpit.paying_orgs) },
                      { label: 'Trialing', value: String(cockpit.trialing_orgs) },
                    ]}
                  />
                  <p className="mt-3 text-[11.5px] text-cy-muted">{cockpit.revenue_note}</p>
                </Surface>
                <Surface>
                  <PanelLabel>Lead sources — live</PanelLabel>
                  {cockpit.lead_sources.length === 0 ? (
                    <p className="text-[12.5px] text-cy-muted">No leads captured yet.</p>
                  ) : (
                    <BarList
                      items={(() => {
                        const max = Math.max(1, ...cockpit.lead_sources.map((s) => s.count));
                        return cockpit.lead_sources.map((s) => ({
                          label: s.status,
                          value: String(s.count),
                          pct: (s.count / max) * 100,
                        }));
                      })()}
                    />
                  )}
                </Surface>
              </div>
            </div>
          )}

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
                          {formatQty(act.quantity)} {act.unit} • {act.co2e_kg?.toFixed(2)} kg CO2e
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === 'leads' && <LeadsPanel />}

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
                          {formatQty(act.quantity)} {act.unit}
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
