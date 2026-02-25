'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import { usePeriods, useReportSummary, useActivities, useSites } from '@/hooks/useEmissions';
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
  PeriodStatusBadge,
  toast,
} from '@/components/ui';
import { ScopePieChart } from '@/components/dashboard/ScopePieChart';
import { CategoryBreakdown } from '@/components/dashboard/CategoryBreakdown';
import {
  GHGInventoryReport,
  DataQualityReport,
  AuditPackageView,
  ExportOptions,
  VerificationWorkflow,
} from '@/components/reports';
import { api } from '@/lib/api';
import { cn, formatCO2e, categoryNames, downloadFile } from '@/lib/utils';
import type {
  GHGInventoryReport as GHGInventoryReportType,
  DataQualitySummary,
  AuditPackage,
  CDPExport,
  ESRSE1Export,
  PeriodStatus,
  AssuranceLevel,
  StatusHistory,
} from '@/lib/api';
import {
  FileText,
  PieChart,
  BarChart3,
  List,
  Loader2,
  Calendar,
  Building2,
  Leaf,
  FileSpreadsheet,
  File,
  ClipboardList,
  Shield,
  Download,
  CheckSquare,
} from 'lucide-react';

type ReportTab = 'summary' | 'by-scope' | 'by-category' | 'by-site' | 'inventory' | 'data-quality' | 'audit' | 'export' | 'verification';

