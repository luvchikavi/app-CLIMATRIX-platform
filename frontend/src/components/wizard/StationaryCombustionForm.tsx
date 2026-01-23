'use client';

/**
 * StationaryCombustionForm - Category 1.1 Stationary Combustion
 *
 * For boilers, furnaces, generators, heaters using:
 * - Natural Gas (volume or energy)
 * - Diesel/Gas Oil
 * - LPG (volume or mass)
 * - Fuel Oil
 * - Coal
 * - Other fuels
 *
 * Supports both quantity-based and spend-based input.
 */

import { useState, useEffect } from 'react';
import { useWizardStore } from '@/stores/wizard';
import { useCreateActivity, useActivityOptions } from '@/hooks/useEmissions';
import { Button, Input } from '@/components/ui';
import { formatCO2e } from '@/lib/utils';
import {
  Calculator,
  Save,
  Plus,
  Loader2,
  DollarSign,
  Scale,
  Info,
  Flame,
  ArrowLeft,
  ChevronDown,
  Search,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { api, SpendConversionResult, EmissionFactor } from '@/lib/api';

type InputMethod = 'quantity' | 'spend';

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'ILS', symbol: '₪', name: 'Israeli Shekel' },
];

// Currency conversion rates to USD (2024 annual averages)
// Source: ECB, OECD
const CURRENCY_RATES_TO_USD: Record<string, number> = {
  USD: 1.00,
  EUR: 1.08,
  GBP: 1.27,
  ILS: 0.27,
  CAD: 0.74,
  AUD: 0.66,
  JPY: 0.0067,
  CNY: 0.14,
  INR: 0.012,
  CHF: 1.13,
  SEK: 0.095,
  NOK: 0.092,
  DKK: 0.145,
};

/**
 * Convert amount from one currency to another via USD
 */
function convertCurrency(amount: number, fromCurrency: string, toCurrency: string): number {
  if (fromCurrency === toCurrency) return amount;

  const fromRate = CURRENCY_RATES_TO_USD[fromCurrency];
  const toRate = CURRENCY_RATES_TO_USD[toCurrency];

  if (!fromRate || !toRate) return amount; // Fallback: no conversion if rate unknown

  // Convert to USD first, then to target currency
  const usdAmount = amount * fromRate;
  return usdAmount / toRate;
}

// Map activity_key to fuel_type for spend conversion
const FUEL_TYPE_MAP: Record<string, string> = {
  'natural_gas_volume': 'natural_gas',
  'natural_gas_kwh': 'natural_gas',
  'natural_gas_m3': 'natural_gas',
  'diesel_volume': 'diesel',
  'diesel_liters': 'diesel',
  'gas_oil_liters': 'diesel',
  'lpg_volume': 'lpg',
  'lpg_liters': 'lpg',
  'lpg_kg': 'lpg',
  'lpg_mass': 'lpg',
  'fuel_oil_liters': 'fuel_oil',
  'fuel_oil_volume': 'fuel_oil',
  'heating_oil_liters': 'heating_oil',
  'heating_oil_volume': 'heating_oil',
  'coal_kg': 'coal',
  'coal_tonnes': 'coal',
  'coal_mass': 'coal',
  'petrol_volume': 'petrol',
  'petrol_liters': 'petrol',
};

interface StationaryCombustionFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function StationaryCombustionForm({ periodId, onSuccess }: StationaryCombustionFormProps) {
  const reset = useWizardStore((s) => s.reset);
  const goBack = useWizardStore((s) => s.goBack);
  const entries = useWizardStore((s) => s.entries);
  const getTotalCO2e = useWizardStore((s) => s.getTotalCO2e);

  // Fetch activity options for 1.1
  const { data: activityOptions, isLoading: isLoadingOptions } = useActivityOptions('1.1');

  // Form state
  const [selectedFactor, setSelectedFactor] = useState<EmissionFactor | null>(null);
  const [description, setDescription] = useState('');
  const [quantity, setQuantity] = useState<number>(0);
  const [inputMethod, setInputMethod] = useState<InputMethod>('quantity');

