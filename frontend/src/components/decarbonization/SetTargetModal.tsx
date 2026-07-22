'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  api,
  DecarbonizationTarget,
  TargetFramework,
  TargetCreateRequest,
} from '@/lib/api';
import { Button, Badge } from '@/components/ui';
import { cn, num } from '@/lib/utils';
import { X, Loader2 } from 'lucide-react';

interface SetTargetModalProps {
  isOpen: boolean;
  onClose: () => void;
  existingTarget?: DecarbonizationTarget;
  baselineEmissions?: number;
  baseYear?: number;
  basePeriodId?: string;
}

// Each pathway carries its canonical target year — picking one drives the
// rest of the form (year + default name), so step 2 never asks cold.
const frameworkOptions = [
  {
    value: 'sbti_1_5c' as TargetFramework,
    label: 'SBTi 1.5°C aligned',
    description: 'Most ambitious pathway — 42% reduction by 2030',
    reduction: 42,
    targetYear: 2030 as number | null,
    defaultName: 'SBTi 1.5°C — 2030',
    recommended: true,
  },
  {
    value: 'sbti_wb2c' as TargetFramework,
    label: 'SBTi well-below 2°C',
    description: 'Less aggressive — 25% reduction by 2030',
    reduction: 25,
    targetYear: 2030 as number | null,
    defaultName: 'SBTi well-below 2°C — 2030',
    recommended: false,
  },
  {
    value: 'net_zero' as TargetFramework,
    label: 'Net zero 2050',
    description: 'Long-term commitment to net zero emissions',
    reduction: 90,
    targetYear: 2050 as number | null,
    defaultName: 'Net zero — 2050',
    recommended: false,
  },
  {
    value: 'custom' as TargetFramework,
    label: 'Custom target',
    description: 'Define your own reduction percentage and year',
    reduction: null,
    targetYear: null as number | null,
    defaultName: 'Custom target',
    recommended: false,
  },
];

