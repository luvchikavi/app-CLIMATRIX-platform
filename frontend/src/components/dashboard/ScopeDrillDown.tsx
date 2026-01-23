'use client';

/**
 * ScopeDrillDown - Shows emission breakdown by source type within a scope
 *
 * Scope 1: Breakdown by fuel type (petrol, diesel, natural gas, etc.)
 * Scope 2: Breakdown by country/grid
 * Scope 3: Breakdown by category
 */

import { ActivityWithEmission } from '@/lib/api';
import { formatCO2e, categoryNames } from '@/lib/utils';
import { X, Flame, Zap, Link2, BarChart3 } from 'lucide-react';

interface ScopeDrillDownProps {
  scope: 1 | 2 | 3;
  activities: ActivityWithEmission[];
  onClose: () => void;
}

// Helper to get display name for activity key
function getActivityDisplayName(activityKey: string): string {
  // Common patterns for display names
  const patterns: [RegExp, string][] = [
    // Scope 1 Fuels
    [/natural_gas/, 'Natural Gas'],
    [/diesel/, 'Diesel'],
    [/petrol|gasoline/, 'Petrol/Gasoline'],
    [/lpg/, 'LPG'],
    [/coal/, 'Coal'],
    [/fuel_oil/, 'Fuel Oil'],
    [/propane/, 'Propane'],
    [/butane/, 'Butane'],
    [/kerosene/, 'Kerosene'],
    // Scope 1 Vehicles
    [/car_petrol/, 'Petrol Cars'],
    [/car_diesel/, 'Diesel Cars'],
    [/car_hybrid/, 'Hybrid Cars'],
    [/van/, 'Vans'],
    [/hgv|truck/, 'Trucks/HGV'],
    // Scope 1 Refrigerants
    [/r-?134a/i, 'R-134a'],
    [/r-?410a/i, 'R-410A'],
    [/r-?404a/i, 'R-404A'],
    [/r-?32/i, 'R-32'],
    [/sf6/i, 'SF6'],
    // Scope 2 Electricity by country
    [/electricity_uk/, 'UK Grid'],
    [/electricity_de/, 'Germany Grid'],
    [/electricity_fr/, 'France Grid'],
    [/electricity_es/, 'Spain Grid'],
    [/electricity_it/, 'Italy Grid'],
    [/electricity_nl/, 'Netherlands Grid'],
    [/electricity_pl/, 'Poland Grid'],
    [/electricity_us_ca/, 'USA - California'],
    [/electricity_us_tx/, 'USA - Texas'],
    [/electricity_us_ny/, 'USA - New York'],
    [/electricity_us_mw/, 'USA - Midwest'],
    [/electricity_us/, 'USA Grid (Average)'],
    [/electricity_ca/, 'Canada Grid'],
    [/electricity_il/, 'Israel Grid'],
    [/electricity_jp/, 'Japan Grid'],
    [/electricity_kr/, 'South Korea Grid'],
    [/electricity_cn/, 'China Grid'],
    [/electricity_sg/, 'Singapore Grid'],
    [/electricity_au/, 'Australia Grid'],
    [/electricity_in/, 'India Grid'],
    [/electricity_eu/, 'EU Grid (Average)'],
    [/electricity_global/, 'Global Average'],
    [/electricity_renewable/, 'Renewable (Certified)'],
    [/district_heat/, 'District Heating'],
    [/steam/, 'Steam'],
    // Scope 3
    [/spend_/, 'Spend-based'],
  ];

  for (const [pattern, name] of patterns) {
    if (pattern.test(activityKey)) {
      return name;
    }
  }

  // Fallback: clean up the key
  return activityKey
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

interface BreakdownItem {
  key: string;
  displayName: string;
  co2e_kg: number;
  count: number;
}

export function ScopeDrillDown({ scope, activities, onClose }: ScopeDrillDownProps) {
  // Filter activities for this scope
  const scopeActivities = activities.filter((a) => a.activity.scope === scope);

  // Group by activity_key (for Scope 1 & 2) or category_code (for Scope 3)
  const breakdown: BreakdownItem[] = [];
  const groupMap = new Map<string, { co2e_kg: number; count: number }>();

  for (const item of scopeActivities) {
    const key = scope === 3 ? item.activity.category_code : item.activity.activity_key;
    const existing = groupMap.get(key);
    if (existing) {
      existing.co2e_kg += item.emission?.co2e_kg || 0;
      existing.count += 1;
    } else {
      groupMap.set(key, {
        co2e_kg: item.emission?.co2e_kg || 0,
        count: 1,
      });
    }
  }

  for (const [key, data] of groupMap) {
    breakdown.push({
      key,
      displayName: scope === 3 ? categoryNames[key] || key : getActivityDisplayName(key),
      co2e_kg: data.co2e_kg,
      count: data.count,
    });
  }

  // Sort by emissions descending
  breakdown.sort((a, b) => b.co2e_kg - a.co2e_kg);

  // Calculate total for percentages
  const totalCO2e = breakdown.reduce((sum, item) => sum + item.co2e_kg, 0);

  const scopeLabels = {
    1: 'Scope 1 - Direct Emissions',
    2: 'Scope 2 - Energy',
    3: 'Scope 3 - Value Chain',
  };

  const scopeIcons = {
    1: <Flame className="w-5 h-5 text-red-500" />,
    2: <Zap className="w-5 h-5 text-amber-500" />,
    3: <Link2 className="w-5 h-5 text-blue-500" />,
  };

  const scopeColors = {
    1: 'bg-red-500',
    2: 'bg-amber-500',
    3: 'bg-blue-500',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-neutral-950/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-background-elevated rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden animate-fade-in-up">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-3">
            {scopeIcons[scope]}
            <div>
              <h2 className="text-lg font-semibold text-foreground">
                {scopeLabels[scope]}
              </h2>
              <p className="text-sm text-foreground-muted">
                {formatCO2e(totalCO2e)} from {scopeActivities.length} activities
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-background-muted transition-colors"
          >
            <X className="w-5 h-5 text-foreground-muted" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-100px)]">
          {breakdown.length === 0 ? (
            <div className="text-center py-8 text-foreground-muted">
              No activities found for this scope
            </div>
          ) : (
            <div className="space-y-3">
              {breakdown.map((item) => {
                const percentage = totalCO2e > 0 ? (item.co2e_kg / totalCO2e) * 100 : 0;
                return (
                  <div key={item.key} className="space-y-1.5">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-foreground-muted" />
                        <span className="font-medium text-foreground">
                          {item.displayName}
                        </span>
                        <span className="text-xs text-foreground-muted">
                          ({item.count} {item.count === 1 ? 'activity' : 'activities'})
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-foreground-muted">
                          {percentage.toFixed(1)}%
                        </span>
                        <span className="font-semibold text-foreground min-w-[100px] text-right">
                          {formatCO2e(item.co2e_kg)}
                        </span>
                      </div>
                    </div>
                    <div className="h-2 bg-background-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full ${scopeColors[scope]} transition-all duration-500 ease-out`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer with info */}
        <div className="px-6 py-4 border-t border-border bg-background-muted/50">
          <p className="text-xs text-foreground-muted">
            {scope === 1 && 'Breakdown by fuel type and source. Click a category in the main dashboard for detailed activities.'}
            {scope === 2 && 'Breakdown by electricity grid/country. Different grids have different emission factors.'}
            {scope === 3 && 'Breakdown by GHG Protocol category. Includes upstream, downstream, and value chain emissions.'}
          </p>
        </div>
      </div>
    </div>
  );
}
