'use client';

/**
 * CapitalGoodsForm - Category 3.2 Capital Goods
 *
 * Supports 3 methods per GHG Protocol:
 * 1. Physical - Asset-based (unit count, m2, kW)
 * 2. Spend - Invoice amount (USD)
 * 3. Supplier-Specific - User provides their own emission factor
 */

import { useState } from 'react';
import { useWizardStore } from '@/stores/wizard';
import { useCreateActivity } from '@/hooks/useEmissions';
import { Button, Input } from '@/components/ui';
import { formatCO2e } from '@/lib/utils';
import {
  Calculator,
  Save,
  Plus,
  Loader2,
  DollarSign,
  Building2,
  FileText,
  Info,
  Eye,
  Database,
  ArrowLeft,
  Car,
  Laptop,
  Factory,
  Scale,
  ClipboardList,
  Package,
} from 'lucide-react';

type Method = 'physical' | 'spend' | 'supplier-specific';

// Asset categories
const ASSET_CATEGORIES = [
  { value: 'vehicles', label: 'Vehicles', icon: Car },
  { value: 'it_equipment', label: 'IT Equipment', icon: Laptop },
  { value: 'buildings', label: 'Buildings', icon: Building2 },
  { value: 'machinery', label: 'Machinery', icon: Factory },
  { value: 'furniture', label: 'Furniture', icon: Building2 },
  { value: 'hvac', label: 'HVAC', icon: Factory },
  { value: 'solar', label: 'Solar/Renewable', icon: Factory },
];

// Asset types grouped by category (matches backend resolver)
const ASSET_TYPES: Record<string, { value: string; label: string; unit: string }[]> = {
  vehicles: [
    { value: 'capital_car_small_unit', label: 'Small Car', unit: 'unit' },
    { value: 'capital_car_medium_unit', label: 'Medium Car', unit: 'unit' },
    { value: 'capital_car_large_unit', label: 'Large Car / SUV', unit: 'unit' },
    { value: 'capital_van_unit', label: 'Van', unit: 'unit' },
    { value: 'capital_truck_unit', label: 'Truck / HGV', unit: 'unit' },
  ],
  it_equipment: [
    { value: 'capital_laptop_unit', label: 'Laptop', unit: 'unit' },
    { value: 'capital_desktop_unit', label: 'Desktop Computer', unit: 'unit' },
    { value: 'capital_monitor_unit', label: 'Monitor', unit: 'unit' },
    { value: 'capital_server_unit', label: 'Server', unit: 'unit' },
    { value: 'capital_smartphone_unit', label: 'Smartphone', unit: 'unit' },
    { value: 'capital_tablet_unit', label: 'Tablet', unit: 'unit' },
    { value: 'capital_printer_unit', label: 'Printer', unit: 'unit' },
  ],
  buildings: [
    { value: 'capital_building_office_m2', label: 'Office Building', unit: 'm2' },
    { value: 'capital_building_warehouse_m2', label: 'Warehouse', unit: 'm2' },
    { value: 'capital_building_retail_m2', label: 'Retail Space', unit: 'm2' },
    { value: 'capital_building_industrial_m2', label: 'Industrial Building', unit: 'm2' },
  ],
  machinery: [
    { value: 'capital_machinery_unit', label: 'Industrial Machinery', unit: 'unit' },
  ],
  furniture: [
    { value: 'capital_furniture_unit', label: 'Office Furniture', unit: 'unit' },
  ],
  hvac: [
    { value: 'capital_hvac_unit', label: 'HVAC System', unit: 'unit' },
  ],
  solar: [
    { value: 'capital_solar_unit', label: 'Solar PV System', unit: 'kW' },
  ],
};

// Spend categories for Spend method
const SPEND_CATEGORIES = [
  { value: 'spend_capital_vehicles', label: 'Vehicles' },
  { value: 'spend_capital_it', label: 'IT Equipment' },
  { value: 'spend_capital_buildings', label: 'Buildings' },
  { value: 'spend_capital_machinery', label: 'Machinery' },
  { value: 'spend_capital_furniture', label: 'Furniture' },
  { value: 'spend_capital_hvac', label: 'HVAC' },
  { value: 'spend_capital_renewable', label: 'Solar/Renewable' },
  { value: 'spend_capital_equipment', label: 'Other Equipment' },
];

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'ILS', symbol: '₪', name: 'Israeli Shekel' },
];

