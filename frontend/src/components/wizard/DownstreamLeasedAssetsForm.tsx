'use client';

/**
 * DownstreamLeasedAssetsForm - Category 3.13 Downstream Leased Assets
 *
 * Emissions from assets OWNED by reporting company and LEASED TO others (lessor).
 *
 * Supports 3 methods per GHG Protocol:
 * 1. Average - Based on floor area (m2) or unit count by asset type
 * 2. Asset-Specific - Based on actual energy consumption (kWh)
 * 3. Spend - Based on rental income (revenue-based)
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
  Home,
  Car,
  Zap,
  Info,
} from 'lucide-react';

// =============================================================================
// DOWNSTREAM LEASED ASSETS DATA DEFINITIONS
// =============================================================================

type LeasedMethod = 'average' | 'asset-specific' | 'spend';

// Asset Types with emission factor estimates
const BUILDING_TYPES = [
  { key: 'office', label: 'Office Building', icon: Building, ef: 150, unit: 'm2' },
  { key: 'warehouse', label: 'Warehouse/Storage', icon: Warehouse, ef: 80, unit: 'm2' },
  { key: 'retail', label: 'Retail Space', icon: Store, ef: 200, unit: 'm2' },
  { key: 'industrial', label: 'Industrial Facility', icon: Factory, ef: 120, unit: 'm2' },
  { key: 'datacenter', label: 'Data Center', icon: Server, ef: 1500, unit: 'm2' },
  { key: 'residential', label: 'Residential', icon: Home, ef: 100, unit: 'm2' },
];

const VEHICLE_EQUIPMENT_TYPES = [
  { key: 'vehicle', label: 'Vehicle (Car/Van)', icon: Car, ef: 2500, unit: 'unit' },
  { key: 'truck', label: 'Truck/HGV', icon: Car, ef: 5000, unit: 'unit' },
  { key: 'equipment', label: 'Equipment/Machinery', icon: Factory, ef: 500, unit: 'unit' },
];

const ENERGY_TYPES = [
  { key: 'electricity', label: 'Electricity', ef: 0.436 },
  { key: 'gas', label: 'Natural Gas', ef: 0.184 },
];

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '\u20AC', name: 'Euro' },
  { code: 'GBP', symbol: '\u00A3', name: 'British Pound' },
  { code: 'ILS', symbol: '\u20AA', name: 'Israeli Shekel' },
];

// Spend emission factor (kg CO2e per USD of rental income)
const SPEND_EF = 0.15;

interface DownstreamLeasedAssetsFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function DownstreamLeasedAssetsForm({ periodId, onSuccess }: DownstreamLeasedAssetsFormProps) {
  const goBack = useWizardStore((s) => s.goBack);
  const resetWizard = useWizardStore((s) => s.reset);
  const createActivity = useCreateActivity(periodId);

  // Method selection
  const [method, setMethod] = useState<LeasedMethod | ''>('');

  // Average method fields
  const [assetCategory, setAssetCategory] = useState<'building' | 'vehicle'>('building');
  const [assetType, setAssetType] = useState('office');
  const [floorArea, setFloorArea] = useState('');
  const [numUnits, setNumUnits] = useState('');

  // Asset-specific method fields
  const [energyType, setEnergyType] = useState('electricity');
  const [energyConsumption, setEnergyConsumption] = useState('');

  // Spend method fields
  const [rentalIncome, setRentalIncome] = useState('');
  const [currency, setCurrency] = useState('USD');

  // Common fields
  const [description, setDescription] = useState('');
  const [tenant, setTenant] = useState('');
  const [location, setLocation] = useState('');
  const [activityDate, setActivityDate] = useState(new Date().toISOString().split('T')[0]);

  // Get current asset type data
  const currentAssetType = useMemo(() => {
    if (assetCategory === 'building') {
      return BUILDING_TYPES.find(b => b.key === assetType);
    }
    return VEHICLE_EQUIPMENT_TYPES.find(v => v.key === assetType);
  }, [assetCategory, assetType]);

  // Preview calculation
  const preview = useMemo(() => {
    if (!method) return null;

    if (method === 'average') {
      if (assetCategory === 'building') {
        const area = parseFloat(floorArea) || 0;
        if (!area) return null;
        const building = BUILDING_TYPES.find(b => b.key === assetType);
        const ef = building?.ef || 100;
        const co2e = area * ef;
        return {
          activityKey: `downstream_leased_${assetType}_m2`,
          quantity: area,
          unit: 'm2',
          co2e,
          formula: `${area.toLocaleString()} m2 x ${ef} kg CO2e/m2 = ${co2e.toFixed(2)} kg CO2e`,
          efSource: 'DEFRA 2024',
        };
      } else {
        const units = parseFloat(numUnits) || 0;
        if (!units) return null;
        const vehicleType = VEHICLE_EQUIPMENT_TYPES.find(v => v.key === assetType);
        const ef = vehicleType?.ef || 500;
        const co2e = units * ef;
        return {
          activityKey: `downstream_leased_${assetType}_unit`,
          quantity: units,
          unit: 'unit',
          co2e,
          formula: `${units} units x ${ef.toLocaleString()} kg CO2e/unit = ${co2e.toLocaleString()} kg CO2e`,
          efSource: 'DEFRA 2024',
        };
      }
    }

    if (method === 'asset-specific') {
      const energy = parseFloat(energyConsumption) || 0;
      if (!energy) return null;
      const energyData = ENERGY_TYPES.find(e => e.key === energyType);
      const ef = energyData?.ef || 0.436;
      const co2e = energy * ef;
      const activityKey = energyType === 'gas'
        ? 'downstream_leased_gas_kwh'
        : 'downstream_leased_electricity_kwh';
      return {
        activityKey,
        quantity: energy,
        unit: 'kWh',
        co2e,
        formula: `${energy.toLocaleString()} kWh x ${ef.toFixed(3)} kg CO2e/kWh = ${co2e.toFixed(2)} kg CO2e`,
        efSource: energyType === 'gas' ? 'DEFRA 2024' : 'IEA 2024',
      };
    }

    if (method === 'spend') {
      const income = parseFloat(rentalIncome) || 0;
      if (!income) return null;
      const co2e = income * SPEND_EF;
      return {
        activityKey: 'downstream_leased_spend_income',
        quantity: income,
        unit: currency,
        co2e,
        formula: `${currency} ${income.toLocaleString()} x ${SPEND_EF} kg CO2e/${currency} = ${co2e.toFixed(2)} kg CO2e`,
        efSource: 'EEIO 2024',
      };
    }

    return null;
  }, [method, assetCategory, assetType, floorArea, numUnits, energyType, energyConsumption, rentalIncome, currency]);

  // Handle save
  const handleSave = async (addAnother: boolean = false) => {
    if (!preview) return;

    const assetLabel = currentAssetType?.label || assetType;

    try {
      await createActivity.mutateAsync({
        scope: 3,
        category_code: '3.13',
        activity_key: preview.activityKey,
        description: description || `Leased: ${assetLabel}${tenant ? ` to ${tenant}` : ''}`,
        quantity: preview.quantity,
        unit: preview.unit,
        activity_date: activityDate,
      });

      if (addAnother) {
        // Reset form but keep method
        setFloorArea('');
        setNumUnits('');
        setEnergyConsumption('');
        setRentalIncome('');
        setDescription('');
        setTenant('');
        setLocation('');
      } else {
        resetWizard();
        onSuccess?.();
      }
    } catch (error) {
      console.error('Failed to save activity:', error);
    }
  };

  const selectClass = "w-full h-10 px-3 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary";

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={goBack}
        className="flex items-center gap-2 text-sm text-foreground-muted hover:text-foreground transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Category
      </button>

      {/* Header */}
      <div className="space-y-2">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Building className="w-5 h-5 text-purple-600" />
          3.13 Downstream Leased Assets
        </h2>
        <p className="text-sm text-foreground-muted">
          Emissions from assets you OWN that are leased TO other entities (you are the lessor/landlord)
        </p>
      </div>

      {/* Info box */}
      <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
        <div className="flex gap-3">
          <Info className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-purple-800">
            <p className="font-medium mb-1">What to report:</p>
            <ul className="list-disc list-inside space-y-1 text-purple-700">
              <li>Buildings, vehicles, or equipment you own and lease to tenants</li>
              <li>Include emissions from energy use during the lease period</li>
              <li>Different from 3.8 where you are the tenant/lessee</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Method Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-medium">Step 1: Select Calculation Method</label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: 'average' as LeasedMethod, label: 'Average', desc: 'Area/Units', icon: <Building className="w-6 h-6" />, color: 'border-green-500 bg-green-50' },
            { value: 'asset-specific' as LeasedMethod, label: 'Asset-Specific', desc: 'Energy data', icon: <Zap className="w-6 h-6" />, color: 'border-amber-500 bg-amber-50' },
            { value: 'spend' as LeasedMethod, label: 'Spend', desc: 'Rental income', icon: <span className="text-2xl">$</span>, color: 'border-blue-500 bg-blue-50' },
          ].map((m) => (
            <button
              key={m.value}
              onClick={() => {
                setMethod(m.value);
                setAssetType('office');
                setAssetCategory('building');
              }}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                method === m.value
                  ? m.color
                  : 'border-border hover:border-foreground-muted'
              }`}
            >
              <div className="mb-2">{m.icon}</div>
              <div className="font-medium text-sm">{m.label}</div>
              <div className="text-xs text-foreground-muted">{m.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Average Method Fields */}
      {method === 'average' && (
        <div className="space-y-4 p-4 bg-green-50 rounded-lg border border-green-200">
          {/* Asset Category Toggle */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Asset Category</label>
            <div className="flex gap-2">
              <button
                onClick={() => { setAssetCategory('building'); setAssetType('office'); }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  assetCategory === 'building'
                    ? 'bg-green-600 text-white'
                    : 'bg-white border border-green-300 text-green-700 hover:bg-green-50'
                }`}
              >
                Building
              </button>
              <button
                onClick={() => { setAssetCategory('vehicle'); setAssetType('vehicle'); }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  assetCategory === 'vehicle'
                    ? 'bg-green-600 text-white'
                    : 'bg-white border border-green-300 text-green-700 hover:bg-green-50'
                }`}
              >
                Vehicle/Equipment
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Asset Type</label>
              <select
                value={assetType}
                onChange={(e) => setAssetType(e.target.value)}
                className={selectClass}
              >
                {assetCategory === 'building' ? (
                  BUILDING_TYPES.map((bt) => (
                    <option key={bt.key} value={bt.key}>{bt.label}</option>
                  ))
                ) : (
                  VEHICLE_EQUIPMENT_TYPES.map((vt) => (
                    <option key={vt.key} value={vt.key}>{vt.label}</option>
                  ))
                )}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                {assetCategory === 'building' ? 'Floor Area (m2)' : 'Number of Units'}
              </label>
              {assetCategory === 'building' ? (
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={floorArea}
                  onChange={(e) => setFloorArea(e.target.value)}
                  placeholder="Enter floor area..."
                />
              ) : (
                <Input
                  type="number"
                  min="0"
                  step="1"
                  value={numUnits}
                  onChange={(e) => setNumUnits(e.target.value)}
                  placeholder="Enter number of units..."
                />
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Tenant (optional)
              </label>
              <Input
                type="text"
                value={tenant}
                onChange={(e) => setTenant(e.target.value)}
                placeholder="e.g., ABC Corporation"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Location (optional)
              </label>
              <Input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g., New York"
              />
            </div>
          </div>
        </div>
      )}

      {/* Asset-Specific Method Fields */}
      {method === 'asset-specific' && (
        <div className="space-y-4 p-4 bg-amber-50 rounded-lg border border-amber-200">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Energy Type</label>
              <select
                value={energyType}
                onChange={(e) => setEnergyType(e.target.value)}
                className={selectClass}
              >
                {ENERGY_TYPES.map((et) => (
                  <option key={et.key} value={et.key}>{et.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Energy Consumption (kWh)
              </label>
              <Input
                type="number"
                min="0"
                step="0.01"
                value={energyConsumption}
                onChange={(e) => setEnergyConsumption(e.target.value)}
                placeholder="Enter energy consumption..."
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Asset Description
              </label>
              <Input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g., Office building leased to tenant"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Tenant (optional)
              </label>
              <Input
                type="text"
                value={tenant}
                onChange={(e) => setTenant(e.target.value)}
                placeholder="e.g., Tech Company Inc"
              />
            </div>
          </div>
        </div>
      )}

      {/* Spend Method Fields */}
      {method === 'spend' && (
        <div className="space-y-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Annual Rental Income
              </label>
              <Input
                type="number"
                min="0"
                step="0.01"
                value={rentalIncome}
                onChange={(e) => setRentalIncome(e.target.value)}
                placeholder="Enter rental income..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className={selectClass}
              >
                {CURRENCIES.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.code} ({c.symbol})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">
              Description (optional)
            </label>
            <Input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Total rental income from all leased properties"
            />
          </div>
        </div>
      )}

      {/* Date */}
      {method && (
        <div className="max-w-xs">
          <label className="block text-sm font-medium text-foreground mb-1.5">Activity Date</label>
          <Input
            type="date"
            value={activityDate}
            onChange={(e) => setActivityDate(e.target.value)}
          />
        </div>
      )}

      {/* Preview */}
      {preview && (
        <div className="p-4 bg-background-muted rounded-lg border border-border">
          <div className="flex items-center gap-2 text-sm font-medium mb-3">
            <Calculator className="w-4 h-4" />
            Emission Preview
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-foreground-muted">Formula:</span>
              <span className="font-mono text-xs">{preview.formula}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-foreground-muted">Source:</span>
              <span>{preview.efSource}</span>
            </div>
            <div className="flex justify-between text-lg font-semibold pt-2 border-t border-border">
              <span>Estimated CO2e:</span>
              <span className="text-primary">{formatCO2e(preview.co2e)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      {method && (
        <div className="flex gap-3 pt-4">
          <Button
            onClick={() => handleSave(false)}
            disabled={!preview || createActivity.isPending}
            className="flex-1"
          >
            {createActivity.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            Save Entry
          </Button>
          <Button
            variant="outline"
            onClick={() => handleSave(true)}
            disabled={!preview || createActivity.isPending}
          >
            <Plus className="w-4 h-4 mr-2" />
            Save & Add Another
          </Button>
        </div>
      )}
    </div>
  );
}
