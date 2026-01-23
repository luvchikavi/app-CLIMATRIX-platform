'use client';

import { CategorySummary } from '@/lib/api';
import { categoryNames, formatCO2e } from '@/lib/utils';
import { ChevronRight } from 'lucide-react';

interface CategoryBreakdownProps {
  categories: CategorySummary[];
  onCategoryClick?: (category: CategorySummary) => void;
}

export function CategoryBreakdown({ categories, onCategoryClick }: CategoryBreakdownProps) {
  if (!categories || categories.length === 0) {
    return (
      <div className="text-center py-8 text-foreground-muted">
        No category data available
      </div>
    );
  }

  // Sort by scope then category
  const sorted = [...categories].sort((a, b) => {
    if (a.scope !== b.scope) return a.scope - b.scope;
    return a.category_code.localeCompare(b.category_code);
  });

  // Find max for bar width calculation
  const maxEmission = Math.max(...categories.map((c) => c.total_co2e_kg));

  return (
    <div className="space-y-3">
      {sorted.map((category) => {
        const percentage = (category.total_co2e_kg / maxEmission) * 100;
        const scopeColors: Record<number, string> = {
          1: 'bg-scope1',
          2: 'bg-scope2',
          3: 'bg-scope3',
        };
        const scopeDots: Record<number, string> = {
          1: 'bg-scope1',
          2: 'bg-scope2',
          3: 'bg-scope3',
        };
        const isClickable = !!onCategoryClick;

        return (
          <button
            key={`${category.scope}-${category.category_code}`}
            className={`w-full text-left space-y-1.5 p-2 -mx-2 rounded-lg transition-colors ${
              isClickable ? 'hover:bg-background-muted cursor-pointer' : ''
            }`}
            onClick={() => onCategoryClick?.(category)}
            disabled={!isClickable}
          >
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full ${scopeDots[category.scope]}`}
                />
                <span className="font-mono text-xs text-foreground-muted">
                  {category.category_code}
                </span>
                <span className="font-medium text-foreground">
                  {categoryNames[category.category_code] || category.category_code}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-foreground">
                  {formatCO2e(category.total_co2e_kg)}
                </span>
                {isClickable && (
                  <ChevronRight className="w-4 h-4 text-foreground-muted" />
                )}
              </div>
            </div>
            <div className="h-2 bg-background-muted rounded-full overflow-hidden">
              <div
                className={`h-full ${scopeColors[category.scope]} transition-all duration-500 ease-out`}
                style={{ width: `${percentage}%` }}
              />
            </div>
          </button>
        );
      })}
    </div>
  );
}
