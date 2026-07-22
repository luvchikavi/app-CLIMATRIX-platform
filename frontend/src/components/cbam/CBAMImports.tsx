'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableEmpty,
} from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { ConfirmDialog } from '@/components/ui';
import { api } from '@/lib/api';
import { formatQty } from '@/lib/utils';
import { LoadSampleDataButton } from '@/components/LoadSampleDataButton';
import { useSampleDataStatus } from '@/hooks/useSampleData';
import type {
  CBAMImport,
  CBAMInstallation,
  CBAMCNCode,
  CBAMScreenDefaults,
} from '@/lib/types';
import { Plus, Package, Trash2 } from 'lucide-react';

const CALCULATION_METHOD_LABELS: Record<string, string> = {
  actual: 'Actual Data',
  default: 'EU Default',
  fallback: 'Fallback',
};

const eur = new Intl.NumberFormat('en-IE', {
  style: 'currency',
  currency: 'EUR',
  maximumFractionDigits: 0,
});

interface ImportFormState {
  installation_id: string;
  cn_code: string;
  product_description: string;
  import_date: string;
  mass_kg: number;
  origin_country: string;
  actual_direct_see?: number;
  actual_indirect_see?: number;
  foreign_carbon_price_eur?: number;
}

const emptyForm = (): ImportFormState => ({
  installation_id: '',
  cn_code: '',
  product_description: '',
  import_date: new Date().toISOString().split('T')[0],
  mass_kg: 0,
  origin_country: '',
});

/**
 * Estimated certificate cost for one import row.
 *
 * emissions x ETS price; the default-value markup (10% in 2026) applies
 * only when the row is calculated from default values, mirroring the
 * screening service.
 */
function estimateCost(imp: CBAMImport, defaults: CBAMScreenDefaults | null): number | null {
  if (!defaults) return null;
  const markup =
    imp.calculation_method === 'actual' ? 1 : 1 + defaults.default_value_markup_pct / 100;
  return imp.total_emissions_tco2e * markup * defaults.ets_price_eur;
}

