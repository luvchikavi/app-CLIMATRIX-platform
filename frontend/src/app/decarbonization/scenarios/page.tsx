'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, ScenarioType } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import { AppShell } from '@/components/layout';
import { CanopyButton, PageHead, PanelLabel, StatCells, Surface } from '@/components/canopy';
import { Badge, BadgeProps, Button, ConfirmDialog, EmptyState, toast } from '@/components/ui';
import { cn, formatMoney } from '@/lib/utils';
import { Loader2, BarChart3, Play, Trash2, X } from 'lucide-react';

const scenarioTypeLabels: Record<string, string> = {
  aggressive: 'Aggressive',
  moderate: 'Moderate',
  conservative: 'Conservative',
  custom: 'Custom',
};

// Soft tint badges — no border variants (design contract: no lines on cards)
const scenarioTypeVariants: Record<string, BadgeProps['variant']> = {
  aggressive: 'error',
  moderate: 'warning',
  conservative: 'success',
  custom: 'primary',
};

export default function ScenariosPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<{ id: string; name: string } | null>(null);

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
      setDeleting(null);
      refresh();
    },
    onError: (e: Error) => {
      setDeleting(null);
      toast.error(e.message);
    },
  });

  return (
    <AppShell>
      <CanopyButton href="/decarbonization" variant="quiet" className="mb-2 inline-block">
        ← Back to plan
      </CanopyButton>
      <div className="flex items-start justify-between gap-4">
        <PageHead
          title="Decarbonization scenarios"
          subtitle="Compare different reduction pathways"
        />
        <CanopyButton onClick={() => setShowCreate(true)} className="shrink-0 mt-1">
          Create scenario
        </CanopyButton>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12" role="status" aria-live="polite">
          <Loader2 className="w-6 h-6 text-cy-accent animate-spin" aria-hidden="true" />
        </div>
      ) : !scenarios || scenarios.length === 0 ? (
        <Surface>
          <EmptyState
            icon={<BarChart3 className="w-8 h-8" strokeWidth={1.5} />}
            title="No scenarios yet"
            description="Create your first scenario to model different reduction pathways."
            action={{ label: 'Create your first scenario', onClick: () => setShowCreate(true) }}
          />
        </Surface>
      ) : (
        <div className="grid gap-4">
          {/* Summary */}
          <Surface>
            <PanelLabel>Scenarios</PanelLabel>
            <StatCells
              cells={[
                { label: 'Total scenarios', value: String(scenarios.length) },
                { label: 'Active', value: String(scenarios.filter((s) => s.is_active).length) },
                { label: 'Inactive', value: String(scenarios.filter((s) => !s.is_active).length) },
              ]}
            />
          </Surface>

          {/* Scenario cards — the active one sits on the accent-soft tint */}
          {scenarios.map((scenario) => (
            <Surface key={scenario.id} tint={scenario.is_active ? 'soft' : 'none'}>
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5 min-w-0">
                  <BarChart3 className="w-4.5 h-4.5 shrink-0 text-cy-muted" strokeWidth={1.75} />
                  <h3 className="text-[16px] font-[650] tracking-[-0.01em] text-cy-ink truncate">
                    {scenario.name}
                  </h3>
                  {scenario.is_active && <Badge variant="success">Active</Badge>}
                </div>
                <Badge variant={scenarioTypeVariants[scenario.scenario_type] ?? 'default'}>
                  {scenarioTypeLabels[scenario.scenario_type]}
                </Badge>
              </div>

              {scenario.description && (
                <p className="text-[13px] text-cy-muted mt-2">{scenario.description}</p>
              )}

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                <Metric
                  label="Total reduction"
                  value={`−${Number(scenario.total_reduction_tco2e || 0).toLocaleString()} t CO₂e`}
                  accent
                />
                <Metric label="Investment" value={formatMoney(scenario.total_investment || 0)} />
                <Metric
                  label="Annual savings"
                  value={`${formatMoney(scenario.total_annual_savings || 0)}/yr`}
                  accent
                />
                <Metric
                  label="Target achievement"
                  value={`${Number(scenario.target_achievement_percent || 0).toFixed(0)}%`}
                />
              </div>

              <div className="flex items-center justify-between mt-5">
                <span className="text-[12.5px] text-cy-muted">
                  {scenario.initiatives_count || 0} initiatives
                </span>
                <div className="flex items-center gap-2">
                  <CanopyButton
                    variant="pill"
                    onClick={() => setExpandedId(expandedId === scenario.id ? null : scenario.id)}
                  >
                    {expandedId === scenario.id ? 'Hide details' : 'View details'}
                  </CanopyButton>
                  {!scenario.is_active && (
                    <CanopyButton
                      className="px-3.5 py-2"
                      onClick={() => activateMutation.mutate(scenario.id)}
                      disabled={activateMutation.isPending}
                    >
                      <Play className="w-3.5 h-3.5 inline-block mr-1 -mt-px" aria-hidden="true" />
                      Activate
                    </CanopyButton>
                  )}
                  <button
                    type="button"
                    onClick={() => setDeleting({ id: scenario.id, name: scenario.name })}
                    className="p-2 rounded-md text-cy-muted hover:text-error hover:bg-cy-row"
                    aria-label={`Delete scenario ${scenario.name}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {expandedId === scenario.id && (
                <ScenarioDetail scenarioId={scenario.id} onChanged={refresh} />
              )}
            </Surface>
          ))}
        </div>
      )}

      <ConfirmDialog
        isOpen={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
        title="Delete scenario"
        message={`Delete scenario "${deleting?.name}"? Its selected initiatives are removed with it.`}
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />

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
    </AppShell>
  );
}

function Metric({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div>
      <p
        className={cn(
          'text-[16px] font-[650] tabular-nums',
          accent ? 'text-cy-accent' : 'text-cy-ink'
        )}
      >
        {value}
      </p>
      <p className="mt-0.5 text-[11.5px] text-cy-muted">{label}</p>
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
    <div className="mt-5">
      <PanelLabel className="mb-2">Initiatives in this scenario</PanelLabel>
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin text-cy-accent" />
      ) : !initiatives || initiatives.length === 0 ? (
        <p className="text-[12.5px] text-cy-muted">
          No initiatives yet — add them from the Recommendations page.
        </p>
      ) : (
        <div className="space-y-1.5">
          {initiatives.map((si) => (
            <div
              key={si.id}
              className="flex items-center justify-between rounded-[10px] bg-cy-row px-3 py-2"
            >
              <div className="text-[13px] text-cy-ink">
                {si.initiative_name}
                <span className="ml-2 text-[11.5px] tabular-nums text-cy-muted">
                  −{Number(si.expected_reduction_tco2e || 0).toLocaleString()} t CO₂e
                </span>
              </div>
              <button
                onClick={() => removeMutation.mutate(si.initiative_id)}
                className="text-cy-muted hover:text-error"
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

  const fieldLabel = 'block text-[11px] font-bold tracking-[0.06em] uppercase text-cy-faint mb-1.5';
  const fieldInput =
    'w-full rounded-[10px] border-0 bg-cy-row px-3 py-2.5 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-label="Create scenario">
      <div className="bg-background-elevated rounded-cy shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-start justify-between px-6 pt-6 pb-1">
          <h2 className="text-[16px] font-bold text-foreground tracking-[-0.01em]">
            Create scenario
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
          {targets.length === 0 ? (
            <div className="text-[12.5px] text-cy-muted">
              You need a decarbonization target first. Go back and click “Set Target”, then create a
              scenario against it.
            </div>
          ) : (
            <>
              <div>
                <label className={fieldLabel}>Name</label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className={fieldInput}
                />
              </div>
              <div>
                <label className={fieldLabel}>Target</label>
                <select
                  value={targetId}
                  onChange={(e) => setTargetId(e.target.value)}
                  className={fieldInput}
                >
                  {targets.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className={fieldLabel}>Ambition</label>
                <select
                  value={type}
                  onChange={(e) => setType(e.target.value as ScenarioType)}
                  className={fieldInput}
                >
                  <option value="conservative">Conservative</option>
                  <option value="moderate">Moderate</option>
                  <option value="aggressive">Aggressive</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="ghost" onClick={onClose}>
                  Cancel
                </Button>
                <Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending || !targetId}>
                  {createMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  Create
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
