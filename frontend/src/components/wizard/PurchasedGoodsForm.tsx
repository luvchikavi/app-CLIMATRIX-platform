'use client';

/**
 * PurchasedGoodsForm - Category 3.1 Purchased Goods & Services
 *
 * Supports 3 methods per GHG Protocol:
 * 1. Physical - Material-based (kg/tonnes) using material type dropdown
 * 2. Spend - EEIO-based (USD/EUR/GBP/ILS) using spend category dropdown
 * 3. Supplier-Specific - User provides their own emission factor
 */

import { useState, useEffect } from 'react';
import { useWizardStore } from '@/stores/wizard';
import { useCreateActivity } from '@/hooks/useEmissions';
import { Button, Input } from '@/components/ui';
import { formatCO2e } from '@/lib/utils';
import { calculateSpendEmissions } from '@/lib/currency';
import {
  Calculator,
  Save,
  Plus,
  Loader2,
  DollarSign,
  Scale,
  FileText,
  Info,
  Eye,
  Database,
  ArrowLeft,
  ShoppingCart,
  ClipboardList,
} from 'lucide-react';

type Method = 'physical' | 'spend' | 'supplier-specific';

// Material types for Physical method (matches backend resolver)
const MATERIAL_TYPES = [
  // Metals
  { value: 'steel_purchased_kg', label: 'Steel - Primary', category: 'Metals' },
  { value: 'steel_recycled_purchased_kg', label: 'Steel - Recycled', category: 'Metals' },
  { value: 'aluminum_purchased_kg', label: 'Aluminum - Primary', category: 'Metals' },
  { value: 'aluminum_recycled_purchased_kg', label: 'Aluminum - Recycled', category: 'Metals' },
  { value: 'copper_purchased_kg', label: 'Copper', category: 'Metals' },
  // Plastics
  { value: 'plastic_pet_purchased_kg', label: 'PET', category: 'Plastics' },
  { value: 'plastic_hdpe_purchased_kg', label: 'HDPE', category: 'Plastics' },
  { value: 'plastic_pvc_purchased_kg', label: 'PVC', category: 'Plastics' },
  { value: 'plastic_pp_purchased_kg', label: 'PP', category: 'Plastics' },
  { value: 'plastic_ldpe_purchased_kg', label: 'LDPE', category: 'Plastics' },
  { value: 'plastic_generic_purchased_kg', label: 'Plastic - Average', category: 'Plastics' },
  // Paper
  { value: 'paper_virgin_purchased_kg', label: 'Paper - Virgin', category: 'Paper' },
  { value: 'paper_recycled_purchased_kg', label: 'Paper - Recycled', category: 'Paper' },
  { value: 'cardboard_purchased_kg', label: 'Cardboard', category: 'Paper' },
  // Glass
  { value: 'glass_purchased_kg', label: 'Glass - Primary', category: 'Glass' },
  { value: 'glass_recycled_purchased_kg', label: 'Glass - Recycled', category: 'Glass' },
  // Textiles
  { value: 'cotton_purchased_kg', label: 'Cotton', category: 'Textiles' },
  { value: 'polyester_purchased_kg', label: 'Polyester', category: 'Textiles' },
  { value: 'textiles_mixed_purchased_kg', label: 'Textiles - Mixed', category: 'Textiles' },
  // Food
  { value: 'beef_purchased_kg', label: 'Beef', category: 'Food' },
  { value: 'poultry_purchased_kg', label: 'Poultry', category: 'Food' },
  { value: 'dairy_purchased_kg', label: 'Dairy', category: 'Food' },
  { value: 'vegetables_purchased_kg', label: 'Vegetables', category: 'Food' },
  { value: 'food_mixed_purchased_kg', label: 'Food - Mixed', category: 'Food' },
  // Other
  { value: 'electronics_purchased_kg', label: 'Electronics', category: 'Other' },
  { value: 'cement_purchased_kg', label: 'Cement', category: 'Construction' },
  { value: 'concrete_purchased_kg', label: 'Concrete', category: 'Construction' },
  { value: 'wood_purchased_kg', label: 'Wood', category: 'Construction' },
  { value: 'timber_purchased_kg', label: 'Timber', category: 'Construction' },
  { value: 'chemicals_purchased_kg', label: 'Chemicals', category: 'Chemicals' },
];

