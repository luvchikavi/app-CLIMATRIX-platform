'use client';

/**
 * WasteForm - Category 3.5 Waste Generated in Operations
 *
 * Supports 3 methods per GHG Protocol:
 * 1. Physical - Weight-based with treatment method (kg)
 * 2. Spend - Disposal cost (USD)
 * 3. Supplier-Specific - User provides own EF from waste contractor
 */

import { useState, useMemo } from 'react';
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
  ArrowLeft,
  Trash2,
  Recycle,
  Info,
  Scale,
  DollarSign,
  ClipboardList,
} from 'lucide-react';
import { LucideIcon } from 'lucide-react';

// =============================================================================
// WASTE DATA DEFINITIONS
// =============================================================================

type WasteMethod = 'physical' | 'spend' | 'supplier-specific';

// Waste Types
const WASTE_TYPES = [
  { key: 'mixed', label: 'Mixed/General Waste', category: 'General' },
  { key: 'commercial', label: 'Commercial Waste', category: 'General' },
  { key: 'paper', label: 'Paper', category: 'Recyclables' },
  { key: 'cardboard', label: 'Cardboard', category: 'Recyclables' },
  { key: 'plastic', label: 'Plastic', category: 'Recyclables' },
  { key: 'metal', label: 'Metal', category: 'Recyclables' },
  { key: 'aluminium', label: 'Aluminium', category: 'Recyclables' },
  { key: 'steel', label: 'Steel', category: 'Recyclables' },
  { key: 'glass', label: 'Glass', category: 'Recyclables' },
  { key: 'food', label: 'Food Waste', category: 'Organic' },
  { key: 'organic', label: 'Organic/Garden Waste', category: 'Organic' },
  { key: 'wood', label: 'Wood', category: 'Other' },
  { key: 'textile', label: 'Textile', category: 'Other' },
  { key: 'electronic', label: 'Electronic/WEEE', category: 'Special' },
  { key: 'construction', label: 'Construction/C&D', category: 'Special' },
  { key: 'hazardous', label: 'Hazardous', category: 'Special' },
  { key: 'batteries', label: 'Batteries', category: 'Special' },
];

// Treatment Methods with emission factor estimates (kg CO2e per kg)
const TREATMENT_METHODS = [
  { key: 'landfill', label: 'Landfill', efEstimate: 0.586 },
  { key: 'recycling', label: 'Recycling', efEstimate: 0.021 },
  { key: 'incineration', label: 'Incineration', efEstimate: 0.021 },
  { key: 'incineration_energy', label: 'Incineration with Energy Recovery', efEstimate: 0.021 },
  { key: 'composting', label: 'Composting', efEstimate: 0.010 },
  { key: 'anaerobic', label: 'Anaerobic Digestion', efEstimate: 0.010 },
  { key: 'wastewater', label: 'Wastewater Treatment', efEstimate: 0.708 },
];

// Waste type + treatment combination EF estimates (kg CO2e per kg)
const EF_ESTIMATES: Record<string, Record<string, number>> = {
  landfill: {
    mixed: 0.586,
    food: 0.587,
    paper: 1.042,
    plastic: 0.025,
    wood: 1.329,
    textile: 2.048,
  },
  recycling: {
    paper: 0.021,
    cardboard: 0.021,
    plastic: 0.021,
    metal: 0.021,
    aluminium: 0.021,
    glass: 0.021,
    mixed: 0.021,
  },
  composting: {
    food: 0.010,
    organic: 0.010,
  },
  incineration: {
    mixed: 0.021,
  },
};

const UNITS = [
  { value: 'kg', label: 'Kilograms (kg)' },
  { value: 'tonnes', label: 'Tonnes' },
];

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'ILS', symbol: '₪', name: 'Israeli Shekel' },
];

// EEIO spend factor estimate (kg CO2e per USD)
const SPEND_EF_ESTIMATE = 0.35;

// =============================================================================
// COMPONENT
// =============================================================================

interface WasteFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function WasteForm({ periodId, onSuccess }: WasteFormProps) {
  const reset = useWizardStore((s) => s.reset);
  const goBack = useWizardStore((s) => s.goBack);
  const createActivity = useCreateActivity(periodId);

  // Form state
  const [method, setMethod] = useState<WasteMethod | ''>('');
  const [wasteType, setWasteType] = useState('');
  const [treatment, setTreatment] = useState('');
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState('kg');
  const [spendAmount, setSpendAmount] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [supplierEf, setSupplierEf] = useState('');
  const [description, setDescription] = useState('');
  const [site, setSite] = useState('');
  const [activityDate, setActivityDate] = useState(new Date().toISOString().split('T')[0]);

