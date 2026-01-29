'use client';

import { PersonalizedRecommendation } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  Loader2,
  Lightbulb,
  TrendingDown,
  DollarSign,
  Clock,
  ArrowRight,
  Zap,
  Truck,
  Leaf,
  Factory,
  Building2,
  Recycle,
} from 'lucide-react';

interface RecommendationsCardProps {
  recommendations?: PersonalizedRecommendation[];
  isLoading?: boolean;
  onViewAll?: () => void;
}

const categoryIcons: Record<string, React.ElementType> = {
  energy_efficiency: Zap,
  renewable_energy: Leaf,
  fleet_transport: Truck,
  supply_chain: Factory,
  process_change: Building2,
  behavior_change: Lightbulb,
  waste_reduction: Recycle,
  carbon_removal: Leaf,
};

const categoryColors: Record<string, string> = {
  energy_efficiency: 'bg-warning/10 text-warning',
  renewable_energy: 'bg-success/10 text-success',
  fleet_transport: 'bg-primary/10 text-primary',
  supply_chain: 'bg-secondary/10 text-secondary',
  process_change: 'bg-error/10 text-error',
  behavior_change: 'bg-warning/10 text-warning',
  waste_reduction: 'bg-success/10 text-success',
  carbon_removal: 'bg-primary/10 text-primary',
};

export function RecommendationsCard({
  recommendations,
  isLoading,
  onViewAll,
}: RecommendationsCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Personalized Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-primary animate-spin" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Personalized Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-foreground-muted">
            <Lightbulb className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No recommendations available yet.</p>
            <p className="text-sm mt-1">Import emission data to get personalized suggestions.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-warning" />
            <span>Top Recommendations for You</span>
          </div>
          {onViewAll && (
            <Button variant="ghost" size="sm" onClick={onViewAll}>
              View All
              <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {recommendations.map((rec, index) => {
            const Icon = categoryIcons[rec.initiative_category] || Lightbulb;
            const colorClass = categoryColors[rec.initiative_category] || 'bg-foreground-muted/10 text-foreground-muted';

            return (
              <div
                key={`${rec.initiative_id}-${rec.target_activity_key}`}
                className="p-4 rounded-lg border border-border hover:border-primary/50 transition-colors"
              >
                <div className="flex items-start gap-4">
                  <div className={cn('p-2 rounded-lg', colorClass)}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h4 className="font-medium text-foreground">{rec.initiative_name}</h4>
                        <p className="text-sm text-foreground-muted mt-0.5">
                          Targets: {rec.target_source_name}
                        </p>
                      </div>
                      <Badge
                        variant={rec.impact_score >= 7 ? 'success' : rec.impact_score >= 4 ? 'warning' : 'secondary'}
                      >
                        {rec.impact_score >= 7 ? 'High Impact' : rec.impact_score >= 4 ? 'Medium' : 'Low'}
                      </Badge>
                    </div>

                    <p className="text-sm text-foreground-muted mt-2 line-clamp-2">
                      {rec.relevance_explanation}
                    </p>

                    <div className="flex flex-wrap items-center gap-4 mt-3">
                      <div className="flex items-center gap-1 text-sm">
                        <TrendingDown className="w-4 h-4 text-success" />
                        <span className="font-medium text-success">
                          -{rec.potential_reduction_tco2e.toLocaleString()} tCO2e
                        </span>
                        <span className="text-foreground-muted">
                          ({rec.reduction_as_percent_of_total.toFixed(1)}%)
                        </span>
                      </div>

                      {rec.estimated_capex && (
                        <div className="flex items-center gap-1 text-sm text-foreground-muted">
                          <DollarSign className="w-4 h-4" />
                          <span>${(rec.estimated_capex / 1000).toFixed(0)}K investment</span>
                        </div>
                      )}

                      {rec.payback_years && (
                        <div className="flex items-center gap-1 text-sm text-foreground-muted">
                          <Clock className="w-4 h-4" />
                          <span>{rec.payback_years.toFixed(1)} yr payback</span>
                        </div>
                      )}
                    </div>

                    {rec.co_benefits && rec.co_benefits.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {rec.co_benefits.slice(0, 3).map((benefit, i) => (
                          <Badge key={i} variant="secondary" className="text-xs">
                            {benefit}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
