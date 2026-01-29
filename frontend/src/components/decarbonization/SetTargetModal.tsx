'use client';

import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  api,
  DecarbonizationTarget,
  TargetFramework,
  TargetCreateRequest,
} from '@/lib/api';
import { Button, Badge } from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  X,
  Target,
  Loader2,
  CheckCircle2,
  Info,
} from 'lucide-react';

interface SetTargetModalProps {
  isOpen: boolean;
  onClose: () => void;
  existingTarget?: DecarbonizationTarget;
  baselineEmissions?: number;
  baseYear?: number;
  basePeriodId?: string;
}

const frameworkOptions = [
  {
    value: 'sbti_1_5c' as TargetFramework,
    label: 'SBTi 1.5°C Aligned',
    description: 'Most ambitious pathway - 42% reduction by 2030',
    reduction: 42,
    recommended: true,
  },
  {
    value: 'sbti_wb2c' as TargetFramework,
    label: 'SBTi Well-Below 2°C',
    description: 'Less aggressive - 25% reduction by 2030',
    reduction: 25,
    recommended: false,
  },
  {
    value: 'net_zero' as TargetFramework,
    label: 'Net Zero 2050',
    description: 'Long-term commitment to net zero emissions',
    reduction: 90,
    recommended: false,
  },
  {
    value: 'custom' as TargetFramework,
    label: 'Custom Target',
    description: 'Define your own reduction percentage',
    reduction: null,
    recommended: false,
  },
];

