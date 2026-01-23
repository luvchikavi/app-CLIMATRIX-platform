'use client';

/**
 * FugitiveEmissionsForm - Category 1.3 Fugitive Emissions
 *
 * For refrigerants and fire suppression systems:
 * - HFCs (R-134a, R-410A, R-32, etc.)
 * - HCFCs (R-123)
 * - Halons (Halon-1211)
 * - Other (FM-200, SF6, etc.)
 *
 * Enter the mass of refrigerant leaked/recharged.
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
  Wind,
  ArrowLeft,
  ChevronDown,
  Search,
  AlertTriangle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { EmissionFactor } from '@/lib/api';

interface FugitiveEmissionsFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function FugitiveEmissionsForm({ periodId, onSuccess }: FugitiveEmissionsFormProps) {
  const reset = useWizardStore((s) => s.reset);
  const goBack = useWizardStore((s) => s.goBack);

  // Fetch activity options for 1.3
  const { data: activityOptions, isLoading: isLoadingOptions } = useActivityOptions('1.3');

  // Form state
  const [selectedFactor, setSelectedFactor] = useState<EmissionFactor | null>(null);
  const [description, setDescription] = useState('');
  const [quantity, setQuantity] = useState<number>(0);

  // Dropdown state
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const createActivity = useCreateActivity(periodId);

  // Group options by type (HFC, HCFC, PFC, etc.)
  const groupOptions = (options: EmissionFactor[]) => {
    const groups: Record<string, EmissionFactor[]> = {
      'HFCs': [],
      'Blends': [],
      'HCFCs': [],
      'Halons': [],
      'PFCs': [],
      'Other': [],
    };

    options?.forEach((opt) => {
      const name = opt.display_name?.toUpperCase() || '';
      const key = opt.activity_key?.toLowerCase() || '';

      if (name.includes('R-4') || name.includes('R-5') || key.includes('blend')) {
        groups['Blends'].push(opt);
      } else if (name.includes('HFC') || name.includes('R-134') || name.includes('R-32') || name.includes('R-125') || name.includes('R-143') || name.includes('R-152') || name.includes('R-227') || name.includes('R-236') || name.includes('R-245') || name.includes('R-365') || name.includes('R-43') || name.includes('FM-200')) {
        groups['HFCs'].push(opt);
      } else if (name.includes('HCFC') || name.includes('R-123') || name.includes('R-22')) {
        groups['HCFCs'].push(opt);
      } else if (name.includes('HALON') || key.includes('halon')) {
        groups['Halons'].push(opt);
      } else if (name.includes('PFC') || name.includes('CF4') || name.includes('C2F6') || name.includes('C3F8') || name.includes('C4F8')) {
        groups['PFCs'].push(opt);
      } else {
        groups['Other'].push(opt);
      }
    });

    return groups;
  };

  const groupedOptions = groupOptions(activityOptions || []);

  const filteredOptions = activityOptions?.filter((factor) =>
    factor.display_name?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const handleSelectFactor = (factor: EmissionFactor) => {
    setSelectedFactor(factor);
    setIsDropdownOpen(false);
    setSearchQuery('');
  };

  const canProceed = selectedFactor && description && quantity > 0;

  const previewCO2e = selectedFactor && quantity
    ? quantity * (selectedFactor.co2e_factor || 0)
    : 0;

  // High GWP warning
  const isHighGWP = selectedFactor && (selectedFactor.co2e_factor || 0) > 1000;

  const handleSave = async () => {
    if (!canProceed || !selectedFactor) return;

    setIsSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      const payload = {
        scope: 1 as const,
        category_code: '1.3',
        activity_key: selectedFactor.activity_key,
        description,
        quantity,
        unit: selectedFactor.activity_unit || 'kg',
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
        category_code: '1.3',
        activity_key: selectedFactor.activity_key,
        description,
        quantity,
        unit: selectedFactor.activity_unit || 'kg',
        activity_date: new Date().toISOString().split('T')[0],
      };

      await createActivity.mutateAsync(payload);

      // Reset form for next entry
      setSelectedFactor(null);
      setDescription('');
      setQuantity(0);
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
          <h2 className="text-xl font-semibold text-foreground">Fugitive Emissions</h2>
          <p className="text-sm text-foreground-muted">Category 1.3 - Refrigerants & fire suppression</p>
        </div>
      </div>

      {/* Info box */}
      <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg flex items-start gap-3">
        <Wind className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-purple-800">
          <p className="font-medium">Track refrigerant leaks and recharges</p>
          <p className="mt-1">Enter the mass (kg) of refrigerant that was leaked or used to recharge systems.</p>
        </div>
      </div>

      {/* Gas Type Selector */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          Refrigerant / Gas Type
        </label>
        {isLoadingOptions ? (
          <div className="flex items-center gap-2 text-foreground-muted">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Loading gas types...</span>
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
                    (GWP: {selectedFactor.co2e_factor?.toLocaleString()})
                  </span>
                </div>
              ) : (
                <span className="text-foreground-muted">Select a refrigerant or gas...</span>
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
                      placeholder="Search gases..."
                      className="w-full pl-9 pr-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
                      autoFocus
                    />
                  </div>
                </div>
                <div className="overflow-y-auto max-h-64">
                  {searchQuery ? (
                    // Show filtered results when searching
                    filteredOptions.map((factor) => (
                      <button
                        key={factor.activity_key}
                        onClick={() => handleSelectFactor(factor)}
                        className="w-full px-4 py-2 text-left text-sm hover:bg-primary/10 transition-colors flex justify-between items-center"
                      >
                        <span className="font-medium">{factor.display_name}</span>
                        <span className="text-xs text-foreground-muted">GWP: {factor.co2e_factor?.toLocaleString()}</span>
                      </button>
                    ))
                  ) : (
                    // Show grouped results when not searching
                    Object.entries(groupedOptions).map(([group, options]) =>
                      options.length > 0 && (
                        <div key={group}>
                          <div className="px-4 py-2 bg-background-muted text-xs font-semibold text-foreground-muted sticky top-0">
                            {group}
                          </div>
                          {options.map((factor) => (
                            <button
                              key={factor.activity_key}
                              onClick={() => handleSelectFactor(factor)}
                              className="w-full px-4 py-2 text-left text-sm hover:bg-primary/10 transition-colors flex justify-between items-center"
                            >
                              <span className="font-medium">{factor.display_name}</span>
                              <span className="text-xs text-foreground-muted">GWP: {factor.co2e_factor?.toLocaleString()}</span>
                            </button>
                          ))}
                        </div>
                      )
                    )
                  )}
                  {filteredOptions.length === 0 && searchQuery && (
                    <div className="px-4 py-3 text-sm text-foreground-muted text-center">
                      No gases found
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Show form only when gas is selected */}
      {selectedFactor && (
        <>
          {/* High GWP Warning */}
          {isHighGWP && (
            <div className="p-3 bg-warning/10 border border-warning/20 rounded-lg flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-warning flex-shrink-0 mt-0.5" />
              <div className="text-sm text-warning">
                <p className="font-medium">High Global Warming Potential</p>
                <p>This gas has a GWP of {selectedFactor.co2e_factor?.toLocaleString()}. Consider transitioning to lower-GWP alternatives.</p>
              </div>
            </div>
          )}

          {/* Emission Factor Info */}
          <div className="p-3 bg-info/10 border border-info/20 rounded-lg text-sm">
            <div className="flex items-center gap-2 text-info">
              <Info className="w-4 h-4" />
              <span>
                GWP (100-year): <strong>{selectedFactor.co2e_factor?.toLocaleString()}</strong> kg CO2e/kg
              </span>
            </div>
            <div className="mt-1 text-info/80">
              Source: {selectedFactor.source}
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
              placeholder="e.g., HVAC system recharge, Chiller leak repair"
            />
          </div>

          {/* Quantity Input */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Mass Leaked/Recharged
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
                value="kg"
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
                {quantity} kg × {selectedFactor.co2e_factor?.toLocaleString()} GWP = {previewCO2e.toLocaleString()} kg CO2e
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
