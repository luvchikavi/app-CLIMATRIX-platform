'use client';

/**
 * LeasedAssetsForm - Category 3.8 Upstream Leased Assets
 *
 * Supports 3 methods per GHG Protocol:
 * 1. Area - Based on floor area (m²) by building type
 * 2. Energy - Based on actual energy consumption (kWh)
 * 3. Spend - Based on rent/lease payments
 */

import { useState, useMemo } from 'react';
import { useWizardStore } from '@/stores/wizard';
import { useCreateActivity } from '@/hooks/useEmissions';
import { Button, Input } from '@/components/ui';
import { formatCO2e } from '@/lib/utils';
import {
  Calculator,
  Save,
  Plus,
  Loader2,
  ArrowLeft,
  Building,
  Warehouse,
  Store,
  Factory,
  Server,
  Zap,
  Info,
} from 'lucide-react';

// =============================================================================
// LEASED ASSETS DATA DEFINITIONS
// =============================================================================

type LeasedMethod = 'area' | 'energy' | 'spend';

// Building Types with emission factor estimates (kg CO2e per m² per year)
const BUILDING_TYPES = [
  { key: 'office', label: 'Office', icon: Building, ef: 120 },
  { key: 'warehouse', label: 'Warehouse', icon: Warehouse, ef: 45 },
  { key: 'retail', label: 'Retail', icon: Store, ef: 180 },
  { key: 'industrial', label: 'Industrial', icon: Factory, ef: 85 },
  { key: 'datacenter', label: 'Data Center', icon: Server, ef: 850 },
  { key: 'mixed', label: 'Mixed Use', icon: Building, ef: 100 },
];

// Countries with grid factors (kg CO2e per kWh)
const COUNTRIES = [
  { code: 'IL', name: 'Israel', gridFactor: 0.53 },
  { code: 'GB', name: 'United Kingdom', gridFactor: 0.21 },
  { code: 'US', name: 'United States', gridFactor: 0.42 },
  { code: 'DE', name: 'Germany', gridFactor: 0.38 },
  { code: 'FR', name: 'France', gridFactor: 0.06 },
  { code: 'NL', name: 'Netherlands', gridFactor: 0.39 },
  { code: 'CH', name: 'Switzerland', gridFactor: 0.01 },
  { code: 'JP', name: 'Japan', gridFactor: 0.47 },
  { code: 'CN', name: 'China', gridFactor: 0.58 },
  { code: 'AU', name: 'Australia', gridFactor: 0.79 },
  { code: 'IN', name: 'India', gridFactor: 0.82 },
  { code: 'OTHER', name: 'Other (Global Avg)', gridFactor: 0.45 },
];

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'ILS', symbol: '₪', name: 'Israeli Shekel' },
];

// Emission factor estimates
const EF_ESTIMATES = {
  gas_per_kwh: 0.18, // kg CO2e per kWh of natural gas
  spend_per_usd: 0.15, // kg CO2e per USD (EEIO)
};

interface LeasedAssetsFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function LeasedAssetsForm({ periodId, onSuccess }: LeasedAssetsFormProps) {
  const goBack = useWizardStore((s) => s.goBack);
  const resetWizard = useWizardStore((s) => s.reset);
  const createActivity = useCreateActivity(periodId);

  // Method selection
  const [method, setMethod] = useState<LeasedMethod>('area');

  // Area method fields
  const [buildingType, setBuildingType] = useState('office');
  const [floorArea, setFloorArea] = useState<number | null>(null);

  // Energy method fields
  const [electricityKwh, setElectricityKwh] = useState<number | null>(null);
  const [gasKwh, setGasKwh] = useState<number | null>(null);
  const [country, setCountry] = useState('IL');

  // Spend method fields
  const [spendAmount, setSpendAmount] = useState<number | null>(null);
  const [currency, setCurrency] = useState('USD');

  // Common fields
  const [description, setDescription] = useState('');
  const [address, setAddress] = useState('');
  const [reportingYear, setReportingYear] = useState(new Date().getFullYear());

  // Calculate estimated emissions
  const estimatedEmissions = useMemo(() => {
    if (method === 'area') {
      if (!floorArea || floorArea <= 0) return null;
      const building = BUILDING_TYPES.find(b => b.key === buildingType);
      return floorArea * (building?.ef || 100);
    }

    if (method === 'energy') {
      const countryData = COUNTRIES.find(c => c.code === country);
      const gridFactor = countryData?.gridFactor || 0.45;

      let total = 0;
      if (electricityKwh && electricityKwh > 0) {
        total += electricityKwh * gridFactor;
      }
      if (gasKwh && gasKwh > 0) {
        total += gasKwh * EF_ESTIMATES.gas_per_kwh;
      }
      return total > 0 ? total : null;
    }

    if (method === 'spend') {
      if (!spendAmount || spendAmount <= 0) return null;
      return spendAmount * EF_ESTIMATES.spend_per_usd;
    }

    return null;
  }, [method, buildingType, floorArea, electricityKwh, gasKwh, country, spendAmount]);