export function SetTargetModal({
  isOpen,
  onClose,
  existingTarget,
  baselineEmissions,
  baseYear = new Date().getFullYear(),
  basePeriodId,
}: SetTargetModalProps) {
  const queryClient = useQueryClient();

  const [step, setStep] = useState(1);
  const [name, setName] = useState(existingTarget?.name || 'SBTi 2030 Target');
  const [framework, setFramework] = useState<TargetFramework>(
    existingTarget?.framework as TargetFramework || 'sbti_1_5c'
  );
  const [targetYear, setTargetYear] = useState(existingTarget?.target_year || 2030);
  const [customReductionPercent, setCustomReductionPercent] = useState(
    existingTarget?.target_reduction_percent || 42
  );
  const [includeScope1, setIncludeScope1] = useState(existingTarget?.includes_scope1 ?? true);
  const [includeScope2, setIncludeScope2] = useState(existingTarget?.includes_scope2 ?? true);
  const [includeScope3, setIncludeScope3] = useState(existingTarget?.includes_scope3 ?? false);
  const [error, setError] = useState<string | null>(null);

  // Calculate target emissions based on framework
  const selectedFramework = frameworkOptions.find(f => f.value === framework);
  const reductionPercent = framework === 'custom' ? customReductionPercent : selectedFramework?.reduction || 42;
  const targetEmissions = baselineEmissions
    ? baselineEmissions * (1 - reductionPercent / 100)
    : 0;

  const createMutation = useMutation({
    mutationFn: (data: TargetCreateRequest) => api.createDecarbonizationTarget(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['decarbonization-targets'] });
      onClose();
    },
    onError: (error: Error) => {
      setError(error.message);
    },
  });

  const handleSubmit = () => {
    if (!baselineEmissions) {
      setError('No baseline emissions available');
      return;
    }

    const data: TargetCreateRequest = {
      name,
      framework,
      base_year: baseYear,
      base_year_period_id: basePeriodId,
      base_year_emissions_tco2e: baselineEmissions,
      target_year: targetYear,
      includes_scope1: includeScope1,
      includes_scope2: includeScope2,
      includes_scope3: includeScope3,
    };

    if (framework === 'custom') {
      data.target_reduction_percent = customReductionPercent;
      data.target_emissions_tco2e = targetEmissions;
    }

    createMutation.mutate(data);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-background rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Target className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-foreground">
                {existingTarget ? 'Edit Target' : 'Set Decarbonization Target'}
              </h2>
              <p className="text-sm text-foreground-muted">
                Step {step} of 3
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-background-muted rounded-lg">
            <X className="w-5 h-5 text-foreground-muted" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-error/10 text-error text-sm">
              {error}
            </div>
          )}

          {/* Step 1: Select Framework */}
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="font-medium text-foreground">Select Target Framework</h3>
              <div className="grid gap-3">
                {frameworkOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setFramework(option.value)}
                    className={cn(
                      "p-4 rounded-lg border text-left transition-colors",
                      framework === option.value
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    )}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-foreground">{option.label}</span>
                          {option.recommended && (
                            <Badge variant="success" className="text-xs">Recommended</Badge>
                          )}
                        </div>
                        <p className="text-sm text-foreground-muted mt-1">{option.description}</p>
                      </div>
                      {framework === option.value && (
                        <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0" />
                      )}
                    </div>
                  </button>
                ))}
              </div>

              {/* Custom reduction input */}
              {framework === 'custom' && (
                <div className="mt-4">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Custom Reduction Percentage
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={customReductionPercent}
                      onChange={(e) => setCustomReductionPercent(Number(e.target.value))}
                      className="w-24 px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                    <span className="text-foreground-muted">%</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Configure Details */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Target Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  placeholder="e.g., SBTi 2030 Target"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Base Year
                  </label>
                  <input
                    type="number"
                    value={baseYear}
                    disabled
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background-muted text-foreground-muted"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Target Year
                  </label>
                  <input
                    type="number"
                    min={baseYear + 1}
                    max={2100}
                    value={targetYear}
                    onChange={(e) => setTargetYear(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Scope Coverage
                </label>
                <div className="flex flex-wrap gap-3">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includeScope1}
                      onChange={(e) => setIncludeScope1(e.target.checked)}
                      className="w-4 h-4 rounded border-border"
                    />
                    <span className="text-foreground">Scope 1</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includeScope2}
                      onChange={(e) => setIncludeScope2(e.target.checked)}
                      className="w-4 h-4 rounded border-border"
                    />
                    <span className="text-foreground">Scope 2</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includeScope3}
                      onChange={(e) => setIncludeScope3(e.target.checked)}
                      className="w-4 h-4 rounded border-border"
                    />
                    <span className="text-foreground">Scope 3</span>
                  </label>
                </div>
                <p className="text-xs text-foreground-muted mt-2">
                  SBTi requires Scope 1+2. Scope 3 is recommended if it's more than 40% of your footprint.
                </p>
              </div>
            </div>
          )}

          {/* Step 3: Review */}
          {step === 3 && (
            <div className="space-y-6">
              <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                <div className="flex items-center gap-2 mb-4">
                  <Info className="w-5 h-5 text-primary" />
                  <span className="font-medium text-foreground">Target Summary</span>
                </div>

                <dl className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <dt className="text-foreground-muted">Target Name</dt>
                    <dd className="font-medium text-foreground">{name}</dd>
                  </div>
                  <div>
                    <dt className="text-foreground-muted">Framework</dt>
                    <dd className="font-medium text-foreground">
                      {frameworkOptions.find(f => f.value === framework)?.label}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-foreground-muted">Base Year Emissions</dt>
                    <dd className="font-medium text-foreground">
                      {baselineEmissions?.toLocaleString()} tCO2e
                    </dd>
                  </div>
                  <div>
                    <dt className="text-foreground-muted">Target ({targetYear})</dt>
                    <dd className="font-medium text-success">
                      {targetEmissions.toLocaleString(undefined, { maximumFractionDigits: 0 })} tCO2e
                    </dd>
                  </div>
                  <div>
                    <dt className="text-foreground-muted">Reduction</dt>
                    <dd className="font-medium text-success">-{reductionPercent}%</dd>
                  </div>
                  <div>
                    <dt className="text-foreground-muted">Scope Coverage</dt>
                    <dd className="font-medium text-foreground">
                      {[includeScope1 && '1', includeScope2 && '2', includeScope3 && '3']
                        .filter(Boolean)
                        .join(', ')}
                    </dd>
                  </div>
                </dl>
              </div>

              <div className="p-3 rounded-lg bg-success/10">
                <p className="text-sm text-success">
                  Setting this target will help you track progress and receive personalized recommendations
                  for achieving your decarbonization goals.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-border">
          <Button
            variant="ghost"
            onClick={() => step > 1 ? setStep(step - 1) : onClose()}
          >
            {step > 1 ? 'Back' : 'Cancel'}
          </Button>
          <Button
            onClick={() => step < 3 ? setStep(step + 1) : handleSubmit()}
            disabled={createMutation.isPending}
          >
            {createMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : step < 3 ? (
              'Continue'
            ) : (
              'Create Target'
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
