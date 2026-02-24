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

  // Region-based market factor state
  const [marketRegion, setMarketRegion] = useState<'israel' | 'europe' | 'usa' | 'other'>('israel');
  const [selectedCountry, setSelectedCountry] = useState('');
  const [selectedSubregion, setSelectedSubregion] = useState('');
  const [marketFactorLoading, setMarketFactorLoading] = useState(false);
  const [autoFilledFactor, setAutoFilledFactor] = useState<number | null>(null);
  const [marketFactorSource, setMarketFactorSource] = useState('');

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const createActivity = useCreateActivity(periodId);

  const fetchMarketFactor = async (country: string, subregion?: string) => {
    setMarketFactorLoading(true);
    try {
      const params = new URLSearchParams({ country });
      if (subregion) params.append('subregion', subregion);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/reference/market-factor?${params}`);
      if (response.ok) {
        const data = await response.json();
        setAutoFilledFactor(data.market_factor_co2e_per_kwh);
        setMarketFactorSource(`${data.source} (${data.source_type})`);
        if (data.warning) {
          // Display warning to user
          console.warn('Market factor warning:', data.warning);
        }
      }
    } catch (error) {
      console.error('Failed to fetch market factor:', error);
    } finally {
      setMarketFactorLoading(false);
    }
  };

  // Get emission factor based on method
  const getEmissionFactor = (): number => {
    switch (method) {
      case 'rec':
        return 0; // RECs = zero emissions
      case 'supplier':
        return supplierEF;
      case 'residual':
        return autoFilledFactor ?? 0.453; // Use auto-filled factor or EU average fallback (AIB 2024)
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
      // For market-based, we use activity keys matching emission_factors.py
      const activityKey = method === 'rec'
        ? 'electricity_renewable'
        : method === 'supplier'
          ? 'electricity_supplier'
          : 'electricity_residual_mix';

      const payload = {
        scope: 2 as const,
        category_code: '2',
        activity_key: activityKey,
        description: `${description}${supplierName ? ` (${supplierName})` : ''}`,
        quantity,
        unit: 'kWh',
        activity_date: new Date().toISOString().split('T')[0],
        // Pass supplier emission factor for supplier-specific method
        ...(method === 'supplier' && supplierEF > 0 ? { supplier_ef: supplierEF } : {}),
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
      // For market-based, we use activity keys matching emission_factors.py
      const activityKey = method === 'rec'
        ? 'electricity_renewable'
        : method === 'supplier'
          ? 'electricity_supplier'
          : 'electricity_residual_mix';

      const payload = {
        scope: 2 as const,
        category_code: '2',
        activity_key: activityKey,
        description: `${description}${supplierName ? ` (${supplierName})` : ''}`,
        quantity,
        unit: 'kWh',
        activity_date: new Date().toISOString().split('T')[0],
        // Pass supplier emission factor for supplier-specific method
        ...(method === 'supplier' && supplierEF > 0 ? { supplier_ef: supplierEF } : {}),
      };

      await createActivity.mutateAsync(payload);

      // Reset form
      setDescription('');
      setQuantity(0);
      setSupplierEF(0);
      setSupplierName('');
      setAutoFilledFactor(null);
      setMarketFactorSource('');
      setSelectedCountry('');
      setSelectedSubregion('');
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

      {/* Region-based Residual Mix Selector */}
      {method === 'residual' && (
        <div className="space-y-4">
          <label className="block text-sm font-medium text-gray-700">
            Region
          </label>
          <div className="grid grid-cols-4 gap-2">
            {[
              { key: 'israel', label: 'Israel' },
              { key: 'europe', label: 'Europe' },
              { key: 'usa', label: 'USA' },
              { key: 'other', label: 'Other' },
            ].map((r) => (
              <button
                key={r.key}
                type="button"
                onClick={() => {
                  setMarketRegion(r.key as typeof marketRegion);
                  setAutoFilledFactor(null);
                  setSelectedCountry('');
                  setSelectedSubregion('');
                }}
                className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
                  marketRegion === r.key
                    ? 'bg-blue-50 border-blue-500 text-blue-700'
                    : 'border-gray-300 text-gray-600 hover:bg-gray-50'
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>

          {/* Region-specific selectors */}
          {marketRegion === 'europe' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                EU Country (AIB Residual Mix)
              </label>
              <select
                value={selectedCountry}
                onChange={(e) => {
                  setSelectedCountry(e.target.value);
                  if (e.target.value) fetchMarketFactor(e.target.value);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">Select country...</option>
                <option value="AT">Austria</option>
                <option value="BE">Belgium</option>
                <option value="BG">Bulgaria</option>
                <option value="HR">Croatia</option>
                <option value="CY">Cyprus</option>
                <option value="CZ">Czech Republic</option>
                <option value="DK">Denmark</option>
                <option value="EE">Estonia</option>
                <option value="FI">Finland</option>
                <option value="FR">France</option>
                <option value="DE">Germany</option>
                <option value="GR">Greece</option>
                <option value="HU">Hungary</option>
                <option value="IE">Ireland</option>
                <option value="IT">Italy</option>
                <option value="LV">Latvia</option>
                <option value="LT">Lithuania</option>
                <option value="LU">Luxembourg</option>
                <option value="MT">Malta</option>
                <option value="NL">Netherlands</option>
                <option value="NO">Norway</option>
                <option value="PL">Poland</option>
                <option value="PT">Portugal</option>
                <option value="RO">Romania</option>
                <option value="SK">Slovakia</option>
                <option value="SI">Slovenia</option>
                <option value="ES">Spain</option>
                <option value="SE">Sweden</option>
                <option value="CH">Switzerland</option>
                <option value="GB">United Kingdom</option>
              </select>
            </div>
          )}

          {marketRegion === 'usa' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                eGRID Subregion (Green-e Residual Mix)
              </label>
              <select
                value={selectedSubregion}
                onChange={(e) => {
                  setSelectedSubregion(e.target.value);
                  if (e.target.value) fetchMarketFactor('US', e.target.value);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">Select subregion...</option>
                <option value="CAMX">CAMX - WECC California</option>
                <option value="ERCT">ERCT - ERCOT Texas</option>
                <option value="FRCC">FRCC - Florida</option>
                <option value="MROW">MROW - MRO West (Midwest)</option>
                <option value="NEWE">NEWE - New England</option>
                <option value="NWPP">NWPP - WECC Northwest</option>
                <option value="NYCW">NYCW - NYC/Westchester</option>
                <option value="NYUP">NYUP - Upstate New York</option>
                <option value="RFCE">RFCE - PJM East</option>
                <option value="RFCM">RFCM - Michigan</option>
                <option value="RFCW">RFCW - PJM West</option>
                <option value="RMPA">RMPA - Rockies</option>
                <option value="SRSO">SRSO - SERC South</option>
                <option value="SRVC">SRVC - Virginia/Carolina</option>
                <option value="SRTV">SRTV - Tennessee Valley</option>
                <option value="SRMW">SRMW - SERC Midwest</option>
                <option value="SPNO">SPNO - SPP North</option>
                <option value="SPSO">SPSO - SPP South</option>
                <option value="AZNM">AZNM - Southwest</option>
              </select>
            </div>
          )}

          {marketRegion === 'other' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Country (iREC / Grid Average)
              </label>
              <select
                value={selectedCountry}
                onChange={(e) => {
                  setSelectedCountry(e.target.value);
                  if (e.target.value) fetchMarketFactor(e.target.value);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">Select country...</option>
                <option value="AU">Australia</option>
                <option value="BR">Brazil</option>
                <option value="CN">China</option>
                <option value="IN">India</option>
                <option value="JP">Japan</option>
                <option value="KR">South Korea</option>
                <option value="SG">Singapore</option>
                <option value="ZA">South Africa</option>
                <option value="TH">Thailand</option>
                <option value="TR">Turkey</option>
                <option value="AE">UAE</option>
                <option value="SA">Saudi Arabia</option>
              </select>
            </div>
          )}

          {marketRegion === 'israel' && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-sm text-amber-700">
                Israel power producer data (BDO יח&quot;פית) will be available once the dataset is provided.
                Currently using IEC grid average as fallback.
              </p>
              <button
                type="button"
                onClick={() => fetchMarketFactor('IL')}
                className="mt-2 text-sm text-amber-600 underline"
              >
                Use Israel grid average →
              </button>
            </div>
          )}

          {/* Auto-filled factor display */}
          {autoFilledFactor !== null && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm font-medium text-green-800">
                Market-based factor: {autoFilledFactor} kg CO2e/kWh
              </p>
              <p className="text-xs text-green-600 mt-1">
                Source: {marketFactorSource}
              </p>
            </div>
          )}

          {marketFactorLoading && (
            <p className="text-sm text-gray-500 animate-pulse">Loading market factor...</p>
          )}
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
