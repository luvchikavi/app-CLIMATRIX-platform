'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import { usePeriods, useReportSummary, useReportByScope, useActivities, useSites } from '@/hooks/useEmissions';
import { AppShell } from '@/components/layout';
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Select,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  EmptyState,
  ScopeBadge,
  Badge,
  KPICard,
} from '@/components/ui';
import { ScopePieChart } from '@/components/dashboard/ScopePieChart';
import { CategoryBreakdown } from '@/components/dashboard/CategoryBreakdown';
import { cn, formatCO2e, categoryNames } from '@/lib/utils';
import {
  Download,
  FileText,
  PieChart,
  BarChart3,
  List,
  Loader2,
  Calendar,
  Building2,
  Leaf,
  TrendingUp,
  FileSpreadsheet,
  File,
  Printer,
} from 'lucide-react';

type ReportTab = 'summary' | 'by-scope' | 'by-category' | 'by-site';

function ReportsPageContent() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { selectedPeriodId, setSelectedPeriodId } = usePeriodStore();

  // All useState hooks
  const [activeTab, setActiveTab] = useState<ReportTab>('summary');
  const [mounted, setMounted] = useState(false);

  // All data fetching hooks (must be before any conditional returns)
  const { data: periods, isLoading: periodsLoading } = usePeriods();
  const activePeriodId = selectedPeriodId || periods?.[0]?.id || '';

  const { data: summary, isLoading: summaryLoading } = useReportSummary(activePeriodId);
  const { data: activities, isLoading: activitiesLoading } = useActivities(activePeriodId);
  const { data: sites } = useSites();

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

  // Group activities by scope
  const activitiesByScope = activities?.reduce((acc, item) => {
    const scope = item.activity.scope;
    if (!acc[scope]) acc[scope] = [];
    acc[scope].push(item);
    return acc;
  }, {} as Record<number, typeof activities>);

  // Group activities by site
  const activitiesBySite = activities?.reduce((acc, item) => {
    const siteId = item.activity.site_id || 'unassigned';
    if (!acc[siteId]) acc[siteId] = [];
    acc[siteId].push(item);
    return acc;
  }, {} as Record<string, typeof activities>);

  const handleExportCSV = () => {
    // In production, this would call the backend export endpoint
    alert('Export to CSV coming soon');
  };

  const handleExportPDF = () => {
    // In production, this would call the backend PDF generation endpoint
    alert('Export to PDF coming soon');
  };

  const tabs: { id: ReportTab; label: string; icon: React.ElementType }[] = [
    { id: 'summary', label: 'Summary', icon: PieChart },
    { id: 'by-scope', label: 'By Scope', icon: BarChart3 },
    { id: 'by-category', label: 'By Category', icon: List },
    { id: 'by-site', label: 'By Site', icon: Building2 },
  ];

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Reports</h1>
          <p className="text-foreground-muted mt-1">
            View and export your emission reports
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select
            value={selectedPeriodId || ''}
            onChange={(e) => setSelectedPeriodId(e.target.value)}
            options={[
              ...(periods?.map((p) => ({ value: p.id, label: p.name })) || []),
            ]}
            className="w-48"
          />
          <Button
            variant="outline"
            onClick={handleExportCSV}
            leftIcon={<FileSpreadsheet className="w-4 h-4" />}
          >
            CSV
          </Button>
          <Button
            variant="outline"
            onClick={handleExportPDF}
            leftIcon={<File className="w-4 h-4" />}
          >
            PDF
          </Button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-foreground-muted">Loading report...</span>
        </div>
      )}

      {/* No Data State */}
      {!isLoading && (!summary || !activities || activities.length === 0) && (
        <Card padding="lg">
          <EmptyState
            icon={<FileText className="w-12 h-12" />}
            title="No data to report"
            description="Add activities to your reporting period to generate reports."
            action={{
              label: 'Add Activity',
              onClick: () => router.push('/dashboard?wizard=true'),
            }}
          />
        </Card>
      )}

      {/* Report Content */}
      {!isLoading && summary && activities && activities.length > 0 && (
        <div className="space-y-6 animate-fade-in">
          {/* Tab Navigation */}
          <div className="flex items-center gap-2 border-b border-border pb-4">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2 rounded-lg transition-colors',
                    activeTab === tab.id
                      ? 'bg-primary text-white'
                      : 'text-foreground-muted hover:bg-background-muted'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Summary Tab */}
          {activeTab === 'summary' && (
            <div className="space-y-6">
              {/* KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card padding="lg">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium text-foreground-muted uppercase tracking-wide">
                        Total Emissions
                      </p>
                      <p className="text-3xl font-bold text-foreground mt-2">
                        {formatCO2e(summary.total_co2e_kg)}
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-primary-light">
                      <Leaf className="w-5 h-5 text-primary" />
                    </div>
                  </div>
                </Card>
                <Card padding="lg" className="border-l-4 border-l-scope1">
                  <p className="text-sm font-medium text-foreground-muted">Scope 1</p>
                  <p className="text-2xl font-bold text-foreground mt-1">
                    {formatCO2e(summary.scope_1_co2e_kg)}
                  </p>
                  <p className="text-xs text-foreground-muted mt-1">Direct emissions</p>
                </Card>
                <Card padding="lg" className="border-l-4 border-l-scope2">
                  <p className="text-sm font-medium text-foreground-muted">Scope 2</p>
                  <p className="text-2xl font-bold text-foreground mt-1">
                    {formatCO2e(summary.scope_2_co2e_kg)}
                  </p>
                  <p className="text-xs text-foreground-muted mt-1">Indirect energy</p>
                </Card>
                <Card padding="lg" className="border-l-4 border-l-scope3">
                  <p className="text-sm font-medium text-foreground-muted">Scope 3</p>
                  <p className="text-2xl font-bold text-foreground mt-1">
                    {formatCO2e(summary.scope_3_co2e_kg + (summary.scope_3_wtt_co2e_kg || 0))}
                  </p>
                  <p className="text-xs text-foreground-muted mt-1">Value chain</p>
                </Card>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="w-5 h-5 text-foreground-muted" />
                      Emissions by Category
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CategoryBreakdown categories={summary.by_category} />
                  </CardContent>
                </Card>
              </div>

              {/* Report Period Info */}
              <Card padding="sm" className="bg-background-muted">
                <div className="flex items-center gap-4 text-sm text-foreground-muted">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    <span>Period: {summary.period_name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <List className="w-4 h-4" />
                    <span>{activities.length} activities</span>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* By Scope Tab */}
          {activeTab === 'by-scope' && (
            <div className="space-y-6">
              {[1, 2, 3].map((scope) => {
                const scopeActivities = activitiesByScope?.[scope] || [];
                const scopeTotal = scopeActivities.reduce(
                  (sum, item) => sum + (item.emission?.co2e_kg || 0),
                  0
                );

                return (
                  <Card key={scope}>
                    <CardHeader>
                      <div className="flex items-center justify-between w-full">
                        <CardTitle className="flex items-center gap-3">
                          <ScopeBadge scope={scope as 1 | 2 | 3} />
                          Scope {scope} Activities
                        </CardTitle>
                        <span className="text-lg font-bold text-foreground">
                          {formatCO2e(scopeTotal)}
                        </span>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {scopeActivities.length === 0 ? (
                        <p className="text-foreground-muted text-center py-4">
                          No Scope {scope} activities recorded
                        </p>
                      ) : (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Description</TableHead>
                              <TableHead>Category</TableHead>
                              <TableHead>Quantity</TableHead>
                              <TableHead className="text-right">CO2e</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {scopeActivities.map((item) => (
                              <TableRow key={item.activity.id}>
                                <TableCell className="font-medium">
                                  {item.activity.description}
                                </TableCell>
                                <TableCell className="text-foreground-muted">
                                  {categoryNames[item.activity.category_code] || item.activity.category_code}
                                </TableCell>
                                <TableCell>
                                  {item.activity.quantity.toLocaleString()} {item.activity.unit}
                                </TableCell>
                                <TableCell className="text-right font-semibold">
                                  {formatCO2e(item.emission?.co2e_kg || 0)}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {/* By Category Tab */}
          {activeTab === 'by-category' && (
            <Card>
              <CardHeader>
                <CardTitle>Emissions by GHG Category</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Scope</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Activities</TableHead>
                      <TableHead className="text-right">Total CO2e</TableHead>
                      <TableHead className="text-right">% of Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {summary.by_category
                      .sort((a, b) => b.total_co2e_kg - a.total_co2e_kg)
                      .map((category) => {
                        const percentage =
                          summary.total_co2e_kg > 0
                            ? (category.total_co2e_kg / summary.total_co2e_kg) * 100
                            : 0;
                        return (
                          <TableRow key={`${category.scope}-${category.category_code}`}>
                            <TableCell>
                              <ScopeBadge scope={category.scope as 1 | 2 | 3} />
                            </TableCell>
                            <TableCell className="font-mono text-sm">
                              {category.category_code}
                            </TableCell>
                            <TableCell>
                              {categoryNames[category.category_code] || category.category_code}
                            </TableCell>
                            <TableCell className="text-right">
                              {category.activity_count}
                            </TableCell>
                            <TableCell className="text-right font-semibold">
                              {formatCO2e(category.total_co2e_kg)}
                            </TableCell>
                            <TableCell className="text-right text-foreground-muted">
                              {percentage.toFixed(1)}%
                            </TableCell>
                          </TableRow>
                        );
                      })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {/* By Site Tab */}
          {activeTab === 'by-site' && (
            <div className="space-y-6">
              {Object.entries(activitiesBySite || {}).map(([siteId, siteActivities]) => {
                const site = sites?.find((s) => s.id === siteId);
                const siteName = site?.name || 'Unassigned';
                const siteTotal = siteActivities?.reduce(
                  (sum, item) => sum + (item.emission?.co2e_kg || 0),
                  0
                ) || 0;

                return (
                  <Card key={siteId}>
                    <CardHeader>
                      <div className="flex items-center justify-between w-full">
                        <CardTitle className="flex items-center gap-3">
                          <Building2 className="w-5 h-5 text-foreground-muted" />
                          {siteName}
                          {site?.country_code && (
                            <Badge variant="secondary">{site.country_code}</Badge>
                          )}
                        </CardTitle>
                        <span className="text-lg font-bold text-foreground">
                          {formatCO2e(siteTotal)}
                        </span>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Scope</TableHead>
                            <TableHead>Description</TableHead>
                            <TableHead>Quantity</TableHead>
                            <TableHead className="text-right">CO2e</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {siteActivities?.map((item) => (
                            <TableRow key={item.activity.id}>
                              <TableCell>
                                <ScopeBadge scope={item.activity.scope as 1 | 2 | 3} />
                              </TableCell>
                              <TableCell className="font-medium">
                                {item.activity.description}
                              </TableCell>
                              <TableCell>
                                {item.activity.quantity.toLocaleString()} {item.activity.unit}
                              </TableCell>
                              <TableCell className="text-right font-semibold">
                                {formatCO2e(item.emission?.co2e_kg || 0)}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}

// Loading fallback for Suspense
function ReportsLoading() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-primary animate-spin" />
    </div>
  );
}

// Main export with Suspense boundary
export default function ReportsPage() {
  return (
    <Suspense fallback={<ReportsLoading />}>
      <ReportsPageContent />
    </Suspense>
  );
}