export function CBAMImports() {
  const [imports, setImports] = useState<CBAMImport[]>([]);
  const [installations, setInstallations] = useState<CBAMInstallation[]>([]);
  const [screenDefaults, setScreenDefaults] = useState<CBAMScreenDefaults | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<ImportFormState>(emptyForm());
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [confirmState, setConfirmState] = useState<{
    open: boolean;
    onConfirm: () => void;
    title: string;
    message: string;
  }>({ open: false, onConfirm: () => {}, title: '', message: '' });

  // CN Code search
  const [cnSearchQuery, setCnSearchQuery] = useState('');
  const [cnSearchResults, setCnSearchResults] = useState<CBAMCNCode[]>([]);
  const [searchingCN, setSearchingCN] = useState(false);
  const [showCNDropdown, setShowCNDropdown] = useState(false);

  // Filters
  const [filterYear, setFilterYear] = useState<number>(new Date().getFullYear());
  const [filterQuarter, setFilterQuarter] = useState<number | ''>('');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [importsData, installationsData] = await Promise.all([
        api.getCBAMImports({
          year: filterYear,
          quarter: filterQuarter || undefined,
        }),
        api.getCBAMInstallations(),
      ]);
      setImports(importsData);
      setInstallations(installationsData);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  }, [filterYear, filterQuarter]);

  // Sample data loads/removes outside this component's manual fetch lane —
  // re-pull whenever that flag flips (also covers the initial load).
  const { data: sampleStatus } = useSampleDataStatus();
  useEffect(() => {
    loadData();
  }, [loadData, sampleStatus?.loaded]);

  useEffect(() => {
    // Reference values for the estimated certificate cost column
    api
      .getCBAMScreenDefaults()
      .then(setScreenDefaults)
      .catch((err) => console.error('Failed to load screening defaults:', err));
  }, []);

  const searchCNCodes = async (query: string) => {
    if (query.length < 2) {
      setCnSearchResults([]);
      return;
    }

    try {
      setSearchingCN(true);
      const results = await api.searchCBAMCNCodes(query);
      setCnSearchResults(results);
      setShowCNDropdown(true);
    } catch (err) {
      console.error('Failed to search CN codes:', err);
    } finally {
      setSearchingCN(false);
    }
  };

  const selectCNCode = (cnCode: CBAMCNCode) => {
    setFormData({
      ...formData,
      cn_code: cnCode.cn_code,
      product_description: cnCode.description,
    });
    setCnSearchQuery(cnCode.cn_code);
    setShowCNDropdown(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!formData.cn_code || !formData.mass_kg) return;
    if (!formData.installation_id && formData.origin_country.trim().length !== 2) {
      setFormError('Enter a 2-letter origin country code (or pick an installation).');
      return;
    }

    try {
      setSaving(true);
      await api.createCBAMImport({
        installation_id: formData.installation_id || undefined,
        cn_code: formData.cn_code,
        product_description: formData.product_description || undefined,
        import_date: formData.import_date,
        // API takes tonnes; the register records mass in kg
        mass_tonnes: formData.mass_kg / 1000,
        origin_country: formData.installation_id
          ? undefined
          : formData.origin_country.trim().toUpperCase(),
        actual_direct_see: formData.actual_direct_see,
        actual_indirect_see: formData.actual_indirect_see,
        foreign_carbon_price_eur: formData.foreign_carbon_price_eur,
      });
      await loadData();
      resetForm();
    } catch (err) {
      console.error('Failed to create import:', err);
      setFormError(err instanceof Error ? err.message : 'Failed to create import');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = (id: string) => {
    setConfirmState({
      open: true,
      onConfirm: async () => {
        setConfirmState((s) => ({ ...s, open: false }));
        try {
          await api.deleteCBAMImport(id);
          await loadData();
        } catch (err) {
          console.error('Failed to delete import:', err);
        }
      },
      title: 'Delete Import',
      message: 'Are you sure you want to delete this import?',
    });
  };

  const resetForm = () => {
    setShowForm(false);
    setFormError(null);
    setFormData(emptyForm());
    setCnSearchQuery('');
    setCnSearchResults([]);
  };

  const totalEmissions = imports.reduce((sum, imp) => sum + imp.total_emissions_tco2e, 0);
  const totalMassKg = imports.reduce((sum, imp) => sum + imp.mass_kg, 0);
  const totalCost = screenDefaults
    ? imports.reduce((sum, imp) => sum + (estimateCost(imp, screenDefaults) ?? 0), 0)
    : null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground">Imports register</h2>
          <p className="text-foreground-muted">
            Log every import of CBAM goods — CN code, mass, origin — and track the estimated
            certificate cost
          </p>
        </div>
        <Button onClick={() => setShowForm(true)} leftIcon={<Plus className="w-4 h-4" />}>
          Add Import
        </Button>
      </div>

      {/* Filters + totals */}
      <Card padding="sm">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Year:</label>
            <Select
              value={String(filterYear)}
              onChange={(e) => setFilterYear(Number(e.target.value))}
              className="w-24"
            >
              {[2024, 2025, 2026].map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Quarter:</label>
            <Select
              value={String(filterQuarter)}
              onChange={(e) => setFilterQuarter(e.target.value ? Number(e.target.value) : '')}
              className="w-24"
            >
              <option value="">All</option>
              {[1, 2, 3, 4].map((q) => (
                <option key={q} value={q}>
                  Q{q}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex-1" />
          <div className="flex items-center gap-4 text-sm">
            <span>
              <strong>{imports.length}</strong> imports
            </span>
            <span>
              <strong>{(totalMassKg / 1000).toFixed(1)}</strong> t
            </span>
            <span>
              <strong>{totalEmissions.toFixed(1)}</strong> tCO2e
            </span>
            {totalCost !== null && (
              <span>
                est. <strong>{eur.format(totalCost)}</strong>
              </span>
            )}
          </div>
        </div>
        {screenDefaults && (
          <p className="mt-2 text-xs text-foreground-muted">
            Certificate cost estimated at €{screenDefaults.ets_price_eur.toFixed(2)}/tCO2e (
            {screenDefaults.ets_price_is_fallback
              ? 'placeholder ETS price'
              : `ETS price of ${screenDefaults.ets_price_date}`}
            ), +{screenDefaults.default_value_markup_pct}% markup on default values.
          </p>
        )}
      </Card>

      {/* Add Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Add New Import</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="relative">
                  <Input
                    label="CN Code *"
                    value={cnSearchQuery}
                    onChange={(e) => {
                      setCnSearchQuery(e.target.value);
                      setFormData({ ...formData, cn_code: e.target.value });
                      searchCNCodes(e.target.value);
                    }}
                    onFocus={() => cnSearchResults.length > 0 && setShowCNDropdown(true)}
                    placeholder="Search CN code or description..."
                    required
                  />
                  {searchingCN && (
                    <div className="absolute right-3 top-9">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                    </div>
                  )}
                  {showCNDropdown && cnSearchResults.length > 0 && (
                    <div className="absolute z-10 w-full mt-1 bg-background-elevated border border-border rounded-lg shadow-lg max-h-60 overflow-auto">
                      {cnSearchResults.map((cn) => (
                        <button
                          key={cn.cn_code}
                          type="button"
                          onClick={() => selectCNCode(cn)}
                          className="w-full px-4 py-2 text-left hover:bg-background-muted flex justify-between items-center"
                        >
                          <div>
                            <p className="font-mono text-sm">{cn.cn_code}</p>
                            <p className="text-xs text-foreground-muted">{cn.description}</p>
                          </div>
                          <Badge variant="secondary" size="sm">
                            {cn.sector}
                          </Badge>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <Input
                  label="Product Description"
                  value={formData.product_description}
                  onChange={(e) =>
                    setFormData({ ...formData, product_description: e.target.value })
                  }
                  placeholder="Optional description"
                />

                <Input
                  label="Mass (kg) *"
                  type="number"
                  step="1"
                  min="0"
                  value={formData.mass_kg || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, mass_kg: parseFloat(e.target.value) || 0 })
                  }
                  required
                />

                <Input
                  label="Import Date *"
                  type="date"
                  value={formData.import_date}
                  onChange={(e) => setFormData({ ...formData, import_date: e.target.value })}
                  required
                />

                <Select
                  label="Installation (optional)"
                  value={formData.installation_id}
                  onChange={(e) => setFormData({ ...formData, installation_id: e.target.value })}
                >
                  <option value="">No installation — enter origin country</option>
                  {installations.map((inst) => (
                    <option key={inst.id} value={inst.id}>
                      {inst.name} ({inst.country_code})
                    </option>
                  ))}
                </Select>

                <Input
                  label={formData.installation_id ? 'Origin Country (from installation)' : 'Origin Country *'}
                  value={
                    formData.installation_id
                      ? installations.find((i) => i.id === formData.installation_id)
                          ?.country_code || ''
                      : formData.origin_country
                  }
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      origin_country: e.target.value.toUpperCase().slice(0, 2),
                    })
                  }
                  placeholder="ISO code, e.g. TR"
                  maxLength={2}
                  disabled={!!formData.installation_id}
                  required={!formData.installation_id}
                />

                <Input
                  label="Actual Direct SEE (optional)"
                  type="number"
                  step="0.001"
                  value={formData.actual_direct_see || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      actual_direct_see: parseFloat(e.target.value) || undefined,
                    })
                  }
                  placeholder="tCO2e/tonne"
                />

                <Input
                  label="Carbon Price Paid (EUR, optional)"
                  type="number"
                  step="0.01"
                  value={formData.foreign_carbon_price_eur || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      foreign_carbon_price_eur: parseFloat(e.target.value) || undefined,
                    })
                  }
                  placeholder="Price paid in origin country"
                />
              </div>

              {formError && <p className="text-sm text-error">{formError}</p>}

              <div className="flex justify-end gap-3">
                <Button type="button" variant="ghost" onClick={resetForm}>
                  Cancel
                </Button>
                <Button type="submit" isLoading={saving}>
                  Create Import
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Imports Table */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>CN Code</TableHead>
              <TableHead>Sector</TableHead>
              <TableHead>Origin</TableHead>
              <TableHead>Mass (kg)</TableHead>
              <TableHead>Emissions</TableHead>
              <TableHead>Method</TableHead>
              <TableHead>Est. certificate cost</TableHead>
              <TableHead className="w-16">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={9} className="text-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto"></div>
                </TableCell>
              </TableRow>
            ) : imports.length === 0 ? (
              <TableEmpty
                colSpan={9}
                icon={<Package className="w-12 h-12" />}
                title="No imports yet"
                description="Record your first CBAM import to start tracking embedded emissions and certificate cost — or load sample data for three worked imports (steel, cement, aluminium) with default-value emissions"
                action={
                  <div className="flex flex-col items-center gap-2">
                    <Button size="sm" onClick={() => setShowForm(true)}>
                      Add Import
                    </Button>
                    <LoadSampleDataButton />
                  </div>
                }
              />
            ) : (
              <>
                {imports.map((imp) => {
                  const cost = estimateCost(imp, screenDefaults);
                  return (
                    <TableRow key={imp.id}>
                      <TableCell>{new Date(imp.import_date).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <div>
                          <p className="font-mono text-sm">{imp.cn_code}</p>
                          {imp.product_description && (
                            <p className="text-xs text-foreground-muted truncate max-w-40">
                              {imp.product_description}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" size="sm">
                          {imp.sector.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>{imp.origin_country || '—'}</TableCell>
                      <TableCell>{formatQty(imp.mass_kg)}</TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium">{formatQty(imp.total_emissions_tco2e)} tCO2e</p>
                          <p className="text-xs text-foreground-muted">
                            D: {formatQty(imp.direct_emissions_tco2e)} / I:{' '}
                            {formatQty(imp.indirect_emissions_tco2e)}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={imp.calculation_method === 'actual' ? 'success' : 'secondary'}
                          size="sm"
                        >
                          {CALCULATION_METHOD_LABELS[imp.calculation_method]}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {cost !== null ? (
                          <span className="font-medium">{eur.format(cost)}</span>
                        ) : (
                          <span className="text-foreground-muted">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(imp.id)}>
                          <Trash2 className="w-4 h-4 text-error" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
                {totalCost !== null && (
                  <TableRow>
                    <TableCell colSpan={4} className="font-semibold">
                      Total
                    </TableCell>
                    <TableCell className="font-semibold">
                      {formatQty(totalMassKg)}
                    </TableCell>
                    <TableCell className="font-semibold">
                      {formatQty(totalEmissions)} tCO2e
                    </TableCell>
                    <TableCell />
                    <TableCell className="font-semibold">{eur.format(totalCost)}</TableCell>
                    <TableCell />
                  </TableRow>
                )}
              </>
            )}
          </TableBody>
        </Table>
      </Card>
      <ConfirmDialog
        isOpen={confirmState.open}
        onClose={() => setConfirmState((s) => ({ ...s, open: false }))}
        onConfirm={confirmState.onConfirm}
        title={confirmState.title}
        message={confirmState.message}
        variant="danger"
        confirmLabel="Delete"
      />
    </div>
  );
}
