'use client';

/**
 * ElectricityMarketForm - Category 2.2 Purchased Electricity (Market-based)
 *
 * Uses supplier-specific or contractual emission factors:
 * - Supplier emission factor (from utility bill)
 * - RECs (Renewable Energy Certificates) - zero emissions
 * - PPAs (Power Purchase Agreements)
 * - Residual mix factor
 */

import { useState } from 'react';
import { useWizardStore } from '@/stores/wizard';
import { useCreateActivity } from '@/hooks/useEmissions';
import { Button, Input } from '@/components/ui';
import { formatCO2e } from '@/lib/utils';
import {
  Save,
  Plus,
  Loader2,
  Info,
  Zap,
  ArrowLeft,
  FileText,
  Leaf,
  Building2,
} from 'lucide-react';
import { cn } from '@/lib/utils';

type MarketMethod = 'supplier' | 'rec' | 'residual';

interface ElectricityMarketFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function ElectricityMarketForm({ periodId, onSuccess }: ElectricityMarketFormProps) {
  const reset = useWizardStore((s) => s.reset);
  const goBack = useWizardStore((s) => s.goBack);

  // Form state
  const [method, setMethod] = useState<MarketMethod>('supplier');
  const [description, setDescription] = useState('');
  const [quantity, setQuantity] = useState<number>(0);
  const [supplierEF, setSupplierEF] = useState<number>(0);
  const [supplierName, setSupplierName] = useState('');

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const createActivity = useCreateActivity(periodId);

  // Get emission factor based on method
  const getEmissionFactor = (): number => {
    switch (method) {
      case 'rec':
        return 0; // RECs = zero emissions
      case 'supplier':
        return supplierEF;
      case 'residual':
        return 0.5; // Default residual mix - should be region-specific
      default:
        return 0;
    }
  };

  const emissionFactor = getEmissionFactor();
  const previewCO2e = quantity * emissionFactor;

  const canProceed = description && quantity > 0 && (method !== 'supplier' || supplierEF >= 0);

