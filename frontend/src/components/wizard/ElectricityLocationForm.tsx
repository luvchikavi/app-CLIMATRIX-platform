'use client';

/**
 * ElectricityLocationForm - Category 2.1 Purchased Electricity (Location-based)
 *
 * Uses grid average emission factors based on geographic location.
 * Supports entering kWh directly or calculating from spend.
 */

import { useState, useEffect } from 'react';
import { useWizardStore } from '@/stores/wizard';
import { useCreateActivity, useActivityOptions, useOrganization } from '@/hooks/useEmissions';
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
  Zap,
  ArrowLeft,
  ChevronDown,
  Search,
  MapPin,
  ExternalLink,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { api, EmissionFactor } from '@/lib/api';

type InputMethod = 'quantity' | 'spend';

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'ILS', symbol: '₪', name: 'Israeli Shekel' },
];

interface ElectricityLocationFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function ElectricityLocationForm({ periodId, onSuccess }: ElectricityLocationFormProps) {
  const reset = useWizardStore((s) => s.reset);
  const goBack = useWizardStore((s) => s.goBack);

  // Fetch activity options for 2.1
  const { data: activityOptions, isLoading: isLoadingOptions } = useActivityOptions('2.1');

  // Fetch organization settings for default region
  const { data: organization } = useOrganization();

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
  const [isLoadingPrice, setIsLoadingPrice] = useState(false);

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const createActivity = useCreateActivity(periodId);

  // Group options by region
  const groupOptions = (options: EmissionFactor[]) => {
    const groups: Record<string, EmissionFactor[]> = {
      'USA - States': [],
      'Europe': [],
      'Asia Pacific': [],
      'Middle East': [],
      'Americas': [],
      'Other': [],
    };

    options?.forEach((opt) => {
      const name = opt.display_name?.toLowerCase() || '';
      const region = opt.region?.toUpperCase() || '';

      if (region.startsWith('US-') || name.includes('usa -')) {
        groups['USA - States'].push(opt);
      } else if (['UK', 'DE', 'FR', 'ES', 'IT', 'NL', 'PL', 'SE', 'NO', 'DK', 'FI', 'PT', 'GR', 'IE', 'CZ', 'HU', 'RO', 'BE', 'AT', 'CH'].includes(region) || name.includes('europe') || name.includes('eu ')) {
        groups['Europe'].push(opt);
      } else if (['JP', 'KR', 'CN', 'SG', 'HK', 'TW', 'AU', 'NZ', 'IN', 'TH', 'MY', 'ID', 'PH', 'VN'].includes(region)) {
        groups['Asia Pacific'].push(opt);
      } else if (['IL', 'AE', 'SA', 'EG', 'TR'].includes(region)) {
        groups['Middle East'].push(opt);
      } else if (['CA', 'MX', 'BR', 'AR', 'CL', 'CO'].includes(region) || name.includes('canada') || name.includes('mexico') || name.includes('brazil')) {
        groups['Americas'].push(opt);
      } else {
        groups['Other'].push(opt);
      }
    });

    return groups;
  };

  // Filter out spend-based options (they have USD/currency units)
  const gridOptions = activityOptions?.filter((f) =>
    f.activity_unit === 'kWh' || f.activity_unit === 'MWh'
  ) || [];

  const groupedOptions = groupOptions(gridOptions);

