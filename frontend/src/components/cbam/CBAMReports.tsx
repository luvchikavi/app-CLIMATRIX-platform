'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Select';
import { toast } from '@/components/ui';
import { api } from '@/lib/api';
import type { CBAMQuarterlyReport } from '@/lib/types';
import {
  FileText,
  CheckCircle,
  Clock,
  AlertCircle,
  FileSpreadsheet,
  Info,
} from 'lucide-react';

const STATUS_CONFIG: Record<string, { color: string; icon: typeof CheckCircle }> = {
  draft: { color: 'bg-cy-row text-cy-ink', icon: FileText },
  review: { color: 'bg-cy-warn-soft text-cy-warn', icon: Clock },
  submitted: { color: 'bg-cy-accent-soft text-cy-accent', icon: CheckCircle },
  accepted: { color: 'bg-cy-accent-soft text-cy-accent', icon: CheckCircle },
  rejected: { color: 'bg-error-50 text-error', icon: AlertCircle },
};

// Transitional reporting years (the quarterly regime ended 31 Dec 2025).
const TRANSITIONAL_YEARS = [2025, 2024];

export function CBAMReports() {
  const [quarterlyReports, setQuarterlyReports] = useState<CBAMQuarterlyReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(TRANSITIONAL_YEARS[0]);
  const [exporting, setExporting] = useState<string | null>(null);

  const loadReports = useCallback(async (year: number) => {
    try {
      setLoading(true);
      setQuarterlyReports(await api.getCBAMQuarterlyReports(year));
    } catch (err) {
      console.error('Failed to load reports:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReports(selectedYear);
  }, [selectedYear, loadReports]);

  const exportReportCSV = async (quarter: number) => {
    try {
      setExporting(`Q${quarter}`);
      const blob = await api.exportCBAMQuarterlyReportCSV(selectedYear, quarter);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cbam_imports_${selectedYear}_Q${quarter}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to export report:', err);
      toast.error('Failed to export report');
    } finally {
      setExporting(null);
    }
  };

  const getQuarterReport = (quarter: number) => {
    return quarterlyReports.find((r) => r.quarter === quarter);
  };

  return (
    <div className="space-y-6">
      {/* Transitional period ended — read-only history */}
      <div className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 flex items-start gap-3 text-sm">
        <Info className="w-4 h-4 text-primary shrink-0 mt-0.5" />
        <span className="text-foreground-muted">
          Transitional reporting ended 31 Dec 2025 — historical reports remain available; the
          definitive regime uses the annual declaration.
        </span>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground">Quarterly reports (history)</h2>
          <p className="text-foreground-muted">
            Read-only transitional-period reports, Q1 2024 – Q4 2025
          </p>
        </div>
        <Select value={String(selectedYear)} onChange={(e) => setSelectedYear(Number(e.target.value))}>
          {TRANSITIONAL_YEARS.map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </Select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((quarter) => {
            const report = getQuarterReport(quarter);
            const statusConfig = report ? STATUS_CONFIG[report.status] : STATUS_CONFIG.draft;

            return (
              <Card key={quarter}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">Q{quarter} {selectedYear}</CardTitle>
                    {report && (
                      <span className={`px-2 py-1 rounded text-xs font-medium ${statusConfig.color}`}>
                        {report.status}
                      </span>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {report ? (
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <p className="text-foreground-muted">Imports</p>
                          <p className="font-semibold">{report.total_imports}</p>
                        </div>
                        <div>
                          <p className="text-foreground-muted">Mass</p>
                          <p className="font-semibold">{report.total_mass_tonnes.toFixed(1)} t</p>
                        </div>
                        <div className="col-span-2">
                          <p className="text-foreground-muted">Emissions</p>
                          <p className="font-semibold text-lg">{report.total_emissions_tco2e.toFixed(1)} tCO2e</p>
                        </div>
                      </div>

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => exportReportCSV(quarter)}
                        isLoading={exporting === `Q${quarter}`}
                        leftIcon={<FileSpreadsheet className="w-3 h-3" />}
                      >
                        CSV
                      </Button>
                    </div>
                  ) : (
                    <div className="text-center py-4 text-foreground-muted text-sm">
                      No report for this quarter
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Sector Breakdown for existing reports */}
      {quarterlyReports.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Sector Breakdown - {selectedYear}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 pr-4">Sector</th>
                    {[1, 2, 3, 4].map((q) => (
                      <th key={q} className="text-right py-2 px-4">
                        Q{q}
                      </th>
                    ))}
                    <th className="text-right py-2 pl-4 font-bold">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {(() => {
                    // Collect all sectors
                    const allSectors = new Set<string>();
                    quarterlyReports.forEach((report) => {
                      Object.keys(report.by_sector || {}).forEach((s) => allSectors.add(s));
                    });

                    return Array.from(allSectors).map((sector) => {
                      const quarterlyValues = [1, 2, 3, 4].map((q) => {
                        const report = getQuarterReport(q);
                        return report?.by_sector?.[sector]?.total_emissions_tco2e || 0;
                      });
                      const total = quarterlyValues.reduce((a, b) => a + b, 0);

                      return (
                        <tr key={sector} className="border-b last:border-0">
                          <td className="py-2 pr-4 capitalize">{sector.replace('_', ' ')}</td>
                          {quarterlyValues.map((val, idx) => (
                            <td key={idx} className="text-right py-2 px-4 text-foreground-muted">
                              {val > 0 ? val.toFixed(1) : '-'}
                            </td>
                          ))}
                          <td className="text-right py-2 pl-4 font-semibold">
                            {total > 0 ? total.toFixed(1) : '-'}
                          </td>
                        </tr>
                      );
                    });
                  })()}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
