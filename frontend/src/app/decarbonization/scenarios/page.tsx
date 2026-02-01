'use client';

import { useQuery } from '@tanstack/react-query';
import { api, Scenario } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  Loader2,
  ArrowLeft,
  BarChart3,
  TrendingDown,
  DollarSign,
  Plus,
  Play,
  Pause,
  CheckCircle2,
  Clock,
  Target,
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

  const { data: scenarios, isLoading } = useQuery({
    queryKey: ['scenarios', user?.organization_id],
    queryFn: () => api.getScenarios(),
    enabled: !!user?.organization_id,
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
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Create Scenario
        </Button>
      </div>

      {/* Scenarios */}
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
              <Button>
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
            <Card>
              <CardContent className="py-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <BarChart3 className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{scenarios.length}</p>
                    <p className="text-sm text-foreground-muted">Total Scenarios</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="py-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-success/10">
                    <CheckCircle2 className="w-5 h-5 text-success" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">
                      {scenarios.filter(s => s.is_active).length}
                    </p>
                    <p className="text-sm text-foreground-muted">Active</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="py-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-warning/10">
                    <Clock className="w-5 h-5 text-warning" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">
                      {scenarios.filter(s => !s.is_active).length}
                    </p>
                    <p className="text-sm text-foreground-muted">Inactive</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Scenario Cards */}
          {scenarios.map((scenario) => (
            <Card
              key={scenario.id}
              className={cn(
                "border-2",
                scenario.is_active ? 'border-primary' : 'border-transparent'
              )}
            >
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <BarChart3 className="w-5 h-5 text-foreground-muted" />
                    <span>{scenario.name}</span>
                    {scenario.is_active && (
                      <Badge variant="success">Active</Badge>
                    )}
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
                  <div>
                    <p className="text-sm text-foreground-muted">Total Reduction</p>
                    <p className="text-xl font-bold text-success">
                      -{Number(scenario.total_reduction_tco2e || 0).toLocaleString()} tCO2e
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-foreground-muted">Investment</p>
                    <p className="text-xl font-bold text-foreground">
                      ${(Number(scenario.total_investment || 0) / 1000).toFixed(0)}K
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-foreground-muted">Annual Savings</p>
                    <p className="text-xl font-bold text-success">
                      ${(Number(scenario.total_annual_savings || 0) / 1000).toFixed(0)}K/yr
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-foreground-muted">Target Achievement</p>
                    <p className="text-xl font-bold text-foreground">
                      {Number(scenario.target_achievement_percent || 0).toFixed(0)}%
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-border">
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-foreground-muted" />
                    <span className="text-sm text-foreground-muted">
                      {scenario.initiatives_count || 0} initiatives
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      View Details
                    </Button>
                    {!scenario.is_active && (
                      <Button size="sm">
                        <Play className="w-4 h-4 mr-1" />
                        Activate
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
