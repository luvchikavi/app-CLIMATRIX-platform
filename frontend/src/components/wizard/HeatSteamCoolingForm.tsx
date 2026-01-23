'use client';

/**
 * HeatSteamCoolingForm - Category 2.3 Purchased Heat/Steam/Cooling
 *
 * For district heating, steam, and cooling from third parties.
 */

import { useState } from 'react';
import { useWizardStore } from '@/stores/wizard';
import { useCreateActivity, useActivityOptions } from '@/hooks/useEmissions';
import { Button, Input } from '@/components/ui';
import { formatCO2e } from '@/lib/utils';
import {
  Save,
  Plus,
  Loader2,
  Info,
  Thermometer,
  ArrowLeft,
  ChevronDown,
  Search,
  Snowflake,
  Flame,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { EmissionFactor } from '@/lib/api';

type EnergyType = 'heat' | 'steam' | 'cooling';

// Default emission factors (DEFRA 2024)
const DEFAULT_FACTORS: Record<EnergyType, { factor: number; source: string }> = {
  heat: { factor: 0.17, source: 'DEFRA 2024 - District heat' },
  steam: { factor: 0.19, source: 'DEFRA 2024 - Steam' },
  cooling: { factor: 0.15, source: 'DEFRA 2024 - District cooling' },
};

interface HeatSteamCoolingFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function HeatSteamCoolingForm({ periodId, onSuccess }: HeatSteamCoolingFormProps) {
  const reset = useWizardStore((s) => s.reset);
  const goBack = useWizardStore((s) => s.goBack);

  // Fetch activity options for 2.3
  const { data: activityOptions, isLoading: isLoadingOptions } = useActivityOptions('2.3');

  // Form state
  const [selectedFactor, setSelectedFactor] = useState<EmissionFactor | null>(null);
  const [energyType, setEnergyType] = useState<EnergyType>('heat');
  const [description, setDescription] = useState('');
  const [quantity, setQuantity] = useState<number>(0);
  const [useCustomFactor, setUseCustomFactor] = useState(false);
  const [customFactor, setCustomFactor] = useState<number>(0);

  // Dropdown state
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const createActivity = useCreateActivity(periodId);

  const filteredOptions = activityOptions?.filter((factor) =>
    factor.display_name?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const handleSelectFactor = (factor: EmissionFactor) => {
    setSelectedFactor(factor);
    setIsDropdownOpen(false);
    setSearchQuery('');
    setUseCustomFactor(false);
  };

  // Get the emission factor to use
  const getEmissionFactor = (): number => {
    if (useCustomFactor && customFactor > 0) {
      return customFactor;
    }
    if (selectedFactor) {
      return selectedFactor.co2e_factor || 0;
    }
    return DEFAULT_FACTORS[energyType].factor;
  };

  const emissionFactor = getEmissionFactor();
  const previewCO2e = quantity * emissionFactor;

  const canProceed = description && quantity > 0;

  const handleSave = async () => {
    if (!canProceed) return;

    setIsSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      const activityKey = selectedFactor?.activity_key || `${energyType}_purchased`;

      const payload = {
        scope: 2 as const,
        category_code: '2.3',
        activity_key: activityKey,
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
    if (!canProceed) return;

    setIsSaving(true);
    setSaveError(null);

    try {
      const activityKey = selectedFactor?.activity_key || `${energyType}_purchased`;

      const payload = {
        scope: 2 as const,
        category_code: '2.3',
        activity_key: activityKey,
        description,
        quantity,
        unit: 'kWh',
        activity_date: new Date().toISOString().split('T')[0],
      };

      await createActivity.mutateAsync(payload);

      // Reset form
      setSelectedFactor(null);
      setDescription('');
      setQuantity(0);
      setCustomFactor(0);
      setUseCustomFactor(false);
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
          <h2 className="text-xl font-semibold text-foreground">Purchased Heat/Steam/Cooling</h2>
          <p className="text-sm text-foreground-muted">Category 2.3 - District energy</p>
        </div>
      </div>

      {/* Info box */}
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
        <Thermometer className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-red-800">
          <p className="font-medium">District heating, steam, and cooling</p>
          <p className="mt-1">Report energy purchased from district systems or third-party suppliers.</p>
        </div>
      </div>

      {/* Energy Type Selection */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          Energy Type
        </label>
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={() => {
              setEnergyType('heat');
              setSelectedFactor(null);
            }}
            className={cn(
              'p-4 rounded-lg border-2 text-center transition-all',
              energyType === 'heat'
                ? 'border-red-500 bg-red-50'
                : 'border-border hover:border-red-300'
            )}
          >
            <Flame className={cn('w-6 h-6 mx-auto', energyType === 'heat' ? 'text-red-600' : 'text-foreground-muted')} />
            <p className="font-medium mt-2">Heat</p>
            <p className="text-xs text-foreground-muted">District heating</p>
          </button>

          <button
            onClick={() => {
              setEnergyType('steam');
              setSelectedFactor(null);
            }}
            className={cn(
              'p-4 rounded-lg border-2 text-center transition-all',
              energyType === 'steam'
                ? 'border-orange-500 bg-orange-50'
                : 'border-border hover:border-orange-300'
            )}
          >
            <Thermometer className={cn('w-6 h-6 mx-auto', energyType === 'steam' ? 'text-orange-600' : 'text-foreground-muted')} />
            <p className="font-medium mt-2">Steam</p>
            <p className="text-xs text-foreground-muted">Industrial steam</p>
          </button>

          <button
            onClick={() => {
              setEnergyType('cooling');
              setSelectedFactor(null);
            }}
            className={cn(
              'p-4 rounded-lg border-2 text-center transition-all',
              energyType === 'cooling'
                ? 'border-blue-500 bg-blue-50'
                : 'border-border hover:border-blue-300'
            )}
          >
            <Snowflake className={cn('w-6 h-6 mx-auto', energyType === 'cooling' ? 'text-blue-600' : 'text-foreground-muted')} />
            <p className="font-medium mt-2">Cooling</p>
            <p className="text-xs text-foreground-muted">District cooling</p>
          </button>
        </div>
      </div>

      {/* Factor Selection - show available factors if any */}
      {activityOptions && activityOptions.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Emission Factor Source (optional)
          </label>
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
                <span className="text-foreground-muted">
                  Use default factor ({DEFAULT_FACTORS[energyType].factor} kg CO2e/kWh)
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
                      placeholder="Search factors..."
                      className="w-full pl-9 pr-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
                      autoFocus
                    />
                  </div>
                </div>
                <div className="overflow-y-auto max-h-48">
                  <button
                    onClick={() => {
                      setSelectedFactor(null);
                      setIsDropdownOpen(false);
                    }}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-primary/10 transition-colors flex justify-between items-center"
                  >
                    <span className="font-medium">Use Default Factor</span>
                    <span className="text-xs text-foreground-muted">{DEFAULT_FACTORS[energyType].factor} kg CO2e/kWh</span>
                  </button>
                  {filteredOptions.map((factor) => (
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
              </div>
            )}
          </div>
        </div>
      )}

      {/* Custom Factor Option */}
      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          id="useCustomFactor"
          checked={useCustomFactor}
          onChange={(e) => setUseCustomFactor(e.target.checked)}
          className="w-4 h-4 text-primary border-border rounded focus:ring-primary"
        />
        <label htmlFor="useCustomFactor" className="text-sm text-foreground">
          Use custom emission factor from supplier
        </label>
      </div>

      {useCustomFactor && (
        <div>
          <label className="block text-sm font-medium text-foreground mb-1.5">
            Custom Emission Factor (kg CO2e/kWh)
          </label>
          <Input
            type="number"
            value={customFactor || ''}
            onChange={(e) => setCustomFactor(parseFloat(e.target.value) || 0)}
            placeholder="e.g., 0.15"
            min={0}
            step={0.001}
          />
        </div>
      )}

      {/* Emission Factor Info */}
      <div className="p-3 bg-info/10 border border-info/20 rounded-lg text-sm">
        <div className="flex items-center gap-2 text-info">
          <Info className="w-4 h-4" />
          <span>
            Emission Factor: <strong>{emissionFactor}</strong> kg CO2e/kWh
          </span>
        </div>
        <div className="mt-1 text-info/80">
          Source: {useCustomFactor ? 'Custom (supplier provided)' : (selectedFactor?.source || DEFAULT_FACTORS[energyType].source)}
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
          placeholder={`e.g., District ${energyType} for main building`}
        />
      </div>

      {/* Quantity Input */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-foreground mb-1.5">
            Energy Consumed
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

      {/* Preview */}
      {quantity > 0 && (
        <div className="p-4 bg-primary/10 border border-primary/20 rounded-lg">
          <h4 className="font-medium text-primary">Estimated Emissions</h4>
          <p className="text-2xl font-bold text-primary">{formatCO2e(previewCO2e)}</p>
          <p className="text-xs text-primary/80 mt-1">
            {quantity.toLocaleString()} kWh × {emissionFactor} kg CO2e/kWh
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
    </div>
  );
}
