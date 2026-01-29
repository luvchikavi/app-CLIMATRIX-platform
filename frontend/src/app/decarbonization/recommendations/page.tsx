'use client';

import { useQuery } from '@tanstack/react-query';
import { api, PersonalizedRecommendation } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  Loader2,
  ArrowLeft,
  Lightbulb,
  TrendingDown,
  DollarSign,
  Clock,
  Zap,
  Truck,
  Leaf,
  Factory,
  Building2,
  Recycle,
  Filter,
  Plus,
} from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

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

const categoryLabels: Record<string, string> = {
  energy_efficiency: 'Energy Efficiency',
  renewable_energy: 'Renewable Energy',
  fleet_transport: 'Fleet & Transport',
  supply_chain: 'Supply Chain',
  process_change: 'Process Change',
  behavior_change: 'Behavior Change',
  waste_reduction: 'Waste Reduction',
  carbon_removal: 'Carbon Removal',
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

export default function RecommendationsPage() {
  const { user } = useAuthStore();
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);

  const { data: recommendations, isLoading } = useQuery({
    queryKey: ['all-recommendations', user?.active_period_id, categoryFilter],
    queryFn: () => api.getRecommendations(user?.active_period_id || '', 50, categoryFilter || undefined),
    enabled: !!user?.active_period_id,
  });

  const categories = Object.keys(categoryLabels);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/decarbonization">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Reduction Recommendations</h1>
            <p className="text-foreground-muted">Personalized initiatives based on your emission profile</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center gap-2 flex-wrap">
            <Filter className="w-4 h-4 text-foreground-muted" />
            <span className="text-sm text-foreground-muted mr-2">Filter by category:</span>
            <Button
              variant={categoryFilter === null ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setCategoryFilter(null)}
            >
              All
            </Button>
            {categories.map((cat) => (
              <Button
                key={cat}
                variant={categoryFilter === cat ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setCategoryFilter(cat)}
              >
                {categoryLabels[cat]}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recommendations List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      ) : !recommendations || recommendations.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-foreground-muted">
              <Lightbulb className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No recommendations found.</p>
              <p className="text-sm mt-1">Try changing the filter or import more emission data.</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {recommendations.map((rec) => {
            const Icon = categoryIcons[rec.initiative_category] || Lightbulb;
            const colorClass = categoryColors[rec.initiative_category] || 'bg-foreground-muted/10 text-foreground-muted';

            return (
              <Card key={`${rec.initiative_id}-${rec.target_activity_key}`} className="hover:border-primary/50 transition-colors">
                <CardContent className="py-4">
                  <div className="flex items-start gap-4">
                    <div className={cn('p-3 rounded-lg', colorClass)}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <h3 className="font-semibold text-foreground text-lg">{rec.initiative_name}</h3>
                          <p className="text-sm text-foreground-muted mt-1">
                            Targets: {rec.target_source_name}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={rec.impact_score >= 7 ? 'success' : rec.impact_score >= 4 ? 'warning' : 'secondary'}>
                            Impact: {rec.impact_score}/10
                          </Badge>
                          <Button size="sm">
                            <Plus className="w-4 h-4 mr-1" />
                            Add to Scenario
                          </Button>
                        </div>
                      </div>

                      <p className="text-foreground-muted mt-3">{rec.relevance_explanation}</p>

                      <div className="flex flex-wrap items-center gap-6 mt-4 pt-4 border-t border-border">
                        <div className="flex items-center gap-2">
                          <TrendingDown className="w-5 h-5 text-success" />
                          <div>
                            <p className="font-semibold text-success">
                              -{Number(rec.potential_reduction_tco2e || 0).toLocaleString()} tCO2e
                            </p>
                            <p className="text-xs text-foreground-muted">
                              {Number(rec.reduction_as_percent_of_total || 0).toFixed(1)}% of total
                            </p>
                          </div>
                        </div>

                        {rec.estimated_capex && (
                          <div className="flex items-center gap-2">
                            <DollarSign className="w-5 h-5 text-foreground-muted" />
                            <div>
                              <p className="font-semibold text-foreground">
                                ${(Number(rec.estimated_capex || 0) / 1000).toFixed(0)}K
                              </p>
                              <p className="text-xs text-foreground-muted">Investment</p>
                            </div>
                          </div>
                        )}

                        {rec.payback_years && (
                          <div className="flex items-center gap-2">
                            <Clock className="w-5 h-5 text-foreground-muted" />
                            <div>
                              <p className="font-semibold text-foreground">
                                {Number(rec.payback_years || 0).toFixed(1)} years
                              </p>
                              <p className="text-xs text-foreground-muted">Payback</p>
                            </div>
                          </div>
                        )}

                        {rec.co_benefits && rec.co_benefits.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 ml-auto">
                            {rec.co_benefits.map((benefit, i) => (
                              <Badge key={i} variant="secondary" className="text-xs">
                                {benefit}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