  // Group waste types by category
  const groupedWasteTypes = useMemo(() => {
    const groups: Record<string, typeof WASTE_TYPES> = {};
    WASTE_TYPES.forEach(wt => {
      if (!groups[wt.category]) groups[wt.category] = [];
      groups[wt.category].push(wt);
    });
    return groups;
  }, []);

  // Get EF estimate for preview
  const getEfEstimate = (wasteKey: string, treatmentKey: string): number => {
    const treatmentEfs = EF_ESTIMATES[treatmentKey];
    if (treatmentEfs && treatmentEfs[wasteKey]) {
      return treatmentEfs[wasteKey];
    }
    // Fallback to treatment default
    const treatmentMethod = TREATMENT_METHODS.find(t => t.key === treatmentKey);
    return treatmentMethod?.efEstimate || 0.5;
  };

  // Build activity key from waste type and treatment
  const getActivityKey = (wasteKey: string, treatmentKey: string): string => {
    // Special cases
    if (wasteKey === 'electronic') {
      return treatmentKey === 'recycling' ? 'waste_ewaste_recycled' : 'waste_ewaste';
    }
    if (wasteKey === 'construction') {
      return treatmentKey === 'recycling' ? 'waste_construction_recycled' : 'waste_construction';
    }
    if (wasteKey === 'hazardous') return 'waste_hazardous';
    if (wasteKey === 'batteries') return 'waste_batteries';

    // Standard: treatment_wastetype
    const treatmentMap: Record<string, string> = {
      landfill: 'landfill',
      recycling: 'recycled',
      incineration: 'incineration',
      incineration_energy: 'incineration_energy',
      composting: 'composted',
      anaerobic: 'anaerobic',
      wastewater: 'wastewater',
    };
    const treatmentPrefix = treatmentMap[treatmentKey] || 'landfill';
    return `waste_${treatmentPrefix}_${wasteKey}`;
  };

  // Preview calculation
  const preview = useMemo(() => {
    if (!method) return null;

    if (method === 'physical') {
      const qty = parseFloat(quantity) || 0;
      if (!wasteType || !treatment || !qty) return null;

      // Convert tonnes to kg for calculation
      const qtyKg = unit === 'tonnes' ? qty * 1000 : qty;
      const ef = getEfEstimate(wasteType, treatment);
      const co2e = qtyKg * ef;

      return {
        activityKey: getActivityKey(wasteType, treatment),
        quantity: qty,
        unit: unit,
        co2e,
        formula: `${qty.toLocaleString()} ${unit} × ${ef.toFixed(3)} kg/${unit === 'tonnes' ? 'tonne' : 'kg'} = ${co2e.toFixed(2)} kg CO2e`,
        efSource: 'DEFRA 2024',
      };
    }

    if (method === 'spend') {
      const amount = parseFloat(spendAmount) || 0;
      if (!amount) return null;

      const { co2e, formula } = calculateSpendEmissions(amount, currency, SPEND_EF_ESTIMATE);
      return {
        activityKey: 'waste_disposal_spend',
        quantity: amount,
        unit: currency,
        co2e,
        formula,
        efSource: 'EEIO 2024',
      };
    }

    if (method === 'supplier-specific') {
      const qty = parseFloat(quantity) || 0;
      const ef = parseFloat(supplierEf) || 0;
      if (!qty || !ef) return null;

      // Convert tonnes to kg for calculation
      const qtyKg = unit === 'tonnes' ? qty * 1000 : qty;
      const co2e = qtyKg * ef;

      return {
        activityKey: 'supplier_specific_3_5',
        quantity: qty,
        unit: unit,
        co2e,
        formula: `${qty.toLocaleString()} ${unit} × ${ef.toFixed(3)} kg CO2e/${unit} = ${co2e.toFixed(2)} kg CO2e`,
        efSource: 'User-provided (Waste Contractor)',
        supplierEf: ef,
      };
    }

    return null;
  }, [method, wasteType, treatment, quantity, unit, spendAmount, currency, supplierEf]);