const fieldLabel = 'block text-[11px] font-bold tracking-[0.06em] uppercase text-cy-faint mb-1.5';
const fieldInput =
  'w-full px-3 py-2.5 rounded-[10px] border-0 bg-cy-row text-[13px] font-semibold text-foreground placeholder:text-cy-faint placeholder:font-normal focus:outline-none focus:ring-2 focus:ring-cy-accent disabled:opacity-50 disabled:cursor-not-allowed';

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
  const [name, setName] = useState(existingTarget?.name || 'SBTi 1.5°C — 2030');
  // Once the user edits the name themselves, framework picks stop clobbering it.
  const [nameTouched, setNameTouched] = useState(!!existingTarget);
  const [framework, setFramework] = useState<TargetFramework>(
    existingTarget?.framework as TargetFramework || 'sbti_1_5c'
  );
  const [targetYear, setTargetYear] = useState(existingTarget?.target_year || 2030);
  const [customReductionPercent, setCustomReductionPercent] = useState(
    num(existingTarget?.target_reduction_percent) || 42
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

  // The chosen pathway drives the form: switching pathway always moves the
  // year to its canonical one (picking "Net zero 2050" while parked on 2030
  // must not keep 2030); the name only follows while the user hasn't named
  // the target themselves.
  const selectFramework = (option: (typeof frameworkOptions)[number]) => {
    const changed = option.value !== framework;
    setFramework(option.value);
    if (option.targetYear && (changed || !existingTarget)) {
      setTargetYear(option.targetYear);
    }
    if (!nameTouched) setName(option.defaultName);
  };

  const createMutation = useMutation({
    // Update in place when editing an existing target; otherwise create a new one.
    // (Previously this always POSTed, stacking duplicate targets on "Edit".)
    mutationFn: (data: TargetCreateRequest) =>
      existingTarget
        ? api.updateDecarbonizationTarget(existingTarget.id, data)
        : api.createDecarbonizationTarget(data),
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
      // Sent for every framework, computed exactly as the review step displays
      // them. For SBTi/net-zero the backend re-derives from the framework and
      // years (TargetCalculationService) and overrides these — that's fine,
      // the explicit values document intent; for custom they're required.
      target_reduction_percent: reductionPercent,
      target_emissions_tco2e: targetEmissions,
    };

    createMutation.mutate(data);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-label="Set target">
      <div className="bg-background-elevated rounded-cy shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between px-6 pt-6 pb-1">
          <div>
            <p className="text-[11px] font-bold tracking-[0.08em] uppercase text-cy-accent mb-1.5">
              Plan · step {step} of 3
            </p>
            <h2 className="text-[16px] font-bold text-foreground tracking-[-0.01em]">
              {existingTarget
                ? 'Edit your target'
                : framework === 'custom'
                  ? 'Set your custom target'
                  : `Set your ${targetYear} target`}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-cy-row rounded-md text-cy-muted hover:text-foreground"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-4 px-3 py-2.5 rounded-[10px] bg-error-50 text-error text-[12.5px]">
              {error}
            </div>
          )}

          {/* Step 1: Select Framework */}
          {step === 1 && (
            <div className="space-y-4">
              {baselineEmissions ? (
                <p className="text-[12.5px] text-cy-muted">
                  Baseline {baseYear} ·{' '}
                  <b className="font-bold text-foreground tabular-nums">
                    {baselineEmissions.toLocaleString(undefined, { maximumFractionDigits: 0 })} t CO₂e
                  </b>
                </p>
              ) : null}
              <div className="grid gap-1">
                {frameworkOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => selectFramework(option)}
                    className={cn(
                      'px-3.5 py-3 rounded-[12px] text-left transition-colors',
                      framework === option.value
                        ? 'bg-cy-accent-soft'
                        : 'hover:bg-cy-row'
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={cn(
                            'text-[13.5px] font-semibold',
                            framework === option.value ? 'text-cy-accent' : 'text-foreground'
                          )}>
                            {option.label}
                          </span>
                          {option.recommended && (
                            <Badge variant="success" size="sm">Recommended</Badge>
                          )}
                        </div>
                        <p className="text-[12.5px] text-cy-muted mt-0.5">{option.description}</p>
                      </div>
                      {framework === option.value && (
                        <span className="text-cy-accent font-bold text-[13px] shrink-0" aria-hidden="true">✓</span>
                      )}
                    </div>
                  </button>
                ))}
              </div>

              {/* Custom reduction input */}
              {framework === 'custom' && (
                <div className="mt-4">
                  <label className={fieldLabel}>Custom reduction</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={customReductionPercent}
                      onChange={(e) => setCustomReductionPercent(Number(e.target.value))}
                      className={cn(fieldInput, 'w-24')}
                    />
                    <span className="text-cy-muted text-[13px]">%</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Configure Details */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <label className={fieldLabel}>Target name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    setNameTouched(true);
                  }}
                  className={fieldInput}
                  placeholder="e.g., Net zero — 2050"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={fieldLabel}>Base year</label>
                  <input
                    type="number"
                    value={baseYear}
                    disabled
                    className={fieldInput}
                  />
                </div>
                <div>
                  <label className={fieldLabel}>Target year</label>
                  <input
                    type="number"
                    min={baseYear + 1}
                    max={2100}
                    value={targetYear}
                    onChange={(e) => setTargetYear(Number(e.target.value))}
                    className={fieldInput}
                  />
                  {framework !== 'custom' && selectedFramework && (
                    <p className="text-[11.5px] text-cy-faint mt-1.5">
                      From your {selectedFramework.label} pathway — adjustable
                    </p>
                  )}
                </div>
              </div>

              <div>
                <label className={fieldLabel}>Scope coverage</label>
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center gap-2 cursor-pointer text-[13px] text-foreground">
                    <input
                      type="checkbox"
                      checked={includeScope1}
                      onChange={(e) => setIncludeScope1(e.target.checked)}
                      className="w-4 h-4 rounded accent-[var(--cy-accent)]"
                    />
                    Scope 1
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer text-[13px] text-foreground">
                    <input
                      type="checkbox"
                      checked={includeScope2}
                      onChange={(e) => setIncludeScope2(e.target.checked)}
                      className="w-4 h-4 rounded accent-[var(--cy-accent)]"
                    />
                    Scope 2
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer text-[13px] text-foreground">
                    <input
                      type="checkbox"
                      checked={includeScope3}
                      onChange={(e) => setIncludeScope3(e.target.checked)}
                      className="w-4 h-4 rounded accent-[var(--cy-accent)]"
                    />
                    Scope 3
                  </label>
                </div>
                <p className="text-[11.5px] text-cy-faint mt-2">
                  SBTi requires Scope 1+2. Scope 3 is recommended if it&apos;s more than 40% of your footprint.
                </p>
              </div>
            </div>
          )}

          {/* Step 3: Review */}
          {step === 3 && (
            <div className="space-y-5">
              <div className="p-4 rounded-[12px] bg-cy-accent-soft">
                <p className="text-[11px] font-bold tracking-[0.08em] uppercase text-cy-accent mb-3.5">
                  Your target
                </p>

                <dl className="grid grid-cols-2 gap-4">
                  <div>
                    <dt className="text-[11.5px] text-cy-muted">Name</dt>
                    <dd className="text-[13px] font-semibold text-foreground">{name}</dd>
                  </div>
                  <div>
                    <dt className="text-[11.5px] text-cy-muted">Framework</dt>
                    <dd className="text-[13px] font-semibold text-foreground">
                      {frameworkOptions.find(f => f.value === framework)?.label}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-[11.5px] text-cy-muted">Baseline ({baseYear})</dt>
                    <dd className="text-[13px] font-semibold text-foreground tabular-nums">
                      {baselineEmissions?.toLocaleString()} t CO₂e
                    </dd>
                  </div>
                  <div>
                    <dt className="text-[11.5px] text-cy-muted">Target ({targetYear})</dt>
                    <dd className="text-[13px] font-semibold text-cy-accent tabular-nums">
                      {targetEmissions.toLocaleString(undefined, { maximumFractionDigits: 0 })} t CO₂e · −{reductionPercent}%
                    </dd>
                  </div>
                  <div>
                    <dt className="text-[11.5px] text-cy-muted">Scope coverage</dt>
                    <dd className="text-[13px] font-semibold text-foreground">
                      {[includeScope1 && '1', includeScope2 && '2', includeScope3 && '3']
                        .filter(Boolean)
                        .join(', ')}
                    </dd>
                  </div>
                </dl>
              </div>

              <p className="text-[12.5px] text-cy-muted">
                Saving this target unlocks your plan — progress tracking and measures matched to your data.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-6 pb-6">
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
                <Loader2 className="w-4 h-4 animate-spin" />
                Saving…
              </>
            ) : step < 3 ? (
              'Continue'
            ) : (
              'Save target'
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
