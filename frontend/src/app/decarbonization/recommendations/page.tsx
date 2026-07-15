'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api, InitiativeCategory, PersonalizedRecommendation } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button, toast } from '@/components/ui';
import { cn, num } from '@/lib/utils';
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
  X,
} from 'lucide-react';
import Link from 'next/link';

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
  const [selectedPeriodId, setSelectedPeriodId] = useState<string | null>(null);
  const [addingRec, setAddingRec] = useState<PersonalizedRecommendation | null>(null);

  const { data: scenarios } = useQuery({
    queryKey: ['scenarios', user?.organization_id],
    queryFn: () => api.getScenarios(),
    enabled: !!user?.organization_id,
  });

  // Fetch periods
  const { data: periods } = useQuery({
    queryKey: ['periods'],
    queryFn: () => api.getPeriods(),
    enabled: !!user?.organization_id,
  });

  // Set default period: follow the top-bar (global) selection when valid
  const globalPeriodId = usePeriodStore((s) => s.selectedPeriodId);
  useEffect(() => {
    if (periods && periods.length > 0 && !selectedPeriodId) {
      const activePeriod = periods.find(p => p.id === globalPeriodId) || periods[0];
      // eslint-disable-next-line react-hooks/set-state-in-effect -- pre-existing intentional state sync on mount/deps change; no behavior change
      setSelectedPeriodId(activePeriod.id);
    }
  }, [periods, selectedPeriodId, globalPeriodId]);

  const { data: recommendations, isLoading } = useQuery({
    queryKey: ['all-recommendations', selectedPeriodId, categoryFilter],
    queryFn: () => api.getRecommendations(selectedPeriodId || '', {
      limit: 50,
      category: categoryFilter as InitiativeCategory | undefined
    }),
    enabled: !!selectedPeriodId,
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
              variant={categoryFilter === null ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setCategoryFilter(null)}
            >
              All
            </Button>
            {categories.map((cat) => (
              <Button
                key={cat}
                variant={categoryFilter === cat ? 'primary' : 'ghost'}
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
                          <Button size="sm" onClick={() => setAddingRec(rec)}>
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

                        {/* num(): "0.00" is a truthy string — guard on the value, not the field */}
                        {num(rec.estimated_capex) > 0 && (
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

                        {num(rec.payback_years) > 0 && (
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

      {addingRec && (
        <AddToScenarioModal
          rec={addingRec}
          scenarios={(scenarios ?? []).map((s) => ({ id: s.id, name: s.name }))}
          onClose={() => setAddingRec(null)}
        />
      )}
    </div>
  );
}

function AddToScenarioModal({
  rec,
  scenarios,
  onClose,
}: {
  rec: PersonalizedRecommendation;
  scenarios: { id: string; name: string }[];
  onClose: () => void;
}) {
  const [scenarioId, setScenarioId] = useState(scenarios[0]?.id || '');
  const [error, setError] = useState<string | null>(null);

  const addMutation = useMutation({
    mutationFn: () =>
      api.addInitiativeToScenario(scenarioId, {
        initiative_id: rec.initiative_id,
        target_activity_key: rec.target_activity_key,
        expected_reduction_tco2e: Number(rec.potential_reduction_tco2e || 0),
        expected_reduction_percent: Number(rec.reduction_as_percent_of_total || 0),
        capex: Number(rec.estimated_capex || 0),
      }),
    onSuccess: () => {
      toast.success('Added to scenario');
      onClose();
    },
    onError: (e: Error) => setError(e.message),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Add to Scenario
            <button onClick={onClose} aria-label="Close">
              <X className="w-5 h-5 text-foreground-muted" />
            </button>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-foreground-muted">
            Add <span className="font-medium text-foreground">{rec.initiative_name}</span> to:
          </p>
          {scenarios.length === 0 ? (
            <div className="text-sm text-foreground-muted">
              You don&apos;t have any scenarios yet.{' '}
              <Link href="/decarbonization/scenarios" className="text-primary underline">
                Create one first
              </Link>
              .
            </div>
          ) : (
            <>
              <select
                value={scenarioId}
                onChange={(e) => setScenarioId(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              >
                {scenarios.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
              {error && <p className="text-sm text-error">{error}</p>}
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={onClose}>
                  Cancel
                </Button>
                <Button onClick={() => addMutation.mutate()} disabled={addMutation.isPending || !scenarioId}>
                  {addMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  Add
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
