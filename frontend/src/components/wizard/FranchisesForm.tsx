'use client';

/**
 * FranchisesForm - Category 3.14 Franchises
 *
 * Emissions from operation of franchises (reported by franchisor).
 *
 * Supports 3 methods per GHG Protocol:
 * 1. Average - Based on franchise type and count/floor area
 * 2. Franchise-Specific - Actual energy/fuel data from franchise locations
 * 3. Spend - Based on franchise revenue (revenue-based)
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
  Store,
  Coffee,
  Utensils,
  Building,
  Hotel,
  Zap,
  Info,
} from 'lucide-react';

// =============================================================================
// FRANCHISES DATA DEFINITIONS
// =============================================================================

type FranchiseMethod = 'average' | 'franchise-specific' | 'spend';

// Franchise Types with emission factor estimates
const FRANCHISE_TYPES = [
  { key: 'restaurant', label: 'Restaurant', icon: Utensils, ef: 50000, unit: 'unit' },
  { key: 'fastfood', label: 'Fast Food', icon: Utensils, ef: 35000, unit: 'unit' },
  { key: 'cafe', label: 'Cafe/Coffee Shop', icon: Coffee, ef: 20000, unit: 'unit' },
  { key: 'retail', label: 'Retail Store', icon: Store, ef: 200, unit: 'm2' },
  { key: 'convenience', label: 'Convenience Store', icon: Store, ef: 25000, unit: 'unit' },
  { key: 'hotel', label: 'Hotel', icon: Hotel, ef: 3500, unit: 'room' },
  { key: 'gym', label: 'Gym/Fitness Center', icon: Building, ef: 150, unit: 'm2' },
  { key: 'gasstation', label: 'Gas Station', icon: Building, ef: 100000, unit: 'unit' },
  { key: 'service', label: 'Service Business', icon: Building, ef: 15000, unit: 'unit' },
  { key: 'generic', label: 'Other/Generic', icon: Building, ef: 30000, unit: 'unit' },
];

const ENERGY_TYPES = [
  { key: 'electricity', label: 'Electricity', ef: 0.436, unit: 'kWh' },
  { key: 'gas', label: 'Natural Gas', ef: 0.184, unit: 'kWh' },
  { key: 'fuel', label: 'Diesel/Petrol', ef: 2.68, unit: 'liters' },
];

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '\u20AC', name: 'Euro' },
  { code: 'GBP', symbol: '\u00A3', name: 'British Pound' },
  { code: 'ILS', symbol: '\u20AA', name: 'Israeli Shekel' },
];

// Spend emission factor (kg CO2e per USD of franchise revenue)
const SPEND_EF = 0.20;

interface FranchisesFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function FranchisesForm({ periodId, onSuccess }: FranchisesFormProps) {
  const goBack = useWizardStore((s) => s.goBack);
  const resetWizard = useWizardStore((s) => s.reset);
  const createActivity = useCreateActivity(periodId);

  // Method selection
  const [method, setMethod] = useState<FranchiseMethod | ''>('');

  // Average method fields
  const [franchiseType, setFranchiseType] = useState('restaurant');
  const [numLocations, setNumLocations] = useState('');
  const [floorArea, setFloorArea] = useState('');
  const [numRooms, setNumRooms] = useState('');

  // Franchise-specific method fields
  const [energyType, setEnergyType] = useState('electricity');
  const [energyConsumption, setEnergyConsumption] = useState('');

  // Spend method fields
  const [franchiseRevenue, setFranchiseRevenue] = useState('');
  const [currency, setCurrency] = useState('USD');

  // Common fields
  const [description, setDescription] = useState('');
  const [franchiseeName, setFranchiseeName] = useState('');
  const [activityDate, setActivityDate] = useState(new Date().toISOString().split('T')[0]);

  // Get current franchise type data
  const currentFranchiseType = useMemo(() => {
    return FRANCHISE_TYPES.find(f => f.key === franchiseType);
  }, [franchiseType]);

  // Determine if this franchise uses area, rooms, or units
  const franchiseUnitType = useMemo(() => {
    if (!currentFranchiseType) return 'unit';
    return currentFranchiseType.unit;
  }, [currentFranchiseType]);

  // Preview calculation
  const preview = useMemo(() => {
    if (!method) return null;

    if (method === 'average') {
      const franchise = FRANCHISE_TYPES.find(f => f.key === franchiseType);
      if (!franchise) return null;

      let quantity = 0;
      let unitLabel = franchise.unit;

      if (franchise.unit === 'unit') {
        quantity = parseFloat(numLocations) || 0;
      } else if (franchise.unit === 'm2') {
        quantity = parseFloat(floorArea) || 0;
      } else if (franchise.unit === 'room') {
        quantity = parseFloat(numRooms) || 0;
      }

      if (!quantity) return null;

      const ef = franchise.ef;
      const co2e = quantity * ef;

      return {
        activityKey: `franchise_${franchiseType}_${franchise.unit}`,
        quantity,
        unit: unitLabel,
        co2e,
        formula: `${quantity.toLocaleString()} ${unitLabel}${quantity !== 1 ? 's' : ''} x ${ef.toLocaleString()} kg CO2e/${unitLabel} = ${co2e.toLocaleString()} kg CO2e`,
        efSource: 'EPA/DEFRA 2024',
      };
    }

    if (method === 'franchise-specific') {
      const energy = parseFloat(energyConsumption) || 0;
      if (!energy) return null;

      const energyData = ENERGY_TYPES.find(e => e.key === energyType);
      if (!energyData) return null;

      const ef = energyData.ef;
      const co2e = energy * ef;

      const activityKey = energyType === 'gas'
        ? 'franchise_gas_kwh'
        : energyType === 'fuel'
        ? 'franchise_fuel_liters'
        : 'franchise_electricity_kwh';

      return {
        activityKey,
        quantity: energy,
        unit: energyData.unit,
        co2e,
        formula: `${energy.toLocaleString()} ${energyData.unit} x ${ef.toFixed(3)} kg CO2e/${energyData.unit} = ${co2e.toFixed(2)} kg CO2e`,
        efSource: energyType === 'fuel' ? 'DEFRA 2024' : 'IEA 2024',
      };
    }

    if (method === 'spend') {
      const revenue = parseFloat(franchiseRevenue) || 0;
      if (!revenue) return null;

      const co2e = revenue * SPEND_EF;
      return {
        activityKey: 'franchise_spend_revenue',
        quantity: revenue,
        unit: currency,
        co2e,
        formula: `${currency} ${revenue.toLocaleString()} x ${SPEND_EF} kg CO2e/${currency} = ${co2e.toFixed(2)} kg CO2e`,
        efSource: 'EEIO 2024',
      };
    }

    return null;
  }, [method, franchiseType, numLocations, floorArea, numRooms, energyType, energyConsumption, franchiseRevenue, currency]);

  // Handle save
  const handleSave = async (addAnother: boolean = false) => {
    if (!preview) return;

    const franchiseLabel = currentFranchiseType?.label || franchiseType;

    try {
      await createActivity.mutateAsync({
        scope: 3,
        category_code: '3.14',
        activity_key: preview.activityKey,
        description: description || `Franchise: ${franchiseLabel}${franchiseeName ? ` (${franchiseeName})` : ''}`,
        quantity: preview.quantity,
        unit: preview.unit,
        activity_date: activityDate,
      });

      if (addAnother) {
        // Reset form but keep method
        setNumLocations('');
        setFloorArea('');
        setNumRooms('');
        setEnergyConsumption('');
        setFranchiseRevenue('');
        setDescription('');
        setFranchiseeName('');
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
          <Store className="w-5 h-5 text-orange-600" />
          3.14 Franchises
        </h2>
        <p className="text-sm text-foreground-muted">
          Emissions from the operation of franchises (reported by franchisor)
        </p>
      </div>

      {/* Info box */}
      <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
        <div className="flex gap-3">
          <Info className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-orange-800">
            <p className="font-medium mb-1">What to report:</p>
            <ul className="list-disc list-inside space-y-1 text-orange-700">
              <li>You are the FRANCHISOR (brand owner) reporting franchisee emissions</li>
              <li>Include all franchise locations operating under your brand</li>
              <li>Can use average data per location or actual energy data</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Method Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-medium">Step 1: Select Calculation Method</label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: 'average' as FranchiseMethod, label: 'Average', desc: 'Type & count', icon: <Store className="w-6 h-6" />, color: 'border-green-500 bg-green-50' },
            { value: 'franchise-specific' as FranchiseMethod, label: 'Specific', desc: 'Energy data', icon: <Zap className="w-6 h-6" />, color: 'border-amber-500 bg-amber-50' },
            { value: 'spend' as FranchiseMethod, label: 'Spend', desc: 'Revenue', icon: <span className="text-2xl">$</span>, color: 'border-blue-500 bg-blue-50' },
          ].map((m) => (
            <button
              key={m.value}
              onClick={() => {
                setMethod(m.value);
                setFranchiseType('restaurant');
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
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Franchise Type</label>
              <select
                value={franchiseType}
                onChange={(e) => setFranchiseType(e.target.value)}
                className={selectClass}
              >
                {FRANCHISE_TYPES.map((ft) => (
                  <option key={ft.key} value={ft.key}>{ft.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                {franchiseUnitType === 'unit' ? 'Number of Locations' :
                 franchiseUnitType === 'm2' ? 'Total Floor Area (m2)' :
                 'Number of Rooms'}
              </label>
              {franchiseUnitType === 'unit' ? (
                <Input
                  type="number"
                  min="0"
                  step="1"
                  value={numLocations}
                  onChange={(e) => setNumLocations(e.target.value)}
                  placeholder="Enter number of franchise locations..."
                />
              ) : franchiseUnitType === 'm2' ? (
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={floorArea}
                  onChange={(e) => setFloorArea(e.target.value)}
                  placeholder="Enter total floor area..."
                />
              ) : (
                <Input
                  type="number"
                  min="0"
                  step="1"
                  value={numRooms}
                  onChange={(e) => setNumRooms(e.target.value)}
                  placeholder="Enter total number of rooms..."
                />
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Description (optional)
              </label>
              <Input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g., All franchise locations in North America"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Franchisee Name (optional)
              </label>
              <Input
                type="text"
                value={franchiseeName}
                onChange={(e) => setFranchiseeName(e.target.value)}
                placeholder="e.g., Regional franchisee group"
              />
            </div>
          </div>
        </div>
      )}

      {/* Franchise-Specific Method Fields */}
      {method === 'franchise-specific' && (
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
                Energy Consumption ({ENERGY_TYPES.find(e => e.key === energyType)?.unit})
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
                Description
              </label>
              <Input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g., Electricity from all franchise locations"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Franchisee Name (optional)
              </label>
              <Input
                type="text"
                value={franchiseeName}
                onChange={(e) => setFranchiseeName(e.target.value)}
                placeholder="e.g., Franchise group with energy data"
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
                Total Franchise Revenue
              </label>
              <Input
                type="number"
                min="0"
                step="0.01"
                value={franchiseRevenue}
                onChange={(e) => setFranchiseRevenue(e.target.value)}
                placeholder="Enter total franchise revenue..."
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
              placeholder="e.g., Total revenue from all franchise operations"
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