const PHYSICAL_UNITS = [
  { value: 'unit', label: 'Units (count)' },
  { value: 'm2', label: 'Square Meters (m2)' },
  { value: 'kW', label: 'Kilowatts (kW)' },
];

interface CapitalGoodsFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function CapitalGoodsForm({ periodId, onSuccess }: CapitalGoodsFormProps) {
  const reset = useWizardStore((s) => s.reset);
  const goBack = useWizardStore((s) => s.goBack);
  const entries = useWizardStore((s) => s.entries);
  const addEntry = useWizardStore((s) => s.addEntry);
  const getTotalCO2e = useWizardStore((s) => s.getTotalCO2e);

  // Form state
  const [method, setMethod] = useState<Method>('physical');
  const [description, setDescription] = useState('');
  const [quantity, setQuantity] = useState<number>(0);
  const [unit, setUnit] = useState('unit');
  const [assetCategory, setAssetCategory] = useState('');
  const [assetType, setAssetType] = useState('');
  const [spendCategory, setSpendCategory] = useState('');
  const [spendAmount, setSpendAmount] = useState<number>(0);
  const [currency, setCurrency] = useState('USD');
  const [supplierEF, setSupplierEF] = useState<number>(0);

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [preview, setPreview] = useState<{ co2e_kg: number; formula: string } | null>(null);

  const createActivity = useCreateActivity(periodId);

  // Get available asset types for selected category
  const availableAssetTypes = assetCategory ? ASSET_TYPES[assetCategory] || [] : [];

  // Update unit when asset type changes
  const handleAssetTypeChange = (value: string) => {
    setAssetType(value);
    const selected = availableAssetTypes.find((t) => t.value === value);
    if (selected) {
      setUnit(selected.unit);
    }
  };

  // Get activity_key based on method
  const getActivityKey = (): string => {
    switch (method) {
      case 'physical':
        return assetType || 'capital_laptop_unit';
      case 'spend':
        return spendCategory || 'spend_capital_equipment';
      case 'supplier-specific':
        return 'supplier_specific_3_2';
      default:
        return 'spend_capital_equipment';
    }
  };

  // Get unit based on method
  const getUnit = (): string => {
    switch (method) {
      case 'physical':
      case 'supplier-specific':
        return unit;
      case 'spend':
        return currency;
      default:
        return 'unit';
    }
  };

  // Get quantity based on method
  const getQuantity = (): number => {
    switch (method) {
      case 'physical':
      case 'supplier-specific':
        return quantity;
      case 'spend':
        return spendAmount;
      default:
        return 0;
    }
  };

  // Validation
  const canSave = (): boolean => {
    if (!description) return false;

    switch (method) {
      case 'physical':
        return !!assetType && quantity > 0;
      case 'spend':
        return !!spendCategory && spendAmount > 0;
      case 'supplier-specific':
        return quantity > 0 && supplierEF > 0;
      default:
        return false;
    }
  };

  // Preview calculation
  const handlePreview = () => {
    if (!canSave()) return;

    let co2e = 0;
    let formula = '';

    switch (method) {
      case 'physical':
        // Use typical capital EF (will be calculated properly by backend)
        const assetEF = unit === 'm2' ? 300 : 500; // Placeholder
        co2e = quantity * assetEF;
        formula = `${quantity} ${unit} × ~${assetEF} kg CO2e/${unit} = ${co2e.toFixed(2)} kg CO2e (estimate)`;
        break;
      case 'spend':
        // Use typical EEIO EF for capital goods
        const spendEF = 0.8; // Placeholder
        co2e = spendAmount * spendEF;
        formula = `${spendAmount} ${currency} × ~${spendEF} kg CO2e/${currency} = ${co2e.toFixed(2)} kg CO2e (estimate)`;
        break;
      case 'supplier-specific':
        co2e = quantity * supplierEF;
        formula = `${quantity} ${unit} × ${supplierEF} kg CO2e/${unit} = ${co2e.toFixed(2)} kg CO2e`;
        break;
    }

    setPreview({ co2e_kg: co2e, formula });
  };