  // Build activity payload
  const buildPayload = () => {
    const basePayload = {
      scope: 3,
      category_code: '3.8',
      activity_date: `${reportingYear}-06-30`, // Mid-year as default
    };

    if (method === 'spend') {
      return {
        ...basePayload,
        activity_key: 'leased_spend_rent',
        quantity: spendAmount,
        unit: 'USD',
        description: description || `Leased assets rent - ${address || 'All properties'}`,
      };
    }

    if (method === 'energy') {
      // Create separate activities for electricity and gas if both provided
      // For simplicity, combine into one with electricity as primary
      const totalEnergy = (electricityKwh || 0) + (gasKwh || 0);
      return {
        ...basePayload,
        activity_key: 'electricity_global',
        quantity: totalEnergy,
        unit: 'kWh',
        description: description || `Leased asset energy - ${electricityKwh || 0} kWh elec, ${gasKwh || 0} kWh gas`,
      };
    }

    // Area method
    const building = BUILDING_TYPES.find(b => b.key === buildingType);
    const activityKeyMap: Record<string, string> = {
      office: 'leased_office_m2_year',
      warehouse: 'leased_warehouse_m2_year',
      retail: 'leased_retail_m2_year',
      industrial: 'leased_industrial_m2_year',
      datacenter: 'leased_datacenter_m2_year',
      mixed: 'leased_office_m2_year',
    };

    return {
      ...basePayload,
      activity_key: activityKeyMap[buildingType] || 'leased_office_m2_year',
      quantity: floorArea,
      unit: 'm2-year',
      description: description || `${building?.label || 'Leased'} space - ${floorArea} m², ${address || 'Unspecified location'}`,
    };
  };

  const isValid = () => {
    if (method === 'spend') {
      return spendAmount && spendAmount > 0;
    }
    if (method === 'energy') {
      return (electricityKwh && electricityKwh > 0) || (gasKwh && gasKwh > 0);
    }
    // Area
    return floorArea && floorArea > 0;
  };

