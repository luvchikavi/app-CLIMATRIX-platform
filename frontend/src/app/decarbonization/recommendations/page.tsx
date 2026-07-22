'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api, InitiativeCategory, PersonalizedRecommendation } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import { AppShell } from '@/components/layout';
import { CanopyButton, PageHead, PillTabs, Surface } from '@/components/canopy';
import { Badge, Button, EmptyState, toast } from '@/components/ui';
import { num, formatMoney } from '@/lib/utils';
import {
  Loader2,
  Lightbulb,
  Zap,
  Truck,
  Leaf,
  Factory,
  Building2,
  Recycle,
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

  const filterTabs = [
    { id: 'all', label: 'All' },
    ...Object.keys(categoryLabels).map((cat) => ({ id: cat, label: categoryLabels[cat] })),
  ];

  return (
    <AppShell>
      <CanopyButton href="/decarbonization" variant="quiet" className="mb-2 inline-block">
        ← Back to plan
      </CanopyButton>
      <PageHead
        title="Reduction recommendations"
        subtitle="Personalized initiatives based on your emission profile"
      />

      {/* Category filter */}
      <Surface padding="tight" className="mb-4">
        <PillTabs
          tabs={filterTabs}
          value={categoryFilter ?? 'all'}
          onChange={(id) => setCategoryFilter(id === 'all' ? null : id)}
        />
      </Surface>

      {/* Recommendations list */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12" role="status" aria-live="polite">
          <Loader2 className="w-6 h-6 text-cy-accent animate-spin" aria-hidden="true" />
        </div>
      ) : !recommendations || recommendations.length === 0 ? (
        <Surface>
          <EmptyState
            icon={<Lightbulb className="w-8 h-8" strokeWidth={1.5} />}
            title="No recommendations found"
            description="Try changing the filter or import more emission data."
          />
        </Surface>
      ) : (
        <div className="grid gap-4">
          {recommendations.map((rec) => {
            const Icon = categoryIcons[rec.initiative_category] || Lightbulb;

            return (
              <Surface key={`${rec.initiative_id}-${rec.target_activity_key}`}>
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-[12px] bg-cy-accent-soft text-cy-accent">
                    <Icon className="w-5 h-5" strokeWidth={1.75} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="text-[16px] font-[650] tracking-[-0.01em] text-cy-ink">
                          {rec.initiative_name}
                        </h3>
                        <p className="text-[12.5px] text-cy-muted mt-0.5">
                          Targets: {rec.target_source_name}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <Badge variant={rec.impact_score >= 7 ? 'success' : rec.impact_score >= 4 ? 'warning' : 'default'}>
                          Impact {rec.impact_score}/10
                        </Badge>
                        <CanopyButton onClick={() => setAddingRec(rec)} className="px-3.5 py-2">
                          Add to scenario
                        </CanopyButton>
                      </div>
                    </div>

                    <p className="text-[13px] text-cy-muted mt-3">{rec.relevance_explanation}</p>

                    <div className="flex flex-wrap items-center gap-x-8 gap-y-2.5 mt-4">
                      <div>
                        <p className="text-[13.5px] font-semibold tabular-nums text-cy-accent">
                          −{Number(rec.potential_reduction_tco2e || 0).toLocaleString()} t CO₂e
                        </p>
                        <p className="text-[11.5px] text-cy-muted mt-0.5">
                          {Number(rec.reduction_as_percent_of_total || 0).toFixed(1)}% of total
                        </p>
                      </div>

                      {/* num(): "0.00" is a truthy string — guard on the value, not the field */}
                      {num(rec.estimated_capex) > 0 && (
                        <div>
                          <p className="text-[13.5px] font-semibold tabular-nums text-cy-ink">
                            {formatMoney(rec.estimated_capex || 0)}
                          </p>
                          <p className="text-[11.5px] text-cy-muted mt-0.5">Investment</p>
                        </div>
                      )}

                      {num(rec.payback_years) > 0 && (
                        <div>
                          <p className="text-[13.5px] font-semibold tabular-nums text-cy-ink">
                            {Number(rec.payback_years || 0).toFixed(1)} years
                          </p>
                          <p className="text-[11.5px] text-cy-muted mt-0.5">Payback</p>
                        </div>
                      )}

                      {rec.co_benefits && rec.co_benefits.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 ml-auto">
                          {rec.co_benefits.map((benefit, i) => (
                            <Badge key={i} variant="default" size="sm">
                              {benefit}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </Surface>
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
    </AppShell>
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-label="Add to scenario">
      <div className="bg-background-elevated rounded-cy shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-start justify-between px-6 pt-6 pb-1">
          <h2 className="text-[16px] font-bold text-foreground tracking-[-0.01em]">
            Add to scenario
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-cy-row rounded-md text-cy-muted hover:text-foreground"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {error && (
            <div className="px-3 py-2.5 rounded-[10px] bg-error-50 text-error text-[12.5px]">
              {error}
            </div>
          )}
          <p className="text-[12.5px] text-cy-muted">
            Add <b className="font-semibold text-foreground">{rec.initiative_name}</b> to:
          </p>
          {scenarios.length === 0 ? (
            <div className="text-[12.5px] text-cy-muted">
              You don&apos;t have any scenarios yet.{' '}
              <Link href="/decarbonization/scenarios" className="font-semibold text-cy-accent">
                Create one first
              </Link>
              .
            </div>
          ) : (
            <>
              <div>
                <label className="block text-[11px] font-bold tracking-[0.06em] uppercase text-cy-faint mb-1.5">
                  Scenario
                </label>
                <select
                  value={scenarioId}
                  onChange={(e) => setScenarioId(e.target.value)}
                  className="w-full rounded-[10px] border-0 bg-cy-row px-3 py-2.5 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent"
                >
                  {scenarios.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="ghost" onClick={onClose}>
                  Cancel
                </Button>
                <Button onClick={() => addMutation.mutate()} disabled={addMutation.isPending || !scenarioId}>
                  {addMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  Add
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
