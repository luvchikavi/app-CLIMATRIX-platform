'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import {
  useSiteDetail,
  usePeriods,
  useActivities,
  useReportSummary,
} from '@/hooks/useEmissions';
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
  EmptyState,
  toast,
} from '@/components/ui';
import { ScopePieChart } from '@/components/dashboard/ScopePieChart';
import { CategoryBreakdown } from '@/components/dashboard/CategoryBreakdown';
import { formatCO2e } from '@/lib/utils';
import { api } from '@/lib/api';
import {
  ArrowLeft,
  Building2,
  MapPin,
  Globe,
  Zap,
  Loader2,
  Upload,
  Leaf,
  PieChart,
  BarChart3,
  List,
  Download,
  FileSpreadsheet,
  File,
} from 'lucide-react';

function SiteDetailContent() {
  const router = useRouter();
  const params = useParams();
  const siteId = params.id as string;
  const { isAuthenticated } = useAuthStore();
  const { selectedPeriodId } = usePeriodStore();
  const [mounted, setMounted] = useState(false);

  const { data: periods } = usePeriods();
  // Only trust the persisted period if it belongs to THIS org's list — a stale
  // localStorage value from another session/org would 404 every query.
  const activePeriodId = periods?.find((p) => p.id === selectedPeriodId)?.id ?? periods?.[0]?.id;

  const { data: siteDetail, isLoading: siteLoading } = useSiteDetail(siteId, activePeriodId);
  const { data: summary } = useReportSummary(activePeriodId || '', siteId);
  const { data: activities, isLoading: activitiesLoading } = useActivities(
    activePeriodId || '',
    { site_id: siteId }
  );

  useEffect(() => { setMounted(true); }, []);
  useEffect(() => {
    if (mounted && !isAuthenticated) router.push('/');
  }, [mounted, isAuthenticated, router]);

  if (!mounted || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  const isLoading = siteLoading;

  const handleExportCSV = async () => {
    if (!activePeriodId) return;
    try {
      await api.downloadReportExport('csv', activePeriodId, siteId);
      toast.success('CSV report downloaded');
    } catch (err: any) {
      toast.error(err.message || 'Failed to export CSV');
    }
  };

  const handleExportPDF = async () => {
    if (!activePeriodId) return;
    try {
      await api.downloadReportExport('pdf', activePeriodId, siteId);
      toast.success('PDF report downloaded');
    } catch (err: any) {
      toast.error(err.message || 'Failed to export PDF');
    }
  };

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/sites')}
            leftIcon={<ArrowLeft className="w-4 h-4" />}
          >
            Sites
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-primary-light">
                <Building2 className="w-5 h-5 text-primary" />
              </div>
              <h1 className="text-2xl font-bold text-foreground">
                {siteDetail?.name || 'Loading...'}
              </h1>
            </div>
            <div className="flex items-center gap-4 mt-1 ml-12">
              {siteDetail?.address && (
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-foreground-muted" />
                  <span className="text-sm text-foreground-muted">{siteDetail.address}</span>
                </div>
              )}
              {siteDetail?.country_code && (
                <div className="flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-foreground-muted" />
                  <span className="text-sm text-foreground-muted">{siteDetail.country_code}</span>
                </div>
              )}
              {siteDetail?.grid_region && (
                <div className="flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5 text-foreground-muted" />
                  <span className="text-sm text-foreground-muted">{siteDetail.grid_region}</span>
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportCSV}
            leftIcon={<FileSpreadsheet className="w-4 h-4" />}
          >
            CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportPDF}
            leftIcon={<File className="w-4 h-4" />}
          >
            PDF
          </Button>
          <Button
            variant="primary"
            onClick={() => router.push('/hub')}
            leftIcon={<Upload className="w-4 h-4" />}
          >
            Upload Data
          </Button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      )}

      {/* Site Detail Content */}
      {!isLoading && siteDetail && (
        <div className="space-y-8 animate-fade-in">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card padding="lg">
              <p className="text-sm font-medium text-foreground-muted uppercase tracking-wide">Total Emissions</p>
              <p className="text-3xl font-bold text-foreground mt-2">{formatCO2e(siteDetail.total_co2e_kg)}</p>
              <p className="text-sm text-foreground-muted mt-1">{siteDetail.activity_count} activities</p>
            </Card>
            <Card padding="lg">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <p className="text-sm font-medium text-foreground-muted">Scope 1</p>
              </div>
              <p className="text-2xl font-bold text-foreground">{formatCO2e(siteDetail.scope_1_co2e_kg)}</p>
            </Card>
            <Card padding="lg">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-amber-500" />
                <p className="text-sm font-medium text-foreground-muted">Scope 2</p>
              </div>
              <p className="text-2xl font-bold text-foreground">{formatCO2e(siteDetail.scope_2_co2e_kg)}</p>
            </Card>
            <Card padding="lg">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-blue-500" />
                <p className="text-sm font-medium text-foreground-muted">Scope 3</p>
              </div>
              <p className="text-2xl font-bold text-foreground">{formatCO2e(siteDetail.scope_3_co2e_kg)}</p>
            </Card>
          </div>

          {/* Charts Row */}
          {summary && (
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
          )}

          {/* Activities Table */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between w-full">
                <CardTitle className="flex items-center gap-2">
                  <List className="w-5 h-5 text-foreground-muted" />
                  Activities
                  <span className="ml-2 px-2 py-0.5 text-xs font-medium rounded-full bg-background-muted text-foreground-muted">
                    {activities?.length || 0}
                  </span>
                </CardTitle>
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
                      <TableHead>Category</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Quantity</TableHead>
                      <TableHead className="text-right">CO2e</TableHead>
                      <TableHead className="text-right">Source</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {activities.map((item) => (
                      <TableRow key={item.activity.id}>
                        <TableCell>
                          <ScopeBadge scope={item.activity.scope as 1 | 2 | 3} />
                        </TableCell>
                        <TableCell className="font-mono text-xs text-foreground-muted">
                          {item.activity.category_code}
                        </TableCell>
                        <TableCell className="font-medium text-foreground max-w-xs truncate">
                          {item.activity.description}
                        </TableCell>
                        <TableCell className="text-foreground-muted">
                          {item.activity.quantity.toLocaleString()} {item.activity.unit}
                        </TableCell>
                        <TableCell className="text-right font-semibold text-foreground">
                          {item.emission?.co2e_kg.toLocaleString(undefined, { maximumFractionDigits: 2 })}
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
                  title="No activities for this site"
                  description="Upload an Excel file or add activities manually to start tracking emissions for this site."
                  action={{
                    label: 'Upload Data',
                    onClick: () => router.push('/hub'),
                  }}
                />
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </AppShell>
  );
}

export default function SiteDetailPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    }>
      <SiteDetailContent />
    </Suspense>
  );
}
