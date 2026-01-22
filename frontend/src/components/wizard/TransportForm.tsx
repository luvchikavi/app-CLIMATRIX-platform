'use client';

/**
 * TransportForm - Category 3.4 Upstream Transport & Distribution
 *
 * Supports 3 methods per GHG Protocol:
 * 1. Distance - Weight × distance based (tonne-km)
 * 2. Spend - Invoice amount (USD)
 * 3. Supplier-Specific - User provides their own emission factor
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
  Truck,
  Ship,
  Plane,
  Train,
  Info,
  Ruler,
  DollarSign,
  ClipboardList,
} from 'lucide-react';

// =============================================================================
// TRANSPORT DATA DEFINITIONS
// =============================================================================

type TransportMethod = 'distance' | 'spend' | 'supplier-specific';

// Distance-based transport modes
const DISTANCE_MODES = [
  { key: 'road-hgv', label: 'Road - HGV (Heavy Goods Vehicle)', activityKey: 'road_freight_hgv', efEstimate: 0.10460 },
  { key: 'road-van', label: 'Road - Van/LGV', activityKey: 'road_freight_van', efEstimate: 0.58946 },
  { key: 'rail', label: 'Rail Freight', activityKey: 'rail_freight', efEstimate: 0.02780 },
  { key: 'sea-container', label: 'Sea - Container Ship', activityKey: 'sea_freight_container', efEstimate: 0.01612 },
  { key: 'sea-bulk', label: 'Sea - Bulk Carrier', activityKey: 'sea_freight_bulk', efEstimate: 0.00354 },
  { key: 'sea-tanker', label: 'Sea - Tanker', activityKey: 'sea_freight_tanker', efEstimate: 0.00509 },
  { key: 'air', label: 'Air Freight', activityKey: 'air_freight', efEstimate: 1.12820 },
  { key: 'air-long', label: 'Air Freight - Long Haul (>3700km)', activityKey: 'air_freight_long', efEstimate: 0.60200 },
  { key: 'air-short', label: 'Air Freight - Short Haul (<3700km)', activityKey: 'air_freight_short', efEstimate: 1.12820 },
];

// Spend-based transport modes
const SPEND_MODES = [
  { key: 'road', label: 'Road Transport', activityKey: 'freight_spend_road', efEstimate: 0.42 },
  { key: 'rail', label: 'Rail Transport', activityKey: 'freight_spend_rail', efEstimate: 0.28 },
  { key: 'sea', label: 'Sea Transport', activityKey: 'freight_spend_sea', efEstimate: 0.18 },
  { key: 'air', label: 'Air Transport', activityKey: 'freight_spend_air', efEstimate: 1.85 },
];

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'ILS', symbol: '₪', name: 'Israeli Shekel' },
];

// =============================================================================
// COMPONENT
// =============================================================================

interface TransportFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function TransportForm({ periodId, onSuccess }: TransportFormProps) {
  const reset = useWizardStore((s) => s.reset);
  const goBack = useWizardStore((s) => s.goBack);
  const createActivity = useCreateActivity(periodId);

  // Form state
  const [method, setMethod] = useState<TransportMethod | ''>('');
  const [transportMode, setTransportMode] = useState('');
  const [weightTonnes, setWeightTonnes] = useState('');
  const [distanceKm, setDistanceKm] = useState('');
  const [spendAmount, setSpendAmount] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [supplierEf, setSupplierEf] = useState('');
  const [description, setDescription] = useState('');
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [activityDate, setActivityDate] = useState(new Date().toISOString().split('T')[0]);

  // Get selected mode details
  const selectedDistanceMode = useMemo(() =>
    DISTANCE_MODES.find(m => m.key === transportMode),
    [transportMode]
  );

  const selectedSpendMode = useMemo(() =>
    SPEND_MODES.find(m => m.key === transportMode),
    [transportMode]
  );

  // Calculate tonne-km for distance method
  const tonneKm = useMemo(() => {
    if (method !== 'distance' && method !== 'supplier-specific') return 0;
    const weight = parseFloat(weightTonnes) || 0;
    const distance = parseFloat(distanceKm) || 0;
    return weight * distance;
  }, [method, weightTonnes, distanceKm]);

  // Preview calculation
  const preview = useMemo(() => {
    if (!method) return null;

    if (method === 'distance') {
      if (!transportMode || !tonneKm) return null;
      const mode = selectedDistanceMode;
      if (!mode) return null;
      const co2e = tonneKm * mode.efEstimate;
      return {
        activityKey: mode.activityKey,
        quantity: tonneKm,
        unit: 'tonne-km',
        co2e,
        formula: `${tonneKm.toFixed(2)} tonne-km × ${mode.efEstimate.toFixed(5)} kg/tonne-km = ${co2e.toFixed(2)} kg CO2e`,
        efSource: 'DEFRA 2024',
      };
    }

    if (method === 'spend') {
      const amount = parseFloat(spendAmount) || 0;
      if (!transportMode || !amount) return null;
      const mode = selectedSpendMode;
      if (!mode) return null;
      const co2e = amount * mode.efEstimate;
      return {
        activityKey: mode.activityKey,
        quantity: amount,
        unit: currency,
        co2e,
        formula: `${currency} ${amount.toLocaleString()} × ${mode.efEstimate.toFixed(2)} kg/${currency} = ${co2e.toFixed(2)} kg CO2e`,
        efSource: 'EEIO 2024',
      };
    }

    if (method === 'supplier-specific') {
      const ef = parseFloat(supplierEf) || 0;
      if (!ef || !tonneKm) return null;
      const co2e = tonneKm * ef;
      return {
        activityKey: 'supplier_specific_3_4',
        quantity: tonneKm,
        unit: 'tonne-km',
        co2e,
        formula: `${tonneKm.toFixed(2)} tonne-km × ${ef.toFixed(5)} kg/tonne-km = ${co2e.toFixed(2)} kg CO2e`,
        efSource: 'User-provided (Supplier)',
        supplierEf: ef,
      };
    }

    return null;
  }, [method, transportMode, tonneKm, spendAmount, currency, supplierEf, selectedDistanceMode, selectedSpendMode]);

  // Build description
  const fullDescription = useMemo(() => {
    const parts = [description];
    if (origin && destination) {
      parts.push(`(${origin} → ${destination})`);
    } else if (origin) {
      parts.push(`(from ${origin})`);
    } else if (destination) {
      parts.push(`(to ${destination})`);
    }
    return parts.filter(Boolean).join(' ');
  }, [description, origin, destination]);

  // Handle save
  const handleSave = async (addAnother: boolean = false) => {
    if (!preview) return;

    try {
      await createActivity.mutateAsync({
        scope: 3,
        category_code: '3.4',
        activity_key: preview.activityKey,
        description: fullDescription || `Transport: ${transportMode}`,
        quantity: preview.quantity,
        unit: preview.unit,
        activity_date: activityDate,
        supplier_ef: preview.supplierEf,
      });

      if (addAnother) {
        // Reset form but keep method
        setTransportMode('');
        setWeightTonnes('');
        setDistanceKm('');
        setSpendAmount('');
        setSupplierEf('');
        setDescription('');
        setOrigin('');
        setDestination('');
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
          <Truck className="w-5 h-5 text-purple-600" />
          3.4 Upstream Transport & Distribution
        </h2>
        <p className="text-sm text-foreground-muted">
          Transport of goods purchased by your organization (inbound logistics)
        </p>
      </div>

      {/* Method Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-medium">Step 1: Select Calculation Method</label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: 'distance' as TransportMethod, label: 'Distance', desc: 'Weight × Distance', Icon: Ruler, color: 'border-purple-500 bg-purple-50' },
            { value: 'spend' as TransportMethod, label: 'Spend', desc: 'Invoice Amount', Icon: DollarSign, color: 'border-green-500 bg-green-50' },
            { value: 'supplier-specific' as TransportMethod, label: 'Supplier', desc: 'Provider EF', Icon: ClipboardList, color: 'border-amber-500 bg-amber-50' },
          ].map((m) => (
            <button
              key={m.value}
              onClick={() => {
                setMethod(m.value);
                setTransportMode('');
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

      {/* Distance Method Fields */}
      {method === 'distance' && (
        <div className="space-y-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Transport Mode</label>
            <select
              value={transportMode}
              onChange={(e) => setTransportMode(e.target.value)}
              className={selectClass}
            >
              <option value="">Select transport mode...</option>
              <optgroup label="Road">
                {DISTANCE_MODES.filter(m => m.key.startsWith('road')).map((mode) => (
                  <option key={mode.key} value={mode.key}>
                    {mode.label} (~{mode.efEstimate.toFixed(4)} kg/t-km)
                  </option>
                ))}
              </optgroup>
              <optgroup label="Rail">
                {DISTANCE_MODES.filter(m => m.key === 'rail').map((mode) => (
                  <option key={mode.key} value={mode.key}>
                    {mode.label} (~{mode.efEstimate.toFixed(4)} kg/t-km)
                  </option>
                ))}
              </optgroup>
              <optgroup label="Sea">
                {DISTANCE_MODES.filter(m => m.key.startsWith('sea')).map((mode) => (
                  <option key={mode.key} value={mode.key}>
                    {mode.label} (~{mode.efEstimate.toFixed(4)} kg/t-km)
                  </option>
                ))}
              </optgroup>
              <optgroup label="Air">
                {DISTANCE_MODES.filter(m => m.key.startsWith('air')).map((mode) => (
                  <option key={mode.key} value={mode.key}>
                    {mode.label} (~{mode.efEstimate.toFixed(4)} kg/t-km)
                  </option>
                ))}
              </optgroup>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Weight (tonnes)"
              type="number"
              step="0.01"
              min="0"
              value={weightTonnes}
              onChange={(e) => setWeightTonnes(e.target.value)}
              placeholder="e.g., 10"
            />
            <Input
              label="Distance (km)"
              type="number"
              step="1"
              min="0"
              value={distanceKm}
              onChange={(e) => setDistanceKm(e.target.value)}
              placeholder="e.g., 500"
            />
          </div>

          {tonneKm > 0 && (
            <div className="p-3 bg-white rounded-lg border">
              <span className="text-sm text-foreground-muted">Calculated: </span>
              <span className="font-medium">{tonneKm.toLocaleString()} tonne-km</span>
              <span className="text-xs text-foreground-muted ml-2">
                ({weightTonnes} tonnes × {distanceKm} km)
              </span>
            </div>
          )}
        </div>
      )}

      {/* Spend Method Fields */}
      {method === 'spend' && (
        <div className="space-y-4 p-4 bg-green-50 rounded-lg border border-green-200">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Transport Mode</label>
            <select
              value={transportMode}
              onChange={(e) => setTransportMode(e.target.value)}
              className={selectClass}
            >
              <option value="">Select transport mode...</option>
              {SPEND_MODES.map((mode) => (
                <option key={mode.key} value={mode.key}>
                  {mode.label} (~{mode.efEstimate.toFixed(2)} kg/USD)
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Spend Amount"
              type="number"
              step="0.01"
              min="0"
              value={spendAmount}
              onChange={(e) => setSpendAmount(e.target.value)}
              placeholder="e.g., 5000"
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
              logistics provider (e.g., from their sustainability report or carbon disclosure).
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Weight (tonnes)"
              type="number"
              step="0.01"
              min="0"
              value={weightTonnes}
              onChange={(e) => setWeightTonnes(e.target.value)}
              placeholder="e.g., 10"
            />
            <Input
              label="Distance (km)"
              type="number"
              step="1"
              min="0"
              value={distanceKm}
              onChange={(e) => setDistanceKm(e.target.value)}
              placeholder="e.g., 500"
            />
          </div>

          <Input
            label="Supplier Emission Factor (kg CO2e per tonne-km)"
            type="number"
            step="0.00001"
            min="0"
            value={supplierEf}
            onChange={(e) => setSupplierEf(e.target.value)}
            placeholder="e.g., 0.085"
            hint="Get this value from your logistics provider's carbon report or EPD"
          />

          {tonneKm > 0 && (
            <div className="p-3 bg-white rounded-lg border">
              <span className="text-sm text-foreground-muted">Calculated: </span>
              <span className="font-medium">{tonneKm.toLocaleString()} tonne-km</span>
            </div>
          )}
        </div>
      )}

      {/* Optional Fields */}
      {method && (
        <div className="space-y-4">
          <Input
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., Raw materials from supplier"
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Origin (optional)"
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
              placeholder="e.g., Shanghai, CN"
            />
            <Input
              label="Destination (optional)"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="e.g., Rotterdam, NL"
            />
          </div>

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
