'use client';

import { useState, useEffect, Suspense, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useQueries } from '@tanstack/react-query';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import { useSiteStore } from '@/stores/site';
import { usePeriods, useReportSummary, useActivities, useSitesBreakdown } from '@/hooks/useEmissions';
import { AppShell } from '@/components/layout';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  ScopeBadge,
  KPICard,
  ScopeKPI,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  EmptyState,
  toast,
} from '@/components/ui';
import { ScopePieChart } from '@/components/dashboard/ScopePieChart';
import { CategoryBreakdown } from '@/components/dashboard/CategoryBreakdown';
import { ScopeDrillDown } from '@/components/dashboard/ScopeDrillDown';
import { SiteBreakdownChart } from '@/components/dashboard/SiteBreakdownChart';
import { SiteSelector } from '@/components/SiteSelector';
import { LoadSampleDataButton } from '@/components/LoadSampleDataButton';
import { SampleDataHero } from '@/components/SampleDataHero';
import { cn, formatCO2e } from '@/lib/utils';
import { useFocusTrap } from '@/hooks/useFocusTrap';
import {
  RefreshCw,
  Loader2,
  Upload,
  X,
  Activity,
  TrendingDown,
  Leaf,
  BarChart3,
  PieChart,
  List,
  Calendar,
  ArrowRight,
  Download,
  Filter,
  Building2,
} from 'lucide-react';
import { api, CategorySummary } from '@/lib/api';