  // Dropdown state
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Spend state
  const [spendAmount, setSpendAmount] = useState<number>(0);
  const [currency, setCurrency] = useState('USD');
  const [unitPrice, setUnitPrice] = useState<number>(0);
  const [systemPrice, setSystemPrice] = useState<number | null>(null);
  const [priceCurrency, setPriceCurrency] = useState<string>('USD'); // The actual currency of the price
  const [priceSource, setPriceSource] = useState('');
  const [isLoadingPrice, setIsLoadingPrice] = useState(false);
  const [spendConversion, setSpendConversion] = useState<SpendConversionResult | null>(null);

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const createActivity = useCreateActivity(periodId);

  // Filter options by search
  const filteredOptions = activityOptions?.filter((factor) =>
    factor.display_name?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  // Get fuel type for spend conversion
  const getFuelType = (): string | null => {
    if (!selectedFactor?.activity_key) return null;
    return FUEL_TYPE_MAP[selectedFactor.activity_key] || null;
  };

  const canUseSpendMethod = getFuelType() !== null;

  // Fetch system price when spend mode is activated
  useEffect(() => {
    if (inputMethod !== 'spend' || !selectedFactor) return;

    const fuelType = getFuelType();
    if (!fuelType) {
      setSystemPrice(null);
      setPriceSource('');
      setPriceCurrency('USD');
      return;
    }

    const fetchSystemPrice = async () => {
      setIsLoadingPrice(true);
      const oldSystemPrice = systemPrice;

      try {
        const prices = await api.getFuelPrices(fuelType, 'Global');
        // First try to find a price in the user's currency
        let priceData = prices.find(p => p.currency === currency);
        // Fall back to USD if not found
        if (!priceData) {
          priceData = prices.find(p => p.currency === 'USD');
        }

        if (priceData) {
          setSystemPrice(priceData.price_per_unit);
          setPriceCurrency(priceData.currency); // Track actual price currency
          setPriceSource(priceData.source);
          if (unitPrice === 0 || unitPrice === oldSystemPrice) {
            setUnitPrice(priceData.price_per_unit);
          }
        } else {
          setSystemPrice(null);
          setPriceCurrency('USD');
          setPriceSource('');
        }
      } catch {
        setSystemPrice(null);
        setPriceCurrency('USD');
        setPriceSource('');
      } finally {
        setIsLoadingPrice(false);
      }
    };

    fetchSystemPrice();
  }, [inputMethod, currency, selectedFactor]);

  // Calculate quantity from spend with currency conversion
  useEffect(() => {
    if (inputMethod !== 'spend' || !spendAmount || spendAmount <= 0 || !unitPrice || unitPrice <= 0 || !selectedFactor) {
      setSpendConversion(null);
      return;
    }

    const fuelType = getFuelType();
    const unit = selectedFactor.activity_unit || 'units';
    const isCustomPrice = systemPrice !== null && unitPrice !== systemPrice;

    // Convert spend amount to price currency if different
    const effectivePriceCurrency = isCustomPrice ? currency : priceCurrency;
    const needsConversion = currency !== effectivePriceCurrency;
    const convertedSpend = needsConversion
      ? convertCurrency(spendAmount, currency, effectivePriceCurrency)
      : spendAmount;

    const calculatedQty = convertedSpend / unitPrice;

    // Build formula string to show the conversion
    let formula: string;
    if (needsConversion) {
      const rate = convertCurrency(1, currency, effectivePriceCurrency);
      formula = `${spendAmount} ${currency} × ${rate.toFixed(4)} = ${convertedSpend.toFixed(2)} ${effectivePriceCurrency} ÷ ${unitPrice} ${effectivePriceCurrency}/${unit} = ${calculatedQty.toFixed(2)} ${unit}`;
    } else {
      formula = `${spendAmount} ${currency} ÷ ${unitPrice} ${effectivePriceCurrency}/${unit} = ${calculatedQty.toFixed(2)} ${unit}`;
    }

    setSpendConversion({
      fuel_type: fuelType || 'custom',
      spend_amount: spendAmount,
      currency: currency,
      fuel_price: unitPrice,
      price_unit: `${effectivePriceCurrency}/${unit}`,
      price_source: isCustomPrice ? 'Custom price (user provided)' : priceSource,
      calculated_quantity: Math.round(calculatedQty * 100) / 100,
      quantity_unit: unit,
      formula,
    });
    setQuantity(Math.round(calculatedQty * 100) / 100);
  }, [inputMethod, spendAmount, unitPrice, currency, priceCurrency, selectedFactor, systemPrice, priceSource]);

  const handleSelectFactor = (factor: EmissionFactor) => {
    setSelectedFactor(factor);
    setIsDropdownOpen(false);
    setSearchQuery('');
    // Reset spend state when changing fuel
    setInputMethod('quantity');
    setSpendAmount(0);
    setUnitPrice(0);
    setSystemPrice(null);
    setPriceCurrency('USD');
    setSpendConversion(null);
  };

  const canProceed = selectedFactor && description && quantity > 0;

  const previewCO2e = selectedFactor && quantity
    ? quantity * (selectedFactor.co2e_factor || 0)
    : 0;

  const handleSave = async () => {
    if (!canProceed || !selectedFactor) return;

    setIsSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      const payload = {
        scope: 1 as const,
        category_code: '1.1',
        activity_key: selectedFactor.activity_key,
        description,
        quantity,
        unit: selectedFactor.activity_unit || 'units',
        activity_date: new Date().toISOString().split('T')[0],
      };

      await createActivity.mutateAsync(payload);
      setSaveSuccess(true);

      setTimeout(() => {
        reset();
        onSuccess?.();
      }, 1500);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to save activity');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveAndAddAnother = async () => {
    if (!canProceed || !selectedFactor) return;

    setIsSaving(true);
    setSaveError(null);

    try {
      const payload = {
        scope: 1 as const,
        category_code: '1.1',
        activity_key: selectedFactor.activity_key,
        description,
        quantity,
        unit: selectedFactor.activity_unit || 'units',
        activity_date: new Date().toISOString().split('T')[0],
      };

      await createActivity.mutateAsync(payload);

      // Reset form for next entry
      setSelectedFactor(null);
      setDescription('');
      setQuantity(0);
      setInputMethod('quantity');
      setSpendAmount(0);
      setSpendConversion(null);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to save activity');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={goBack}
          className="p-2 hover:bg-background-muted rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-xl font-semibold text-foreground">Stationary Combustion</h2>
          <p className="text-sm text-foreground-muted">Category 1.1 - Boilers, furnaces, generators</p>
        </div>
      </div>

      {/* Info box */}
      <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg flex items-start gap-3">
        <Flame className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-orange-800">
          <p className="font-medium">Select your fuel type and enter consumption data</p>
          <p className="mt-1">You can enter either the physical quantity or the amount spent on fuel.</p>
        </div>
      </div>

      {/* Fuel Type Selector */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          Fuel Type
        </label>
        {isLoadingOptions ? (
          <div className="flex items-center gap-2 text-foreground-muted">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Loading fuel types...</span>
          </div>
        ) : (
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className={cn(
                'w-full px-4 py-3 rounded-lg border-2 text-left',
                'bg-background-elevated transition-all duration-200',
                'flex items-center justify-between',
                isDropdownOpen ? 'border-primary ring-2 ring-primary/20' : 'border-border hover:border-primary/50'
              )}
            >
              {selectedFactor ? (
                <div className="flex-1">
                  <span className="font-medium text-foreground">{selectedFactor.display_name}</span>
                  <span className="ml-2 text-xs text-foreground-muted">({selectedFactor.activity_unit})</span>
                </div>
              ) : (
                <span className="text-foreground-muted">Select a fuel type...</span>
              )}
              <ChevronDown className={cn('w-5 h-5 text-foreground-muted transition-transform', isDropdownOpen && 'rotate-180')} />
            </button>

            {isDropdownOpen && (
              <div className="absolute z-50 w-full mt-2 bg-background-elevated border border-border rounded-lg shadow-lg max-h-64 overflow-hidden">
                <div className="p-2 border-b border-border">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground-muted" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search fuels..."
                      className="w-full pl-9 pr-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
                      autoFocus
                    />
                  </div>
                </div>
                <div className="overflow-y-auto max-h-48">
                  {filteredOptions.map((factor) => (
                    <button
                      key={factor.activity_key}
                      onClick={() => handleSelectFactor(factor)}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-primary/10 transition-colors flex justify-between items-center"
                    >
                      <span className="font-medium">{factor.display_name}</span>
                      <span className="text-xs text-foreground-muted">{factor.activity_unit}</span>
                    </button>
                  ))}
                  {filteredOptions.length === 0 && (
                    <div className="px-4 py-3 text-sm text-foreground-muted text-center">
                      No fuels found
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Show form only when fuel is selected */}
      {selectedFactor && (
        <>
          {/* Emission Factor Info */}
          <div className="p-3 bg-info/10 border border-info/20 rounded-lg text-sm">
            <div className="flex items-center gap-2 text-info">
              <Info className="w-4 h-4" />
              <span>
                Emission Factor: <strong>{selectedFactor.co2e_factor}</strong> {selectedFactor.factor_unit || `kg CO2e/${selectedFactor.activity_unit}`}
              </span>
            </div>
            <div className="mt-1 text-info/80">
              Source: {selectedFactor.source} | Region: {selectedFactor.region}
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">
              Description
            </label>
            <Input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Main building boiler, Backup generator"
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
                  }}
                  className={cn(
                    'flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition-colors',
                    inputMethod === 'quantity'
                      ? 'bg-primary text-white border-primary'
                      : 'bg-background border-border hover:bg-background-muted'
                  )}
                >
                  <Scale className="w-4 h-4" />
                  <span className="font-medium">Physical Quantity</span>
                </button>
                <button
                  onClick={() => setInputMethod('spend')}
                  className={cn(
                    'flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition-colors',
                    inputMethod === 'spend'
                      ? 'bg-primary text-white border-primary'
                      : 'bg-background border-border hover:bg-background-muted'
                  )}
                >
                  <DollarSign className="w-4 h-4" />
                  <span className="font-medium">Money Spent</span>
                </button>
              </div>
            </div>
          )}

          {/* Quantity Input */}
          {inputMethod === 'quantity' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Quantity
                </label>
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

          {/* Spend Input */}
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
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1.5">
                    Currency
                  </label>
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="w-full h-10 px-3 border border-border rounded-lg bg-background text-foreground"
                  >
                    {CURRENCIES.map((c) => (
                      <option key={c.code} value={c.code}>
                        {c.symbol} {c.code}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Price per {selectedFactor.activity_unit} ({priceCurrency})
                </label>
                <Input
                  type="number"
                  value={unitPrice || ''}
                  onChange={(e) => setUnitPrice(parseFloat(e.target.value) || 0)}
                  placeholder={isLoadingPrice ? 'Loading...' : 'Enter price'}
                  min={0}
                  step={0.01}
                  disabled={isLoadingPrice}
                />
                {systemPrice !== null && unitPrice !== systemPrice && (
                  <button
                    onClick={() => setUnitPrice(systemPrice)}
                    className="mt-1 text-xs text-primary hover:underline"
                  >
                    Reset to system price ({systemPrice} {priceCurrency})
                  </button>
                )}
                {currency !== priceCurrency && unitPrice === systemPrice && (
                  <p className="mt-1 text-xs text-foreground-muted">
                    Note: Price is in {priceCurrency}. Your {currency} amount will be converted automatically.
                  </p>
                )}
              </div>

              {spendConversion && (
                <div className="p-4 bg-success/10 border border-success/20 rounded-lg">
                  <h4 className="font-medium text-success flex items-center gap-2">
                    <Calculator className="w-4 h-4" />
                    Calculated Quantity
                  </h4>
                  <p className="text-2xl font-bold text-success mt-1">
                    {spendConversion.calculated_quantity.toLocaleString()} {spendConversion.quantity_unit}
                  </p>
                  <p className="text-xs text-success/80 mt-1">{spendConversion.formula}</p>
                </div>
              )}
            </div>
          )}

          {/* Preview */}
          {quantity > 0 && (
            <div className="p-4 bg-primary/10 border border-primary/20 rounded-lg">
              <h4 className="font-medium text-primary">Estimated Emissions</h4>
              <p className="text-2xl font-bold text-primary">{formatCO2e(previewCO2e)}</p>
              <p className="text-xs text-primary/80 mt-1">
                {quantity} {selectedFactor.activity_unit} × {selectedFactor.co2e_factor} kg CO2e/{selectedFactor.activity_unit}
              </p>
            </div>
          )}

          {/* Success message */}
          {saveSuccess && (
            <div className="p-4 bg-success/10 border border-success/20 rounded-lg">
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
        </>
      )}
    </div>
  );
}
