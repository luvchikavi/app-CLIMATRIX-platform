'use client';

import { useWizardStore } from '@/stores/wizard';
import { useOrganization } from '@/hooks/useEmissions';
import { ScopeSelector } from './ScopeSelector';
import { CategorySelector } from './CategorySelector';
import { ActivitySelector } from './ActivitySelector';
import { DetailsForm } from './DetailsForm';
import { ReviewStep } from './ReviewStep';
import { PurchasedGoodsForm } from './PurchasedGoodsForm';
import { CapitalGoodsForm } from './CapitalGoodsForm';
import { TransportForm } from './TransportForm';
import { WasteForm } from './WasteForm';
import { BusinessTravelForm } from './BusinessTravelForm';
import { CommutingForm } from './CommutingForm';
import { LeasedAssetsForm } from './LeasedAssetsForm';
import { DownstreamTransportForm } from './DownstreamTransportForm';
import { ProcessingSoldProductsForm } from './ProcessingSoldProductsForm';
import { UseSoldProductsForm } from './UseSoldProductsForm';
import { EndOfLifeForm } from './EndOfLifeForm';
import { DownstreamLeasedAssetsForm } from './DownstreamLeasedAssetsForm';
import { FranchisesForm } from './FranchisesForm';
import { Globe, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

// Categories with specialized forms (skip activity selector)
const SPECIALIZED_CATEGORIES = ['3.1', '3.2', '3.4', '3.5', '3.6', '3.7', '3.8', '3.9', '3.10', '3.11', '3.12', '3.13', '3.14'];

interface ActivityWizardProps {
  periodId: string;
  onSuccess?: () => void;
}

/**
 * Multi-step wizard for adding emission activities
 *
 * Steps:
 * 1. Select Scope (1, 2, 3)
 * 2. Select Category (1.1, 2, 3.1, etc.)
 * 3. Select Activity Type (from explicit activity_key list)
 * 4. Enter Details (quantity, description, date)
 * 5. Review & Submit
 */
export function ActivityWizard({ periodId, onSuccess }: ActivityWizardProps) {
  const step = useWizardStore((s) => s.step);
  const selectedCategory = useWizardStore((s) => s.selectedCategory);
  const { data: org } = useOrganization();

  // Progress indicator - adjust for specialized categories that skip activity step
  const isSpecialized = SPECIALIZED_CATEGORIES.includes(selectedCategory || '');
  const steps = isSpecialized
    ? ['scope', 'category', 'details', 'review']
    : ['scope', 'category', 'activity', 'details', 'review'];
  const stepLabels = isSpecialized
    ? ['Scope', 'Category', 'Details', 'Review']
    : ['Scope', 'Category', 'Activity', 'Details', 'Review'];
  const currentStepIndex = steps.indexOf(step);

  return (
    <div className="max-w-2xl mx-auto">
      {/* Region indicator */}
      {org && (
        <div className="mb-6 flex items-center justify-end gap-2 text-sm text-foreground-muted">
          <Globe className="w-4 h-4" />
          <span>
            Using <strong className="text-foreground">{org.default_region}</strong> emission factors
          </span>
        </div>
      )}

      {/* Progress steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-3">
          {steps.map((s, i) => (
            <div key={s} className="flex items-center">
              <div
                className={cn(
                  'flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium transition-colors',
                  i < currentStepIndex && 'bg-primary text-white',
                  i === currentStepIndex && 'bg-primary text-white ring-4 ring-primary/20',
                  i > currentStepIndex && 'bg-background-muted text-foreground-muted'
                )}
              >
                {i < currentStepIndex ? (
                  <Check className="w-4 h-4" />
                ) : (
                  i + 1
                )}
              </div>
              {i < steps.length - 1 && (
                <div
                  className={cn(
                    'w-16 h-0.5 mx-2',
                    i < currentStepIndex ? 'bg-primary' : 'bg-background-muted'
                  )}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between text-xs text-foreground-muted">
          {stepLabels.map((label, i) => (
            <span
              key={label}
              className={cn(
                'transition-colors',
                i <= currentStepIndex && 'text-foreground font-medium'
              )}
            >
              {label}
            </span>
          ))}
        </div>
      </div>

      {/* Step content */}
      <div className="animate-fade-in">
        {step === 'scope' && <ScopeSelector />}
        {step === 'category' && <CategorySelector />}
        {step === 'activity' && <ActivitySelector />}
        {step === 'details' && (
          // Use specialized forms for certain categories
          selectedCategory === '3.1' ? (
            <PurchasedGoodsForm periodId={periodId} onSuccess={onSuccess} />
          ) : selectedCategory === '3.2' ? (
            <CapitalGoodsForm periodId={periodId} onSuccess={onSuccess} />
          ) : selectedCategory === '3.4' ? (
            <TransportForm periodId={periodId} onSuccess={onSuccess} />
          ) : selectedCategory === '3.5' ? (
            <WasteForm periodId={periodId} onSuccess={onSuccess} />
          ) : selectedCategory === '3.6' ? (
            <BusinessTravelForm periodId={periodId} onSuccess={onSuccess} />
          ) : selectedCategory === '3.7' ? (
            <CommutingForm periodId={periodId} onSuccess={onSuccess} />
          ) : selectedCategory === '3.8' ? (
            <LeasedAssetsForm periodId={periodId} onSuccess={onSuccess} />
          ) : selectedCategory === '3.9' ? (
            <DownstreamTransportForm periodId={periodId} onSuccess={onSuccess} />
          ) : selectedCategory === '3.10' ? (
            <ProcessingSoldProductsForm periodId={periodId} onSuccess={onSuccess} />
          ) : selectedCategory === '3.11' ? (
            <UseSoldProductsForm periodId={periodId} onSuccess={onSuccess} />
          ) : selectedCategory === '3.12' ? (
            <EndOfLifeForm periodId={periodId} onSuccess={onSuccess} />
          ) : selectedCategory === '3.13' ? (
            <DownstreamLeasedAssetsForm periodId={periodId} onSuccess={onSuccess} />
          ) : selectedCategory === '3.14' ? (
            <FranchisesForm periodId={periodId} onSuccess={onSuccess} />
          ) : (
            <DetailsForm periodId={periodId} onSuccess={onSuccess} />
          )
        )}
        {step === 'review' && <ReviewStep periodId={periodId} onSuccess={onSuccess} />}
      </div>
    </div>
  );
}

export { ScopeSelector } from './ScopeSelector';
export { CategorySelector } from './CategorySelector';
export { ActivitySelector } from './ActivitySelector';
export { DetailsForm } from './DetailsForm';
export { ReviewStep } from './ReviewStep';