function DashboardContent() {
  const router = useRouter();
  const { isAuthenticated, organization, user } = useAuthStore();
  const { selectedPeriodId } = usePeriodStore();
  const { selectedSiteId } = useSiteStore();

  // All useState hooks at top
  const [mounted, setMounted] = useState(false);
  const [drillDownCategory, setDrillDownCategory] = useState<CategorySummary | null>(null);
  const [drillDownScope, setDrillDownScope] = useState<1 | 2 | 3 | null>(null);
  const categoryTrapRef = useFocusTrap<HTMLDivElement>(!!drillDownCategory);

  // All data fetching hooks (must be before any conditional returns)
  const { data: periods, isLoading: periodsLoading } = usePeriods();
  // Only trust the persisted period if it belongs to THIS org's list — a stale
  // localStorage value from another session/org would 404 every query.
  const globalPeriodId = periods?.find((p) => p.id === selectedPeriodId)?.id ?? periods?.[0]?.id;

  // What the user wants to SEE here: the top-bar period, a specific year, or
  // every period combined ('all'). Site filtering composes via SiteSelector.
  const [viewScope, setViewScope] = useState<'selected' | 'all' | string>('selected');
  const allMode = viewScope === 'all';
  const activePeriodId = allMode
    ? globalPeriodId
    : viewScope === 'selected'
      ? globalPeriodId
      : viewScope;

  const {
    data: periodSummary,
    isLoading: summaryLoading,
    isError: summaryError,
    refetch: refetchSummary
  } = useReportSummary(activePeriodId || '', selectedSiteId || undefined);

  const { data: periodActivities, isLoading: activitiesLoading } = useActivities(
    activePeriodId || '',
    selectedSiteId ? { site_id: selectedSiteId } : undefined
  );

  // 'All years': pull each period's summary + activities and merge client-side.
  const allSummaryQueries = useQueries({
    queries: (periods ?? []).map((p) => ({
      queryKey: ['report-summary', p.id, selectedSiteId],
      queryFn: () => api.getReportSummary(p.id, selectedSiteId || undefined),
      enabled: allMode,
    })),
  });
  const allActivityQueries = useQueries({
    queries: (periods ?? []).map((p) => ({
      queryKey: ['activities', p.id, selectedSiteId ? { site_id: selectedSiteId } : undefined],
      queryFn: () =>
        api.getActivities(p.id, selectedSiteId ? { site_id: selectedSiteId } : undefined),
      enabled: allMode,
    })),
  });

  const summary = allMode
    ? (() => {
        const parts = allSummaryQueries.map((q) => q.data).filter(Boolean);
        if (!parts.length) return undefined;
        const sum = (f: (s: NonNullable<typeof parts[number]>) => number | null | undefined) =>
          parts.reduce((n, s) => n + (f(s!) || 0), 0);
        const byCat = new Map<string, CategorySummary>();
        parts.forEach((s) =>
          (s!.by_category || []).forEach((c: CategorySummary) => {
            const prev = byCat.get(c.category_code);
            if (prev) {
              prev.total_co2e_kg += c.total_co2e_kg;
              prev.activity_count += c.activity_count;
            } else byCat.set(c.category_code, { ...c });
          })
        );
        return {
          ...parts[0]!,
          period_name: 'All years combined',
          total_co2e_kg: sum((s) => s.total_co2e_kg),
          scope_1_co2e_kg: sum((s) => s.scope_1_co2e_kg),
          scope_2_co2e_kg: sum((s) => s.scope_2_co2e_kg),
          scope_2_location_based_co2e_kg: sum((s) => s.scope_2_location_based_co2e_kg),
          scope_2_market_based_co2e_kg: null,
          scope_3_co2e_kg: sum((s) => s.scope_3_co2e_kg),
          scope_3_wtt_co2e_kg: sum((s) => s.scope_3_wtt_co2e_kg),
          total_co2e_tonnes: sum((s) => s.total_co2e_kg) / 1000,
          by_category: Array.from(byCat.values()).sort(
            (a, b) => b.total_co2e_kg - a.total_co2e_kg
          ),
        };
      })()
    : periodSummary;

  const activities = allMode
    ? allActivityQueries.flatMap((q) => q.data ?? [])
    : periodActivities;

  // Site breakdown chart: omitting the period id aggregates org-wide.
  const { data: sitesBreakdown } = useSitesBreakdown(allMode ? undefined : activePeriodId);

  // Reviewing a specific import lives on the Activity Ledger (its batch
  // filter) — the dashboard always shows the whole period.
  const filteredActivities = activities ?? [];

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

  // (Onboarding is now handled by the required /setup gate in AppShell.)

  // Conditional return AFTER all hooks
  if (!mounted || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  const isLoading = periodsLoading || summaryLoading;

  const displayTotals = {
    total: summary?.total_co2e_kg || 0,
    scope1: summary?.scope_1_co2e_kg || 0,
    scope2: summary?.scope_2_co2e_kg || 0,
    scope2LocationBased: summary?.scope_2_location_based_co2e_kg || 0,
    scope2MarketBased: summary?.scope_2_market_based_co2e_kg,
    scope3: summary?.scope_3_co2e_kg || 0,
  };

  // Calculate percentages for scope breakdown
  const totalEmissions = displayTotals.total;
  const scope1Pct = totalEmissions > 0 ? (displayTotals.scope1 / totalEmissions) * 100 : 0;
  const scope2Pct = totalEmissions > 0 ? (displayTotals.scope2 / totalEmissions) * 100 : 0;
  const scope3Pct = totalEmissions > 0 ? (displayTotals.scope3 / totalEmissions) * 100 : 0;

  // Get activity counts per scope (from filtered activities)
  const scope1Activities = filteredActivities.filter(a => a.activity.scope === 1).length;
  const scope2Activities = filteredActivities.filter(a => a.activity.scope === 2).length;
  const scope3Activities = filteredActivities.filter(a => a.activity.scope === 3).length;

  // Export activities to Excel (uses filtered activities)
  const exportToExcel = () => {
    if (filteredActivities.length === 0) return;

    // Create CSV content
    const headers = ['Scope', 'Category', 'Description', 'Activity Key', 'Quantity', 'Unit', 'Emission Factor', 'Factor Unit', 'CO2e (kg)', 'Source', 'Date'];
    const rows = filteredActivities.map(item => [
      `Scope ${item.activity.scope}`,
      item.activity.category_code,
      item.activity.description,
      item.activity.activity_key,
      item.activity.quantity,
      item.activity.unit,
      item.emission?.factor_value?.toFixed(4) || '',
      item.emission?.factor_unit || '',
      item.emission?.co2e_kg?.toFixed(2) || '',
      item.emission?.factor_source || '',
      item.activity.activity_date,
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    ].join('\n');

    // Download as CSV (Excel compatible)
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const exportName = summary?.period_name || 'export';
    a.download = `activities_${exportName}_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
          <div className="flex items-center gap-4 mt-1">
            <p className="text-foreground-muted">
              Track and manage your organization&apos;s emissions
            </p>
            {/* What to show: the top-bar period, one specific year, or everything */}
            <select
              value={viewScope}
              onChange={(e) => setViewScope(e.target.value)}
              className="rounded-lg border border-border bg-background px-2 py-1 text-sm text-foreground"
              title="Which data this dashboard shows"
            >
              <option value="selected">
                {periods?.find((p) => p.id === globalPeriodId)?.name || 'Current period'}
              </option>
              {(periods ?? [])
                .filter((p) => p.id !== globalPeriodId)
                .map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              <option value="all">All years combined</option>
            </select>
            <SiteSelector compact />
          </div>
        </div>
        {/* Analysis zone: the dashboard only READS the inventory. Data comes in
            through the Data Hub; exports live on Reports — one home per feature. */}
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetchSummary()}
            leftIcon={<RefreshCw className="w-4 h-4" />}
          >
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push('/hub')}
            leftIcon={<Upload className="w-4 h-4" />}
          >
            Data Hub
          </Button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-20" role="status" aria-live="polite">
          <Loader2 className="w-8 h-8 animate-spin text-primary" aria-hidden="true" />
          <span className="ml-3 text-foreground-muted">Loading dashboard...</span>
        </div>
      )}

      {/* Error State */}
      {!isLoading && summaryError && (
        <Card padding="lg">
          <div className="text-center py-8">
            <div className="mx-auto w-12 h-12 rounded-full bg-error/10 flex items-center justify-center mb-4">
              <X className="w-6 h-6 text-error" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              Failed to load dashboard data
            </h3>
            <p className="text-foreground-muted mb-4">
              There was a problem fetching your emissions data. This may be a temporary issue.
            </p>
            <Button
              variant="primary"
              onClick={() => refetchSummary()}
              leftIcon={<RefreshCw className="w-4 h-4" />}
            >
              Retry
            </Button>
          </div>
        </Card>
      )}

      {/* No Periods State */}
      {!isLoading && periods && periods.length === 0 && (
        <Card padding="lg">
          <EmptyState
            icon={<Calendar className="w-12 h-12" />}
            title="No reporting periods"
            description="Create a reporting period to start tracking your organization's emissions."
            action={{
              label: 'Create Period',
              onClick: () => router.push('/settings?tab=periods'),
            }}
          />
          <div className="flex flex-col items-center pb-8 -mt-8">
            <LoadSampleDataButton caption="Or explore Climatrix with a realistic sample dataset — removable in one click." />
          </div>
        </Card>
      )}

      {/* Dashboard Content */}
      {!isLoading && summary && (
        <div className="space-y-8 animate-fade-in">
          {/* Front-page hero for brand-new orgs: one click brings the whole
              app alive with the sample dataset — dashboard, report, scenarios.
              Self-hides while sample data is loaded. */}
          {totalEmissions === 0 && filteredActivities.length === 0 && <SampleDataHero />}

          {/* Total Emissions KPI */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
            <Card padding="lg" className="lg:col-span-1">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground-muted uppercase tracking-wide">
                    Total Emissions
                  </p>
                  <p className="text-4xl font-bold text-foreground mt-2 tracking-tight">
                    {formatCO2e(displayTotals.total)}
                  </p>
                  <p className="text-sm text-foreground-muted mt-1">
                    {summary.period_name}
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-primary-light">
                  <Leaf className="w-6 h-6 text-primary" />
                </div>
              </div>

              {/* Activity count */}
              <div className="mt-4 pt-4 border-t border-border-muted">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-foreground-muted">Total Activities</span>
                  <span className="font-semibold text-foreground">
                    {filteredActivities.length}
                  </span>
                </div>
              </div>
            </Card>

            {/* Scope KPIs */}
            <ScopeKPI
              scope={1}
              value={displayTotals.scope1}
              percentage={scope1Pct}
              activityCount={scope1Activities}
              onClick={() => scope1Activities > 0 && setDrillDownScope(1)}
            />
            <ScopeKPI
              scope={2}
              label="Scope 2 - Location-based"
              value={displayTotals.scope2LocationBased}
              percentage={scope2Pct}
              activityCount={scope2Activities}
              onClick={() => scope2Activities > 0 && setDrillDownScope(2)}
            />
            <ScopeKPI
              scope={2}
              label="Scope 2 - Market-based"
              value={displayTotals.scope2MarketBased ?? 0}
              activityCount={displayTotals.scope2MarketBased != null ? scope2Activities : undefined}
              onClick={() => scope2Activities > 0 && setDrillDownScope(2)}
            />
            <ScopeKPI
              scope={3}
              value={displayTotals.scope3}
              percentage={scope3Pct}
              activityCount={scope3Activities}
              onClick={() => scope3Activities > 0 && setDrillDownScope(3)}
            />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pie Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="w-5 h-5 text-foreground-muted" />
                  Emissions by Scope
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScopePieChart data={summary} />
              </CardContent>
            </Card>

            {/* Category Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-foreground-muted" />
                  Emissions by Category
                </CardTitle>
                <p className="text-xs text-foreground-muted mt-1">Click a category to see activities</p>
              </CardHeader>
              <CardContent>
                <CategoryBreakdown
                  categories={summary.by_category}
                  onCategoryClick={(category) => setDrillDownCategory(category)}
                />
              </CardContent>
            </Card>
          </div>

          {/* Site Breakdown Chart */}
          {sitesBreakdown && sitesBreakdown.length > 0 && !selectedSiteId && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-foreground-muted" />
                  Emissions by Site
                </CardTitle>
                <p className="text-xs text-foreground-muted mt-1">Click a site to filter the dashboard</p>
              </CardHeader>
              <CardContent>
                <SiteBreakdownChart
                  data={sitesBreakdown}
                  onSiteClick={(siteId) => useSiteStore.getState().setSelectedSiteId(siteId)}
                />
              </CardContent>
            </Card>
          )}

          {/* Activities Table */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between w-full">
                <CardTitle className="flex items-center gap-2">
                  <List className="w-5 h-5 text-foreground-muted" />
                  Recent Activities
                  <span className="ml-2 px-2 py-0.5 text-xs font-medium rounded-full bg-background-muted text-foreground-muted">
                    {filteredActivities.length}
                  </span>
                </CardTitle>
                <div className="flex items-center gap-2">
                  {filteredActivities.length > 0 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={exportToExcel}
                      leftIcon={<Download className="w-4 h-4" />}
                    >
                      Export
                    </Button>
                  )}
                  {filteredActivities.length > 10 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => router.push('/activities')}
                      rightIcon={<ArrowRight className="w-4 h-4" />}
                    >
                      View All
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {activitiesLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                </div>
              ) : filteredActivities.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Scope</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Activity</TableHead>
                      <TableHead>Quantity</TableHead>
                      <TableHead className="text-right">EF</TableHead>
                      <TableHead className="text-right">CO2e</TableHead>
                      <TableHead className="text-right">Source</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredActivities.slice(0, 10).map((item) => (
                      <TableRow key={item.activity.id} clickable>
                        <TableCell>
                          <ScopeBadge scope={item.activity.scope as 1 | 2 | 3} />
                        </TableCell>
                        <TableCell className="font-medium text-foreground max-w-xs truncate">
                          {item.activity.is_demo && (
                            <Badge variant="warning" size="sm" className="mr-1.5">
                              Demo
                            </Badge>
                          )}
                          {item.activity.description}
                        </TableCell>
                        <TableCell className="text-foreground-muted font-mono text-xs">
                          {item.activity.activity_key}
                        </TableCell>
                        <TableCell className="text-foreground-muted">
                          {item.activity.quantity.toLocaleString()} {item.activity.unit}
                        </TableCell>
                        <TableCell className="text-right text-xs text-foreground-muted">
                          {item.emission?.factor_value
                            ? `${item.emission.factor_value.toLocaleString(undefined, { maximumFractionDigits: 4 })} ${item.emission.factor_unit || ''}`
                            : '-'}
                        </TableCell>
                        <TableCell className="text-right font-semibold text-foreground">
                          {item.emission?.co2e_kg.toLocaleString(undefined, {
                            maximumFractionDigits: 2,
                          })}
                          <span className="text-foreground-muted font-normal ml-1">kg</span>
                        </TableCell>
                        <TableCell className="text-right text-xs text-foreground-muted">
                          {item.emission?.factor_source || '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <EmptyState
                  variant="minimal"
                  title="No activities yet"
                  description="Add your first activity to start tracking emissions"
                  action={{
                    label: 'Add Activity',
                    onClick: () => router.push('/activities?add=1'),
                  }}
                />
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Scope Drill-Down Modal */}
      {drillDownScope && (activities || []).length > 0 && (
        <ScopeDrillDown
          scope={drillDownScope}
          activities={activities || []}
          onClose={() => setDrillDownScope(null)}
        />
      )}

      {/* Category Drill-Down Modal */}
      {drillDownCategory && (activities || []).length > 0 && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label="Category Activities">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-neutral-950/50 backdrop-blur-sm"
            onClick={() => setDrillDownCategory(null)}
          />

          {/* Modal */}
          <div ref={categoryTrapRef} className="relative bg-background-elevated rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden animate-fade-in-up">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <div>
                <div className="flex items-center gap-2">
                  <Filter className="w-5 h-5 text-foreground-muted" />
                  <h2 className="text-lg font-semibold text-foreground">
                    Category {drillDownCategory.category_code} Activities
                  </h2>
                </div>
                <p className="text-sm text-foreground-muted mt-1">
                  {formatCO2e(drillDownCategory.total_co2e_kg)} total from {drillDownCategory.activity_count} activities
                </p>
              </div>
              <button
                onClick={() => setDrillDownCategory(null)}
                className="p-2 rounded-lg hover:bg-background-muted transition-colors"
              >
                <X className="w-5 h-5 text-foreground-muted" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-100px)]">
              {(() => {
                // Use all activities (not batch-filtered) since the summary chart shows all data
                const categoryActivities = (activities || []).filter(
                  (item) =>
                    item.activity.scope === drillDownCategory.scope &&
                    item.activity.category_code === drillDownCategory.category_code
                );

                if (categoryActivities.length === 0) {
                  return (
                    <div className="text-center py-8 text-foreground-muted">
                      No activities found for this category
                    </div>
                  );
                }

                return (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Description</TableHead>
                        <TableHead>Activity Key</TableHead>
                        <TableHead>Quantity</TableHead>
                        <TableHead className="text-right">EF</TableHead>
                        <TableHead className="text-right">CO2e</TableHead>
                        <TableHead>Date</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {categoryActivities.map((item) => (
                        <TableRow key={item.activity.id}>
                          <TableCell className="font-medium text-foreground max-w-xs">
                            {item.activity.description}
                          </TableCell>
                          <TableCell className="text-foreground-muted font-mono text-xs">
                            {item.activity.activity_key}
                          </TableCell>
                          <TableCell className="text-foreground-muted">
                            {item.activity.quantity.toLocaleString()} {item.activity.unit}
                          </TableCell>
                          <TableCell className="text-right text-xs text-foreground-muted">
                            {item.emission?.factor_value
                              ? `${item.emission.factor_value.toLocaleString(undefined, { maximumFractionDigits: 4 })}`
                              : '-'}
                          </TableCell>
                          <TableCell className="text-right font-semibold text-foreground">
                            {item.emission?.co2e_kg.toLocaleString(undefined, {
                              maximumFractionDigits: 2,
                            })}
                            <span className="text-foreground-muted font-normal ml-1">kg</span>
                          </TableCell>
                          <TableCell className="text-foreground-muted text-sm">
                            {item.activity.activity_date}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                );
              })()}
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

// Loading fallback for Suspense
function DashboardLoading() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-primary animate-spin" />
    </div>
  );
}

// Main export with Suspense boundary (for useSearchParams)
export default function DashboardPage() {
  return (
    <Suspense fallback={<DashboardLoading />}>
      <DashboardContent />
    </Suspense>
  );
}
