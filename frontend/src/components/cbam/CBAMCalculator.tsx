'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import type { CBAMEmissionCalculationResult, CBAMCNCode } from '@/lib/types';
import { Calculator, AlertTriangle, CheckCircle, Info, Search } from 'lucide-react';

export function CBAMCalculator() {
  const [cnCode, setCnCode] = useState('');
  const [cnSearchQuery, setCnSearchQuery] = useState('');
  const [cnSearchResults, setCnSearchResults] = useState<CBAMCNCode[]>([]);
  const [showCNDropdown, setShowCNDropdown] = useState(false);
  const [searchingCN, setSearchingCN] = useState(false);

  const [countryCode, setCountryCode] = useState('');
  const [massTonnes, setMassTonnes] = useState<number>(100);
  const [actualDirectSee, setActualDirectSee] = useState<number | ''>('');
  const [actualIndirectSee, setActualIndirectSee] = useState<number | ''>('');
  const [electricityMwh, setElectricityMwh] = useState<number | ''>('');
  const [foreignCarbonPrice, setForeignCarbonPrice] = useState<number | ''>('');

  const [calculating, setCalculating] = useState(false);
  const [result, setResult] = useState<CBAMEmissionCalculationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  const selectCNCode = (cn: CBAMCNCode) => {
    setCnCode(cn.cn_code);
    setCnSearchQuery(cn.cn_code + ' - ' + cn.description);
    setShowCNDropdown(false);
  };

  const calculate = async () => {
    if (!cnCode || !countryCode || !massTonnes) {
      setError('Please fill in CN Code, Country Code, and Mass');
      return;
    }

    try {
      setCalculating(true);
      setError(null);

      const data = await api.calculateCBAMEmissions({
        cn_code: cnCode,
        mass_tonnes: massTonnes,
        country_code: countryCode.toUpperCase(),
        actual_direct_see: actualDirectSee || undefined,
        actual_indirect_see: actualIndirectSee || undefined,
        electricity_consumption_mwh: electricityMwh || undefined,
        foreign_carbon_price_eur: foreignCarbonPrice || undefined,
      });

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Calculation failed');
      setResult(null);
    } finally {
      setCalculating(false);
    }
  };

  const reset = () => {
    setCnCode('');
    setCnSearchQuery('');
    setCountryCode('');
    setMassTonnes(100);
    setActualDirectSee('');
    setActualIndirectSee('');
    setElectricityMwh('');
    setForeignCarbonPrice('');
    setResult(null);
    setError(null);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-foreground">Emissions Calculator</h2>
        <p className="text-foreground-muted">Preview CBAM embedded emissions before recording imports</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="w-5 h-5" />
              Calculate Embedded Emissions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* CN Code Search */}
              <div className="relative">
                <Input
                  label="CN Code *"
                  value={cnSearchQuery}
                  onChange={(e) => {
                    setCnSearchQuery(e.target.value);
                    searchCNCodes(e.target.value);
                  }}
                  onFocus={() => cnSearchResults.length > 0 && setShowCNDropdown(true)}
                  placeholder="Search by CN code or product name..."
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

              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Country of Origin *"
                  value={countryCode}
                  onChange={(e) => setCountryCode(e.target.value.toUpperCase())}
                  placeholder="e.g., CN, IN, TR"
                  maxLength={2}
                />
                <Input
                  label="Mass (tonnes) *"
                  type="number"
                  step="0.001"
                  min="0"
                  value={massTonnes}
                  onChange={(e) => setMassTonnes(parseFloat(e.target.value) || 0)}
                />
              </div>

              <div className="border-t pt-4">
                <p className="text-sm font-medium mb-3">
                  Optional: Actual Installation Data
                  <span className="font-normal text-foreground-muted ml-2">
                    (leave blank to use EU default values)
                  </span>
                </p>

                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="Direct SEE (tCO2e/t)"
                    type="number"
                    step="0.001"
                    value={actualDirectSee}
                    onChange={(e) => setActualDirectSee(parseFloat(e.target.value) || '')}
                    placeholder="From installation"
                  />
                  <Input
                    label="Indirect SEE (tCO2e/t)"
                    type="number"
                    step="0.001"
                    value={actualIndirectSee}
                    onChange={(e) => setActualIndirectSee(parseFloat(e.target.value) || '')}
                    placeholder="From installation"
                  />
                  <Input
                    label="Electricity (MWh)"
                    type="number"
                    step="0.001"
                    value={electricityMwh}
                    onChange={(e) => setElectricityMwh(parseFloat(e.target.value) || '')}
                    placeholder="Total consumption"
                  />
                  <Input
                    label="Foreign Carbon Price (EUR)"
                    type="number"
                    step="0.01"
                    value={foreignCarbonPrice}
                    onChange={(e) => setForeignCarbonPrice(parseFloat(e.target.value) || '')}
                    placeholder="Price paid/tCO2e"
                  />
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-2 text-error text-sm">
                  <AlertTriangle className="w-4 h-4" />
                  {error}
                </div>
              )}

              <div className="flex gap-3">
                <Button onClick={calculate} isLoading={calculating} className="flex-1">
                  Calculate Emissions
                </Button>
                <Button variant="outline" onClick={reset}>
                  Reset
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        <Card>
          <CardHeader>
            <CardTitle>Calculation Results</CardTitle>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="space-y-6">
                {/* Summary */}
                <div className="bg-background-muted rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-sm text-foreground-muted">Product</p>
                      <p className="font-mono">{result.summary.cn_code}</p>
                      <Badge variant="secondary" size="sm" className="mt-1">
                        {result.summary.sector}
                      </Badge>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-foreground-muted">Method</p>
                      <Badge
                        variant={result.summary.calculation_method === 'actual' ? 'success' : 'secondary'}
                      >
                        {result.summary.calculation_method === 'actual' ? 'Actual Data' : 'EU Default'}
                      </Badge>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-foreground-muted">Mass</p>
                      <p className="text-xl font-bold">{result.summary.mass_tonnes} t</p>
                    </div>
                    <div>
                      <p className="text-sm text-foreground-muted">Total Emissions</p>
                      <p className="text-xl font-bold text-primary">
                        {result.summary.total_emissions_tco2e.toFixed(3)} tCO2e
                      </p>
                    </div>
                  </div>
                </div>

                {/* SEE Details */}
                <div>
                  <h4 className="font-medium mb-2">Specific Embedded Emissions (SEE)</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="bg-background-muted rounded p-3">
                      <p className="text-foreground-muted">Direct</p>
                      <p className="font-semibold">{result.embedded_emissions.direct_see.toFixed(4)} tCO2e/t</p>
                    </div>
                    <div className="bg-background-muted rounded p-3">
                      <p className="text-foreground-muted">Indirect</p>
                      <p className="font-semibold">{result.embedded_emissions.indirect_see.toFixed(4)} tCO2e/t</p>
                    </div>
                    <div className="bg-primary/10 rounded p-3">
                      <p className="text-foreground-muted">Total</p>
                      <p className="font-semibold">{result.embedded_emissions.total_see.toFixed(4)} tCO2e/t</p>
                    </div>
                  </div>
                </div>

                {/* Emissions Breakdown */}
                <div>
                  <h4 className="font-medium mb-2">Emissions Breakdown</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-foreground-muted">Direct Emissions</span>
                      <span className="font-medium">
                        {result.embedded_emissions.direct_emissions_tco2e.toFixed(3)} tCO2e
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-foreground-muted">Indirect Emissions</span>
                      <span className="font-medium">
                        {result.embedded_emissions.indirect_emissions_tco2e.toFixed(3)} tCO2e
                      </span>
                    </div>
                    <div className="flex justify-between items-center pt-2 border-t">
                      <span className="font-medium">Total Embedded Emissions</span>
                      <span className="font-bold text-primary">
                        {result.embedded_emissions.total_emissions_tco2e.toFixed(3)} tCO2e
                      </span>
                    </div>
                  </div>
                </div>

                {/* Carbon Price Deduction */}
                {result.carbon_price_deduction.deduction_tco2e > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Carbon Price Deduction</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-foreground-muted">Foreign Price</span>
                        <span>{result.carbon_price_deduction.foreign_carbon_price_eur} EUR/tCO2e</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-foreground-muted">Deduction</span>
                        <span className="text-success">
                          -{result.carbon_price_deduction.deduction_tco2e.toFixed(3)} tCO2e
                        </span>
                      </div>
                      <div className="flex justify-between font-medium pt-2 border-t">
                        <span>Net Emissions</span>
                        <span>{result.carbon_price_deduction.net_emissions_tco2e.toFixed(3)} tCO2e</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* CBAM Cost Estimate */}
                <div className="bg-blue-50 rounded-lg p-4">
                  <h4 className="font-medium mb-2 flex items-center gap-2">
                    <Info className="w-4 h-4" />
                    Estimated CBAM Cost
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-foreground-muted">Gross Cost</p>
                      <p className="font-semibold">
                        {result.carbon_price_deduction.gross_cbam_cost_eur.toFixed(2)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-foreground-muted">Net Cost (after deductions)</p>
                      <p className="font-bold text-lg">
                        {result.carbon_price_deduction.net_cbam_cost_eur.toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Warnings */}
                {result.warnings.length > 0 && (
                  <div className="border-l-4 border-yellow-400 bg-yellow-50 p-3">
                    <h4 className="font-medium text-yellow-800 flex items-center gap-2 mb-2">
                      <AlertTriangle className="w-4 h-4" />
                      Notes
                    </h4>
                    <ul className="text-sm text-yellow-700 space-y-1">
                      {result.warnings.map((warning, idx) => (
                        <li key={idx}>- {warning}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-foreground-muted">
                <Calculator className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Enter product details and click Calculate to preview emissions</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
