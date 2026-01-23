'use client';

/**
 * Scope2Comparison - Location vs Market-based comparison for Scope 2
 *
 * Shows the difference between:
 * - Location-based: Grid average emission factor
 * - Market-based: Residual mix (excludes tracked renewable energy)
 */

import { useScope2Comparison } from '@/hooks/useEmissions';
import { formatCO2e } from '@/lib/utils';
import { Loader2, TrendingUp, TrendingDown, Minus, AlertCircle, Zap, Info } from 'lucide-react';

interface Scope2ComparisonProps {
  periodId: string;
}

export function Scope2Comparison({ periodId }: Scope2ComparisonProps) {
  const { data, isLoading, error } = useScope2Comparison(periodId);

  if (isLoading) {
    return (
      <div className="p-6 bg-background-elevated rounded-lg border border-border">
        <div className="flex items-center gap-2 text-foreground-muted">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Loading Scope 2 comparison...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-error/10 border border-error/20 rounded-lg">
        <div className="flex items-center gap-2 text-error">
          <AlertCircle className="w-4 h-4" />
          <span>Failed to load Scope 2 comparison</span>
        </div>
      </div>
    );
  }

  if (!data || data.total_activities === 0) {
    return (
      <div className="p-6 bg-background-elevated rounded-lg border border-border">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-amber-100 rounded-lg">
            <Zap className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">Scope 2 Comparison</h3>
            <p className="text-sm text-foreground-muted">Location vs Market-based</p>
          </div>
        </div>
        <p className="text-foreground-muted text-sm">
          No Scope 2 activities found. Add electricity consumption to see the comparison.
        </p>
      </div>
    );
  }

  const hasMarketData = data.total_market_co2e_kg !== null;
  const difference = data.total_difference_kg || 0;
  const differencePercent = data.total_difference_percent || 0;

  return (
    <div className="p-6 bg-background-elevated rounded-lg border border-border">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-amber-100 rounded-lg">
          <Zap className="w-5 h-5 text-amber-600" />
        </div>
        <div>
          <h3 className="font-semibold text-foreground">Scope 2 Comparison</h3>
          <p className="text-sm text-foreground-muted">Location vs Market-based ({data.total_activities} activities)</p>
        </div>
      </div>

      {/* Main comparison */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* Location-based */}
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="text-sm font-medium text-blue-700 mb-1">Location-based</div>
          <div className="text-2xl font-bold text-blue-900">
            {formatCO2e(data.total_location_co2e_kg)}
          </div>
          <div className="text-xs text-blue-600 mt-1">Grid average factor</div>
        </div>

        {/* Market-based */}
        <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
          <div className="text-sm font-medium text-purple-700 mb-1">Market-based</div>
          <div className="text-2xl font-bold text-purple-900">
            {hasMarketData ? formatCO2e(data.total_market_co2e_kg!) : 'N/A'}
          </div>
          <div className="text-xs text-purple-600 mt-1">
            {hasMarketData ? 'Residual mix factor' : 'No market factor available'}
          </div>
        </div>
      </div>

      {/* Difference indicator */}
      {hasMarketData && (
        <div className={`p-3 rounded-lg border ${
          difference > 0
            ? 'bg-red-50 border-red-200'
            : difference < 0
              ? 'bg-green-50 border-green-200'
              : 'bg-gray-50 border-gray-200'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {difference > 0 ? (
                <TrendingUp className="w-4 h-4 text-red-600" />
              ) : difference < 0 ? (
                <TrendingDown className="w-4 h-4 text-green-600" />
              ) : (
                <Minus className="w-4 h-4 text-gray-600" />
              )}
              <span className={`text-sm font-medium ${
                difference > 0 ? 'text-red-700' : difference < 0 ? 'text-green-700' : 'text-gray-700'
              }`}>
                {difference > 0 ? 'Market-based is higher' : difference < 0 ? 'Location-based is higher' : 'No difference'}
              </span>
            </div>
            <div className={`text-sm font-bold ${
              difference > 0 ? 'text-red-700' : difference < 0 ? 'text-green-700' : 'text-gray-700'
            }`}>
              {difference > 0 ? '+' : ''}{formatCO2e(Math.abs(difference))} ({differencePercent > 0 ? '+' : ''}{differencePercent.toFixed(1)}%)
            </div>
          </div>
        </div>
      )}

      {/* Info about methods */}
      <div className="mt-4 p-3 bg-info/10 border border-info/20 rounded-lg">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-info mt-0.5" />
          <div className="text-xs text-info">
            <p className="font-medium">GHG Protocol requires dual reporting for Scope 2</p>
            <p className="mt-1">
              <strong>Location-based</strong> uses grid average factors. <strong>Market-based</strong> uses residual mix factors, which exclude renewable energy with certificates.
            </p>
          </div>
        </div>
      </div>

      {/* Countries without market factor */}
      {data.countries_without_market_factor.length > 0 && (
        <div className="mt-3 text-xs text-foreground-muted">
          <span className="font-medium">Note:</span> Market factors not available for: {data.countries_without_market_factor.join(', ')}
        </div>
      )}
    </div>
  );
}
