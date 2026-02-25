'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { ConfirmDialog, toast } from '@/components/ui';
import { api } from '@/lib/api';
import type { CBAMQuarterlyReport, CBAMAnnualDeclaration } from '@/lib/types';
import {
  FileText,
  Download,
  Send,
  RefreshCw,
  CheckCircle,
  Clock,
  AlertCircle,
  FileSpreadsheet,
  FileCode,
} from 'lucide-react';

const STATUS_CONFIG: Record<string, { color: string; icon: typeof CheckCircle }> = {
  draft: { color: 'bg-gray-100 text-gray-700', icon: FileText },
  review: { color: 'bg-yellow-100 text-yellow-700', icon: Clock },
  submitted: { color: 'bg-green-100 text-green-700', icon: CheckCircle },
  accepted: { color: 'bg-green-100 text-green-700', icon: CheckCircle },
  rejected: { color: 'bg-red-100 text-red-700', icon: AlertCircle },
};

export function CBAMReports() {
  const [quarterlyReports, setQuarterlyReports] = useState<CBAMQuarterlyReport[]>([]);
  const [annualDeclarations, setAnnualDeclarations] = useState<CBAMAnnualDeclaration[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [generating, setGenerating] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<string | null>(null);
  const [exporting, setExporting] = useState<string | null>(null);
  const [confirmState, setConfirmState] = useState<{open: boolean; onConfirm: () => void; title: string; message: string}>({open: false, onConfirm: () => {}, title: '', message: ''});

  const currentYear = new Date().getFullYear();
  const isDefinitivePhase = currentYear >= 2026;

  useEffect(() => {
    loadReports();
  }, [selectedYear]);

  const loadReports = async () => {
    try {
      setLoading(true);
      const [quarterly, annual] = await Promise.all([
        api.getCBAMQuarterlyReports(selectedYear),
        isDefinitivePhase ? api.getCBAMAnnualDeclarations() : Promise.resolve([]),
      ]);
      setQuarterlyReports(quarterly);
      setAnnualDeclarations(annual);
    } catch (err) {
      console.error('Failed to load reports:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateQuarterlyReport = async (quarter: number) => {
    try {
      setGenerating(`Q${quarter}`);
      await api.generateCBAMQuarterlyReport(selectedYear, quarter);
      await loadReports();
    } catch (err) {
      console.error('Failed to generate report:', err);
    } finally {
      setGenerating(null);
    }
  };

  const submitQuarterlyReport = (quarter: number) => {
    setConfirmState({
      open: true,
      onConfirm: async () => {
        setConfirmState(s => ({...s, open: false}));
        try {
          setSubmitting(`Q${quarter}`);
          await api.submitCBAMQuarterlyReport(selectedYear, quarter);
          await loadReports();
        } catch (err) {
          console.error('Failed to submit report:', err);
        } finally {
          setSubmitting(null);
        }
      },
      title: 'Submit Report',
      message: `Are you sure you want to submit the Q${quarter} ${selectedYear} report?`,
    });
  };

  const exportReport = async (quarter: number, format: 'xml' | 'csv') => {
    try {
      setExporting(`Q${quarter}-${format}`);

      let blob: Blob;
      let filename: string;

      if (format === 'xml') {
        blob = await api.exportCBAMQuarterlyReportXML(selectedYear, quarter);
        filename = `cbam_quarterly_report_${selectedYear}_Q${quarter}.xml`;
      } else {
        blob = await api.exportCBAMQuarterlyReportCSV(selectedYear, quarter);
        filename = `cbam_imports_${selectedYear}_Q${quarter}.csv`;
      }

      // Download the file
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground">CBAM Reports</h2>
          <p className="text-foreground-muted">
            {isDefinitivePhase ? 'Annual declarations and quarterly reports' : 'Quarterly transitional reports'}
          </p>
        </div>
        <Select value={String(selectedYear)} onChange={(e) => setSelectedYear(Number(e.target.value))}>
          {[2024, 2025, 2026].map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </Select>
      </div>

      {/* Quarterly Reports */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Quarterly Reports - {selectedYear}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((quarter) => {
            const report = getQuarterReport(quarter);
            const statusConfig = report ? STATUS_CONFIG[report.status] : STATUS_CONFIG.draft;
            const StatusIcon = statusConfig.icon;
            const isGenerating = generating === `Q${quarter}`;
            const isSubmitting = submitting === `Q${quarter}`;

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

                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => generateQuarterlyReport(quarter)}
                          isLoading={isGenerating}
                          leftIcon={<RefreshCw className="w-3 h-3" />}
                        >
                          Refresh
                        </Button>

                        {report.status === 'draft' && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => submitQuarterlyReport(quarter)}
                            isLoading={isSubmitting}
                            leftIcon={<Send className="w-3 h-3" />}
                          >
                            Submit
                          </Button>
                        )}

                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => exportReport(quarter, 'xml')}
                          isLoading={exporting === `Q${quarter}-xml`}
                          leftIcon={<FileCode className="w-3 h-3" />}
                        >
                          XML
                        </Button>

                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => exportReport(quarter, 'csv')}
                          isLoading={exporting === `Q${quarter}-csv`}
                          leftIcon={<FileSpreadsheet className="w-3 h-3" />}
                        >
                          CSV
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-4">
                      <p className="text-foreground-muted mb-3">No report generated</p>
                      <Button
                        size="sm"
                        onClick={() => generateQuarterlyReport(quarter)}
                        isLoading={isGenerating}
                      >
                        Generate Report
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

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

      {/* Annual Declarations (2026+) */}
      {isDefinitivePhase && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Annual Declarations</h3>
          {annualDeclarations.length > 0 ? (
            <div className="space-y-4">
              {annualDeclarations.map((declaration) => (
                <Card key={declaration.id}>
                  <CardContent className="py-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-semibold">{declaration.year} Annual Declaration</h4>
                        <p className="text-sm text-foreground-muted">
                          {declaration.total_imports} imports | {declaration.certificates_required.toFixed(0)} certificates required
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xl font-bold">{declaration.net_emissions_tco2e.toFixed(1)} tCO2e</p>
                        <p className="text-sm text-foreground-muted">
                          Est. cost: {declaration.estimated_cost_eur.toFixed(0)}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-foreground-muted">
                <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No annual declarations yet</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
      <ConfirmDialog
        isOpen={confirmState.open}
        onClose={() => setConfirmState(s => ({...s, open: false}))}
        onConfirm={confirmState.onConfirm}
        title={confirmState.title}
        message={confirmState.message}
        variant="warning"
        confirmLabel="Submit"
      />
    </div>
  );
}