  const handleSave = async () => {
    if (!canProceed) return;

    setIsSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      // For market-based, we use a special activity key
      const activityKey = method === 'rec'
        ? 'electricity_rec_zero'
        : method === 'supplier'
          ? 'electricity_supplier_specific'
          : 'electricity_residual_mix';

      const payload = {
        scope: 2 as const,
        category_code: '2.2',
        activity_key: activityKey,
        description: `${description}${supplierName ? ` (${supplierName})` : ''}`,
        quantity,
        unit: 'kWh',
        activity_date: new Date().toISOString().split('T')[0],
        // Note: custom_emission_factor would be used here in production
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
      const activityKey = method === 'rec'
        ? 'electricity_rec_zero'
        : method === 'supplier'
          ? 'electricity_supplier_specific'
          : 'electricity_residual_mix';

      const payload = {
        scope: 2 as const,
        category_code: '2.2',
        activity_key: activityKey,
        description: `${description}${supplierName ? ` (${supplierName})` : ''}`,
        quantity,
        unit: 'kWh',
        activity_date: new Date().toISOString().split('T')[0],
      };

      await createActivity.mutateAsync(payload);

      // Reset form
      setDescription('');
      setQuantity(0);
      setSupplierEF(0);
      setSupplierName('');
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
          <p className="text-sm text-foreground-muted">Category 2.2 - Market-based method</p>
        </div>
      </div>

      {/* Info box */}
      <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
        <Zap className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-green-800">
          <p className="font-medium">Market-based accounting</p>
          <p className="mt-1">Uses contractual instruments like supplier emission factors, RECs, or PPAs to calculate emissions.</p>
        </div>
      </div>

      {/* Method Selection */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          Select Method
        </label>
        <div className="grid grid-cols-1 gap-3">
          <button
            onClick={() => setMethod('supplier')}
            className={cn(
              'p-4 rounded-lg border-2 text-left transition-all',
              method === 'supplier'
                ? 'border-primary bg-primary/5'
                : 'border-border hover:border-primary/50'
            )}
          >
            <div className="flex items-center gap-3">
              <div className={cn(
                'p-2 rounded-lg',
                method === 'supplier' ? 'bg-primary/20' : 'bg-background-muted'
              )}>
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <p className="font-medium">Supplier-Specific Factor</p>
                <p className="text-sm text-foreground-muted">Use the emission factor from your electricity bill or supplier</p>
              </div>
            </div>
          </button>

          <button
            onClick={() => setMethod('rec')}
            className={cn(
              'p-4 rounded-lg border-2 text-left transition-all',
              method === 'rec'
                ? 'border-primary bg-primary/5'
                : 'border-border hover:border-primary/50'
            )}
          >
            <div className="flex items-center gap-3">
              <div className={cn(
                'p-2 rounded-lg',
                method === 'rec' ? 'bg-green-100' : 'bg-background-muted'
              )}>
                <Leaf className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="font-medium">RECs / Green Tariff / PPA</p>
                <p className="text-sm text-foreground-muted">Renewable energy certificates or power purchase agreement (zero emissions)</p>
              </div>
            </div>
          </button>

          <button
            onClick={() => setMethod('residual')}
            className={cn(
              'p-4 rounded-lg border-2 text-left transition-all',
              method === 'residual'
                ? 'border-primary bg-primary/5'
                : 'border-border hover:border-primary/50'
            )}
          >
            <div className="flex items-center gap-3">
              <div className={cn(
                'p-2 rounded-lg',
                method === 'residual' ? 'bg-primary/20' : 'bg-background-muted'
              )}>
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <p className="font-medium">Residual Mix</p>
                <p className="text-sm text-foreground-muted">Grid mix minus renewable energy claims (for untracked electricity)</p>
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Method-specific info */}
      {method === 'rec' && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2 text-green-700">
            <Leaf className="w-4 h-4" />
            <span className="font-medium">Zero emissions</span>
          </div>
          <p className="text-sm text-green-600 mt-1">
            Electricity covered by RECs, green tariffs, or PPAs is reported as zero emissions under market-based accounting.
          </p>
        </div>
      )}

      {/* Supplier Factor Input */}
      {method === 'supplier' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">
              Supplier Name (optional)
            </label>
            <Input
              type="text"
              value={supplierName}
              onChange={(e) => setSupplierName(e.target.value)}
              placeholder="e.g., National Grid, EDF, Con Edison"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">
              Supplier Emission Factor (kg CO2e/kWh)
            </label>
            <Input
              type="number"
              value={supplierEF || ''}
              onChange={(e) => setSupplierEF(parseFloat(e.target.value) || 0)}
              placeholder="e.g., 0.35"
              min={0}
              step={0.001}
            />
            <p className="text-xs text-foreground-muted mt-1">
              Find this on your electricity bill or contact your supplier
            </p>
          </div>
        </div>
      )}

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-1.5">
          Description
        </label>
        <Input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder={method === 'rec'
            ? "e.g., Office electricity covered by RECs"
            : "e.g., Main office electricity"
          }
        />
      </div>

      {/* Quantity Input */}
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

      {/* Emission Factor Summary */}
      {quantity > 0 && (
        <div className="p-3 bg-info/10 border border-info/20 rounded-lg text-sm">
          <div className="flex items-center gap-2 text-info">
            <Info className="w-4 h-4" />
            <span>
              Emission Factor: <strong>{emissionFactor}</strong> kg CO2e/kWh
              {method === 'rec' && <span className="ml-2 text-green-600">(Renewable - Zero Emissions)</span>}
            </span>
          </div>
        </div>
      )}

      {/* Preview */}
      {quantity > 0 && (
        <div className={cn(
          'p-4 rounded-lg border',
          method === 'rec'
            ? 'bg-green-50 border-green-200'
            : 'bg-primary/10 border-primary/20'
        )}>
          <h4 className={cn(
            'font-medium',
            method === 'rec' ? 'text-green-700' : 'text-primary'
          )}>
            Estimated Emissions
          </h4>
          <p className={cn(
            'text-2xl font-bold',
            method === 'rec' ? 'text-green-700' : 'text-primary'
          )}>
            {method === 'rec' ? '0 kg CO2e' : formatCO2e(previewCO2e)}
          </p>
          <p className={cn(
            'text-xs mt-1',
            method === 'rec' ? 'text-green-600' : 'text-primary/80'
          )}>
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