  const handleSave = async (addAnother = false) => {
    if (!isValid()) return;

    const payload = buildPayload();
    await createActivity.mutateAsync(payload as any);

    if (addAnother) {
      // Reset form but keep method
      setDescription('');
      setAddress('');
      setFloorArea(null);
      setElectricityKwh(null);
      setGasKwh(null);
      setSpendAmount(null);
    } else {
      resetWizard();
      onSuccess?.();
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Upstream Leased Assets</h2>
          <p className="text-sm text-foreground-muted">Category 3.8 - Assets leased by your company</p>
        </div>
        <Button variant="ghost" size="sm" onClick={goBack}>
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back
        </Button>
      </div>

      {/* Info Box */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
        <strong>Note:</strong> Only include assets where you do NOT have operational control.
        If you control the asset's operations, report in Scope 1 (fuel) or Scope 2 (electricity).
      </div>

      {/* Method Selection */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">Calculation Method</label>
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => setMethod('area')}
            className={`p-3 rounded-lg border text-sm font-medium transition-colors ${
              method === 'area'
                ? 'bg-primary/10 border-primary text-primary'
                : 'bg-background border-border text-foreground hover:border-primary/50'
            }`}
          >
            <Building className="w-5 h-5 mx-auto mb-1" />
            Area
            <span className="block text-xs text-foreground-muted mt-1">Floor space (m²)</span>
          </button>
          <button
            onClick={() => setMethod('energy')}
            className={`p-3 rounded-lg border text-sm font-medium transition-colors ${
              method === 'energy'
                ? 'bg-primary/10 border-primary text-primary'
                : 'bg-background border-border text-foreground hover:border-primary/50'
            }`}
          >
            <Zap className="w-5 h-5 mx-auto mb-1" />
            Energy
            <span className="block text-xs text-foreground-muted mt-1">Actual kWh</span>
          </button>
          <button
            onClick={() => setMethod('spend')}
            className={`p-3 rounded-lg border text-sm font-medium transition-colors ${
              method === 'spend'
                ? 'bg-primary/10 border-primary text-primary'
                : 'bg-background border-border text-foreground hover:border-primary/50'
            }`}
          >
            <Calculator className="w-5 h-5 mx-auto mb-1" />
            Spend
            <span className="block text-xs text-foreground-muted mt-1">Rent payments</span>
          </button>
        </div>
      </div>

      {/* Area Method */}
      {method === 'area' && (
        <div className="space-y-4">
          {/* Building Type */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Building Type</label>
            <div className="grid grid-cols-3 gap-2">
              {BUILDING_TYPES.map(b => {
                const Icon = b.icon;
                return (
                  <button
                    key={b.key}
                    onClick={() => setBuildingType(b.key)}
                    className={`p-3 rounded-lg border text-sm font-medium transition-colors ${
                      buildingType === b.key
                        ? 'bg-primary/10 border-primary text-primary'
                        : 'bg-background border-border text-foreground hover:border-primary/50'
                    }`}
                  >
                    <Icon className="w-4 h-4 mx-auto mb-1" />
                    {b.label}
                    <span className="block text-xs text-foreground-muted mt-1">
                      ~{b.ef} kg/m²/yr
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Floor Area */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Floor Area (m²)</label>
            <Input
              type="number"
              value={floorArea || ''}
              onChange={(e) => setFloorArea(e.target.value ? Number(e.target.value) : null)}
              placeholder="e.g., 500"
              min={1}
            />
          </div>
        </div>
      )}

      {/* Energy Method */}
      {method === 'energy' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Electricity (kWh/year)</label>
              <Input
                type="number"
                value={electricityKwh || ''}
                onChange={(e) => setElectricityKwh(e.target.value ? Number(e.target.value) : null)}
                placeholder="e.g., 50000"
                min={0}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Natural Gas (kWh/year)</label>
              <Input
                type="number"
                value={gasKwh || ''}
                onChange={(e) => setGasKwh(e.target.value ? Number(e.target.value) : null)}
                placeholder="e.g., 10000"
                min={0}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Country (for grid factor)</label>
            <select
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground"
            >
              {COUNTRIES.map(c => (
                <option key={c.code} value={c.code}>
                  {c.name} ({c.gridFactor} kg CO2e/kWh)
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Spend Method */}
      {method === 'spend' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Annual Rent/Lease</label>
              <Input
                type="number"
                value={spendAmount || ''}
                onChange={(e) => setSpendAmount(e.target.value ? Number(e.target.value) : null)}
                placeholder="e.g., 120000"
                min={0}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground"
              >
                {CURRENCIES.map(c => (
                  <option key={c.code} value={c.code}>{c.code} - {c.name}</option>
                ))}
              </select>
            </div>
          </div>
          <p className="text-xs text-foreground-muted">
            Enter total annual rent/lease payments for assets not under your operational control.
          </p>
        </div>
      )}

      {/* Common Fields */}
      <div className="space-y-4 border-t border-border pt-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Address/Location (Optional)</label>
            <Input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="e.g., 123 Main St, London"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Reporting Year</label>
            <Input
              type="number"
              value={reportingYear}
              onChange={(e) => setReportingYear(Number(e.target.value))}
              min={2020}
              max={2030}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-1">Description (Optional)</label>
          <Input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., Regional sales office"
          />
        </div>
      </div>

      {/* Emission Estimate */}
      {estimatedEmissions !== null && (
        <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-primary mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-foreground">Estimated Annual Emissions</h4>
              <p className="text-2xl font-bold text-primary mt-1">
                {formatCO2e(estimatedEmissions)}
              </p>
              <p className="text-xs text-foreground-muted mt-1">
                {method === 'area' && floorArea && (
                  <>
                    {floorArea.toLocaleString()} m² × ~{BUILDING_TYPES.find(b => b.key === buildingType)?.ef || 100} kg CO2e/m²/year
                  </>
                )}
                {method === 'energy' && (
                  <>
                    {electricityKwh ? `${electricityKwh.toLocaleString()} kWh electricity` : ''}
                    {electricityKwh && gasKwh ? ' + ' : ''}
                    {gasKwh ? `${gasKwh.toLocaleString()} kWh gas` : ''}
                  </>
                )}
                {method === 'spend' && spendAmount && (
                  <>
                    {currency} {spendAmount.toLocaleString()} × EEIO factor
                  </>
                )}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 pt-4">
        <Button
          variant="outline"
          className="flex-1"
          onClick={() => handleSave(true)}
          disabled={!isValid() || createActivity.isPending}
        >
          {createActivity.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <Plus className="w-4 h-4 mr-2" />
          )}
          Save & Add Another
        </Button>
        <Button
          className="flex-1"
          onClick={() => handleSave(false)}
          disabled={!isValid() || createActivity.isPending}
        >
          {createActivity.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          Save
        </Button>
      </div>
    </div>
  );
}
