'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import { usePeriods, useReportSummary, useActivities } from '@/hooks/useEmissions';
import { AppShell } from '@/components/layout';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
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
} from '@/components/ui';
import { ScopePieChart } from '@/components/dashboard/ScopePieChart';
import { CategoryBreakdown } from '@/components/dashboard/CategoryBreakdown';
import { Scope2Comparison } from '@/components/dashboard/Scope2Comparison';
import { ScopeDrillDown } from '@/components/dashboard/ScopeDrillDown';
import { ActivityWizard } from '@/components/wizard';
import { ImportHistory } from '@/components/ImportHistory';
import { useWizardStore } from '@/stores/wizard';
import { cn } from '@/lib/utils';
import { formatCO2e } from '@/lib/utils';
import {
  Plus,
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
  ArrowLeft,
  Download,
  Filter,
} from 'lucide-react';
import { CategorySummary } from '@/lib/api';

// Back button for wizard - only shows when not on first step
function WizardBackButton() {
  const step = useWizardStore((s) => s.step);
  const goBack = useWizardStore((s) => s.goBack);

  if (step === 'scope') return null;

  return (
    <button
      onClick={goBack}
      className="flex items-center gap-1 px-3 py-2 text-sm text-foreground-muted hover:text-foreground hover:bg-background-muted rounded-lg transition-colors"
    >
      <ArrowLeft className="w-4 h-4" />
      Back
    </button>
  );
}

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated } = useAuthStore();
  const { selectedPeriodId } = usePeriodStore();

  // All useState hooks at top
  const [showWizard, setShowWizard] = useState(searchParams.get('wizard') === 'true');
  const [mounted, setMounted] = useState(false);
  const [drillDownCategory, setDrillDownCategory] = useState<CategorySummary | null>(null);
  const [drillDownScope, setDrillDownScope] = useState<1 | 2 | 3 | null>(null);

  // All data fetching hooks (must be before any conditional returns)
  const { data: periods, isLoading: periodsLoading } = usePeriods();
  const activePeriodId = selectedPeriodId || periods?.[0]?.id;

  const {
    data: summary,
    isLoading: summaryLoading,
    refetch: refetchSummary
  } = useReportSummary(activePeriodId || '');

  const { data: activities, isLoading: activitiesLoading } = useActivities(activePeriodId || '');

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

  const isLoading = periodsLoading || summaryLoading;

  // Calculate percentages for scope breakdown
  const totalEmissions = summary?.total_co2e_kg || 0;
  const scope1Pct = totalEmissions > 0 ? ((summary?.scope_1_co2e_kg || 0) / totalEmissions) * 100 : 0;
  const scope2Pct = totalEmissions > 0 ? ((summary?.scope_2_co2e_kg || 0) / totalEmissions) * 100 : 0;
  const scope3Pct = totalEmissions > 0 ? ((summary?.scope_3_co2e_kg || 0) / totalEmissions) * 100 : 0;

  // Get activity counts per scope
  const scope1Activities = activities?.filter(a => a.activity.scope === 1).length || 0;
  const scope2Activities = activities?.filter(a => a.activity.scope === 2).length || 0;
  const scope3Activities = activities?.filter(a => a.activity.scope === 3).length || 0;

  // Export activities to Excel
  const exportToExcel = () => {
    if (!activities || activities.length === 0) return;

    // Create CSV content
    const headers = ['Scope', 'Category', 'Description', 'Activity Key', 'Quantity', 'Unit', 'Emission Factor', 'Factor Unit', 'CO2e (kg)', 'Source', 'Date'];
    const rows = activities.map(item => [
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
    a.download = `activities_${summary?.period_name || 'export'}_${new Date().toISOString().split('T')[0]}.csv`;
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
          <p className="text-foreground-muted mt-1">
            Track and manage your organization's emissions
          </p>
        </div>
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
            onClick={() => router.push(`/import?period=${activePeriodId}`)}
            leftIcon={<Upload className="w-4 h-4" />}
          >
            Import
          </Button>
          <Button
            variant="primary"
            onClick={() => setShowWizard(true)}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Add Activity
          </Button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-foreground-muted">Loading dashboard...</span>
        </div>
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
        </Card>
      )}

      {/* Dashboard Content */}
      {!isLoading && summary && (
        <div className="space-y-8 animate-fade-in">
          {/* Total Emissions KPI */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <Card padding="lg" className="lg:col-span-1">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground-muted uppercase tracking-wide">
                    Total Emissions
                  </p>
                  <p className="text-4xl font-bold text-foreground mt-2 tracking-tight">
                    {formatCO2e(summary.total_co2e_kg)}
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
                    {activities?.length || 0}
                  </span>
                </div>
              </div>
            </Card>

            {/* Scope KPIs */}
            <ScopeKPI
              scope={1}
              value={summary.scope_1_co2e_kg}
              percentage={scope1Pct}
              activityCount={scope1Activities}
              onClick={() => scope1Activities > 0 && setDrillDownScope(1)}
            />
            <ScopeKPI
              scope={2}
              value={summary.scope_2_co2e_kg}
              percentage={scope2Pct}
              activityCount={scope2Activities}
              onClick={() => scope2Activities > 0 && setDrillDownScope(2)}
            />
            <ScopeKPI
              scope={3}
              value={summary.scope_3_co2e_kg + (summary.scope_3_wtt_co2e_kg || 0)}
              percentage={scope3Pct}
              activityCount={scope3Activities}
              onClick={() => scope3Activities > 0 && setDrillDownScope(3)}
            />
          </div>

          {/* WTT Notice (if applicable) */}
          {summary.scope_3_wtt_co2e_kg > 0 && (
            <Card padding="sm" className="bg-info-50 border-info/20">
              <div className="flex items-center gap-3">
                <Activity className="w-5 h-5 text-info" />
                <p className="text-sm text-info-700">
                  <span className="font-medium">Category 3.3 (WTT):</span>{' '}
                  {formatCO2e(summary.scope_3_wtt_co2e_kg)} auto-calculated from Scope 1 & 2 activities
                </p>
              </div>
            </Card>
          )}

          {/* Scope 2 Location vs Market Comparison */}
          {summary.scope_2_co2e_kg > 0 && activePeriodId && (
            <Scope2Comparison periodId={activePeriodId} />
          )}

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

          {/* Recent Activities Table */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between w-full">
                <CardTitle className="flex items-center gap-2">
                  <List className="w-5 h-5 text-foreground-muted" />
                  Recent Activities
                  {activities && (
                    <span className="ml-2 px-2 py-0.5 text-xs font-medium rounded-full bg-background-muted text-foreground-muted">
                      {activities.length}
                    </span>
                  )}
                </CardTitle>
                <div className="flex items-center gap-2">
                  {activities && activities.length > 0 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={exportToExcel}
                      leftIcon={<Download className="w-4 h-4" />}
                    >
                      Export
                    </Button>
                  )}
                  {activities && activities.length > 10 && (
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
              ) : activities && activities.length > 0 ? (
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
                    {activities.slice(0, 10).map((item) => (
                      <TableRow key={item.activity.id} clickable>
                        <TableCell>
                          <ScopeBadge scope={item.activity.scope as 1 | 2 | 3} />
                        </TableCell>
                        <TableCell className="font-medium text-foreground max-w-xs truncate">
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
                    onClick: () => setShowWizard(true),
                  }}
                />
              )}
            </CardContent>
          </Card>

          {/* Import History */}
          <ImportHistory periodId={activePeriodId} limit={5} />
        </div>
      )}

      {/* Activity Wizard Modal */}
      {showWizard && activePeriodId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-neutral-950/50 backdrop-blur-sm"
            onClick={() => setShowWizard(false)}
          />

          {/* Modal */}
          <div className="relative bg-background-elevated rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden animate-fade-in-up">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <div>
                <h2 className="text-lg font-semibold text-foreground">Add Activity</h2>
                <p className="text-sm text-foreground-muted">Record a new emission activity</p>
              </div>
              <div className="flex items-center gap-2">
                <WizardBackButton />
                <button
                  onClick={() => setShowWizard(false)}
                  className="p-2 rounded-lg hover:bg-background-muted transition-colors"
                >
                  <X className="w-5 h-5 text-foreground-muted" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
              <ActivityWizard
                periodId={activePeriodId}
                onSuccess={() => {
                  setShowWizard(false);
                  refetchSummary();
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Scope Drill-Down Modal */}
      {drillDownScope && activities && (
        <ScopeDrillDown
          scope={drillDownScope}
          activities={activities}
          onClose={() => setDrillDownScope(null)}
        />
      )}

      {/* Category Drill-Down Modal */}
      {drillDownCategory && activities && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-neutral-950/50 backdrop-blur-sm"
            onClick={() => setDrillDownCategory(null)}
          />

          {/* Modal */}
          <div className="relative bg-background-elevated rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden animate-fade-in-up">
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
                const filteredActivities = activities.filter(
                  (item) =>
                    item.activity.scope === drillDownCategory.scope &&
                    item.activity.category_code === drillDownCategory.category_code
                );

                if (filteredActivities.length === 0) {
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
                      {filteredActivities.map((item) => (
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
