'use client';

import { useState, useRef, useEffect } from 'react';
import { useWizardStore } from '@/stores/wizard';
import { useActivityOptions } from '@/hooks/useEmissions';
import { Loader2, AlertCircle, AlertTriangle, DollarSign, Activity, Search, ChevronDown, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { EmissionFactor } from '@/lib/api';

// FIX-4: Helper to determine if an option is spend-based
const CURRENCY_UNITS = ['USD', 'EUR', 'GBP', 'ILS', 'CAD', 'AUD', 'JPY', 'CHF', '$'];

function isSpendBased(factor: EmissionFactor): boolean {
  const unit = (factor.unit || factor.activity_unit || '').toUpperCase();
  return CURRENCY_UNITS.some(currency => unit.includes(currency)) ||
    (factor.activity_key || '').toLowerCase().includes('spend');
}

export function ActivitySelector() {
  const selectedCategory = useWizardStore((s) => s.selectedCategory);
  const setActivityKey = useWizardStore((s) => s.setActivityKey);

  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFactor, setSelectedFactor] = useState<EmissionFactor | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const { data: options, isLoading, error } = useActivityOptions(selectedCategory || '');

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  if (!selectedCategory) return null;

  // FIX-4: Group options by calculation method
  const uniqueOptions = options?.filter((factor, index, self) =>
    index === self.findIndex(f => f.activity_key === factor.activity_key)
  ) || [];

  // Filter by search query
  const filteredOptions = uniqueOptions.filter(factor =>
    factor.display_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    factor.activity_key?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const spendBasedOptions = filteredOptions.filter(isSpendBased);
  const activityBasedOptions = filteredOptions.filter(f => !isSpendBased(f));

  const handleSelect = (factor: EmissionFactor) => {
    setSelectedFactor(factor);
    setActivityKey(factor.activity_key, {
      ...factor,
      activity_unit: factor.unit || factor.activity_unit || '',
    });
    setIsOpen(false);
    setSearchQuery('');
  };

  const totalOptions = uniqueOptions.length;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-foreground">Select Activity Type</h2>
        <p className="text-sm text-foreground-muted">Category {selectedCategory}</p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-2 text-foreground-muted">Loading activity options...</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-error/10 border border-error/20 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-error flex-shrink-0 mt-0.5" />
          <p className="text-error">Failed to load activity options. Please try again.</p>
        </div>
      )}

      {!isLoading && !error && uniqueOptions.length > 0 && (
        <div ref={dropdownRef} className="relative">
          {/* Dropdown Trigger */}
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className={cn(
              'w-full px-4 py-3 rounded-lg border-2 text-left',
              'bg-background-elevated transition-all duration-200',
              'flex items-center justify-between',
              isOpen ? 'border-primary ring-2 ring-primary/20' : 'border-border hover:border-primary/50'
            )}
          >
            {selectedFactor ? (
              <div className="flex-1">
                <span className="font-medium text-foreground">{selectedFactor.display_name}</span>
                <span className="ml-2 text-xs text-foreground-muted">
                  ({selectedFactor.unit || selectedFactor.activity_unit})
                </span>
              </div>
            ) : (
              <span className="text-foreground-muted">
                Choose an activity type ({totalOptions} options)
              </span>
            )}
            <ChevronDown className={cn(
              'w-5 h-5 text-foreground-muted transition-transform',
              isOpen && 'rotate-180'
            )} />
          </button>

          {/* Dropdown Panel */}
          {isOpen && (
            <div className="absolute z-50 w-full mt-2 bg-background-elevated border border-border rounded-lg shadow-lg max-h-80 overflow-hidden">
              {/* Search Input */}
              <div className="p-2 border-b border-border">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground-muted" />
                  <input
                    ref={searchInputRef}
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search activities..."
                    className="w-full pl-9 pr-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>
              </div>

              {/* Options List */}
              <div className="overflow-y-auto max-h-60">
                {/* Activity-based options */}
                {activityBasedOptions.length > 0 && (
                  <div>
                    <div className="px-3 py-2 bg-background-muted border-b border-border flex items-center gap-2 sticky top-0">
                      <Activity className="w-3.5 h-3.5 text-green-600" />
                      <span className="text-xs font-medium text-foreground-muted">Activity-Based ({activityBasedOptions.length})</span>
                    </div>
                    {activityBasedOptions.map((factor, index) => (
                      <button
                        key={factor.id || `activity-${factor.activity_key}-${index}`}
                        onClick={() => handleSelect(factor)}
                        className={cn(
                          'w-full px-3 py-2 text-left text-sm',
                          'hover:bg-primary/10 transition-colors',
                          'flex items-center justify-between',
                          selectedFactor?.activity_key === factor.activity_key && 'bg-primary/5'
                        )}
                      >
                        <div className="flex-1 min-w-0">
                          <span className="font-medium text-foreground truncate block">{factor.display_name}</span>
                          <span className="text-xs text-foreground-muted">
                            {factor.unit || factor.activity_unit}
                            {factor.co2e_factor && ` • ${factor.co2e_factor} kg CO2e`}
                          </span>
                        </div>
                        {selectedFactor?.activity_key === factor.activity_key && (
                          <Check className="w-4 h-4 text-primary flex-shrink-0" />
                        )}
                      </button>
                    ))}
                  </div>
                )}

                {/* Spend-based options */}
                {spendBasedOptions.length > 0 && (
                  <div>
                    <div className="px-3 py-2 bg-background-muted border-b border-border flex items-center gap-2 sticky top-0">
                      <DollarSign className="w-3.5 h-3.5 text-blue-600" />
                      <span className="text-xs font-medium text-foreground-muted">Spend-Based ({spendBasedOptions.length})</span>
                      <span className="text-xs bg-secondary/20 text-secondary px-1.5 py-0.5 rounded">EEIO</span>
                    </div>
                    {spendBasedOptions.map((factor, index) => (
                      <button
                        key={factor.id || `spend-${factor.activity_key}-${index}`}
                        onClick={() => handleSelect(factor)}
                        className={cn(
                          'w-full px-3 py-2 text-left text-sm',
                          'hover:bg-secondary/10 transition-colors',
                          'flex items-center justify-between',
                          selectedFactor?.activity_key === factor.activity_key && 'bg-secondary/5'
                        )}
                      >
                        <div className="flex-1 min-w-0">
                          <span className="font-medium text-foreground truncate block">{factor.display_name}</span>
                          <span className="text-xs text-foreground-muted">
                            {factor.unit || factor.activity_unit}
                            {factor.co2e_factor && ` • ${factor.co2e_factor} kg CO2e`}
                          </span>
                        </div>
                        {selectedFactor?.activity_key === factor.activity_key && (
                          <Check className="w-4 h-4 text-secondary flex-shrink-0" />
                        )}
                      </button>
                    ))}
                  </div>
                )}

                {/* No results */}
                {filteredOptions.length === 0 && searchQuery && (
                  <div className="px-3 py-6 text-center text-sm text-foreground-muted">
                    No activities found for "{searchQuery}"
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Selected Factor Details Card */}
      {selectedFactor && (
        <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg">
          <div className="flex items-start gap-3">
            <div className={cn(
              'p-2 rounded-lg',
              isSpendBased(selectedFactor) ? 'bg-blue-100' : 'bg-green-100'
            )}>
              {isSpendBased(selectedFactor) ? (
                <DollarSign className="w-5 h-5 text-blue-600" />
              ) : (
                <Activity className="w-5 h-5 text-green-600" />
              )}
            </div>
            <div className="flex-1">
              <h4 className="font-medium text-foreground">{selectedFactor.display_name}</h4>
              <div className="mt-1 flex flex-wrap gap-2">
                <span className="text-xs bg-background-muted text-foreground-muted px-2 py-1 rounded">
                  Unit: {selectedFactor.unit || selectedFactor.activity_unit}
                </span>
                {selectedFactor.co2e_factor && (
                  <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">
                    EF: {selectedFactor.co2e_factor} kg CO2e/{selectedFactor.unit || selectedFactor.activity_unit}
                  </span>
                )}
                {selectedFactor.source && (
                  <span className="text-xs bg-background-muted text-foreground-muted px-2 py-1 rounded">
                    Source: {selectedFactor.source}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* If no options found at all */}
      {uniqueOptions.length === 0 && options && options.length === 0 && (
        <div className="p-4 bg-warning/10 border border-warning/20 rounded-lg flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
          <p className="text-warning">No activity types available for this category.</p>
        </div>
      )}
    </div>
  );
}
