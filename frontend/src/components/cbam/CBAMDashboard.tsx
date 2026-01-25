'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { KPICard } from '@/components/ui/KPICard';
import { Button } from '@/components/ui/Button';
import { api } from '@/lib/api';
import type { CBAMDashboard as CBAMDashboardType } from '@/lib/types';
import {
  Scale,
  Factory,
  Package,
  FileText,
  TrendingUp,
  Globe,
  AlertCircle,
  CheckCircle,
  Clock,
} from 'lucide-react';

interface CBAMDashboardProps {
  onNavigate: (view: 'installations' | 'imports' | 'reports' | 'calculator') => void;
}

export function CBAMDashboard({ onNavigate }: CBAMDashboardProps) {
  const [dashboard, setDashboard] = useState<CBAMDashboardType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await api.getCBAMDashboard();
      setDashboard(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="bg-error/10 border-error">
        <CardContent className="flex items-center gap-3 py-4">
          <AlertCircle className="w-5 h-5 text-error" />
          <span className="text-error">{error}</span>
          <Button variant="outline" size="sm" onClick={loadDashboard}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const getQuarterStatus = (quarter: number) => {
    const report = dashboard?.quarterly_reports.find((r) => r.quarter === quarter);
    if (!report) return { status: 'not_started', icon: Clock, color: 'text-foreground-muted' };
    if (report.status === 'submitted') return { status: 'submitted', icon: CheckCircle, color: 'text-success' };
    if (report.status === 'draft') return { status: 'draft', icon: FileText, color: 'text-warning' };
    return { status: report.status, icon: Clock, color: 'text-foreground-muted' };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">CBAM Dashboard</h1>
          <p className="text-foreground-muted">
            Carbon Border Adjustment Mechanism - {dashboard?.year}
            <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium">
              {dashboard?.phase === 'transitional' ? 'Transitional Phase' : 'Definitive Phase'}
            </span>
          </p>
        </div>
        <Button onClick={() => onNavigate('calculator')} leftIcon={<Scale className="w-4 h-4" />}>
          Calculate Emissions
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Installations"
          value={dashboard?.installations.total || 0}
          icon={<Factory className="w-5 h-5" />}
          onClick={() => onNavigate('installations')}
        />
        <KPICard
          title="Imports YTD"
          value={dashboard?.imports.total_count || 0}
          icon={<Package className="w-5 h-5" />}
          onClick={() => onNavigate('imports')}
        />
        <KPICard
          title="Total Mass"
          value={(dashboard?.imports.total_mass_tonnes || 0).toFixed(1)}
          unit="tonnes"
          icon={<TrendingUp className="w-5 h-5" />}
        />
        <KPICard
          title="Total Emissions"
          value={(dashboard?.imports.total_emissions_tco2e || 0).toFixed(1)}
          unit="tCO2e"
          icon={<Globe className="w-5 h-5" />}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Emissions by Sector */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Emissions by Sector</CardTitle>
          </CardHeader>
          <CardContent>
            {dashboard?.by_sector && dashboard.by_sector.length > 0 ? (
              <div className="space-y-4">
                {dashboard.by_sector.map((sector) => {
                  const maxEmissions = Math.max(...dashboard.by_sector.map((s) => s.total_emissions_tco2e));
                  const percentage = maxEmissions > 0 ? (sector.total_emissions_tco2e / maxEmissions) * 100 : 0;

                  return (
                    <div key={sector.sector} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium capitalize">{sector.sector.replace('_', ' ')}</span>
                        <span className="text-foreground-muted">
                          {sector.total_emissions_tco2e.toFixed(1)} tCO2e ({sector.import_count} imports)
                        </span>
                      </div>
                      <div className="h-2 bg-background-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full transition-all"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 text-foreground-muted">
                <Package className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No imports recorded yet</p>
                <Button variant="outline" size="sm" className="mt-3" onClick={() => onNavigate('imports')}>
                  Add First Import
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quarterly Reports Status */}
        <Card>
          <CardHeader>
            <CardTitle>Quarterly Reports</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[1, 2, 3, 4].map((quarter) => {
                const { status, icon: Icon, color } = getQuarterStatus(quarter);
                const report = dashboard?.quarterly_reports.find((r) => r.quarter === quarter);

                return (
                  <div
                    key={quarter}
                    className="flex items-center justify-between p-3 bg-background-muted rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <Icon className={`w-5 h-5 ${color}`} />
                      <div>
                        <p className="font-medium">Q{quarter} {dashboard?.year}</p>
                        <p className="text-xs text-foreground-muted capitalize">{status.replace('_', ' ')}</p>
                      </div>
                    </div>
                    {report && (
                      <span className="text-sm text-foreground-muted">
                        {report.total_emissions_tco2e.toFixed(1)} tCO2e
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
            <Button variant="outline" className="w-full mt-4" onClick={() => onNavigate('reports')}>
              Manage Reports
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Installations by Country */}
      {dashboard?.installations.by_country && Object.keys(dashboard.installations.by_country).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Installations by Country</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {Object.entries(dashboard.installations.by_country).map(([country, count]) => (
                <div
                  key={country}
                  className="px-3 py-2 bg-background-muted rounded-lg flex items-center gap-2"
                >
                  <span className="font-medium">{country}</span>
                  <span className="text-foreground-muted">({count})</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
