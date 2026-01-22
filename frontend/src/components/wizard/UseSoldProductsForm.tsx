'use client';

/**
 * UseSoldProductsForm - Category 3.11 Use of Sold Products
 *
 * Supports 3 methods per GHG Protocol:
 * 1. Direct Use-Phase - Based on product lifetime energy consumption (kWh)
 * 2. Fuel-Based - For fuel-consuming products (liters over lifetime)
 * 3. Spend - Revenue-based using EEIO factors
 *
 * Applicable when company sells energy/fuel-consuming products.
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
  Zap,
  Info,
  Car,
  Monitor,
  Refrigerator,
  Fuel,
  DollarSign,
} from 'lucide-react';

// =============================================================================
// DATA DEFINITIONS
// =============================================================================

type UseMethod = 'direct' | 'fuel' | 'spend';

// Product types with their categories
const PRODUCT_TYPES = [
  // Vehicles
  { key: 'vehicle-car', label: 'Vehicle - Car/Passenger', category: 'vehicle', energyType: 'fuel' },
  { key: 'vehicle-truck', label: 'Vehicle - Truck/Commercial', category: 'vehicle', energyType: 'fuel' },
  { key: 'vehicle-motorcycle', label: 'Vehicle - Motorcycle', category: 'vehicle', energyType: 'fuel' },
  // Appliances
  { key: 'appliance-refrigerator', label: 'Appliance - Refrigerator', category: 'appliance', energyType: 'electricity' },
  { key: 'appliance-washer', label: 'Appliance - Washing Machine', category: 'appliance', energyType: 'electricity' },
  { key: 'appliance-ac', label: 'Appliance - Air Conditioner', category: 'appliance', energyType: 'electricity' },
  { key: 'appliance-heater', label: 'Appliance - Heater', category: 'appliance', energyType: 'electricity' },
  { key: 'appliance-other', label: 'Appliance - Other', category: 'appliance', energyType: 'electricity' },
  // Electronics
  { key: 'electronics-computer', label: 'Electronics - Computer/Laptop', category: 'electronics', energyType: 'electricity' },
  { key: 'electronics-server', label: 'Electronics - Server/Data Center', category: 'electronics', energyType: 'electricity' },
  { key: 'electronics-tv', label: 'Electronics - TV/Display', category: 'electronics', energyType: 'electricity' },
  { key: 'electronics-phone', label: 'Electronics - Phone/Mobile', category: 'electronics', energyType: 'electricity' },
  { key: 'electronics-other', label: 'Electronics - Other', category: 'electronics', energyType: 'electricity' },
  // Machinery
  { key: 'machinery-industrial', label: 'Machinery - Industrial', category: 'machinery', energyType: 'electricity' },
  { key: 'machinery-motor', label: 'Machinery - Motor/Pump', category: 'machinery', energyType: 'electricity' },
  // Lighting
  { key: 'lighting-led', label: 'Lighting - LED/CFL', category: 'lighting', energyType: 'electricity' },
  { key: 'lighting-other', label: 'Lighting - Other', category: 'lighting', energyType: 'electricity' },
  // Buildings
  { key: 'building-residential', label: 'Building - Residential', category: 'building', energyType: 'electricity' },
  { key: 'building-commercial', label: 'Building - Commercial', category: 'building', energyType: 'electricity' },
  // HVAC
  { key: 'hvac', label: 'HVAC System', category: 'hvac', energyType: 'electricity' },
  // Other
  { key: 'other', label: 'Other', category: 'other', energyType: 'electricity' },
];

const FUEL_TYPES = [
  { key: 'petrol', label: 'Petrol/Gasoline', activityKey: 'use_phase_petrol_liters', efEstimate: 2.31 },
  { key: 'diesel', label: 'Diesel', activityKey: 'use_phase_diesel_liters', efEstimate: 2.68 },
  { key: 'natural_gas', label: 'Natural Gas', activityKey: 'use_phase_natural_gas_kwh', efEstimate: 0.184, unit: 'kWh' },
  { key: 'lpg', label: 'LPG', activityKey: 'use_phase_lpg_liters', efEstimate: 1.51 },
];

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'ILS', symbol: '₪', name: 'Israeli Shekel' },
  { code: 'CHF', symbol: 'Fr', name: 'Swiss Franc' },
];

// Emission factors
const ELECTRICITY_EF = 0.436; // kg CO2e per kWh
const SPEND_EF = 0.25; // kg CO2e per USD

// =============================================================================
// COMPONENT
// =============================================================================

interface UseSoldProductsFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function UseSoldProductsForm({ periodId, onSuccess }: UseSoldProductsFormProps) {
  const reset = useWizardStore((s) => s.reset);
  const goBack = useWizardStore((s) => s.goBack);
  const createActivity = useCreateActivity(periodId);

  // Form state
  const [method, setMethod] = useState<UseMethod | ''>('');
  const [productType, setProductType] = useState('');
  const [unitsSold, setUnitsSold] = useState('');
  const [lifetimeEnergy, setLifetimeEnergy] = useState('');
  const [fuelType, setFuelType] = useState('');
  const [lifetimeFuel, setLifetimeFuel] = useState('');
  const [lifetimeYears, setLifetimeYears] = useState('');
  const [revenue, setRevenue] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [description, setDescription] = useState('');
  const [activityDate, setActivityDate] = useState(new Date().toISOString().split('T')[0]);

  // Get selected product type details
  const selectedProductType = useMemo(() =>
    PRODUCT_TYPES.find(p => p.key === productType),
    [productType]
  );

  // Get selected fuel type details
  const selectedFuelType = useMemo(() =>
    FUEL_TYPES.find(f => f.key === fuelType),
    [fuelType]
  );

  // Preview calculation
  const preview = useMemo(() => {
    if (!method) return null;

    if (method === 'direct') {
      const units = parseFloat(unitsSold) || 0;
      const energy = parseFloat(lifetimeEnergy) || 0;
      if (!units || !energy) return null;
      const totalEnergy = units * energy;
      const co2e = totalEnergy * ELECTRICITY_EF;
      return {
        activityKey: 'use_phase_electricity_kwh',
        quantity: totalEnergy,
        unit: 'kWh',
        co2e,
        formula: `${units.toLocaleString()} units × ${energy.toLocaleString()} kWh/unit × ${ELECTRICITY_EF} kg/kWh = ${co2e.toFixed(2)} kg CO2e`,
        efSource: 'IEA World Average 2024',
      };
    }

    if (method === 'fuel') {
      const units = parseFloat(unitsSold) || 0;
      const fuel = parseFloat(lifetimeFuel) || 0;
      if (!units || !fuel || !fuelType) return null;
      const fuelTypeData = selectedFuelType;
      if (!fuelTypeData) return null;
      const totalFuel = units * fuel;
      const co2e = totalFuel * fuelTypeData.efEstimate;
      const fuelUnit = fuelTypeData.unit || 'liters';
      return {
        activityKey: fuelTypeData.activityKey,
        quantity: totalFuel,
        unit: fuelUnit,
        co2e,
        formula: `${units.toLocaleString()} units × ${fuel.toLocaleString()} ${fuelUnit}/unit × ${fuelTypeData.efEstimate} kg/${fuelUnit} = ${co2e.toFixed(2)} kg CO2e`,
        efSource: 'DEFRA 2024',
      };
    }

    if (method === 'spend') {
      const amount = parseFloat(revenue) || 0;
      if (!amount) return null;
      const co2e = amount * SPEND_EF;
      return {
        activityKey: 'use_phase_spend_products',
        quantity: amount,
        unit: currency,
        co2e,
        formula: `${currency} ${amount.toLocaleString()} × ${SPEND_EF} kg CO2e/${currency} = ${co2e.toFixed(2)} kg CO2e`,
        efSource: 'USEEIO 2.0',
      };
    }

    return null;
  }, [method, unitsSold, lifetimeEnergy, fuelType, lifetimeFuel, revenue, currency, selectedFuelType]);

  // Build description
  const fullDescription = useMemo(() => {
    const parts = [];
    if (selectedProductType) {
      parts.push(`${selectedProductType.label} use phase`);
    }
    if (description) {
      parts.push(description);
    }
    if (lifetimeYears) {
      parts.push(`(${lifetimeYears} year lifetime)`);
    }
    return parts.filter(Boolean).join(' - ') || 'Use of Sold Products';
  }, [selectedProductType, description, lifetimeYears]);

  // Handle save
  const handleSave = async (addAnother: boolean = false) => {
    if (!preview) return;

    try {
      await createActivity.mutateAsync({
        scope: 3,
        category_code: '3.11',
        activity_key: preview.activityKey,
        description: fullDescription,
        quantity: preview.quantity,
        unit: preview.unit,
        activity_date: activityDate,
      });

      if (addAnother) {
        setProductType('');
        setUnitsSold('');
        setLifetimeEnergy('');
        setFuelType('');
        setLifetimeFuel('');
        setLifetimeYears('');
        setRevenue('');
        setDescription('');
      } else {
        reset();
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
          <Zap className="w-5 h-5 text-blue-600" />
          3.11 Use of Sold Products
        </h2>
        <p className="text-sm text-foreground-muted">
          Emissions from the use phase of products sold by your company during their lifetime
        </p>
      </div>

      {/* Applicability Note */}
      <div className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
        <Info className="w-4 h-4 text-blue-700 mt-0.5 flex-shrink-0" />
        <p className="text-sm text-blue-800">
          <strong>When to use:</strong> If your company sells energy/fuel-consuming products (vehicles,
          appliances, electronics, machinery, buildings). This is often the largest Scope 3 category
          for manufacturers.
        </p>
      </div>

      {/* Method Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-medium">Step 1: Select Calculation Method</label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: 'direct' as UseMethod, label: 'Direct', desc: 'Lifetime Energy', Icon: Zap, color: 'border-blue-500 bg-blue-50' },
            { value: 'fuel' as UseMethod, label: 'Fuel-Based', desc: 'Lifetime Fuel', Icon: Fuel, color: 'border-orange-500 bg-orange-50' },
            { value: 'spend' as UseMethod, label: 'Spend', desc: 'Revenue-Based', Icon: DollarSign, color: 'border-green-500 bg-green-50' },
          ].map((m) => (
            <button
              key={m.value}
              onClick={() => {
                setMethod(m.value);
                setProductType('');
                setFuelType('');
              }}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                method === m.value
                  ? m.color
                  : 'border-border hover:border-foreground-muted'
              }`}
            >
              <m.Icon className="w-6 h-6 mb-1 text-foreground-muted" />
              <div className="font-medium text-sm">{m.label}</div>
              <div className="text-xs text-foreground-muted">{m.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Direct Method Fields */}
      {method === 'direct' && (
        <div className="space-y-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Product Type</label>
            <select
              value={productType}
              onChange={(e) => setProductType(e.target.value)}
              className={selectClass}
            >
              <option value="">Select product type...</option>
              <optgroup label="Appliances">
                {PRODUCT_TYPES.filter(p => p.category === 'appliance').map((pt) => (
                  <option key={pt.key} value={pt.key}>{pt.label}</option>
                ))}
              </optgroup>
              <optgroup label="Electronics">
                {PRODUCT_TYPES.filter(p => p.category === 'electronics').map((pt) => (
                  <option key={pt.key} value={pt.key}>{pt.label}</option>
                ))}
              </optgroup>
              <optgroup label="Machinery">
                {PRODUCT_TYPES.filter(p => p.category === 'machinery').map((pt) => (
                  <option key={pt.key} value={pt.key}>{pt.label}</option>
                ))}
              </optgroup>
              <optgroup label="Lighting">
                {PRODUCT_TYPES.filter(p => p.category === 'lighting').map((pt) => (
                  <option key={pt.key} value={pt.key}>{pt.label}</option>
                ))}
              </optgroup>
              <optgroup label="Buildings">
                {PRODUCT_TYPES.filter(p => p.category === 'building').map((pt) => (
                  <option key={pt.key} value={pt.key}>{pt.label}</option>
                ))}
              </optgroup>
              <optgroup label="HVAC">
                {PRODUCT_TYPES.filter(p => p.category === 'hvac').map((pt) => (
                  <option key={pt.key} value={pt.key}>{pt.label}</option>
                ))}
              </optgroup>
              <optgroup label="Other">
                {PRODUCT_TYPES.filter(p => p.category === 'other').map((pt) => (
                  <option key={pt.key} value={pt.key}>{pt.label}</option>
                ))}
              </optgroup>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Units Sold"
              type="number"
              step="1"
              min="0"
              value={unitsSold}
              onChange={(e) => setUnitsSold(e.target.value)}
              placeholder="e.g., 10000"
            />
            <Input
              label="Lifetime Energy (kWh/unit)"
              type="number"
              step="1"
              min="0"
              value={lifetimeEnergy}
              onChange={(e) => setLifetimeEnergy(e.target.value)}
              placeholder="e.g., 5000"
              hint="Total electricity consumed over product lifetime"
            />
          </div>

          <Input
            label="Expected Lifetime (years) - optional"
            type="number"
            step="1"
            min="1"
            value={lifetimeYears}
            onChange={(e) => setLifetimeYears(e.target.value)}
            placeholder="e.g., 10"
          />
        </div>
      )}

      {/* Fuel-Based Method Fields */}
      {method === 'fuel' && (
        <div className="space-y-4 p-4 bg-orange-50 rounded-lg border border-orange-200">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Product Type</label>
            <select
              value={productType}
              onChange={(e) => setProductType(e.target.value)}
              className={selectClass}
            >
              <option value="">Select product type...</option>
              <optgroup label="Vehicles">
                {PRODUCT_TYPES.filter(p => p.category === 'vehicle').map((pt) => (
                  <option key={pt.key} value={pt.key}>{pt.label}</option>
                ))}
              </optgroup>
              <optgroup label="Other Fuel-Consuming">
                {PRODUCT_TYPES.filter(p => p.category === 'machinery' || p.category === 'hvac').map((pt) => (
                  <option key={pt.key} value={pt.key}>{pt.label}</option>
                ))}
              </optgroup>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Fuel Type</label>
            <select
              value={fuelType}
              onChange={(e) => setFuelType(e.target.value)}
              className={selectClass}
            >
              <option value="">Select fuel type...</option>
              {FUEL_TYPES.map((ft) => (
                <option key={ft.key} value={ft.key}>
                  {ft.label} (~{ft.efEstimate} kg CO2e/{ft.unit || 'liter'})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Units Sold"
              type="number"
              step="1"
              min="0"
              value={unitsSold}
              onChange={(e) => setUnitsSold(e.target.value)}
              placeholder="e.g., 5000"
            />
            <Input
              label={`Lifetime Fuel (${selectedFuelType?.unit || 'liters'}/unit)`}
              type="number"
              step="1"
              min="0"
              value={lifetimeFuel}
              onChange={(e) => setLifetimeFuel(e.target.value)}
              placeholder="e.g., 15000"
              hint="Total fuel consumed over product lifetime"
            />
          </div>

          <Input
            label="Expected Lifetime (years) - optional"
            type="number"
            step="1"
            min="1"
            value={lifetimeYears}
            onChange={(e) => setLifetimeYears(e.target.value)}
            placeholder="e.g., 12"
          />
        </div>
      )}

      {/* Spend Method Fields */}
      {method === 'spend' && (
        <div className="space-y-4 p-4 bg-green-50 rounded-lg border border-green-200">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Revenue from Products"
              type="number"
              step="0.01"
              min="0"
              value={revenue}
              onChange={(e) => setRevenue(e.target.value)}
              placeholder="e.g., 5000000"
            />
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className={selectClass}
              >
                {CURRENCIES.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.symbol} {c.code} - {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <p className="text-xs text-foreground-muted">
            Uses EEIO factors. Less accurate than product-specific methods. Best used when product-level data is unavailable.
          </p>
        </div>
      )}

      {/* Optional Fields */}
      {method && (
        <div className="space-y-4">
          <Input
            label="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., 2024 Model refrigerators sold globally"
          />

          <Input
            label="Activity Date"
            type="date"
            value={activityDate}
            onChange={(e) => setActivityDate(e.target.value)}
          />
        </div>
      )}

      {/* Preview */}
      {preview && (
        <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg space-y-3">
          <div className="flex items-center gap-2 text-primary">
            <Calculator className="w-5 h-5" />
            <span className="font-medium">Calculation Preview</span>
          </div>
          <div className="text-sm space-y-1">
            <p><strong>Activity Key:</strong> {preview.activityKey}</p>
            <p><strong>Formula:</strong> {preview.formula}</p>
            <p><strong>Source:</strong> {preview.efSource}</p>
          </div>
          <div className="text-2xl font-bold text-primary">
            {formatCO2e(preview.co2e)}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <Button
          variant="outline"
          onClick={() => handleSave(true)}
          disabled={!preview || createActivity.isPending}
        >
          <Plus className="w-4 h-4 mr-2" />
          Save & Add Another
        </Button>
        <Button
          onClick={() => handleSave(false)}
          disabled={!preview || createActivity.isPending}
        >
          {createActivity.isPending ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          {createActivity.isPending ? 'Saving...' : 'Save Entry'}
        </Button>
      </div>
    </div>
  );
}
