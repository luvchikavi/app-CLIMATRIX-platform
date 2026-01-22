'use client';

/**
 * ProcessingSoldProductsForm - Category 3.10 Processing of Sold Products
 *
 * Supports 3 methods per GHG Protocol:
 * 1. Average - Industry average processing emissions by product type (kg)
 * 2. Site-Specific - Actual processing energy data from customer (kWh)
 * 3. Spend - Revenue-based using EEIO factors
 *
 * Applicable when company sells intermediate products that require further
 * processing by third parties before end use.
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
  Factory,
  Info,
  BarChart3,
  Zap,
  DollarSign,
} from 'lucide-react';

// =============================================================================
// DATA DEFINITIONS
// =============================================================================

type ProcessingMethod = 'average' | 'site-specific' | 'spend';

// Product types with their processing emission factors (kg CO2e per kg processed)
const PRODUCT_TYPES = [
  { key: 'steel', label: 'Steel/Iron', activityKey: 'processing_steel_kg', efEstimate: 1.85 },
  { key: 'aluminum', label: 'Aluminum', activityKey: 'processing_aluminum_kg', efEstimate: 8.14 },
  { key: 'metal', label: 'Metal (Other)', activityKey: 'processing_metal_kg', efEstimate: 2.50 },
  { key: 'plastic', label: 'Plastic/Polymer', activityKey: 'processing_plastic_kg', efEstimate: 3.10 },
  { key: 'chemical', label: 'Chemical/Petrochemical', activityKey: 'processing_chemical_kg', efEstimate: 2.80 },
  { key: 'textile', label: 'Textile/Fabric', activityKey: 'processing_textile_kg', efEstimate: 5.50 },
  { key: 'paper', label: 'Paper/Pulp', activityKey: 'processing_paper_kg', efEstimate: 0.92 },
  { key: 'glass', label: 'Glass', activityKey: 'processing_glass_kg', efEstimate: 0.86 },
  { key: 'food', label: 'Food/Agricultural', activityKey: 'processing_food_kg', efEstimate: 0.75 },
  { key: 'electronics', label: 'Electronics/Components', activityKey: 'processing_electronics_kg', efEstimate: 12.50 },
  { key: 'wood', label: 'Wood/Timber', activityKey: 'processing_wood_kg', efEstimate: 0.45 },
  { key: 'other', label: 'Other', activityKey: 'processing_generic_kg', efEstimate: 2.00 },
];

const PROCESSING_TYPES = [
  'Melting/Smelting',
  'Forging/Forming',
  'Machining',
  'Molding/Extrusion',
  'Assembly',
  'Chemical Processing',
  'Refining',
  'Weaving/Knitting',
  'Milling/Grinding',
  'Heat Treatment',
  'Surface Treatment',
  'Other',
];

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'ILS', symbol: '₪', name: 'Israeli Shekel' },
  { code: 'CHF', symbol: 'Fr', name: 'Swiss Franc' },
];

// Site-specific: energy-based factor
const ENERGY_EF = 0.436; // kg CO2e per kWh (global average)

// Spend-based: manufacturing factor
const SPEND_EF = 0.38; // kg CO2e per USD

// =============================================================================
// COMPONENT
// =============================================================================

interface ProcessingSoldProductsFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function ProcessingSoldProductsForm({ periodId, onSuccess }: ProcessingSoldProductsFormProps) {
  const reset = useWizardStore((s) => s.reset);
  const goBack = useWizardStore((s) => s.goBack);
  const createActivity = useCreateActivity(periodId);

  // Form state
  const [method, setMethod] = useState<ProcessingMethod | ''>('');
  const [productType, setProductType] = useState('');
  const [processingType, setProcessingType] = useState('');
  const [quantitySold, setQuantitySold] = useState('');
  const [processingEnergy, setProcessingEnergy] = useState('');
  const [revenue, setRevenue] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [description, setDescription] = useState('');
  const [customer, setCustomer] = useState('');
  const [activityDate, setActivityDate] = useState(new Date().toISOString().split('T')[0]);

  // Get selected product type details
  const selectedProductType = useMemo(() =>
    PRODUCT_TYPES.find(p => p.key === productType),
    [productType]
  );

  // Preview calculation
  const preview = useMemo(() => {
    if (!method) return null;

    if (method === 'average') {
      const quantity = parseFloat(quantitySold) || 0;
      if (!productType || !quantity) return null;
      const product = selectedProductType;
      if (!product) return null;
      const co2e = quantity * product.efEstimate;
      return {
        activityKey: product.activityKey,
        quantity,
        unit: 'kg',
        co2e,
        formula: `${quantity.toLocaleString()} kg × ${product.efEstimate.toFixed(2)} kg CO2e/kg = ${co2e.toFixed(2)} kg CO2e`,
        efSource: 'DEFRA 2024 (Industry Average)',
      };
    }

    if (method === 'site-specific') {
      const energy = parseFloat(processingEnergy) || 0;
      if (!energy) return null;
      const co2e = energy * ENERGY_EF;
      return {
        activityKey: 'processing_energy_kwh',
        quantity: energy,
        unit: 'kWh',
        co2e,
        formula: `${energy.toLocaleString()} kWh × ${ENERGY_EF} kg CO2e/kWh = ${co2e.toFixed(2)} kg CO2e`,
        efSource: 'IEA World Average 2024',
      };
    }

    if (method === 'spend') {
      const amount = parseFloat(revenue) || 0;
      if (!amount) return null;
      const co2e = amount * SPEND_EF;
      return {
        activityKey: 'processing_spend_manufacturing',
        quantity: amount,
        unit: currency,
        co2e,
        formula: `${currency} ${amount.toLocaleString()} × ${SPEND_EF.toFixed(2)} kg CO2e/${currency} = ${co2e.toFixed(2)} kg CO2e`,
        efSource: 'USEEIO 2.0 (Manufacturing)',
      };
    }

    return null;
  }, [method, productType, quantitySold, processingEnergy, revenue, currency, selectedProductType]);

  // Build description
  const fullDescription = useMemo(() => {
    const parts = [description];
    if (selectedProductType && method === 'average') {
      parts.unshift(`${selectedProductType.label} processing`);
    }
    if (processingType) {
      parts.push(`(${processingType})`);
    }
    if (customer) {
      parts.push(`- ${customer}`);
    }
    return parts.filter(Boolean).join(' ');
  }, [description, selectedProductType, processingType, customer, method]);

  // Handle save
  const handleSave = async (addAnother: boolean = false) => {
    if (!preview) return;

    try {
      await createActivity.mutateAsync({
        scope: 3,
        category_code: '3.10',
        activity_key: preview.activityKey,
        description: fullDescription || 'Processing of Sold Products',
        quantity: preview.quantity,
        unit: preview.unit,
        activity_date: activityDate,
      });

      if (addAnother) {
        // Reset form but keep method
        setProductType('');
        setProcessingType('');
        setQuantitySold('');
        setProcessingEnergy('');
        setRevenue('');
        setDescription('');
        setCustomer('');
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
          <Factory className="w-5 h-5 text-amber-800" />
          3.10 Processing of Sold Products
        </h2>
        <p className="text-sm text-foreground-muted">
          Emissions from downstream processing of intermediate products sold by your company
        </p>
      </div>

      {/* Applicability Note */}
      <div className="flex items-start gap-2 p-3 bg-amber-50 rounded-lg border border-amber-200">
        <Info className="w-4 h-4 text-amber-700 mt-0.5 flex-shrink-0" />
        <p className="text-sm text-amber-800">
          <strong>When to use:</strong> If your company sells raw materials, components, or semi-finished
          goods that require further processing by customers before end use (e.g., steel billets for casting,
          plastic pellets for molding, fabric for garment manufacturing).
        </p>
      </div>

      {/* Method Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-medium">Step 1: Select Calculation Method</label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: 'average' as ProcessingMethod, label: 'Average', desc: 'By Product Type', Icon: BarChart3, color: 'border-amber-600 bg-amber-50' },
            { value: 'site-specific' as ProcessingMethod, label: 'Site-Specific', desc: 'Processing Energy', Icon: Zap, color: 'border-blue-500 bg-blue-50' },
            { value: 'spend' as ProcessingMethod, label: 'Spend', desc: 'Revenue-Based', Icon: DollarSign, color: 'border-green-500 bg-green-50' },
          ].map((m) => (
            <button
              key={m.value}
              onClick={() => {
                setMethod(m.value);
                setProductType('');
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

      {/* Average Method Fields */}
      {method === 'average' && (
        <div className="space-y-4 p-4 bg-amber-50 rounded-lg border border-amber-200">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Product Type</label>
            <select
              value={productType}
              onChange={(e) => setProductType(e.target.value)}
              className={selectClass}
            >
              <option value="">Select product type...</option>
              {PRODUCT_TYPES.map((pt) => (
                <option key={pt.key} value={pt.key}>
                  {pt.label} (~{pt.efEstimate.toFixed(2)} kg CO2e/kg)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Processing Type (optional)</label>
            <select
              value={processingType}
              onChange={(e) => setProcessingType(e.target.value)}
              className={selectClass}
            >
              <option value="">Select processing type...</option>
              {PROCESSING_TYPES.map((pt) => (
                <option key={pt} value={pt}>{pt}</option>
              ))}
            </select>
          </div>

          <Input
            label="Quantity Sold (kg)"
            type="number"
            step="0.01"
            min="0"
            value={quantitySold}
            onChange={(e) => setQuantitySold(e.target.value)}
            placeholder="e.g., 5000"
            hint="Total weight of intermediate products sold for processing"
          />
        </div>
      )}

      {/* Site-Specific Method Fields */}
      {method === 'site-specific' && (
        <div className="space-y-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start gap-2 p-3 bg-white rounded-lg border border-blue-300">
            <Info className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-blue-800">
              <strong>Site-Specific Method:</strong> Use actual energy consumption data from your
              customer's processing facility. This is the most accurate method when data is available.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Product Type (optional)</label>
            <select
              value={productType}
              onChange={(e) => setProductType(e.target.value)}
              className={selectClass}
            >
              <option value="">Select product type...</option>
              {PRODUCT_TYPES.map((pt) => (
                <option key={pt.key} value={pt.key}>{pt.label}</option>
              ))}
            </select>
          </div>

          <Input
            label="Processing Energy (kWh)"
            type="number"
            step="1"
            min="0"
            value={processingEnergy}
            onChange={(e) => setProcessingEnergy(e.target.value)}
            placeholder="e.g., 150000"
            hint="Total electricity consumed in processing your products"
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
              placeholder="e.g., 500000"
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
            Uses EEIO manufacturing sector factors. Less accurate than product-specific or site-specific methods.
          </p>
        </div>
      )}

      {/* Optional Fields */}
      {method && (
        <div className="space-y-4">
          <Input
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., Steel billets for automotive casting"
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Customer/Processor (optional)"
              value={customer}
              onChange={(e) => setCustomer(e.target.value)}
              placeholder="e.g., Foundry Inc."
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
