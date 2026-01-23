'use client';

/**
 * CommutingForm - Category 3.7 Employee Commuting
 *
 * Supports 3 methods per GHG Protocol:
 * 1. Survey - Detailed by transport mode (most accurate)
 * 2. Average - National/regional averages per employee
 * 3. Spend - Based on commuting reimbursement costs
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
  Car,
  Train,
  Bike,
  Home,
  Users,
  Info,
} from 'lucide-react';

// =============================================================================
// COMMUTING DATA DEFINITIONS
// =============================================================================

type CommutingMethod = 'survey' | 'average' | 'spend';

// Transport Modes for Survey method
const TRANSPORT_MODES = [
  { key: 'car_petrol', label: 'Car - Petrol', icon: Car, ef: 0.17, category: 'Car' },
  { key: 'car_diesel', label: 'Car - Diesel', icon: Car, ef: 0.17, category: 'Car' },
  { key: 'car_hybrid', label: 'Car - Hybrid', icon: Car, ef: 0.12, category: 'Car' },
  { key: 'car_electric', label: 'Car - Electric', icon: Car, ef: 0.05, category: 'Car' },
  { key: 'motorcycle', label: 'Motorcycle', icon: Car, ef: 0.10, category: 'Motorized' },
  { key: 'bus', label: 'Bus', icon: Train, ef: 0.089, category: 'Public Transit' },
  { key: 'rail', label: 'Rail/Train', icon: Train, ef: 0.035, category: 'Public Transit' },
  { key: 'metro', label: 'Metro/Subway', icon: Train, ef: 0.029, category: 'Public Transit' },
  { key: 'ebike', label: 'E-Bike', icon: Bike, ef: 0.006, category: 'Zero/Low Emission' },
  { key: 'bicycle', label: 'Bicycle', icon: Bike, ef: 0, category: 'Zero/Low Emission' },
  { key: 'walk', label: 'Walk', icon: Bike, ef: 0, category: 'Zero/Low Emission' },
  { key: 'wfh', label: 'Work from Home', icon: Home, ef: 0.5, category: 'Remote' }, // per day
];

// Countries for Average method
const COUNTRIES = [
  { code: 'IL', name: 'Israel', avgKmPerEmployee: 6500 },
  { code: 'GB', name: 'United Kingdom', avgKmPerEmployee: 5800 },
  { code: 'US', name: 'United States', avgKmPerEmployee: 8500 },
  { code: 'DE', name: 'Germany', avgKmPerEmployee: 5200 },
  { code: 'FR', name: 'France', avgKmPerEmployee: 4800 },
  { code: 'NL', name: 'Netherlands', avgKmPerEmployee: 4200 },
  { code: 'JP', name: 'Japan', avgKmPerEmployee: 4500 },
  { code: 'AU', name: 'Australia', avgKmPerEmployee: 7200 },
  { code: 'OTHER', name: 'Other (Global Avg)', avgKmPerEmployee: 5500 },
];

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar', toUSD: 1.00 },
  { code: 'EUR', symbol: '€', name: 'Euro', toUSD: 1.08 },
  { code: 'GBP', symbol: '£', name: 'British Pound', toUSD: 1.27 },
  { code: 'ILS', symbol: '₪', name: 'Israeli Shekel', toUSD: 0.27 },
];

// Emission factor estimates
const EF_ESTIMATES = {
  average_per_employee_km: 0.12, // kg CO2e per employee-km (weighted average)
  spend_per_usd: 0.15, // kg CO2e per USD spent
  wfh_per_day: 0.5, // kg CO2e per WFH day (energy use)
};

interface CommutingFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function CommutingForm({ periodId, onSuccess }: CommutingFormProps) {
  const goBack = useWizardStore((s) => s.goBack);
  const resetWizard = useWizardStore((s) => s.reset);
  const createActivity = useCreateActivity(periodId);

  // Method selection
  const [method, setMethod] = useState<CommutingMethod>('survey');

  // Survey method fields
  const [transportMode, setTransportMode] = useState('car_petrol');
  const [numEmployees, setNumEmployees] = useState<number | null>(null);
  const [avgDistanceOneWay, setAvgDistanceOneWay] = useState<number | null>(null);
  const [workingDays, setWorkingDays] = useState(220);
  const [remoteWorkPct, setRemoteWorkPct] = useState(0);

  // Average method fields
  const [country, setCountry] = useState('IL');
  const [avgNumEmployees, setAvgNumEmployees] = useState<number | null>(null);

  // Spend method fields
  const [spendAmount, setSpendAmount] = useState<number | null>(null);
  const [currency, setCurrency] = useState('USD');

  // Common fields
  const [siteDepartment, setSiteDepartment] = useState('');
  const [description, setDescription] = useState('');
  const [reportingYear, setReportingYear] = useState(new Date().getFullYear());

  // Calculate estimated emissions
  const estimatedEmissions = useMemo(() => {
    if (method === 'survey') {
      if (!numEmployees || numEmployees <= 0) return null;

      const mode = TRANSPORT_MODES.find(m => m.key === transportMode);
      if (!mode) return null;

      if (mode.key === 'wfh') {
        // WFH: employees * days * EF per day
        const days = workingDays * (1 - remoteWorkPct / 100);
        return numEmployees * days * mode.ef;
      }

      // Regular commuting: employees * distance * 2 (round trip) * days * (1 - remote%) * EF
      if (!avgDistanceOneWay || avgDistanceOneWay <= 0) return null;
      const effectiveDays = workingDays * (1 - remoteWorkPct / 100);
      const totalKm = numEmployees * avgDistanceOneWay * 2 * effectiveDays;
      return totalKm * mode.ef;
    }

    if (method === 'average') {
      if (!avgNumEmployees || avgNumEmployees <= 0) return null;
      const countryData = COUNTRIES.find(c => c.code === country);
      const avgKm = countryData?.avgKmPerEmployee || 5500;
      return avgNumEmployees * avgKm * EF_ESTIMATES.average_per_employee_km;
    }

    if (method === 'spend') {
      if (!spendAmount || spendAmount <= 0) return null;
      // Convert to USD first, then apply emission factor
      const currencyRate = CURRENCIES.find(c => c.code === currency)?.toUSD || 1;
      const amountInUSD = spendAmount * currencyRate;
      return amountInUSD * EF_ESTIMATES.spend_per_usd;
    }

    return null;
  }, [
    method, transportMode, numEmployees, avgDistanceOneWay, workingDays,
    remoteWorkPct, avgNumEmployees, country, spendAmount, currency
  ]);

  // Build activity payload
  const buildPayload = () => {
    const basePayload = {
      scope: 3,
      category_code: '3.7',
      activity_date: `${reportingYear}-06-30`, // Mid-year as default
    };

    if (method === 'spend') {
      return {
        ...basePayload,
        activity_key: 'commute_spend_general',
        quantity: spendAmount,
        unit: currency,
        description: description || `Employee commuting reimbursement - ${siteDepartment || 'All employees'}`,
      };
    }

    if (method === 'average') {
      const countryData = COUNTRIES.find(c => c.code === country);
      const avgKm = countryData?.avgKmPerEmployee || 5500;
      return {
        ...basePayload,
        activity_key: 'commute_average',
        quantity: (avgNumEmployees || 0) * avgKm,
        unit: 'employee-km',
        description: description || `Employee commuting (${countryData?.name || 'Global'} average) - ${avgNumEmployees} employees`,
      };
    }

    // Survey method
    const mode = TRANSPORT_MODES.find(m => m.key === transportMode);
    const activityKeyMap: Record<string, string> = {
      car_petrol: 'commute_car_petrol',
      car_diesel: 'commute_car_diesel',
      car_hybrid: 'commute_car_hybrid',
      car_electric: 'commute_car_electric',
      motorcycle: 'commute_motorcycle',
      bus: 'commute_bus',
      rail: 'commute_rail',
      metro: 'commute_rail',
      ebike: 'commute_ebike',
      bicycle: 'commute_bicycle',
      walk: 'commute_walk',
      wfh: 'commute_wfh_day',
    };

    if (transportMode === 'wfh') {
      const wfhDays = (numEmployees || 0) * workingDays;
      return {
        ...basePayload,
        activity_key: 'commute_wfh_day',
        quantity: wfhDays,
        unit: 'days',
        description: description || `Work from Home - ${numEmployees} employees, ${workingDays} days/year`,
      };
    }

    const effectiveDays = workingDays * (1 - remoteWorkPct / 100);
    const totalKm = (numEmployees || 0) * (avgDistanceOneWay || 0) * 2 * effectiveDays;

    return {
      ...basePayload,
      activity_key: activityKeyMap[transportMode] || 'commute_car_petrol',
      quantity: totalKm,
      unit: 'km',
      description: description || `${mode?.label || 'Commuting'} - ${numEmployees} employees, ${avgDistanceOneWay}km one-way`,
    };
  };

  const isValid = () => {
    if (method === 'spend') {
      return spendAmount && spendAmount > 0;
    }
    if (method === 'average') {
      return avgNumEmployees && avgNumEmployees > 0;
    }
    // Survey
    if (transportMode === 'wfh') {
      return numEmployees && numEmployees > 0 && workingDays > 0;
    }
    return numEmployees && numEmployees > 0 && avgDistanceOneWay && avgDistanceOneWay > 0;
  };

  const handleSave = async (addAnother = false) => {
    if (!isValid()) return;

    const payload = buildPayload();
    await createActivity.mutateAsync(payload as any);

    if (addAnother) {
      // Reset form but keep method
      setDescription('');
      setSiteDepartment('');
      setNumEmployees(null);
      setAvgDistanceOneWay(null);
      setAvgNumEmployees(null);
      setSpendAmount(null);
    } else {
      resetWizard();
      onSuccess?.();
    }
  };

  // Group transport modes by category
  const groupedModes = TRANSPORT_MODES.reduce((acc, mode) => {
    if (!acc[mode.category]) acc[mode.category] = [];
    acc[mode.category].push(mode);
    return acc;
  }, {} as Record<string, typeof TRANSPORT_MODES>);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Employee Commuting</h2>
          <p className="text-sm text-foreground-muted">Category 3.7 - Record employee travel to/from work</p>
        </div>
        <Button variant="ghost" size="sm" onClick={goBack}>
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back
        </Button>
      </div>

      {/* Method Selection */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">Calculation Method</label>
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => setMethod('survey')}
            className={`p-3 rounded-lg border text-sm font-medium transition-colors ${
              method === 'survey'
                ? 'bg-primary/10 border-primary text-primary'
                : 'bg-background border-border text-foreground hover:border-primary/50'
            }`}
          >
            <Users className="w-5 h-5 mx-auto mb-1" />
            Survey
            <span className="block text-xs text-foreground-muted mt-1">Most accurate</span>
          </button>
          <button
            onClick={() => setMethod('average')}
            className={`p-3 rounded-lg border text-sm font-medium transition-colors ${
              method === 'average'
                ? 'bg-primary/10 border-primary text-primary'
                : 'bg-background border-border text-foreground hover:border-primary/50'
            }`}
          >
            <Users className="w-5 h-5 mx-auto mb-1" />
            Average
            <span className="block text-xs text-foreground-muted mt-1">National avg</span>
          </button>
          <button
            onClick={() => setMethod('spend')}
            className={`p-3 rounded-lg border text-sm font-medium transition-colors ${
              method === 'spend'
                ? 'bg-primary/10 border-primary text-primary'
                : 'bg-background border-border text-foreground hover:border-primary/50'
            }`}
          >
            <Calculator className="w-5 h-5 mx-auto mb-1" />
            Spend
            <span className="block text-xs text-foreground-muted mt-1">Reimbursements</span>
          </button>
        </div>
      </div>

      {/* Survey Method */}
      {method === 'survey' && (
        <div className="space-y-4">
          {/* Transport Mode Selection */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Transport Mode</label>
            <div className="space-y-3">
              {Object.entries(groupedModes).map(([category, modes]) => (
                <div key={category}>
                  <p className="text-xs text-foreground-muted mb-1">{category}</p>
                  <div className="grid grid-cols-4 gap-2">
                    {modes.map(mode => {
                      const Icon = mode.icon;
                      return (
                        <button
                          key={mode.key}
                          onClick={() => setTransportMode(mode.key)}
                          className={`p-2 rounded-lg border text-xs font-medium transition-colors ${
                            transportMode === mode.key
                              ? 'bg-primary/10 border-primary text-primary'
                              : 'bg-background border-border text-foreground hover:border-primary/50'
                          }`}
                        >
                          <Icon className="w-4 h-4 mx-auto mb-1" />
                          {mode.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Employee Count */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Number of Employees</label>
            <Input
              type="number"
              value={numEmployees || ''}
              onChange={(e) => setNumEmployees(e.target.value ? Number(e.target.value) : null)}
              placeholder="e.g., 50"
              min={1}
            />
          </div>

          {/* Distance (not for WFH) */}
          {transportMode !== 'wfh' && (
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Average Distance One-Way (km)</label>
              <Input
                type="number"
                value={avgDistanceOneWay || ''}
                onChange={(e) => setAvgDistanceOneWay(e.target.value ? Number(e.target.value) : null)}
                placeholder="e.g., 25"
                min={0}
              />
            </div>
          )}

          {/* Working Days */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Working Days/Year</label>
              <Input
                type="number"
                value={workingDays}
                onChange={(e) => setWorkingDays(Math.max(1, Number(e.target.value)))}
                min={1}
                max={365}
              />
            </div>
            {transportMode !== 'wfh' && (
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">% Remote Work</label>
                <Input
                  type="number"
                  value={remoteWorkPct}
                  onChange={(e) => setRemoteWorkPct(Math.min(100, Math.max(0, Number(e.target.value))))}
                  min={0}
                  max={100}
                  placeholder="0"
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Average Method */}
      {method === 'average' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Number of Employees</label>
            <Input
              type="number"
              value={avgNumEmployees || ''}
              onChange={(e) => setAvgNumEmployees(e.target.value ? Number(e.target.value) : null)}
              placeholder="e.g., 500"
              min={1}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Country</label>
            <select
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground"
            >
              {COUNTRIES.map(c => (
                <option key={c.code} value={c.code}>
                  {c.name} (~{c.avgKmPerEmployee.toLocaleString()} km/employee/year)
                </option>
              ))}
            </select>
          </div>
          <p className="text-xs text-foreground-muted">
            Uses national average commuting distance and mode mix.
          </p>
        </div>
      )}

      {/* Spend Method */}
      {method === 'spend' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Annual Spend Amount</label>
              <Input
                type="number"
                value={spendAmount || ''}
                onChange={(e) => setSpendAmount(e.target.value ? Number(e.target.value) : null)}
                placeholder="e.g., 75000"
                min={0}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground"
              >
                {CURRENCIES.map(c => (
                  <option key={c.code} value={c.code}>{c.code} - {c.name}</option>
                ))}
              </select>
            </div>
          </div>
          <p className="text-xs text-foreground-muted">
            Enter total annual commuting reimbursements, subsidies, or allowances.
          </p>
        </div>
      )}

      {/* Common Fields */}
      <div className="space-y-4 border-t border-border pt-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Site/Department (Optional)</label>
            <Input
              type="text"
              value={siteDepartment}
              onChange={(e) => setSiteDepartment(e.target.value)}
              placeholder="e.g., Headquarters"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Reporting Year</label>
            <Input
              type="number"
              value={reportingYear}
              onChange={(e) => setReportingYear(Number(e.target.value))}
              min={2020}
              max={2030}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-1">Description (Optional)</label>
          <Input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., Sales team commuting"
          />
        </div>
      </div>

      {/* Emission Estimate */}
      {estimatedEmissions !== null && (
        <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-primary mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-foreground">Estimated Annual Emissions</h4>
              <p className="text-2xl font-bold text-primary mt-1">
                {formatCO2e(estimatedEmissions)}
              </p>
              <p className="text-xs text-foreground-muted mt-1">
                {method === 'survey' && transportMode !== 'wfh' && numEmployees && avgDistanceOneWay && (
                  <>
                    {numEmployees} employees × {avgDistanceOneWay} km × 2 (round trip) × {Math.round(workingDays * (1 - remoteWorkPct / 100))} days
                  </>
                )}
                {method === 'survey' && transportMode === 'wfh' && numEmployees && (
                  <>
                    {numEmployees} employees × {workingDays} WFH days
                  </>
                )}
                {method === 'average' && avgNumEmployees && (
                  <>
                    {avgNumEmployees} employees × ~{(COUNTRIES.find(c => c.code === country)?.avgKmPerEmployee || 5500).toLocaleString()} km/year
                  </>
                )}
                {method === 'spend' && spendAmount && (
                  <>
                    Based on {currency} {spendAmount.toLocaleString()} annual spend
                  </>
                )}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 pt-4">
        <Button
          variant="outline"
          className="flex-1"
          onClick={() => handleSave(true)}
          disabled={!isValid() || createActivity.isPending}
        >
          {createActivity.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <Plus className="w-4 h-4 mr-2" />
          )}
          Save & Add Another
        </Button>
        <Button
          className="flex-1"
          onClick={() => handleSave(false)}
          disabled={!isValid() || createActivity.isPending}
        >
          {createActivity.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          Save
        </Button>
      </div>
    </div>
  );
}
