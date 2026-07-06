'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, ScenarioType } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button, toast } from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  Loader2,
  ArrowLeft,
  BarChart3,
  Plus,
  Play,
  CheckCircle2,
  Clock,
  Target,
  Trash2,
  X,
} from 'lucide-react';
import Link from 'next/link';

const scenarioTypeLabels: Record<string, string> = {
  aggressive: 'Aggressive',
  moderate: 'Moderate',
  conservative: 'Conservative',
  custom: 'Custom',
};

const scenarioTypeColors: Record<string, string> = {
  aggressive: 'bg-error/10 text-error border-error/20',
  moderate: 'bg-warning/10 text-warning border-warning/20',
  conservative: 'bg-success/10 text-success border-success/20',
  custom: 'bg-primary/10 text-primary border-primary/20',
};

export default function ScenariosPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { data: scenarios, isLoading } = useQuery({
    queryKey: ['scenarios', user?.organization_id],
    queryFn: () => api.getScenarios(),
    enabled: !!user?.organization_id,
  });

  const { data: targets } = useQuery({
    queryKey: ['decarbonization-targets', user?.organization_id],
    queryFn: () => api.getDecarbonizationTargets(),
    enabled: !!user?.organization_id,
  });

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: ['scenarios', user?.organization_id] });

  const activateMutation = useMutation({
    mutationFn: (id: string) => api.activateScenario(id),
    onSuccess: () => {
      toast.success('Scenario activated');
      refresh();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteScenario(id),
    onSuccess: () => {
      toast.success('Scenario deleted');
      setExpandedId(null);
      refresh();
    },
    onError: (e: Error) => toast.error(e.message),
  });

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
            <h1 className="text-2xl font-bold text-foreground">Decarbonization Scenarios</h1>
            <p className="text-foreground-muted">Compare different reduction pathways</p>
          </div>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Create Scenario
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      ) : !scenarios || scenarios.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <BarChart3 className="w-16 h-16 mx-auto mb-4 text-foreground-muted opacity-50" />
              <h3 className="text-lg font-medium text-foreground mb-2">No Scenarios Yet</h3>
              <p className="text-foreground-muted mb-4">
                Create your first scenario to model different reduction pathways
              </p>
              <Button onClick={() => setShowCreate(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Scenario
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <SummaryStat icon={<BarChart3 className="w-5 h-5 text-primary" />} bg="bg-primary/10" value={scenarios.length} label="Total Scenarios" />
            <SummaryStat icon={<CheckCircle2 className="w-5 h-5 text-success" />} bg="bg-success/10" value={scenarios.filter((s) => s.is_active).length} label="Active" />
            <SummaryStat icon={<Clock className="w-5 h-5 text-warning" />} bg="bg-warning/10" value={scenarios.filter((s) => !s.is_active).length} label="Inactive" />
          </div>

          {/* Scenario Cards */}
          {scenarios.map((scenario) => (
            <Card
              key={scenario.id}
              className={cn('border-2', scenario.is_active ? 'border-primary' : 'border-transparent')}
            >
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <BarChart3 className="w-5 h-5 text-foreground-muted" />
                    <span>{scenario.name}</span>
                    {scenario.is_active && <Badge variant="success">Active</Badge>}
                  </div>
                  <Badge className={scenarioTypeColors[scenario.scenario_type]}>
                    {scenarioTypeLabels[scenario.scenario_type]}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {scenario.description && (
                  <p className="text-foreground-muted mb-4">{scenario.description}</p>
                )}

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <Metric label="Total Reduction" value={`-${Number(scenario.total_reduction_tco2e || 0).toLocaleString()} tCO2e`} accent="text-success" />
                  <Metric label="Investment" value={`$${(Number(scenario.total_investment || 0) / 1000).toFixed(0)}K`} />
                  <Metric label="Annual Savings" value={`$${(Number(scenario.total_annual_savings || 0) / 1000).toFixed(0)}K/yr`} accent="text-success" />
                  <Metric label="Target Achievement" value={`${Number(scenario.target_achievement_percent || 0).toFixed(0)}%`} />
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-border">
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-foreground-muted" />
                    <span className="text-sm text-foreground-muted">
                      {scenario.initiatives_count || 0} initiatives
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setExpandedId(expandedId === scenario.id ? null : scenario.id)}
                    >
                      {expandedId === scenario.id ? 'Hide' : 'View Details'}
                    </Button>
                    {!scenario.is_active && (
                      <Button size="sm" onClick={() => activateMutation.mutate(scenario.id)} disabled={activateMutation.isPending}>
                        <Play className="w-4 h-4 mr-1" />
                        Activate
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        if (confirm(`Delete scenario "${scenario.name}"?`)) deleteMutation.mutate(scenario.id);
                      }}
                    >
                      <Trash2 className="w-4 h-4 text-error" />
                    </Button>
                  </div>
                </div>

                {expandedId === scenario.id && (
                  <ScenarioDetail scenarioId={scenario.id} onChanged={refresh} />
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {showCreate && (
        <CreateScenarioModal
          targets={(targets ?? []).map((t) => ({ id: t.id, name: t.name }))}
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            refresh();
          }}
        />
      )}
    </div>
  );
}

function SummaryStat({ icon, bg, value, label }: { icon: React.ReactNode; bg: string; value: number; label: string }) {
  return (
    <Card>
      <CardContent className="py-4">
        <div className="flex items-center gap-3">
          <div className={cn('p-2 rounded-lg', bg)}>{icon}</div>
          <div>
            <p className="text-2xl font-bold text-foreground">{value}</p>
            <p className="text-sm text-foreground-muted">{label}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function Metric({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div>
      <p className="text-sm text-foreground-muted">{label}</p>
      <p className={cn('text-xl font-bold', accent || 'text-foreground')}>{value}</p>
    </div>
  );
}

function ScenarioDetail({ scenarioId, onChanged }: { scenarioId: string; onChanged: () => void }) {
  const queryClient = useQueryClient();
  const { data: initiatives, isLoading } = useQuery({
    queryKey: ['scenario-initiatives', scenarioId],
    queryFn: () => api.getScenarioInitiatives(scenarioId),
  });

  const removeMutation = useMutation({
    mutationFn: (initiativeId: string) => api.removeInitiativeFromScenario(scenarioId, initiativeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scenario-initiatives', scenarioId] });
      onChanged();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="mt-4 pt-4 border-t border-border">
      <p className="text-sm font-medium text-foreground mb-2">Initiatives in this scenario</p>
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin text-primary" />
      ) : !initiatives || initiatives.length === 0 ? (
        <p className="text-sm text-foreground-muted">
          No initiatives yet — add them from the Recommendations page.
        </p>
      ) : (
        <div className="space-y-2">
          {initiatives.map((si) => (
            <div key={si.id} className="flex items-center justify-between rounded-lg bg-background-muted px-3 py-2">
              <div className="text-sm text-foreground">
                {si.initiative_name}
                <span className="ml-2 text-xs text-foreground-muted">
                  −{Number(si.expected_reduction_tco2e || 0).toLocaleString()} tCO2e
                </span>
              </div>
              <button
                onClick={() => removeMutation.mutate(si.initiative_id)}
                className="text-foreground-muted hover:text-error"
                aria-label="Remove initiative"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CreateScenarioModal({
  targets,
  onClose,
  onCreated,
}: {
  targets: { id: string; name: string }[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const [name, setName] = useState('New Scenario');
  const [type, setType] = useState<ScenarioType>('moderate' as ScenarioType);
  const [targetId, setTargetId] = useState(targets[0]?.id || '');
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () =>
      api.createScenario({ name, target_id: targetId, scenario_type: type }),
    onSuccess: () => {
      toast.success('Scenario created');
      onCreated();
    },
    onError: (e: Error) => setError(e.message),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Create Scenario
            <button onClick={onClose} aria-label="Close">
              <X className="w-5 h-5 text-foreground-muted" />
            </button>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {targets.length === 0 ? (
            <div className="text-sm text-foreground-muted">
              You need a decarbonization target first. Go back and click “Set Target”, then create a
              scenario against it.
            </div>
          ) : (
            <>
              <div>
                <label className="text-sm font-medium text-foreground">Name</label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-foreground">Target</label>
                <select
                  value={targetId}
                  onChange={(e) => setTargetId(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                >
                  {targets.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-foreground">Ambition</label>
                <select
                  value={type}
                  onChange={(e) => setType(e.target.value as ScenarioType)}
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
                >
                  <option value="conservative">Conservative</option>
                  <option value="moderate">Moderate</option>
                  <option value="aggressive">Aggressive</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
              {error && <p className="text-sm text-error">{error}</p>}
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={onClose}>
                  Cancel
                </Button>
                <Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending || !targetId}>
                  {createMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  Create
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