// Spend categories for Spend method (matches backend resolver)
const SPEND_CATEGORIES = [
  { value: 'spend_office_supplies', label: 'Office Supplies' },
  { value: 'spend_it_equipment', label: 'IT Equipment' },
  { value: 'spend_it_services', label: 'IT Services' },
  { value: 'spend_professional', label: 'Professional Services' },
  { value: 'spend_legal_services', label: 'Legal Services' },
  { value: 'spend_marketing', label: 'Marketing' },
  { value: 'spend_food_beverages', label: 'Food & Beverages' },
  { value: 'spend_cleaning_services', label: 'Cleaning Services' },
  { value: 'spend_telecommunications', label: 'Telecommunications' },
  { value: 'spend_insurance', label: 'Insurance' },
  { value: 'spend_banking', label: 'Banking' },
  { value: 'spend_printing', label: 'Printing' },
  { value: 'spend_furniture', label: 'Furniture' },
  { value: 'spend_chemicals', label: 'Chemicals' },
  { value: 'spend_other', label: 'Other' },
];

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'ILS', symbol: '₪', name: 'Israeli Shekel' },
];

const PHYSICAL_UNITS = [
  { value: 'kg', label: 'Kilograms (kg)' },
  { value: 'tonnes', label: 'Tonnes' },
];

interface PurchasedGoodsFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function PurchasedGoodsForm({ periodId, onSuccess }: PurchasedGoodsFormProps) {
  const reset = useWizardStore((s) => s.reset);
  const goBack = useWizardStore((s) => s.goBack);
  const entries = useWizardStore((s) => s.entries);
  const addEntry = useWizardStore((s) => s.addEntry);
  const getTotalCO2e = useWizardStore((s) => s.getTotalCO2e);

  // Form state
  const [method, setMethod] = useState<Method>('physical');
  const [description, setDescription] = useState('');
  const [quantity, setQuantity] = useState<number>(0);
  const [unit, setUnit] = useState('kg');
  const [materialType, setMaterialType] = useState('');
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

  // Get activity_key based on method
  const getActivityKey = (): string => {
    switch (method) {
      case 'physical':
        return materialType || 'plastic_generic_purchased_kg';
      case 'spend':
        return spendCategory || 'spend_other';
      case 'supplier-specific':
        return 'supplier_specific_3_1';
      default:
        return 'spend_other';
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
        return 'kg';
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
        return !!materialType && quantity > 0;
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
        // Use typical material EF (will be calculated properly by backend)
        const materialEF = 2.5; // Placeholder, backend will use actual factor
        co2e = quantity * materialEF;
        formula = `${quantity} ${unit} × ~${materialEF} kg CO2e/${unit} = ${co2e.toFixed(2)} kg CO2e (estimate)`;
        break;
      case 'spend':
        // Use typical EEIO EF with currency conversion
        const spendEF = 0.5; // Placeholder, backend will use actual factor
        const spendResult = calculateSpendEmissions(spendAmount, currency, spendEF);
        co2e = spendResult.co2e;
        formula = spendResult.formula + ' (estimate)';
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
        category_code: '3.1',
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

      console.log('[3.1 Form] Saving activity:', payload);

      await createActivity.mutateAsync(payload);

      setSaveSuccess(true);

      // Reset and close after brief success message
      setTimeout(() => {
        reset();
        onSuccess?.();
      }, 1500);
    } catch (error) {
      console.error('[3.1 Form] Save error:', error);
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
        category_code: '3.1',
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

  // Group materials by category for dropdown
  const groupedMaterials = MATERIAL_TYPES.reduce((acc, material) => {
    if (!acc[material.category]) acc[material.category] = [];
    acc[material.category].push(material);
    return acc;
  }, {} as Record<string, typeof MATERIAL_TYPES>);

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
          <ShoppingCart className="w-5 h-5 text-blue-600" />
          3.1 Purchased Goods & Services
        </h2>
        <p className="text-sm text-foreground-muted">
          Select a method and enter your data
        </p>
      </div>

      {/* Method Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-medium">Step 1: Select Calculation Method</label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: 'physical' as Method, label: 'Physical', desc: 'Material weight', Icon: Scale, color: 'border-green-500 bg-green-50' },
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
                <strong>Physical Method:</strong> Enter the weight of purchased materials. Best for raw
                materials, packaging, and goods where you know the weight.
              </>
            )}
            {method === 'spend' && (
              <>
                <strong>Spend Method:</strong> Enter the invoice amount. Uses EEIO (Economic Input-Output)
                factors. Best when you only have purchase invoices.
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
          placeholder="e.g., Office furniture purchase, Steel for manufacturing"
        />
      </div>

      {/* Physical Method Fields */}
      {method === 'physical' && (
        <>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Material Type</label>
            <select
              value={materialType}
              onChange={(e) => setMaterialType(e.target.value)}
              className="w-full h-10 px-3 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Select material...</option>
              {Object.entries(groupedMaterials).map(([category, materials]) => (
                <optgroup key={category} label={category}>
                  {materials.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>
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
                className="w-full h-10 px-3 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {PHYSICAL_UNITS.map((u) => (
                  <option key={u.value} value={u.value}>
                    {u.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </>
      )}

      {/* Spend Method Fields */}
      {method === 'spend' && (
        <>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Spend Category</label>
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
              placeholder="e.g., 2.5"
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
