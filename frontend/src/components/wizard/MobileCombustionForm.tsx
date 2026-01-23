'use client';

/**
 * MobileCombustionForm - Category 1.2 Mobile Combustion
 *
 * For company vehicles:
 * - Cars (petrol, diesel, hybrid, electric)
 * - Vans and trucks
 * - Motorcycles
 *
 * Supports both fuel-based (liters) and distance-based (km) input.
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
  Car,
  ArrowLeft,
  ChevronDown,
  Search,
  Fuel,
  MapPin,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { api, EmissionFactor } from '@/lib/api';

type InputMethod = 'fuel' | 'distance' | 'spend';

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'ILS', symbol: '₪', name: 'Israeli Shekel' },
];

// Map activity_key to fuel_type for spend conversion
const FUEL_TYPE_MAP: Record<string, string> = {
  'diesel_mobile': 'diesel',
  'diesel_mobile_liters': 'diesel',
  'petrol_mobile': 'petrol',
  'petrol_mobile_liters': 'petrol',
  'gasoline_mobile': 'petrol',
};

interface MobileCombustionFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function MobileCombustionForm({ periodId, onSuccess }: MobileCombustionFormProps) {
  const reset = useWizardStore((s) => s.reset);
  const goBack = useWizardStore((s) => s.goBack);

  // Fetch activity options for 1.2
  const { data: activityOptions, isLoading: isLoadingOptions } = useActivityOptions('1.2');

  // Form state
  const [selectedFactor, setSelectedFactor] = useState<EmissionFactor | null>(null);
  const [description, setDescription] = useState('');
  const [quantity, setQuantity] = useState<number>(0);
  const [inputMethod, setInputMethod] = useState<InputMethod>('fuel');

  // Dropdown state
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Spend state
  const [spendAmount, setSpendAmount] = useState<number>(0);
  const [currency, setCurrency] = useState('USD');
  const [unitPrice, setUnitPrice] = useState<number>(0);
  const [systemPrice, setSystemPrice] = useState<number | null>(null);
  const [priceSource, setPriceSource] = useState('');
  const [isLoadingPrice, setIsLoadingPrice] = useState(false);

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const createActivity = useCreateActivity(periodId);

  // Separate fuel-based and distance-based options
  const fuelOptions = activityOptions?.filter((f) =>
    f.activity_unit === 'liters' || f.activity_unit === 'L' || f.activity_unit === 'gallons'
  ) || [];

  const distanceOptions = activityOptions?.filter((f) =>
    f.activity_unit === 'km' || f.activity_unit === 'miles'
  ) || [];

  const currentOptions = inputMethod === 'distance' ? distanceOptions : fuelOptions;

  const filteredOptions = currentOptions.filter((factor) =>
    factor.display_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Get fuel type for spend conversion
  const getFuelType = (): string | null => {
    if (!selectedFactor?.activity_key) return null;
    return FUEL_TYPE_MAP[selectedFactor.activity_key] || null;
  };

  // Can use spend method when a fuel type with price mapping is selected (not distance-based)
  const canUseSpendMethod = getFuelType() !== null && inputMethod !== 'distance';

  // Fetch system price when spend mode is activated
  useEffect(() => {
    if (inputMethod !== 'spend' || !selectedFactor) return;

    const fuelType = getFuelType();
    if (!fuelType) {
      setSystemPrice(null);
      setPriceSource('');
      return;
    }

    const fetchSystemPrice = async () => {
      setIsLoadingPrice(true);
      const oldSystemPrice = systemPrice;

      try {
        const prices = await api.getFuelPrices(fuelType, 'Global');
        let priceData = prices.find(p => p.currency === currency);
        if (!priceData) {
          priceData = prices.find(p => p.currency === 'USD');
        }

        if (priceData) {
          setSystemPrice(priceData.price_per_unit);
          setPriceSource(priceData.source);
          if (unitPrice === 0 || unitPrice === oldSystemPrice) {
            setUnitPrice(priceData.price_per_unit);
          }
        } else {
          setSystemPrice(null);
          setPriceSource('');
        }
      } catch {
        setSystemPrice(null);
        setPriceSource('');
      } finally {
        setIsLoadingPrice(false);
      }
    };

    fetchSystemPrice();
  }, [inputMethod, currency, selectedFactor]);

  // Calculate quantity from spend
  useEffect(() => {
    if (inputMethod !== 'spend' || !spendAmount || !unitPrice || !selectedFactor) return;
    const calculatedQty = spendAmount / unitPrice;
    setQuantity(Math.round(calculatedQty * 100) / 100);
  }, [inputMethod, spendAmount, unitPrice, selectedFactor]);

  const handleSelectFactor = (factor: EmissionFactor) => {
    setSelectedFactor(factor);
    setIsDropdownOpen(false);
    setSearchQuery('');
  };

  const handleMethodChange = (method: InputMethod) => {
    setInputMethod(method);
    setSelectedFactor(null);
    setQuantity(0);
    setSpendAmount(0);
    setUnitPrice(0);
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
        category_code: '1.2',
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
        category_code: '1.2',
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
      setSpendAmount(0);
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
          <h2 className="text-xl font-semibold text-foreground">Mobile Combustion</h2>
          <p className="text-sm text-foreground-muted">Category 1.2 - Company vehicles</p>
        </div>
      </div>

      {/* Info box */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-3">
        <Car className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-800">
          <p className="font-medium">Track emissions from company-owned vehicles</p>
          <p className="mt-1">You can enter fuel consumption (liters) or distance traveled (km).</p>
        </div>
      </div>

      {/* Input Method Toggle */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          How do you want to enter data?
        </label>
        <div className="flex gap-2">
          <button
            onClick={() => handleMethodChange('fuel')}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition-colors',
              inputMethod === 'fuel' || inputMethod === 'spend'
                ? 'bg-primary text-white border-primary'
                : 'bg-background border-border hover:bg-background-muted'
            )}
          >
            <Fuel className="w-4 h-4" />
            <span className="font-medium">Fuel Consumed</span>
          </button>
          <button
            onClick={() => handleMethodChange('distance')}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition-colors',
              inputMethod === 'distance'
                ? 'bg-primary text-white border-primary'
                : 'bg-background border-border hover:bg-background-muted'
            )}
          >
            <MapPin className="w-4 h-4" />
            <span className="font-medium">Distance Traveled</span>
          </button>
        </div>
      </div>

      {/* Vehicle/Fuel Type Selector */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          {inputMethod === 'distance' ? 'Vehicle Type' : 'Fuel Type'}
        </label>
        {isLoadingOptions ? (
          <div className="flex items-center gap-2 text-foreground-muted">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Loading options...</span>
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
                <span className="text-foreground-muted">
                  Select {inputMethod === 'distance' ? 'vehicle type' : 'fuel type'}...
                </span>
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
                      placeholder="Search..."
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
                      No options found
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Show form only when type is selected */}
      {selectedFactor && (
        <>
          {/* Emission Factor Info */}
          <div className="p-3 bg-info/10 border border-info/20 rounded-lg text-sm">
            <div className="flex items-center gap-2 text-info">
              <Info className="w-4 h-4" />
              <span>
                Emission Factor: <strong>{selectedFactor.co2e_factor}</strong> kg CO2e/{selectedFactor.activity_unit}
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
              placeholder="e.g., Sales team vehicles, Delivery trucks"
            />
          </div>

          {/* Spend toggle for fuel-based */}
          {canUseSpendMethod && (
            <div className="flex gap-2">
              <button
                onClick={() => setInputMethod('fuel')}
                className={cn(
                  'flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg border text-sm transition-colors',
                  inputMethod === 'fuel'
                    ? 'bg-primary/10 text-primary border-primary'
                    : 'bg-background border-border hover:bg-background-muted'
                )}
              >
                <Scale className="w-4 h-4" />
                <span>Enter Quantity</span>
              </button>
              <button
                onClick={() => setInputMethod('spend')}
                className={cn(
                  'flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg border text-sm transition-colors',
                  inputMethod === 'spend'
                    ? 'bg-primary/10 text-primary border-primary'
                    : 'bg-background border-border hover:bg-background-muted'
                )}
              >
                <DollarSign className="w-4 h-4" />
                <span>Enter Spend</span>
              </button>
            </div>
          )}

          {/* Quantity Input */}
          {(inputMethod === 'fuel' || inputMethod === 'distance') && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  {inputMethod === 'distance' ? 'Distance' : 'Quantity'}
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
                  Price per {selectedFactor.activity_unit} ({currency})
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
              </div>

              {quantity > 0 && (
                <div className="p-4 bg-success/10 border border-success/20 rounded-lg">
                  <h4 className="font-medium text-success flex items-center gap-2">
                    <Calculator className="w-4 h-4" />
                    Calculated Quantity
                  </h4>
                  <p className="text-2xl font-bold text-success mt-1">
                    {quantity.toLocaleString()} {selectedFactor.activity_unit}
                  </p>
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
