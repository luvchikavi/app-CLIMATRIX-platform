'use client';

import { useWizardStore } from '@/stores/wizard';
import { Calculator, Eye, Info, Database, Save, Plus, Loader2, DollarSign, Scale } from 'lucide-react';
import { useState, useEffect } from 'react';
import { Button, Input } from '@/components/ui';
import { formatCO2e } from '@/lib/utils';
import { useCreateActivity } from '@/hooks/useEmissions';
import { api, SpendConversionResult } from '@/lib/api';

type InputMethod = 'quantity' | 'spend';

interface PreviewResult {
  co2e_kg: number;
  formula: string;
  factor_value: number;
  factor_source: string;
  factor_unit: string;
}

interface DetailsFormProps {
  periodId: string;
  onSuccess?: () => void;
}

// Currency options
const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'ILS', symbol: '₪', name: 'Israeli Shekel' },
];

// Map activity_key to fuel_type for spend conversion
// ALL Scope 1 fuels should have spend option
const FUEL_TYPE_MAP: Record<string, string> = {
  // =============================================
  // SCOPE 1.1 - STATIONARY COMBUSTION
  // =============================================
  // Diesel
  'diesel_volume': 'diesel',
  'diesel_liters': 'diesel',
  'diesel_stationary': 'diesel',
  'diesel_gas_oil': 'diesel',
  'gas_oil_liters': 'diesel',
  // Petrol/Gasoline
  'petrol_volume': 'petrol',
  'petrol_liters': 'petrol',
  'petrol_stationary': 'petrol',
  'gasoline_volume': 'petrol',
  'gasoline_liters': 'petrol',
  // Natural Gas
  'natural_gas_volume': 'natural_gas',
  'natural_gas_kwh': 'natural_gas',
  'natural_gas_stationary': 'natural_gas',
  'natural_gas_m3': 'natural_gas',
  // LPG
  'lpg_volume': 'lpg',
  'lpg_liters': 'lpg',
  'lpg_kg': 'lpg',
  'lpg_mass': 'lpg',
  // Heating/Burning Oil
  'heating_oil_volume': 'heating_oil',
  'heating_oil_liters': 'heating_oil',
  'burning_oil_liters': 'heating_oil',
  'burning_oil_volume': 'heating_oil',
  'fuel_oil_liters': 'heating_oil',
  'fuel_oil_volume': 'heating_oil',
  // Coal
  'coal_kg': 'coal',
  'coal_tonnes': 'coal',
  'coal_industrial': 'coal',
  'coal_mass': 'coal',

  // =============================================
  // SCOPE 1.2 - MOBILE COMBUSTION (Fuel-based)
  // Note: km-based activities don't support spend (need fuel efficiency)
  // =============================================
  'diesel_mobile': 'diesel',
  'diesel_mobile_liters': 'diesel',
  'petrol_mobile': 'petrol',
  'petrol_mobile_liters': 'petrol',
  'gasoline_mobile': 'petrol',

  // =============================================
  // SCOPE 1.3 - FUGITIVE EMISSIONS (Refrigerants)
  // =============================================
  'refrigerant_r134a': 'refrigerant_r134a',
  'refrigerant_r410a': 'refrigerant_r410a',
  'refrigerant_r32': 'refrigerant_r32',
  'refrigerant_r404a': 'refrigerant_r404a',
  'refrigerant_co2': 'refrigerant_co2',
  'refrigerant_hfc23': 'refrigerant_hfc23',
  'r134a': 'refrigerant_r134a',
  'r410a': 'refrigerant_r410a',
  'r32': 'refrigerant_r32',
  'r404a': 'refrigerant_r404a',
  'hfc23': 'refrigerant_hfc23',
  'hfc_23': 'refrigerant_hfc23',

  // =============================================
  // SCOPE 1.4 - PROCESS EMISSIONS (Industrial)
  // =============================================
  // Cement & Clinker
  'cement_production': 'cement_production',
  'clinker_production': 'clinker_production',
  // Lime
  'quicklite_ite_production': 'quicklime_production',
  'quicklime_production': 'quicklime_production',
  'dolomitic_lime_production': 'dolomitic_lime_production',
  // Glass
  'glass_production': 'glass_production',
  // Ammonia
  'ammonia_production': 'ammonia_production',
  // Iron & Steel
  'iron_steel_production': 'iron_steel_production',
  'steel_eaf_production': 'steel_eaf_production',
  // Aluminum
  'aluminum_primary_production': 'aluminum_primary_production',
  // Chemicals
  'nitric_acid_production': 'nitric_acid_production',
  'adipic_acid_production': 'adipic_acid_production',
  // Hydrogen
  'hydrogen_smr_production': 'hydrogen_smr_production',
  // Petrochemicals
  'ethylene_production': 'ethylene_production',

  // =============================================
  // SCOPE 2 - PURCHASED ELECTRICITY
  // =============================================
  'electricity_kwh': 'electricity',
  'electricity_uk': 'electricity',
  'electricity_us': 'electricity',
  'electricity_il': 'electricity',
  'electricity_global': 'electricity',
};

