'use client';

import { useCallback, useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { KPICard } from '@/components/ui/KPICard';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { toast } from '@/components/ui';
import { api } from '@/lib/api';
import type { CBAMAnnualDeclarationDetail } from '@/lib/types';
import {
  AlertTriangle,
  CalendarClock,
  FileSpreadsheet,
  FileText,
  Globe,
  Info,
  Landmark,
  RefreshCw,
  Send,
  Wallet,
} from 'lucide-react';

const SUBMIT_ON_HOLD_TOOLTIP =
  'On hold until validated against the real CBAM Registry schema';

const FIRST_DECLARATION_YEAR = 2026;

function declarationYears(): number[] {
  const current = Math.max(FIRST_DECLARATION_YEAR, new Date().getFullYear());
  const years: number[] = [];
  for (let y = current; y >= FIRST_DECLARATION_YEAR; y--) years.push(y);
  return years;
}

// API decimals arrive as strings — String.toLocaleString ignores the options,
// so coerce first or "275.0000000000" renders verbatim.
const fmtT = (value: number | string) =>
  Number(value).toLocaleString('en-GB', { maximumFractionDigits: 1 });
const fmtEur = (value: number | string) =>
  Number(value).toLocaleString('en-GB', { maximumFractionDigits: 0 });

export function CBAMAnnualDeclaration() {
  const [selectedYear, setSelectedYear] = useState(FIRST_DECLARATION_YEAR);
  const [detail, setDetail] = useState<CBAMAnnualDeclarationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [exporting, setExporting] = useState(false);

  const loadDeclaration = useCallback(async (year: number) => {
    try {
      setLoading(true);
      const declarations = await api.getCBAMAnnualDeclarations();
      if (declarations.some((d) => d.year === year)) {
        setDetail(await api.getCBAMAnnualDeclarationDetail(year));
      } else {
        setDetail(null);
      }
    } catch (err) {
      console.error('Failed to load annual declaration:', err);
      toast.error('Failed to load the annual declaration');
      setDetail(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDeclaration(selectedYear);
  }, [selectedYear, loadDeclaration]);

  const generateDraft = async () => {
    try {
      setGenerating(true);
      const draft = await api.generateCBAMAnnualDeclaration(selectedYear);
      setDetail(draft);
      toast.success(`Declaration draft for ${selectedYear} generated`);
    } catch (err) {
      console.error('Failed to generate declaration draft:', err);
      toast.error('Failed to generate the declaration draft');
    } finally {
      setGenerating(false);
    }
  };

  const setStatus = async (status: 'draft' | 'ready') => {
    try {
      setUpdatingStatus(true);
      const updated = await api.updateCBAMAnnualDeclarationStatus(selectedYear, status);
      setDetail((d) => (d ? { ...d, status: updated.status } : d));
      toast.success(
        status === 'ready' ? 'Declaration marked as ready' : 'Declaration moved back to draft'
      );
    } catch (err) {
      console.error('Failed to update declaration status:', err);
      toast.error('Failed to update the declaration status');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const exportCSV = async () => {
    try {
      setExporting(true);
      const blob = await api.exportCBAMAnnualDeclarationCSV(selectedYear);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cbam_annual_declaration_${selectedYear}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to export declaration CSV:', err);
      toast.error('Failed to export the declaration CSV');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-xl font-bold text-foreground">Annual declaration</h2>
          <p className="text-foreground-muted">
            Definitive regime — the {FIRST_DECLARATION_YEAR} declaration is due 30 September{' '}
            {FIRST_DECLARATION_YEAR + 1} with certificate surrender
          </p>
        </div>
        <Select
          value={String(selectedYear)}
          onChange={(e) => setSelectedYear(Number(e.target.value))}
        >
          {declarationYears().map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </Select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : !detail ? (
        /* No draft yet — generate CTA */
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-50 text-foreground-muted" />
            <h3 className="font-semibold text-foreground mb-1">
              No declaration draft for {selectedYear} yet
            </h3>
            <p className="text-sm text-foreground-muted max-w-xl mx-auto mb-4">
              Generating a draft aggregates your {selectedYear} imports register: default-value
              lines use the Commission default values with the {selectedYear} markup, actual
              installation data is kept as recorded, and carbon prices paid abroad are deducted.
            </p>
            <Button onClick={generateDraft} isLoading={generating}>
              Generate draft
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Stale warning */}
          {detail.stale && (
            <div className="rounded-lg border border-warning/30 bg-warning/10 px-4 py-3 flex items-center gap-3 text-sm">
              <AlertTriangle className="w-4 h-4 text-warning shrink-0" />
              <span className="text-foreground">
                The imports register changed since this draft was generated — regenerate to
                refresh the totals.
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={generateDraft}
                isLoading={generating}
                className="ml-auto shrink-0"
              >
                Regenerate
              </Button>
            </div>
          )}

          {/* Status + actions */}
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3 flex-wrap text-sm">
              <Badge variant={detail.status === 'ready' ? 'success' : 'default'}>
                {detail.status}
              </Badge>
              <span className="flex items-center gap-1.5 text-foreground-muted">
                <CalendarClock className="w-4 h-4" />
                Due {new Date(detail.submission_deadline).toLocaleDateString('en-GB', {
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric',
                })}
              </span>
              <span className="text-foreground-muted">
                {detail.data_quality.default_lines} of {detail.data_quality.total_lines} lines on
                default values ({detail.data_quality.default_share_pct}%)
              </span>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <Button
                variant="outline"
                size="sm"
                onClick={generateDraft}
                isLoading={generating}
                leftIcon={<RefreshCw className="w-3 h-3" />}
              >
                Regenerate draft
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={exportCSV}
                isLoading={exporting}
                leftIcon={<FileSpreadsheet className="w-3 h-3" />}
              >
                Export CSV
              </Button>
              {detail.status === 'ready' ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setStatus('draft')}
                  isLoading={updatingStatus}
                >
                  Back to draft
                </Button>
              ) : (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setStatus('ready')}
                  isLoading={updatingStatus}
                >
                  Mark as ready
                </Button>
              )}
              <span title={SUBMIT_ON_HOLD_TOOLTIP} className="inline-block">
                <Button
                  variant="primary"
                  size="sm"
                  disabled
                  leftIcon={<Send className="w-3 h-3" />}
                >
                  Submit to Registry
                </Button>
              </span>
            </div>
          </div>

          {/* Totals */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <KPICard
              title="Embedded emissions"
              value={fmtT(detail.gross_emissions_tco2e)}
              unit="tCO2e"
              icon={<Globe className="w-5 h-5" />}
            />
            <KPICard
              title="Certificates to surrender"
              value={fmtT(detail.certificates_required)}
              icon={<Landmark className="w-5 h-5" />}
            />
            <KPICard
              title="Estimated cost"
              value={`€${fmtEur(detail.estimated_cost_eur)}`}
              unit={`at €${detail.ets_price_eur}/tCO2e`}
              icon={<Wallet className="w-5 h-5" />}
            />
            <KPICard
              title="Carbon price deductions"
              value={fmtT(detail.deductions_tco2e)}
              unit={`tCO2e · €${fmtEur(detail.deductions_eur)} paid abroad`}
              icon={<FileText className="w-5 h-5" />}
            />
          </div>

          {/* Per-sector breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Breakdown by sector</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-foreground-muted">
                      <th className="text-left py-2 pr-4 font-medium">Sector</th>
                      <th className="text-right py-2 px-4 font-medium">Imports</th>
                      <th className="text-right py-2 px-4 font-medium">Mass (t)</th>
                      <th className="text-right py-2 px-4 font-medium">Emissions (tCO2e)</th>
                      <th className="text-right py-2 px-4 font-medium">Deductions (tCO2e)</th>
                      <th className="text-right py-2 px-4 font-medium">Net (tCO2e)</th>
                      <th className="text-right py-2 pl-4 font-medium">Est. cost (€)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(detail.by_sector).map(([sector, s]) => (
                      <tr key={sector} className="border-b last:border-0">
                        <td className="py-2 pr-4 capitalize">{sector.replace('_', ' ')}</td>
                        <td className="text-right py-2 px-4">{s.import_count ?? '-'}</td>
                        <td className="text-right py-2 px-4">
                          {s.mass_tonnes != null ? fmtT(s.mass_tonnes) : '-'}
                        </td>
                        <td className="text-right py-2 px-4">{fmtT(s.gross_emissions_tco2e)}</td>
                        <td className="text-right py-2 px-4">
                          {s.deductions_tco2e != null ? fmtT(s.deductions_tco2e) : '-'}
                        </td>
                        <td className="text-right py-2 px-4">{fmtT(s.net_emissions_tco2e)}</td>
                        <td className="text-right py-2 pl-4">{fmtEur(s.estimated_cost_eur)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Per-line drill list */}
          <Card>
            <CardHeader>
              <CardTitle>Declaration lines ({detail.lines.length})</CardTitle>
            </CardHeader>
            <CardContent>
              {detail.lines.length === 0 ? (
                <p className="text-sm text-foreground-muted text-center py-4">
                  No imports registered for {selectedYear} — add imports in the imports register,
                  then regenerate the draft.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-foreground-muted">
                        <th className="text-left py-2 pr-4 font-medium">Date</th>
                        <th className="text-left py-2 px-4 font-medium">CN code</th>
                        <th className="text-left py-2 px-4 font-medium">Origin</th>
                        <th className="text-right py-2 px-4 font-medium">Mass (t)</th>
                        <th className="text-left py-2 px-4 font-medium">Intensity source</th>
                        <th className="text-right py-2 px-4 font-medium">Emissions (tCO2e)</th>
                        <th className="text-right py-2 px-4 font-medium">Deduction (tCO2e)</th>
                        <th className="text-right py-2 px-4 font-medium">Net (tCO2e)</th>
                        <th className="text-right py-2 pl-4 font-medium">Est. cost (€)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.lines.map((line) => (
                        <tr key={line.import_id} className="border-b last:border-0">
                          <td className="py-2 pr-4 whitespace-nowrap">{line.import_date}</td>
                          <td className="py-2 px-4">
                            <span className="font-medium">{line.cn_code}</span>
                            {line.product_description && (
                              <span className="block text-xs text-foreground-muted max-w-[16rem] truncate">
                                {line.product_description}
                              </span>
                            )}
                          </td>
                          <td className="py-2 px-4">{line.origin_country || '-'}</td>
                          <td className="text-right py-2 px-4">{fmtT(line.mass_tonnes)}</td>
                          <td className="py-2 px-4">
                            <span title={line.intensity_source_detail}>
                              <Badge
                                size="sm"
                                variant={line.intensity_source === 'actual' ? 'success' : 'warning'}
                              >
                                {line.intensity_source === 'actual'
                                  ? 'Actual'
                                  : `Default +${fmtT(line.markup_pct)}%`}
                              </Badge>
                            </span>
                          </td>
                          <td className="text-right py-2 px-4">{fmtT(line.emissions_tco2e)}</td>
                          <td className="text-right py-2 px-4">
                            {line.deduction_tco2e > 0 ? fmtT(line.deduction_tco2e) : '-'}
                          </td>
                          <td className="text-right py-2 px-4">{fmtT(line.net_emissions_tco2e)}</td>
                          <td className="text-right py-2 pl-4">{fmtEur(line.estimated_cost_eur)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Assumptions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="w-4 h-4" />
                Assumptions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-foreground-muted list-disc pl-5">
                {detail.assumptions.map((assumption, idx) => (
                  <li key={idx}>{assumption}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
