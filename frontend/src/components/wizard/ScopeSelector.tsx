'use client';

import { useWizardStore } from '@/stores/wizard';
import { Flame, Zap, Globe } from 'lucide-react';
import { cn } from '@/lib/utils';

const SCOPES = [
  {
    scope: 1 as const,
    name: 'Scope 1',
    subtitle: 'Direct Emissions',
    description: 'Fuel combustion, company vehicles, refrigerants',
    icon: Flame,
    bgColor: 'bg-scope1',
    lightBg: 'hover:bg-[var(--color-scope1-light)]',
    borderColor: 'border-scope1/30',
    ringColor: 'focus:ring-scope1/30',
  },
  {
    scope: 2 as const,
    name: 'Scope 2',
    subtitle: 'Indirect Energy',
    description: 'Purchased electricity, heat, steam, cooling',
    icon: Zap,
    bgColor: 'bg-scope2',
    lightBg: 'hover:bg-[var(--color-scope2-light)]',
    borderColor: 'border-scope2/30',
    ringColor: 'focus:ring-scope2/30',
  },
  {
    scope: 3 as const,
    name: 'Scope 3',
    subtitle: 'Value Chain',
    description: 'Purchased goods, travel, waste, freight',
    icon: Globe,
    bgColor: 'bg-scope3',
    lightBg: 'hover:bg-[var(--color-scope3-light)]',
    borderColor: 'border-scope3/30',
    ringColor: 'focus:ring-scope3/30',
  },
];

export function ScopeSelector() {
  const setScope = useWizardStore((s) => s.setScope);

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-foreground">What type of emission?</h2>
        <p className="mt-2 text-foreground-muted">Select the scope that best matches your activity</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {SCOPES.map((scope) => {
          const Icon = scope.icon;
          return (
            <button
              key={scope.scope}
              onClick={() => setScope(scope.scope)}
              className={cn(
                'p-6 rounded-xl border-2 text-left transition-all duration-200',
                'hover:shadow-md hover:scale-[1.02] focus:outline-none focus:ring-2',
                scope.borderColor,
                scope.lightBg,
                scope.ringColor
              )}
            >
              <div className="flex items-start gap-4">
                <div className={cn('p-3 rounded-lg', scope.bgColor)}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">{scope.name}</h3>
                  <p className="text-sm font-medium text-foreground-muted">{scope.subtitle}</p>
                  <p className="mt-2 text-sm text-foreground-muted">{scope.description}</p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