export function DetailsForm({ periodId, onSuccess }: DetailsFormProps) {
  const selectedFactor = useWizardStore((s) => s.selectedFactor);
  const entry = useWizardStore((s) => s.entry);
  const setEntryField = useWizardStore((s) => s.setEntryField);
  const addEntry = useWizardStore((s) => s.addEntry);
  const reset = useWizardStore((s) => s.reset);
  const entries = useWizardStore((s) => s.entries);
  const getTotalCO2e = useWizardStore((s) => s.getTotalCO2e);

  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Spend-based input state
  const [inputMethod, setInputMethod] = useState<InputMethod>('quantity');
  const [spendAmount, setSpendAmount] = useState<number>(0);
  const [currency, setCurrency] = useState<string>('USD');
  const [spendConversion, setSpendConversion] = useState<SpendConversionResult | null>(null);
  const [isConverting, setIsConverting] = useState(false);
  const [conversionError, setConversionError] = useState<string | null>(null);

  // Price state - always editable
  const [unitPrice, setUnitPrice] = useState<number>(0);
  const [systemPrice, setSystemPrice] = useState<number | null>(null);
  const [priceSource, setPriceSource] = useState<string>('');
  const [isLoadingPrice, setIsLoadingPrice] = useState(false);

  const createActivity = useCreateActivity(periodId);

  // Get fuel type for the selected activity
  const getFuelType = (): string | null => {
    if (!entry.activity_key) return null;
    return FUEL_TYPE_MAP[entry.activity_key] || null;
  };

  // Check if spend-based input is available for this activity
  const canUseSpendMethod = getFuelType() !== null;

  // Fetch system price when spend mode is activated or currency changes
  useEffect(() => {
    if (inputMethod !== 'spend') {
      return;
    }

    const fuelType = getFuelType();
    if (!fuelType) {
      setSystemPrice(null);
      setPriceSource('');
      return;
    }

    const fetchSystemPrice = async () => {
      setIsLoadingPrice(true);
      setConversionError(null);

      // Remember old system price to check if user modified the price
      const oldSystemPrice = systemPrice;

      try {
        const prices = await api.getFuelPrices(fuelType, selectedFactor?.region || 'Global');
        // Find price matching currency, or fallback to USD
        let priceData = prices.find(p => p.currency === currency);
        if (!priceData) {
          priceData = prices.find(p => p.currency === 'USD');
        }

        if (priceData) {
          setSystemPrice(priceData.price_per_unit);
          setPriceSource(priceData.source);
          // Set unitPrice if:
          // 1. It's 0 (initial state)
          // 2. It equals the old system price (user hasn't modified it)
          if (unitPrice === 0 || unitPrice === oldSystemPrice) {
            setUnitPrice(priceData.price_per_unit);
          }
        } else {
          setSystemPrice(null);
          setPriceSource('');
        }
      } catch (error) {
        setSystemPrice(null);
        setPriceSource('');
      } finally {
        setIsLoadingPrice(false);
      }
    };

    fetchSystemPrice();
  }, [inputMethod, currency, entry.activity_key, selectedFactor?.region]);

  // Calculate quantity when spend amount or price changes
  useEffect(() => {
    if (inputMethod !== 'spend' || !spendAmount || spendAmount <= 0 || !unitPrice || unitPrice <= 0) {
      setSpendConversion(null);
      return;
    }

    const fuelType = getFuelType();
    const unit = selectedFactor?.activity_unit || 'units';
    const calculatedQty = spendAmount / unitPrice;
    const isCustomPrice = systemPrice !== null && unitPrice !== systemPrice;

    setSpendConversion({
      fuel_type: fuelType || 'custom',
      spend_amount: spendAmount,
      currency: currency,
      fuel_price: unitPrice,
      price_unit: `${currency}/${unit}`,
      price_source: isCustomPrice ? 'Custom price (user provided)' : priceSource,
      calculated_quantity: Math.round(calculatedQty * 100) / 100,
      quantity_unit: unit,
      formula: `${spendAmount} ${currency} ÷ ${unitPrice} ${currency}/${unit} = ${(calculatedQty).toFixed(2)} ${unit}`,
    });
    setEntryField('quantity', Math.round(calculatedQty * 100) / 100);
    setConversionError(null);
  }, [inputMethod, spendAmount, unitPrice, currency, selectedFactor?.activity_unit, systemPrice, priceSource]);

  if (!selectedFactor) return null;

  const handlePreview = () => {
    if (entry.quantity && selectedFactor) {
      // Use the ACTUAL emission factor from the selected factor
      const factorValue = selectedFactor.co2e_factor || 0;
      const co2e = entry.quantity * factorValue;

      setPreview({
        co2e_kg: co2e,
        formula: `${entry.quantity} ${selectedFactor.activity_unit} x ${factorValue} ${selectedFactor.factor_unit || 'kg CO2e/' + selectedFactor.activity_unit} = ${co2e.toFixed(2)} kg CO2e`,
        factor_value: factorValue,
        factor_source: selectedFactor.source || 'Unknown',
        factor_unit: selectedFactor.factor_unit || `kg CO2e/${selectedFactor.activity_unit}`,
      });
    }
  };

  // FIX-1: Date is no longer required for annual reporting
  const canProceed =
    entry.description &&
    entry.quantity &&
    entry.quantity > 0;

  // Calculate preview emission using actual factor
  const previewCO2e = selectedFactor && entry.quantity
    ? entry.quantity * (selectedFactor.co2e_factor || 0)
    : 0;

  // Save single activity directly
  const handleSave = async () => {
    // Debug: Log current state
    console.log('[Wizard Save] Attempting save with:', {
      canProceed,
      hasSelectedFactor: !!selectedFactor,
      entry,
    });

    if (!canProceed) {
      console.warn('[Wizard Save] Cannot proceed - missing description or quantity');
      setSaveError('Please fill in description and quantity');
      return;
    }

    if (!selectedFactor) {
      console.warn('[Wizard Save] No emission factor selected');
      setSaveError('No emission factor selected. Please go back and select an activity.');
      return;
    }

    setIsSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      const activityDate = entry.activity_date || new Date().toISOString().split('T')[0];

      const payload = {
        scope: entry.scope as 1 | 2 | 3,
        category_code: entry.category_code!,
        activity_key: entry.activity_key!,
        description: entry.description!,
        quantity: entry.quantity!,
        unit: entry.unit!,
        activity_date: activityDate,
      };

      console.log('[Wizard Save] Sending to API:', payload);

      await createActivity.mutateAsync(payload);

      console.log('[Wizard Save] Success!');
      setSaveSuccess(true);

      // Reset and close after brief success message
      setTimeout(() => {
        reset();
        onSuccess?.();
      }, 1500);
    } catch (error) {
      console.error('[Wizard Save] Error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to save activity';
      setSaveError(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  // Add to queue and continue adding
  const handleSaveAndAddAnother = async () => {
    console.log('[Wizard Save & Add] Attempting with:', {
      canProceed,
      hasSelectedFactor: !!selectedFactor,
      entry,
    });

    if (!canProceed) {
      setSaveError('Please fill in description and quantity');
      return;
    }

    if (!selectedFactor) {
      setSaveError('No emission factor selected. Please go back and select an activity.');
      return;
    }

    setIsSaving(true);
    setSaveError(null);

    try {
      const activityDate = entry.activity_date || new Date().toISOString().split('T')[0];

      const payload = {
        scope: entry.scope as 1 | 2 | 3,
        category_code: entry.category_code!,
        activity_key: entry.activity_key!,
        description: entry.description!,
        quantity: entry.quantity!,
        unit: entry.unit!,
        activity_date: activityDate,
      };

      console.log('[Wizard Save & Add] Sending to API:', payload);

      await createActivity.mutateAsync(payload);

      console.log('[Wizard Save & Add] Success! Adding entry and resetting form.');

      // Add to local entries list for display
      addEntry();

      // Clear form but keep wizard open
      setPreview(null);
    } catch (error) {
      console.error('[Wizard Save & Add] Error:', error);
      setSaveError(error instanceof Error ? error.message : 'Failed to save activity');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-foreground">Enter Details</h2>
        <p className="text-foreground-muted">{selectedFactor.display_name}</p>
      </div>

      {/* Activity info with emission factor details */}
      <div className="p-4 bg-info/10 border border-info/20 rounded-lg space-y-2">
        <div className="flex items-center gap-2">
          <Calculator className="w-5 h-5 text-info" />
          <span className="font-medium text-info">
            Unit: {selectedFactor.activity_unit}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-info/70" />
          <span className="text-sm text-info/80">
            Emission Factor: <strong>{selectedFactor.co2e_factor}</strong> {selectedFactor.factor_unit || `kg CO2e/${selectedFactor.activity_unit}`}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-info/70" />
          <span className="text-sm text-info/80">
            Source: <strong>{selectedFactor.source || 'DEFRA'}</strong> {selectedFactor.year ? `(${selectedFactor.year})` : ''} | Region: {selectedFactor.region || 'Global'}
          </span>
        </div>
      </div>

      {/* Form fields */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-foreground mb-1.5">
            Description
          </label>
          <Input
            type="text"
            value={entry.description || ''}
            onChange={(e) => setEntryField('description', e.target.value)}
            placeholder="e.g., Office building electricity, Company fleet"
          />
        </div>

        {/* Input Method Toggle */}
        {canUseSpendMethod && (
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              How do you want to enter data?
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setInputMethod('quantity');
                  setSpendConversion(null);
                  setUnitPrice(0);
                  setSystemPrice(null);
                }}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition-colors ${
                  inputMethod === 'quantity'
                    ? 'bg-primary text-white border-primary'
                    : 'bg-background border-border hover:bg-background-muted'
                }`}
              >
                <Scale className="w-4 h-4" />
                <span className="font-medium">Physical Quantity</span>
              </button>
              <button
                onClick={() => {
                  setInputMethod('spend');
                  setUnitPrice(0);  // Will be populated by useEffect with system price
                }}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition-colors ${
                  inputMethod === 'spend'
                    ? 'bg-primary text-white border-primary'
                    : 'bg-background border-border hover:bg-background-muted'
                }`}
              >
                <DollarSign className="w-4 h-4" />
                <span className="font-medium">Money Spent</span>
              </button>
            </div>
          </div>
        )}

        {/* Quantity Input (default method) */}
        {inputMethod === 'quantity' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Quantity
              </label>
              <Input
                type="number"
                value={entry.quantity || ''}
                onChange={(e) => setEntryField('quantity', parseFloat(e.target.value) || 0)}
                placeholder="0"
                min={0}
                step={0.01}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Unit
              </label>
              <Input
                type="text"
                value={selectedFactor.activity_unit}
                disabled
                className="bg-background-muted"
              />
            </div>
          </div>
        )}

        {/* Spend Input (alternative method) */}
        {inputMethod === 'spend' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Amount Spent
                </label>
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
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Currency
                </label>
                <select
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  className="w-full h-10 px-3 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  {CURRENCIES.map((c) => (
                    <option key={c.code} value={c.code}>
                      {c.symbol} {c.code} - {c.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Price Input - Always Editable */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Price per {selectedFactor?.activity_unit || 'unit'} ({currency})
              </label>
              <div className="relative">
                <Input
                  type="number"
                  value={unitPrice || ''}
                  onChange={(e) => setUnitPrice(parseFloat(e.target.value) || 0)}
                  placeholder={isLoadingPrice ? 'Loading...' : `Enter price in ${currency}`}
                  min={0}
                  step={0.01}
                  disabled={isLoadingPrice}
                />
                {isLoadingPrice && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    <Loader2 className="w-4 h-4 animate-spin text-foreground-muted" />
                  </div>
                )}
              </div>
              {/* Price source info */}
              {systemPrice !== null && (
                <div className="mt-1.5 text-xs text-foreground-muted">
                  {unitPrice === systemPrice ? (
                    <span>System price from: {priceSource}</span>
                  ) : (
                    <span>
                      System price: {systemPrice} {currency}/{selectedFactor?.activity_unit}
                      <button
                        onClick={() => setUnitPrice(systemPrice)}
                        className="ml-2 text-primary hover:underline"
                      >
                        Reset to system price
                      </button>
                    </span>
                  )}
                </div>
              )}
              {systemPrice === null && !isLoadingPrice && getFuelType() && (
                <div className="mt-1.5 text-xs text-warning">
                  No system price available for this currency. Enter your price manually.
                </div>
              )}
            </div>

            {/* Conversion Result */}
            {isConverting && (
              <div className="flex items-center gap-2 text-foreground-muted">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Converting...</span>
              </div>
            )}

            {conversionError && (
              <div className="p-3 bg-error/10 border border-error/20 rounded-lg text-error text-sm">
                {conversionError}
              </div>
            )}

            {spendConversion && !isConverting && (
              <div className="p-4 bg-success/10 border border-success/20 rounded-lg space-y-2">
                <h4 className="font-medium text-success flex items-center gap-2">
                  <Calculator className="w-4 h-4" />
                  Conversion Result
                </h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-foreground-muted">Fuel Price:</span>
                    <p className="font-semibold">{spendConversion.fuel_price} {spendConversion.price_unit}</p>
                  </div>
                  <div>
                    <span className="text-foreground-muted">Calculated Quantity:</span>
                    <p className="font-semibold text-lg">{spendConversion.calculated_quantity.toLocaleString()} {spendConversion.quantity_unit}</p>
                  </div>
                </div>
                <p className="text-xs text-success/80 font-mono">{spendConversion.formula}</p>
                <p className="text-xs text-foreground-muted">
                  Source: {spendConversion.price_source}
                </p>
              </div>
            )}
          </div>
        )}

        {/* FIX-1: Removed Activity Date field - not needed for annual reporting */}
      </div>

      {/* Preview with emission factor details */}
      {preview && (
        <div className="p-4 bg-success/10 border border-success/20 rounded-lg space-y-2">
          <h4 className="font-medium text-success">Estimated Emissions</h4>
          <p className="text-2xl font-bold text-success">
            {formatCO2e(preview.co2e_kg)}
          </p>
          <p className="text-sm text-success/80 font-mono">{preview.formula}</p>
          <div className="pt-2 border-t border-success/20 mt-2">
            <p className="text-xs text-success/70">
              Factor: {preview.factor_value} {preview.factor_unit} | Source: {preview.factor_source}
            </p>
          </div>
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
          <p className="text-success/80 mt-1">
            Emissions: {formatCO2e(previewCO2e)}
          </p>
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
            variant="outline"
            onClick={handlePreview}
            disabled={!entry.quantity || isSaving}
            leftIcon={<Eye className="w-4 h-4" />}
          >
            Preview Calculation
          </Button>
          <Button
            variant="outline"
            onClick={handleSaveAndAddAnother}
            disabled={!canProceed || isSaving}
            leftIcon={isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          >
            Save & Add Another
          </Button>
          <Button
            variant="primary"
            onClick={handleSave}
            disabled={!canProceed || isSaving}
            leftIcon={isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          >
            Save
          </Button>
        </div>
      )}
    </div>
  );
}