  // Handle save
  const handleSave = async (addAnother: boolean = false) => {
    if (!preview) return;

    const wasteTypeLabel = WASTE_TYPES.find(w => w.key === wasteType)?.label;
    const treatmentLabel = TREATMENT_METHODS.find(t => t.key === treatment)?.label;

    try {
      await createActivity.mutateAsync({
        scope: 3,
        category_code: '3.5',
        activity_key: preview.activityKey,
        description: description || `${wasteTypeLabel || 'Waste'} - ${treatmentLabel || treatment}`,
        quantity: preview.quantity,
        unit: preview.unit,
        activity_date: activityDate,
        supplier_ef: preview.supplierEf,
      });

      if (addAnother) {
        // Reset form but keep method
        setWasteType('');
        setTreatment('');
        setQuantity('');
        setSpendAmount('');
        setSupplierEf('');
        setDescription('');
        setSite('');
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
          <Trash2 className="w-5 h-5 text-green-600" />
          3.5 Waste Generated in Operations
        </h2>
        <p className="text-sm text-foreground-muted">
          Disposal and treatment of waste generated by your organization
        </p>
      </div>

      {/* Method Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-medium">Step 1: Select Calculation Method</label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: 'physical' as WasteMethod, label: 'Physical', desc: 'Weight-based', Icon: Scale, color: 'border-green-500 bg-green-50' },
            { value: 'spend' as WasteMethod, label: 'Spend', desc: 'Disposal Cost', Icon: DollarSign, color: 'border-blue-500 bg-blue-50' },
            { value: 'supplier-specific' as WasteMethod, label: 'Supplier', desc: 'Contractor EF', Icon: ClipboardList, color: 'border-amber-500 bg-amber-50' },
          ].map((m) => (
            <button
              key={m.value}
              onClick={() => {
                setMethod(m.value);
                setWasteType('');
                setTreatment('');
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

      {/* Physical Method Fields */}
      {method === 'physical' && (
        <div className="space-y-4 p-4 bg-green-50 rounded-lg border border-green-200">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Waste Type</label>
              <select
                value={wasteType}
                onChange={(e) => setWasteType(e.target.value)}
                className={selectClass}
              >
                <option value="">Select waste type...</option>
                {Object.entries(groupedWasteTypes).map(([category, types]) => (
                  <optgroup key={category} label={category}>
                    {types.map((wt) => (
                      <option key={wt.key} value={wt.key}>
                        {wt.label}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Treatment Method</label>
              <select
                value={treatment}
                onChange={(e) => setTreatment(e.target.value)}
                className={selectClass}
              >
                <option value="">Select treatment...</option>
                {TREATMENT_METHODS.map((t) => (
                  <option key={t.key} value={t.key}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Quantity"
              type="number"
              step="0.01"
              min="0"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="e.g., 500"
            />
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Unit</label>
              <select
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                className={selectClass}
              >
                {UNITS.map((u) => (
                  <option key={u.value} value={u.value}>
                    {u.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {wasteType && treatment && (
            <div className="p-3 bg-white rounded-lg border flex items-center gap-2">
              <Recycle className="w-4 h-4 text-green-600" />
              <span className="text-sm">
                <strong>{WASTE_TYPES.find(w => w.key === wasteType)?.label}</strong>
                {' → '}
                <strong>{TREATMENT_METHODS.find(t => t.key === treatment)?.label}</strong>
              </span>
            </div>
          )}
        </div>
      )}

      {/* Spend Method Fields */}
      {method === 'spend' && (
        <div className="space-y-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Spend Amount"
              type="number"
              step="0.01"
              min="0"
              value={spendAmount}
              onChange={(e) => setSpendAmount(e.target.value)}
              placeholder="e.g., 2000"
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
        </div>
      )}

      {/* Supplier-Specific Method Fields */}
      {method === 'supplier-specific' && (
        <div className="space-y-4 p-4 bg-amber-50 rounded-lg border border-amber-200">
          <div className="flex items-start gap-2 p-3 bg-white rounded-lg border border-amber-300">
            <Info className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-amber-800">
              <strong>Supplier-Specific Method:</strong> Enter the emission factor provided by your
              waste contractor (e.g., from their sustainability report or waste manifest).
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Waste Type (optional)</label>
            <select
              value={wasteType}
              onChange={(e) => setWasteType(e.target.value)}
              className={selectClass}
            >
              <option value="">Select waste type...</option>
              {Object.entries(groupedWasteTypes).map(([category, types]) => (
                <optgroup key={category} label={category}>
                  {types.map((wt) => (
                    <option key={wt.key} value={wt.key}>
                      {wt.label}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Quantity"
              type="number"
              step="0.01"
              min="0"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="e.g., 500"
            />
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Unit</label>
              <select
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                className={selectClass}
              >
                {UNITS.map((u) => (
                  <option key={u.value} value={u.value}>
                    {u.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <Input
            label="Supplier Emission Factor (kg CO2e per kg or tonne)"
            type="number"
            step="0.001"
            min="0"
            value={supplierEf}
            onChange={(e) => setSupplierEf(e.target.value)}
            placeholder="e.g., 0.45"
            hint="Get this value from your waste contractor's carbon report"
          />
        </div>
      )}

      {/* Optional Fields */}
      {method && (
        <div className="space-y-4">
          <Input
            label="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., Office waste Q1"
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Site (optional)"
              value={site}
              onChange={(e) => setSite(e.target.value)}
              placeholder="e.g., Main Office"
            />
            <Input
              label="Activity Date"
              type="date"
              value={activityDate}
              onChange={(e) => setActivityDate(e.target.value)}
            />
          </div>
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