function ReportsPageContent() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { isAuthenticated, user } = useAuthStore();
  const { selectedPeriodId, setSelectedPeriodId } = usePeriodStore();

  // All useState hooks
  const [activeTab, setActiveTab] = useState<ReportTab>('summary');
  const [mounted, setMounted] = useState(false);

  // All data fetching hooks (must be before any conditional returns)
  const { data: periods, isLoading: periodsLoading } = usePeriods();
  const activePeriodId = selectedPeriodId || periods?.[0]?.id || '';
  const activePeriod = periods?.find(p => p.id === activePeriodId);

  const { data: summary, isLoading: summaryLoading } = useReportSummary(activePeriodId);
  const { data: activities, isLoading: activitiesLoading } = useActivities(activePeriodId);
  const { data: sites } = useSites();

  // Phase 1 specific queries - only fetch when on relevant tabs
  const { data: ghgInventory, isLoading: inventoryLoading } = useQuery({
    queryKey: ['ghg-inventory', activePeriodId],
    queryFn: () => api.getGHGInventoryReport(activePeriodId),
    enabled: !!activePeriodId && activeTab === 'inventory',
  });

  const { data: dataQuality, isLoading: qualityLoading } = useQuery({
    queryKey: ['data-quality', activePeriodId],
    queryFn: () => api.getDataQualitySummary(activePeriodId),
    enabled: !!activePeriodId && activeTab === 'data-quality',
  });

  const { data: auditPackage, isLoading: auditLoading } = useQuery({
    queryKey: ['audit-package', activePeriodId],
    queryFn: () => api.getAuditPackage(activePeriodId),
    enabled: !!activePeriodId && activeTab === 'audit',
  });

  const { data: cdpExport, isLoading: cdpLoading } = useQuery({
    queryKey: ['cdp-export', activePeriodId],
    queryFn: () => api.exportCDP(activePeriodId),
    enabled: !!activePeriodId && activeTab === 'export',
  });

  const { data: esrsExport, isLoading: esrsLoading } = useQuery({
    queryKey: ['esrs-export', activePeriodId],
    queryFn: () => api.exportESRSE1(activePeriodId),
    enabled: !!activePeriodId && activeTab === 'export',
  });

  const { data: statusHistory } = useQuery({
    queryKey: ['status-history', activePeriodId],
    queryFn: () => api.getPeriodStatusHistory(activePeriodId),
    enabled: !!activePeriodId && activeTab === 'verification',
  });

  // Mutations for verification workflow
  const transitionMutation = useMutation({
    mutationFn: (newStatus: PeriodStatus) => api.transitionPeriodStatus(activePeriodId, newStatus),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['periods'] });
      queryClient.invalidateQueries({ queryKey: ['status-history', activePeriodId] });
    },
  });

  const verifyMutation = useMutation({
    mutationFn: (data: { assurance_level: AssuranceLevel; verified_by: string; verification_statement: string }) =>
      api.verifyPeriod(activePeriodId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['periods'] });
      queryClient.invalidateQueries({ queryKey: ['status-history', activePeriodId] });
    },
  });

  const lockMutation = useMutation({
    mutationFn: () => api.lockPeriod(activePeriodId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['periods'] });
      queryClient.invalidateQueries({ queryKey: ['status-history', activePeriodId] });
    },
  });

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

  const handleExportCSV = async () => {
    if (!activePeriodId) {
      toast.error('Please select a reporting period');
      return;
    }
    try {
      await api.downloadReportExport('csv', activePeriodId);
      toast.success('CSV report downloaded');
    } catch (err: any) {
      toast.error(err.message || 'Failed to export CSV');
    }
  };

  const handleExportPDF = async () => {
    if (!activePeriodId) {
      toast.error('Please select a reporting period');
      return;
    }
    try {
      await api.downloadReportExport('pdf', activePeriodId);
      toast.success('PDF report downloaded');
    } catch (err: any) {
      toast.error(err.message || 'Failed to export PDF');
    }
  };

  const handleExportCDP = async () => {
    if (cdpExport) {
      downloadFile(
        JSON.stringify(cdpExport, null, 2),
        `cdp-export-${activePeriod?.name?.replace(/\s+/g, '-') || 'report'}.json`,
        'application/json'
      );
    }
  };

  const handleExportESRS = async () => {
    if (esrsExport) {
      downloadFile(
        JSON.stringify(esrsExport, null, 2),
        `esrs-e1-export-${activePeriod?.name?.replace(/\s+/g, '-') || 'report'}.json`,
        'application/json'
      );
    }
  };

  const tabs: { id: ReportTab; label: string; icon: React.ElementType }[] = [
    { id: 'summary', label: 'Summary', icon: PieChart },
    { id: 'by-scope', label: 'By Scope', icon: BarChart3 },
    { id: 'by-category', label: 'By Category', icon: List },
    { id: 'by-site', label: 'By Site', icon: Building2 },
    { id: 'inventory', label: 'GHG Inventory', icon: FileText },
    { id: 'data-quality', label: 'Data Quality', icon: CheckSquare },
    { id: 'audit', label: 'Audit Package', icon: ClipboardList },
    { id: 'export', label: 'Export', icon: Download },
    { id: 'verification', label: 'Verification', icon: Shield },
  ];

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-foreground">Reports</h1>
            {activePeriod && <PeriodStatusBadge status={activePeriod.status} />}
          </div>
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

      {/* Report Content - Always show tabs */}
      {!isLoading && (
        <div className="space-y-6 animate-fade-in">
          {/* Tab Navigation - Always visible */}
          <div className="flex items-center gap-2 border-b border-border pb-4 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2 rounded-lg transition-colors whitespace-nowrap',
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

          {/* No Data State - Show for data-dependent tabs only */}
          {(!summary || !activities || activities.length === 0) &&
           !['verification', 'export', 'inventory', 'data-quality', 'audit'].includes(activeTab) && (
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

          {/* Summary Tab */}
          {activeTab === 'summary' && summary && (
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
                    <span>{activities?.length || 0} activities</span>
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
          {activeTab === 'by-category' && summary && (
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

          {/* GHG Inventory Tab */}
          {activeTab === 'inventory' && (
            inventoryLoading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                <span className="ml-3 text-foreground-muted">Loading GHG inventory report...</span>
              </div>
            ) : ghgInventory ? (
              <GHGInventoryReport report={ghgInventory} />
            ) : (
              <Card padding="lg">
                <EmptyState
                  icon={<FileText className="w-12 h-12" />}
                  title="Unable to generate report"
                  description="There was an issue generating the GHG inventory report. Please try again."
                />
              </Card>
            )
          )}

          {/* Data Quality Tab */}
          {activeTab === 'data-quality' && (
            qualityLoading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                <span className="ml-3 text-foreground-muted">Loading data quality report...</span>
              </div>
            ) : dataQuality ? (
              <DataQualityReport report={dataQuality} />
            ) : (
              <Card padding="lg">
                <EmptyState
                  icon={<CheckSquare className="w-12 h-12" />}
                  title="Unable to generate report"
                  description="There was an issue generating the data quality report. Please try again."
                />
              </Card>
            )
          )}

          {/* Audit Package Tab */}
          {activeTab === 'audit' && (
            auditLoading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                <span className="ml-3 text-foreground-muted">Loading audit package...</span>
              </div>
            ) : auditPackage ? (
              <AuditPackageView auditPackage={auditPackage} />
            ) : (
              <Card padding="lg">
                <EmptyState
                  icon={<ClipboardList className="w-12 h-12" />}
                  title="Unable to generate audit package"
                  description="There was an issue generating the audit package. Please try again."
                />
              </Card>
            )
          )}

          {/* Export Tab */}
          {activeTab === 'export' && (
            <ExportOptions
              cdpData={cdpExport}
              esrsData={esrsExport}
              cdpLoading={cdpLoading}
              esrsLoading={esrsLoading}
              onExportCDP={handleExportCDP}
              onExportESRS={handleExportESRS}
            />
          )}

          {/* Verification Tab */}
          {activeTab === 'verification' && activePeriod && (
            <VerificationWorkflow
              period={activePeriod}
              statusHistory={statusHistory}
              userRole={user?.role as 'admin' | 'editor' | 'viewer' | undefined}
              onTransition={async (newStatus) => {
                await transitionMutation.mutateAsync(newStatus);
              }}
              onVerify={async (data) => {
                await verifyMutation.mutateAsync(data);
              }}
              onLock={async () => {
                await lockMutation.mutateAsync();
              }}
            />
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
