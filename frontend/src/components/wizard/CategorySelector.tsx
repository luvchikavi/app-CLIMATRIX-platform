'use client';

import { useWizardStore, CATEGORIES } from '@/stores/wizard';
import { cn } from '@/lib/utils';

export function CategorySelector() {
  const selectedScope = useWizardStore((s) => s.selectedScope);
  const setCategory = useWizardStore((s) => s.setCategory);

  if (!selectedScope) return null;

  const categories = CATEGORIES[selectedScope];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-foreground">Select Category</h2>
        <p className="text-foreground-muted">Scope {selectedScope} emissions</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {categories.map((category) => (
          <button
            key={category.code}
            onClick={() => setCategory(category.code)}
            disabled={category.code === '3.3'} // 3.3 is auto-calculated
            className={cn(
              'p-4 rounded-xl border-2 border-border text-left transition-all duration-200',
              category.code === '3.3'
                ? 'opacity-50 cursor-not-allowed bg-background-muted'
                : 'hover:border-primary/50 hover:bg-primary-light hover:shadow-md'
            )}
          >
            <div className="flex items-start justify-between">
              <div>
                <span className="text-sm font-mono text-foreground-muted">{category.code}</span>
                <h3 className="font-semibold text-foreground">{category.name}</h3>
                <p className="text-sm text-foreground-muted mt-1">{category.description}</p>
              </div>
              {category.code === '3.3' && (
                <span className="text-xs bg-background-muted text-foreground-muted px-2 py-1 rounded">
                  Auto
                </span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