  const filteredOptions = gridOptions.filter((factor) =>
    factor.display_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    factor.region?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Auto-select grid based on organization's default region or country
  useEffect(() => {
    if (selectedFactor || !gridOptions.length || !organization) return;

    // Try to find a matching grid based on organization's default_region or country_code
    const regionToMatch = organization.default_region || organization.country_code;
    if (!regionToMatch || regionToMatch === 'Global') return;

    const matchedFactor = gridOptions.find((f) =>
      f.region?.toUpperCase() === regionToMatch.toUpperCase() ||
      f.activity_key?.toLowerCase().includes(`electricity_${regionToMatch.toLowerCase()}`)
    );

    if (matchedFactor) {
      setSelectedFactor(matchedFactor);
    }
  }, [gridOptions, organization, selectedFactor]);

  // Fetch electricity price when spend mode is activated
  useEffect(() => {
    if (inputMethod !== 'spend' || !selectedFactor) return;

    const fetchSystemPrice = async () => {
      setIsLoadingPrice(true);
      const oldSystemPrice = systemPrice;

      try {
        const prices = await api.getFuelPrices('electricity', selectedFactor.region || 'Global');
        let priceData = prices.find(p => p.currency === currency);
        if (!priceData) {
          priceData = prices.find(p => p.currency === 'USD');
        }

        if (priceData) {
          setSystemPrice(priceData.price_per_unit);
          if (unitPrice === 0 || unitPrice === oldSystemPrice) {
            setUnitPrice(priceData.price_per_unit);
          }
        } else {
          setSystemPrice(null);
        }
      } catch {
        setSystemPrice(null);
      } finally {
        setIsLoadingPrice(false);
      }
    };

    fetchSystemPrice();
  }, [inputMethod, currency, selectedFactor]);

  // Calculate quantity from spend
  useEffect(() => {
    if (inputMethod !== 'spend' || !spendAmount || !unitPrice) return;
    const calculatedQty = spendAmount / unitPrice;
    setQuantity(Math.round(calculatedQty * 100) / 100);
  }, [inputMethod, spendAmount, unitPrice]);

  const handleSelectFactor = (factor: EmissionFactor) => {
    setSelectedFactor(factor);
    setIsDropdownOpen(false);
    setSearchQuery('');
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
        scope: 2 as const,
        category_code: '2.1',
        activity_key: selectedFactor.activity_key,
        description,
        quantity,
        unit: 'kWh',
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
        scope: 2 as const,
        category_code: '2.1',
        activity_key: selectedFactor.activity_key,
        description,
        quantity,
        unit: 'kWh',
        activity_date: new Date().toISOString().split('T')[0],
      };

      await createActivity.mutateAsync(payload);

      // Reset form for next entry
      setSelectedFactor(null);
      setDescription('');
      setQuantity(0);
      setInputMethod('quantity');
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
          <h2 className="text-xl font-semibold text-foreground">Purchased Electricity</h2>
          <p className="text-sm text-foreground-muted">Category 2.1 - Location-based method</p>
        </div>
      </div>

      {/* Info box */}
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-3">
        <Zap className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-yellow-800">
          <p className="font-medium">Location-based accounting</p>
          <p className="mt-1">Uses grid average emission factors based on where you consume electricity. Select your grid region below.</p>
        </div>
      </div>

      {/* Grid Region Selector */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          <MapPin className="w-4 h-4 inline mr-1" />
          Grid Region
        </label>
        {isLoadingOptions ? (
          <div className="flex items-center gap-2 text-foreground-muted">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Loading grid regions...</span>
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
                  <span className="ml-2 text-xs text-foreground-muted">
                    ({selectedFactor.co2e_factor} kg CO2e/kWh)
                  </span>
                </div>
              ) : (
                <span className="text-foreground-muted">Select your electricity grid region...</span>
              )}
              <ChevronDown className={cn('w-5 h-5 text-foreground-muted transition-transform', isDropdownOpen && 'rotate-180')} />
            </button>

            {isDropdownOpen && (
              <div className="absolute z-50 w-full mt-2 bg-background-elevated border border-border rounded-lg shadow-lg max-h-80 overflow-hidden">
                <div className="p-2 border-b border-border">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground-muted" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search by country or region..."
                      className="w-full pl-9 pr-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
                      autoFocus
                    />
                  </div>
                </div>
                <div className="overflow-y-auto max-h-64">
                  {searchQuery ? (
                    filteredOptions.map((factor) => (
                      <button
                        key={factor.activity_key}
                        onClick={() => handleSelectFactor(factor)}
                        className="w-full px-4 py-2 text-left text-sm hover:bg-primary/10 transition-colors flex justify-between items-center"
                      >
                        <span className="font-medium">{factor.display_name}</span>
                        <span className="text-xs text-foreground-muted">{factor.co2e_factor} kg CO2e/kWh</span>
                      </button>
                    ))
                  ) : (
                    Object.entries(groupedOptions).map(([group, options]) =>
                      options.length > 0 && (
                        <div key={group}>
                          <div className="px-4 py-2 bg-background-muted text-xs font-semibold text-foreground-muted sticky top-0">
                            {group} ({options.length})
                          </div>
                          {options.map((factor) => (
                            <button
                              key={factor.activity_key}
                              onClick={() => handleSelectFactor(factor)}
                              className="w-full px-4 py-2 text-left text-sm hover:bg-primary/10 transition-colors flex justify-between items-center"
                            >
                              <span className="font-medium">{factor.display_name}</span>
                              <span className="text-xs text-foreground-muted">{factor.co2e_factor} kg CO2e/kWh</span>
                            </button>
                          ))}
                        </div>
                      )
                    )
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Show form only when grid is selected */}
      {selectedFactor && (
        <>
          {/* Emission Factor Info */}
          <div className="p-3 bg-info/10 border border-info/20 rounded-lg text-sm">
            <div className="flex items-center gap-2 text-info">
              <Info className="w-4 h-4" />
              <span>
                Grid Emission Factor: <strong>{selectedFactor.co2e_factor}</strong> kg CO2e/kWh
              </span>
            </div>
            <div className="mt-1 text-info/80 flex items-center gap-2 flex-wrap">
              <span>Source: {selectedFactor.source} ({selectedFactor.year}) | Region: {selectedFactor.region}</span>
              {(selectedFactor.region?.startsWith('US') || selectedFactor.source?.includes('eGRID')) && (
                <a
                  href="https://www.epa.gov/egrid"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-primary hover:underline"
                >
                  <ExternalLink className="w-3 h-3" />
                  EPA eGRID
                </a>
              )}
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
              placeholder="e.g., Main office electricity, Manufacturing facility"
            />
          </div>

          {/* Input Method Toggle */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              How do you want to enter data?
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setInputMethod('quantity');
                  setSpendAmount(0);
                }}
                className={cn(
                  'flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition-colors',
                  inputMethod === 'quantity'
                    ? 'bg-primary text-white border-primary'
                    : 'bg-background border-border hover:bg-background-muted'
                )}
              >
                <Scale className="w-4 h-4" />
                <span className="font-medium">kWh Consumed</span>
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

          {/* Quantity Input */}
          {inputMethod === 'quantity' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Electricity Consumed
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
                  value="kWh"
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
                  Price per kWh ({currency})
                </label>
                <Input
                  type="number"
                  value={unitPrice || ''}
                  onChange={(e) => setUnitPrice(parseFloat(e.target.value) || 0)}
                  placeholder={isLoadingPrice ? 'Loading...' : 'Enter electricity price'}
                  min={0}
                  step={0.001}
                  disabled={isLoadingPrice}
                />
                {systemPrice !== null && unitPrice !== systemPrice && (
                  <button
                    onClick={() => setUnitPrice(systemPrice)}
                    className="mt-1 text-xs text-primary hover:underline"
                  >
                    Reset to system price ({systemPrice} {currency}/kWh)
                  </button>
                )}
              </div>

              {quantity > 0 && (
                <div className="p-4 bg-success/10 border border-success/20 rounded-lg">
                  <h4 className="font-medium text-success flex items-center gap-2">
                    <Calculator className="w-4 h-4" />
                    Calculated Consumption
                  </h4>
                  <p className="text-2xl font-bold text-success mt-1">
                    {quantity.toLocaleString()} kWh
                  </p>
                  <p className="text-xs text-success/80 mt-1">
                    {spendAmount} {currency} ÷ {unitPrice} {currency}/kWh
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
                {quantity.toLocaleString()} kWh × {selectedFactor.co2e_factor} kg CO2e/kWh
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
