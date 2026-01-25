'use client';

import { useState, useEffect } from 'react';
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
import { api } from '@/lib/api';
import type { CBAMImport, CBAMImportCreate, CBAMInstallation, CBAMCNCode } from '@/lib/types';
import { Plus, Package, Trash2, Search, X, Calculator } from 'lucide-react';

const CALCULATION_METHOD_LABELS: Record<string, string> = {
  actual: 'Actual Data',
  default: 'EU Default',
  fallback: 'Fallback',
};

export function CBAMImports() {
  const [imports, setImports] = useState<CBAMImport[]>([]);
  const [installations, setInstallations] = useState<CBAMInstallation[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<CBAMImportCreate>({
    installation_id: '',
    cn_code: '',
    product_description: '',
    import_date: new Date().toISOString().split('T')[0],
    mass_tonnes: 0,
  });
  const [saving, setSaving] = useState(false);

  // CN Code search
  const [cnSearchQuery, setCnSearchQuery] = useState('');
  const [cnSearchResults, setCnSearchResults] = useState<CBAMCNCode[]>([]);
  const [searchingCN, setSearchingCN] = useState(false);
  const [showCNDropdown, setShowCNDropdown] = useState(false);

  // Filters
  const [filterYear, setFilterYear] = useState<number>(new Date().getFullYear());
  const [filterQuarter, setFilterQuarter] = useState<number | ''>('');

  useEffect(() => {
    loadData();
  }, [filterYear, filterQuarter]);

  const loadData = async () => {
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
  };

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
    if (!formData.installation_id || !formData.cn_code || !formData.mass_tonnes) return;

    try {
      setSaving(true);
      await api.createCBAMImport(formData);
      await loadData();
      resetForm();
    } catch (err) {
      console.error('Failed to create import:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this import?')) return;

    try {
      await api.deleteCBAMImport(id);
      await loadData();
    } catch (err) {
      console.error('Failed to delete import:', err);
    }
  };

  const resetForm = () => {
    setShowForm(false);
    setFormData({
      installation_id: '',
      cn_code: '',
      product_description: '',
      import_date: new Date().toISOString().split('T')[0],
      mass_tonnes: 0,
    });
    setCnSearchQuery('');
    setCnSearchResults([]);
  };

  const totalEmissions = imports.reduce((sum, imp) => sum + imp.total_emissions_tco2e, 0);
  const totalMass = imports.reduce((sum, imp) => sum + imp.mass_tonnes, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground">CBAM Imports</h2>
          <p className="text-foreground-muted">Track imported goods and their embedded emissions</p>
        </div>
        <Button onClick={() => setShowForm(true)} leftIcon={<Plus className="w-4 h-4" />}>
          Add Import
        </Button>
      </div>

      {/* Filters */}
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
              <strong>{totalMass.toFixed(1)}</strong> tonnes
            </span>
            <span>
              <strong>{totalEmissions.toFixed(1)}</strong> tCO2e
            </span>
          </div>
        </div>
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
                <Select
                  label="Installation *"
                  value={formData.installation_id}
                  onChange={(e) => setFormData({ ...formData, installation_id: e.target.value })}
                  required
                >
                  <option value="">Select installation...</option>
                  {installations.map((inst) => (
                    <option key={inst.id} value={inst.id}>
                      {inst.name} ({inst.country_code})
                    </option>
                  ))}
                </Select>

                <div className="relative">
                  <Input
                    label="CN Code *"
                    value={cnSearchQuery}
                    onChange={(e) => {
                      setCnSearchQuery(e.target.value);
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
                  onChange={(e) => setFormData({ ...formData, product_description: e.target.value })}
                  placeholder="Optional description"
                />

                <Input
                  label="Import Date *"
                  type="date"
                  value={formData.import_date}
                  onChange={(e) => setFormData({ ...formData, import_date: e.target.value })}
                  required
                />

                <Input
                  label="Mass (tonnes) *"
                  type="number"
                  step="0.001"
                  min="0"
                  value={formData.mass_tonnes || ''}
                  onChange={(e) => setFormData({ ...formData, mass_tonnes: parseFloat(e.target.value) || 0 })}
                  required
                />

                <Input
                  label="Actual Direct SEE (optional)"
                  type="number"
                  step="0.001"
                  value={formData.actual_direct_see || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, actual_direct_see: parseFloat(e.target.value) || undefined })
                  }
                  placeholder="tCO2e/tonne"
                />

                <Input
                  label="Actual Indirect SEE (optional)"
                  type="number"
                  step="0.001"
                  value={formData.actual_indirect_see || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, actual_indirect_see: parseFloat(e.target.value) || undefined })
                  }
                  placeholder="tCO2e/tonne"
                />

                <Input
                  label="Foreign Carbon Price (EUR)"
                  type="number"
                  step="0.01"
                  value={formData.foreign_carbon_price_eur || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, foreign_carbon_price_eur: parseFloat(e.target.value) || undefined })
                  }
                  placeholder="Price paid in origin country"
                />
              </div>

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
              <TableHead>Mass</TableHead>
              <TableHead>SEE</TableHead>
              <TableHead>Emissions</TableHead>
              <TableHead>Method</TableHead>
              <TableHead className="w-16">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto"></div>
                </TableCell>
              </TableRow>
            ) : imports.length === 0 ? (
              <TableEmpty
                colSpan={8}
                icon={<Package className="w-12 h-12" />}
                title="No imports yet"
                description="Record your first CBAM import to start tracking embedded emissions"
                action={
                  <Button size="sm" onClick={() => setShowForm(true)}>
                    Add Import
                  </Button>
                }
              />
            ) : (
              imports.map((imp) => (
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
                  <TableCell>{imp.mass_tonnes.toFixed(3)} t</TableCell>
                  <TableCell>
                    <div className="text-xs">
                      <p>D: {imp.direct_see.toFixed(3)}</p>
                      <p>I: {imp.indirect_see.toFixed(3)}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="font-medium">{imp.total_emissions_tco2e.toFixed(3)} tCO2e</p>
                      <p className="text-xs text-foreground-muted">
                        D: {imp.direct_emissions_tco2e.toFixed(3)} / I: {imp.indirect_emissions_tco2e.toFixed(3)}
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
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(imp.id)}>
                      <Trash2 className="w-4 h-4 text-error" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