  // Save activity
  const handleSave = async () => {
    if (!canSave()) {
      setSaveError('Please fill in all required fields');
      return;
    }

    setIsSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      const payload: any = {
        scope: 3 as const,
        category_code: '3.2',
        activity_key: getActivityKey(),
        description,
        quantity: getQuantity(),
        unit: getUnit(),
        activity_date: new Date().toISOString().split('T')[0],
      };

      // For supplier-specific, add the EF to the payload
      if (method === 'supplier-specific') {
        payload.supplier_ef = supplierEF;
      }

      console.log('[3.2 Form] Saving activity:', payload);

      await createActivity.mutateAsync(payload);

      setSaveSuccess(true);

      // Reset and close after brief success message
      setTimeout(() => {
        reset();
        onSuccess?.();
      }, 1500);
    } catch (error) {
      console.error('[3.2 Form] Save error:', error);
      setSaveError(error instanceof Error ? error.message : 'Failed to save activity');
    } finally {
      setIsSaving(false);
    }
  };

  // Save and add another
  const handleSaveAndAddAnother = async () => {
    if (!canSave()) {
      setSaveError('Please fill in all required fields');
      return;
    }

    setIsSaving(true);
    setSaveError(null);

    try {
      const payload: any = {
        scope: 3 as const,
        category_code: '3.2',
        activity_key: getActivityKey(),
        description,
        quantity: getQuantity(),
        unit: getUnit(),
        activity_date: new Date().toISOString().split('T')[0],
      };

      if (method === 'supplier-specific') {
        payload.supplier_ef = supplierEF;
      }

      await createActivity.mutateAsync(payload);

      // Reset form but keep wizard open
      setDescription('');
      setQuantity(0);
      setSpendAmount(0);
      setSupplierEF(0);
      setPreview(null);
      addEntry();
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to save activity');
    } finally {
      setIsSaving(false);
    }
  };

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
          <Package className="w-5 h-5 text-indigo-600" />
          3.2 Capital Goods
        </h2>
        <p className="text-sm text-foreground-muted">
          Equipment, vehicles, buildings, and other capital purchases
        </p>
      </div>

      {/* Method Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-medium">Step 1: Select Calculation Method</label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: 'physical' as Method, label: 'Physical', desc: 'Asset count/m2', Icon: Scale, color: 'border-green-500 bg-green-50' },
            { value: 'spend' as Method, label: 'Spend', desc: 'Invoice amount', Icon: DollarSign, color: 'border-blue-500 bg-blue-50' },
            { value: 'supplier-specific' as Method, label: 'Supplier', desc: 'Custom EF', Icon: ClipboardList, color: 'border-amber-500 bg-amber-50' },
          ].map((m) => (
            <button
              key={m.value}
              onClick={() => setMethod(m.value)}
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

      {/* Method-specific info */}
      <div className="p-3 bg-info/10 border border-info/20 rounded-lg">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-info mt-0.5" />
          <div className="text-sm text-info">
            {method === 'physical' && (
              <>
                <strong>Physical Method:</strong> Enter the number of assets purchased or building area (m2).
                Best for vehicles, IT equipment, and buildings where you know the quantity.
              </>
            )}
            {method === 'spend' && (
              <>
                <strong>Spend Method:</strong> Enter the invoice amount. Uses EEIO factors for capital goods.
                Best when you only have purchase invoices.
              </>
            )}
            {method === 'supplier-specific' && (
              <>
                <strong>Supplier-Specific Method:</strong> Enter your own emission factor from EPD or
                supplier data. This is the most accurate method per GHG Protocol.
              </>
            )}
          </div>
        </div>
      </div>

      {/* Description (always shown) */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-1.5">Description</label>
        <Input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="e.g., Company fleet vehicles, Office laptops"
        />
      </div>

      {/* Physical Method Fields */}
      {method === 'physical' && (
        <>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Asset Category</label>
            <select
              value={assetCategory}
              onChange={(e) => {
                setAssetCategory(e.target.value);
                setAssetType(''); // Reset asset type when category changes
              }}
              className="w-full h-10 px-3 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Select category...</option>
              {ASSET_CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
          {assetCategory && (
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Asset Type</label>
              <select
                value={assetType}
                onChange={(e) => handleAssetTypeChange(e.target.value)}
                className="w-full h-10 px-3 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">Select type...</option>
                {availableAssetTypes.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label} ({t.unit})
                  </option>
                ))}
              </select>
            </div>
          )}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Quantity</label>
              <Input
                type="number"
                value={quantity || ''}
                onChange={(e) => setQuantity(parseFloat(e.target.value) || 0)}
                placeholder="0"
                min={0}
                step={0.01}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Unit</label>
              <Input type="text" value={unit} disabled className="bg-background-muted" />
            </div>
          </div>
        </>
      )}

      {/* Spend Method Fields */}
      {method === 'spend' && (
        <>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Asset Category</label>
            <select
              value={spendCategory}
              onChange={(e) => setSpendCategory(e.target.value)}
              className="w-full h-10 px-3 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-secondary"
            >
              <option value="">Select category...</option>
              {SPEND_CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Amount</label>
              <Input
                type="number"
                value={spendAmount || ''}
                onChange={(e) => setSpendAmount(parseFloat(e.target.value) || 0)}
                placeholder="0"
                min={0}
                step={0.01}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full h-10 px-3 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-secondary"
              >
                {CURRENCIES.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.symbol} {c.code} - {c.name}
                  </option>
                ))}
              </select>
              {currency !== 'USD' && (
                <p className="mt-1 text-xs text-foreground-muted">
                  EEIO factors are in USD. Your {currency} amount will be converted automatically.
                </p>
              )}
            </div>
          </div>
        </>
      )}

      {/* Supplier-Specific Method Fields */}
      {method === 'supplier-specific' && (
        <>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Quantity</label>
              <Input
                type="number"
                value={quantity || ''}
                onChange={(e) => setQuantity(parseFloat(e.target.value) || 0)}
                placeholder="0"
                min={0}
                step={0.01}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Unit</label>
              <select
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                className="w-full h-10 px-3 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-accent"
              >
                {PHYSICAL_UNITS.map((u) => (
                  <option key={u.value} value={u.value}>
                    {u.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">
              Supplier Emission Factor (kg CO2e per {unit})
            </label>
            <Input
              type="number"
              value={supplierEF || ''}
              onChange={(e) => setSupplierEF(parseFloat(e.target.value) || 0)}
              placeholder="e.g., 500"
              min={0}
              step={0.001}
            />
            <p className="mt-1 text-xs text-foreground-muted">
              Enter the emission factor from your supplier's EPD or environmental data
            </p>
          </div>
        </>
      )}

      {/* Preview */}
      {preview && (
        <div className="p-4 bg-success/10 border border-success/20 rounded-lg space-y-2">
          <h4 className="font-medium text-success flex items-center gap-2">
            <Calculator className="w-4 h-4" />
            Estimated Emissions
          </h4>
          <p className="text-2xl font-bold text-success">{formatCO2e(preview.co2e_kg)}</p>
          <p className="text-sm text-success/80 font-mono">{preview.formula}</p>
        </div>
      )}

      {/* Accumulated entries summary */}
      {entries.length > 0 && (
        <div className="p-4 bg-info/10 border border-info/20 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-info" />
              <span className="font-medium text-info">
                {entries.length} {entries.length === 1 ? 'activity' : 'activities'} saved this session
              </span>
            </div>
            <span className="text-lg font-bold text-info">{formatCO2e(getTotalCO2e())}</span>
          </div>
        </div>
      )}

      {/* Success message */}
      {saveSuccess && (
        <div className="p-4 bg-success/10 border border-success/20 rounded-lg animate-fade-in">
          <div className="flex items-center gap-2 text-success">
            <Save className="w-5 h-5" />
            <span className="font-semibold">Activity saved successfully!</span>
          </div>
        </div>
      )}

      {/* Error message */}
      {saveError && (
        <div className="p-4 bg-error/10 border border-error/20 rounded-lg">
          <p className="text-error">{saveError}</p>
        </div>
      )}

      {/* Actions */}
      {!saveSuccess && (
        <div className="flex flex-wrap items-center gap-3">
          <Button
            variant="ghost"
            onClick={goBack}
            disabled={isSaving}
            leftIcon={<ArrowLeft className="w-4 h-4" />}
          >
            Back
          </Button>
          <div className="flex-1" />
          <Button
            variant="outline"
            onClick={handlePreview}
            disabled={!canSave() || isSaving}
            leftIcon={<Eye className="w-4 h-4" />}
          >
            Preview
          </Button>
          <Button
            variant="outline"
            onClick={handleSaveAndAddAnother}
            disabled={!canSave() || isSaving}
            leftIcon={isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          >
            Save & Add Another
          </Button>
          <Button
            variant="primary"
            onClick={handleSave}
            disabled={!canSave() || isSaving}
            leftIcon={isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          >
            Save
          </Button>
        </div>
      )}
    </div>
  );
}
