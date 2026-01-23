'use client';

/**
 * EndOfLifeForm - Category 3.12 End-of-Life Treatment of Sold Products
 *
 * Supports 2 methods per GHG Protocol:
 * 1. Waste-Type - Material and disposal method based (kg)
 * 2. Spend - Disposal cost based (USD)
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
  Recycle,
  Package,
  Info,
} from 'lucide-react';

// =============================================================================
// END-OF-LIFE DATA DEFINITIONS
// =============================================================================

type EOLMethod = 'waste-type' | 'spend';

// Material Types (what the sold products are made of)
const MATERIAL_TYPES = [
  { key: 'metal', label: 'Metal', category: 'Recyclables' },
  { key: 'aluminum', label: 'Aluminum', category: 'Recyclables' },
  { key: 'steel', label: 'Steel', category: 'Recyclables' },
  { key: 'plastic', label: 'Plastic', category: 'Recyclables' },
  { key: 'paper', label: 'Paper/Cardboard', category: 'Recyclables' },
  { key: 'glass', label: 'Glass', category: 'Recyclables' },
  { key: 'textile', label: 'Textile', category: 'Recyclables' },
  { key: 'wood', label: 'Wood', category: 'Other' },
  { key: 'organic', label: 'Organic/Food', category: 'Organic' },
  { key: 'electronics', label: 'Electronics/E-Waste', category: 'Special' },
  { key: 'batteries', label: 'Batteries', category: 'Special' },
  { key: 'hazardous', label: 'Hazardous', category: 'Special' },
  { key: 'mixed', label: 'Mixed', category: 'General' },
  { key: 'other', label: 'Other', category: 'General' },
];

// Disposal Methods with emission factor estimates (kg CO2e per kg)
const DISPOSAL_METHODS = [
  { key: 'recycling', label: 'Recycling', efEstimate: 0.021 },
  { key: 'landfill', label: 'Landfill', efEstimate: 0.460 },
  { key: 'incineration', label: 'Incineration', efEstimate: 0.918 },
  { key: 'incineration_energy', label: 'Incineration with Energy Recovery', efEstimate: 0.429 },
  { key: 'composting', label: 'Composting', efEstimate: 0.010 },
  { key: 'anaerobic', label: 'Anaerobic Digestion', efEstimate: 0.010 },
  { key: 'special', label: 'Special Treatment', efEstimate: 0.750 },
];

// Material + disposal combination EF estimates (kg CO2e per kg)
const EF_ESTIMATES: Record<string, Record<string, number>> = {
  recycling: {
    metal: 0.021,
    aluminum: 0.021,
    steel: 0.021,
    plastic: 0.021,
    paper: 0.021,
    glass: 0.021,
    textile: 0.021,
    electronics: 0.021,
    mixed: 0.021,
  },
  landfill: {
    organic: 0.587,
    plastic: 0.010,
    paper: 1.042,
    wood: 0.735,
    textile: 0.587,
    mixed: 0.460,
  },
  composting: {
    organic: 0.010,
  },
  anaerobic: {
    organic: 0.010,
  },
  incineration: {
    mixed: 0.918,
    plastic: 0.918,
    paper: 0.918,
    textile: 0.918,
  },
  incineration_energy: {
    mixed: 0.429,
    plastic: 0.429,
    paper: 0.429,
    textile: 0.429,
  },
  special: {
    electronics: 0.500,
    batteries: 0.750,
    hazardous: 1.200,
  },
};

const UNITS = [
  { value: 'kg', label: 'Kilograms (kg)' },
  { value: 'tonnes', label: 'Tonnes' },
];

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '\u20AC', name: 'Euro' },
  { code: 'GBP', symbol: '\u00A3', name: 'British Pound' },
  { code: 'ILS', symbol: '\u20AA', name: 'Israeli Shekel' },
];

// EEIO spend factor estimate (kg CO2e per USD)
const SPEND_EF_ESTIMATE = 0.40;

// =============================================================================
// COMPONENT
// =============================================================================

interface EndOfLifeFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function EndOfLifeForm({ periodId, onSuccess }: EndOfLifeFormProps) {
  const reset = useWizardStore((s) => s.reset);
  const goBack = useWizardStore((s) => s.goBack);
  const createActivity = useCreateActivity(periodId);

  // Form state
  const [method, setMethod] = useState<EOLMethod | ''>('');
  const [materialType, setMaterialType] = useState('');
  const [disposal, setDisposal] = useState('');
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState('kg');
  const [spendAmount, setSpendAmount] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [productDescription, setProductDescription] = useState('');
  const [unitsDisposed, setUnitsDisposed] = useState('');
  const [activityDate, setActivityDate] = useState(new Date().toISOString().split('T')[0]);

  // Group material types by category
  const groupedMaterialTypes = useMemo(() => {
    const groups: Record<string, typeof MATERIAL_TYPES> = {};
    MATERIAL_TYPES.forEach(mt => {
      if (!groups[mt.category]) groups[mt.category] = [];
      groups[mt.category].push(mt);
    });
    return groups;
  }, []);

  // Get EF estimate for preview
  const getEfEstimate = (materialKey: string, disposalKey: string): number => {
    const disposalEfs = EF_ESTIMATES[disposalKey];
    if (disposalEfs && disposalEfs[materialKey]) {
      return disposalEfs[materialKey];
    }
    // Fallback to disposal default
    const disposalMethod = DISPOSAL_METHODS.find(d => d.key === disposalKey);
    return disposalMethod?.efEstimate || 0.5;
  };

  // Build activity key from material type and disposal method
  const getActivityKey = (materialKey: string, disposalKey: string): string => {
    // Special cases - materials with dedicated activity keys
    if (materialKey === 'batteries') return 'eol_batteries';
    if (materialKey === 'hazardous') return 'eol_hazardous';

    // Map disposal method to activity key prefix
    if (disposalKey === 'recycling') {
      const materialMap: Record<string, string> = {
        metal: 'eol_recycling_metal',
        aluminum: 'eol_recycling_metal',
        steel: 'eol_recycling_metal',
        plastic: 'eol_recycling_plastic',
        paper: 'eol_recycling_paper',
        glass: 'eol_recycling_glass',
        electronics: 'eol_recycling_ewaste',
        textile: 'eol_recycling_textile',
        mixed: 'eol_recycling_mixed',
      };
      return materialMap[materialKey] || 'eol_recycling_mixed';
    }

    if (disposalKey === 'landfill') {
      const materialMap: Record<string, string> = {
        organic: 'eol_landfill_organic',
        plastic: 'eol_landfill_plastic',
        paper: 'eol_landfill_paper',
        wood: 'eol_landfill_wood',
        textile: 'eol_landfill_textile',
        mixed: 'eol_landfill_mixed',
      };
      return materialMap[materialKey] || 'eol_landfill_mixed';
    }

    if (disposalKey === 'incineration') return 'eol_incineration';
    if (disposalKey === 'incineration_energy') return 'eol_incineration_energy';
    if (disposalKey === 'composting') return 'eol_composting';
    if (disposalKey === 'anaerobic') return 'eol_anaerobic_digestion';
    if (disposalKey === 'special') {
      if (materialKey === 'electronics') return 'eol_ewaste_mixed';
      return 'eol_hazardous';
    }

    return 'eol_landfill_mixed';
  };

  // Preview calculation
  const preview = useMemo(() => {
    if (!method) return null;

    if (method === 'waste-type') {
      const qty = parseFloat(quantity) || 0;
      if (!materialType || !disposal || !qty) return null;

      // Convert tonnes to kg for calculation
      const qtyKg = unit === 'tonnes' ? qty * 1000 : qty;
      const ef = getEfEstimate(materialType, disposal);
      const co2e = qtyKg * ef;

      return {
        activityKey: getActivityKey(materialType, disposal),
        quantity: qty,
        unit: unit,
        co2e,
        formula: `${qty.toLocaleString()} ${unit} x ${ef.toFixed(3)} kg CO2e/${unit === 'tonnes' ? 'tonne' : 'kg'} = ${co2e.toFixed(2)} kg CO2e`,
        efSource: 'DEFRA 2024',
      };
    }

    if (method === 'spend') {
      const amount = parseFloat(spendAmount) || 0;
      if (!amount) return null;

      const { co2e, formula } = calculateSpendEmissions(amount, currency, SPEND_EF_ESTIMATE);
      return {
        activityKey: 'eol_spend_disposal',
        quantity: amount,
        unit: currency,
        co2e,
        formula,
        efSource: 'EEIO 2024',
      };
    }

    return null;
  }, [method, materialType, disposal, quantity, unit, spendAmount, currency]);

  // Handle save
  const handleSave = async (addAnother: boolean = false) => {
    if (!preview) return;

    const materialLabel = MATERIAL_TYPES.find(m => m.key === materialType)?.label;
    const disposalLabel = DISPOSAL_METHODS.find(d => d.key === disposal)?.label;

    try {
      await createActivity.mutateAsync({
        scope: 3,
        category_code: '3.12',
        activity_key: preview.activityKey,
        description: productDescription || `EOL: ${materialLabel || 'Products'} - ${disposalLabel || disposal}`,
        quantity: preview.quantity,
        unit: preview.unit,
        activity_date: activityDate,
      });

      if (addAnother) {
        // Reset form but keep method
        setMaterialType('');
        setDisposal('');
        setQuantity('');
        setSpendAmount('');
        setProductDescription('');
        setUnitsDisposed('');
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
          <Package className="w-5 h-5 text-amber-700" />
          3.12 End-of-Life Treatment of Sold Products
        </h2>
        <p className="text-sm text-foreground-muted">
          Emissions from disposal and treatment of products sold by your company at end of their useful life
        </p>
      </div>

      {/* Info box */}
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
        <div className="flex gap-3">
          <Info className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-amber-800">
            <p className="font-medium mb-1">What to report:</p>
            <ul className="list-disc list-inside space-y-1 text-amber-700">
              <li>Estimate how customers dispose of your products at end of life</li>
              <li>Include recycling, landfill, incineration, or other disposal methods</li>
              <li>Use industry averages if specific data is unavailable</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Method Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-medium">Step 1: Select Calculation Method</label>
        <div className="grid grid-cols-2 gap-3">
          {[
            { value: 'waste-type' as EOLMethod, label: 'Waste-Type', desc: 'Material & disposal', icon: <Recycle className="w-6 h-6" />, color: 'border-green-500 bg-green-50' },
            { value: 'spend' as EOLMethod, label: 'Spend', desc: 'Disposal cost', icon: <span className="text-2xl">$</span>, color: 'border-blue-500 bg-blue-50' },
          ].map((m) => (
            <button
              key={m.value}
              onClick={() => {
                setMethod(m.value);
                setMaterialType('');
                setDisposal('');
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

      {/* Waste-Type Method Fields */}
      {method === 'waste-type' && (
        <div className="space-y-4 p-4 bg-green-50 rounded-lg border border-green-200">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Material Type</label>
              <select
                value={materialType}
                onChange={(e) => setMaterialType(e.target.value)}
                className={selectClass}
              >
                <option value="">Select material...</option>
                {Object.entries(groupedMaterialTypes).map(([category, types]) => (
                  <optgroup key={category} label={category}>
                    {types.map((mt) => (
                      <option key={mt.key} value={mt.key}>
                        {mt.label}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Disposal Method</label>
              <select
                value={disposal}
                onChange={(e) => setDisposal(e.target.value)}
                className={selectClass}
              >
                <option value="">Select disposal method...</option>
                {DISPOSAL_METHODS.map((dm) => (
                  <option key={dm.key} value={dm.key}>
                    {dm.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-foreground mb-1.5">Weight</label>
              <Input
                type="number"
                min="0"
                step="0.01"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="Enter weight..."
              />
            </div>
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

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Product Description
              </label>
              <Input
                type="text"
                value={productDescription}
                onChange={(e) => setProductDescription(e.target.value)}
                placeholder="e.g., Plastic packaging from sold products"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Units Disposed (optional)
              </label>
              <Input
                type="number"
                min="0"
                value={unitsDisposed}
                onChange={(e) => setUnitsDisposed(e.target.value)}
                placeholder="Number of product units"
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
                Total Disposal Cost
              </label>
              <Input
                type="number"
                min="0"
                step="0.01"
                value={spendAmount}
                onChange={(e) => setSpendAmount(e.target.value)}
                placeholder="Enter disposal cost..."
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
              value={productDescription}
              onChange={(e) => setProductDescription(e.target.value)}
              placeholder="e.g., Estimated EOL treatment of all sold products"
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
