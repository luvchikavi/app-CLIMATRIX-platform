'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { usePeriods, useReportSummary } from '@/hooks/useEmissions';
import { AppShell } from '@/components/layout';
import { Card, CardHeader, CardTitle, CardContent, Button, Badge, EmptyState } from '@/components/ui';
import { ScopePieChart } from '@/components/dashboard/ScopePieChart';
import { formatCO2e } from '@/lib/utils';
import {
  Leaf,
  ArrowLeft,
  Flame,
  Zap,
  Globe,
  ArrowRight,
  Plus,
  FileText,
  Upload,
  Loader2,
} from 'lucide-react';

export default function GHGModulePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  // All useState hooks
  const [mounted, setMounted] = useState(false);

  // All data fetching hooks (must be before any conditional returns)
  const { data: periods, isLoading: periodsLoading } = usePeriods();
  const activePeriodId = periods?.[0]?.id || '';
  const { data: summary, isLoading: summaryLoading } = useReportSummary(activePeriodId);

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

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex items-center gap-4 mb-8">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/modules')}
          leftIcon={<ArrowLeft className="w-4 h-4" />}
        >
          Modules
        </Button>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
            <Leaf className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">GHG Inventory</h1>
            <p className="text-foreground-muted">Greenhouse Gas Emissions Tracking</p>
          </div>
        </div>
        <Badge variant="success" className="ml-auto">Active</Badge>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Card
          padding="md"
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => router.push('/dashboard?wizard=true')}
        >
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-primary-light">
              <Plus className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Add Activity</h3>
              <p className="text-sm text-foreground-muted">Record new emission data</p>
            </div>
            <ArrowRight className="w-5 h-5 text-foreground-muted ml-auto" />
          </div>
        </Card>

        <Card
          padding="md"
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => router.push('/import')}
        >
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-secondary/10">
              <Upload className="w-5 h-5 text-secondary" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Import Data</h3>
              <p className="text-sm text-foreground-muted">Bulk upload from file</p>
            </div>
            <ArrowRight className="w-5 h-5 text-foreground-muted ml-auto" />
          </div>
        </Card>

        <Card
          padding="md"
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => router.push('/reports')}
        >
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-info/10">
              <FileText className="w-5 h-5 text-info" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">View Reports</h3>
              <p className="text-sm text-foreground-muted">Analyze emissions data</p>
            </div>
            <ArrowRight className="w-5 h-5 text-foreground-muted ml-auto" />
          </div>
        </Card>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      )}

      {/* Module Overview */}
      {!isLoading && summary && (
        <div className="space-y-6">
          {/* Scope Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card padding="lg" className="border-l-4 border-l-scope1">
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-lg bg-scope1/10">
                  <Flame className="w-6 h-6 text-scope1" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-foreground">Scope 1</h3>
              <p className="text-sm text-foreground-muted mb-3">Direct Emissions</p>
              <p className="text-2xl font-bold text-foreground">
                {formatCO2e(summary.scope_1_co2e_kg)}
              </p>
              <p className="text-xs text-foreground-muted mt-1">
                Fuel combustion, vehicles, refrigerants
              </p>
            </Card>

            <Card padding="lg" className="border-l-4 border-l-scope2">
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-lg bg-scope2/10">
                  <Zap className="w-6 h-6 text-scope2" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-foreground">Scope 2</h3>
              <p className="text-sm text-foreground-muted mb-3">Indirect Energy</p>
              <p className="text-2xl font-bold text-foreground">
                {formatCO2e(summary.scope_2_co2e_kg)}
              </p>
              <p className="text-xs text-foreground-muted mt-1">
                Purchased electricity, heat, steam
              </p>
            </Card>

            <Card padding="lg" className="border-l-4 border-l-scope3">
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-lg bg-scope3/10">
                  <Globe className="w-6 h-6 text-scope3" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-foreground">Scope 3</h3>
              <p className="text-sm text-foreground-muted mb-3">Value Chain</p>
              <p className="text-2xl font-bold text-foreground">
                {formatCO2e(summary.scope_3_co2e_kg + (summary.scope_3_wtt_co2e_kg || 0))}
              </p>
              <p className="text-xs text-foreground-muted mt-1">
                Purchased goods, travel, waste, freight
              </p>
            </Card>
          </div>

          {/* Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Emissions Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ScopePieChart data={summary} />
            </CardContent>
          </Card>
        </div>
      )}

      {/* No Data State */}
      {!isLoading && (!summary || summary.total_co2e_kg === 0) && (
        <Card padding="lg">
          <EmptyState
            icon={<Leaf className="w-12 h-12" />}
            title="No emissions data yet"
            description="Start tracking your GHG emissions by adding activities or importing data."
            action={{
              label: 'Add Activity',
              onClick: () => router.push('/dashboard?wizard=true'),
            }}
          />
        </Card>
      )}
    </AppShell>
  );
}
