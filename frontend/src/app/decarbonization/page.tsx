'use client';

import { useState, useEffect, Suspense } from 'react';
import { useAuthStore } from '@/stores/auth';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  api,
  EmissionProfileAnalysis,
  PersonalizedRecommendation,
  DecarbonizationTarget,
  Scenario,
  ReportingPeriod,
} from '@/lib/api';
import { AppShell } from '@/components/layout';
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Badge,
  EmptyState,
} from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  Target,
  Loader2,
  TrendingDown,
  Zap,
  DollarSign,
  BarChart3,
  Leaf,
  ArrowRight,
  Plus,
  CheckCircle2,
  AlertCircle,
  Factory,
  Plane,
  Truck,
  Building2,
  Lightbulb,
  LineChart,
} from 'lucide-react';

// Components
import { EmissionProfileCard } from '@/components/decarbonization/EmissionProfileCard';
import { RecommendationsCard } from '@/components/decarbonization/RecommendationsCard';
import { TargetProgressCard } from '@/components/decarbonization/TargetProgressCard';
import { SetTargetModal } from '@/components/decarbonization/SetTargetModal';

function DecarbonizationPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isAuthenticated } = useAuthStore();

  const [mounted, setMounted] = useState(false);
  const [selectedPeriodId, setSelectedPeriodId] = useState<string | null>(null);
  const [showTargetModal, setShowTargetModal] = useState(false);

  // Fetch reporting periods
  const { data: periods } = useQuery({
    queryKey: ['periods'],
    queryFn: () => api.getPeriods(),
    enabled: isAuthenticated,
  });

  // Set default period
  useEffect(() => {
    if (periods && periods.length > 0 && !selectedPeriodId) {
      // Find latest non-locked period, or fall back to first
      const activePeriod = periods.find(p => !p.is_locked) || periods[0];
      setSelectedPeriodId(activePeriod.id);
    }
  }, [periods, selectedPeriodId]);

  // Fetch emission profile
  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ['emission-profile', selectedPeriodId],
    queryFn: () => api.getEmissionProfile(selectedPeriodId!),
    enabled: !!selectedPeriodId,
  });

  // Fetch recommendations
  const { data: recommendations, isLoading: recommendationsLoading } = useQuery({
    queryKey: ['recommendations', selectedPeriodId],
    queryFn: () => api.getRecommendations(selectedPeriodId!, { limit: 5 }),
    enabled: !!selectedPeriodId,
  });

  // Fetch targets
  const { data: targets } = useQuery({
    queryKey: ['decarbonization-targets'],
    queryFn: () => api.getDecarbonizationTargets(),
    enabled: isAuthenticated,
  });

  // Fetch scenarios
  const { data: scenarios } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => api.getScenarios(),
    enabled: isAuthenticated,
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isAuthenticated) {
      router.push('/');
    }
  }, [mounted, isAuthenticated, router]);

  if (!mounted || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  const activeTarget = targets?.find(t => t.is_active);
  const activeScenario = scenarios?.find(s => s.is_active);

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Decarbonization Pathways</h1>
          <p className="text-foreground-muted mt-1">
            Data-driven reduction planning based on your actual emissions
          </p>
        </div>
        <div className="flex items-center gap-3">
          {periods && periods.length > 0 && (
            <select
              value={selectedPeriodId || ''}
              onChange={(e) => setSelectedPeriodId(e.target.value)}
              className="px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm"
            >
              {periods.map((period) => (
                <option key={period.id} value={period.id}>
                  {period.name}
                </option>
              ))}
            </select>
          )}
          <Button onClick={() => setShowTargetModal(true)}>
            <Target className="w-4 h-4 mr-2" />
            {activeTarget ? 'Edit Target' : 'Set Target'}
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      {profile && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card padding="md">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Factory className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">
                  {profile.total_co2e_tonnes.toLocaleString()}
                </p>
                <p className="text-sm text-foreground-muted">Total tCO2e</p>
              </div>
            </div>
          </Card>
          <Card padding="md">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-success/10">
                <TrendingDown className="w-5 h-5 text-success" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">
                  {profile.top_sources.length}
                </p>
                <p className="text-sm text-foreground-muted">Emission Sources</p>
              </div>
            </div>
          </Card>
          <Card padding="md">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-secondary/10">
                <Lightbulb className="w-5 h-5 text-secondary" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">
                  {recommendations?.length || 0}
                </p>
                <p className="text-sm text-foreground-muted">Recommendations</p>
              </div>
            </div>
          </Card>
          <Card padding="md">
            <div className="flex items-center gap-3">
              <div className={cn(
                "p-2 rounded-lg",
                profile.trend_direction === 'decreasing' ? 'bg-success/10' :
                profile.trend_direction === 'increasing' ? 'bg-error/10' : 'bg-foreground-muted/10'
              )}>
                <LineChart className={cn(
                  "w-5 h-5",
                  profile.trend_direction === 'decreasing' ? 'text-success' :
                  profile.trend_direction === 'increasing' ? 'text-error' : 'text-foreground-muted'
                )} />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">
                  {profile.yoy_change_percent !== null && profile.yoy_change_percent !== undefined
                    ? `${profile.yoy_change_percent > 0 ? '+' : ''}${profile.yoy_change_percent}%`
                    : 'N/A'}
                </p>
                <p className="text-sm text-foreground-muted">YoY Change</p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Emission Profile */}
        <div className="lg:col-span-2 space-y-6">
          {/* Emission Profile */}
          <EmissionProfileCard
            profile={profile}
            isLoading={profileLoading}
          />

          {/* Top Recommendations */}
          <RecommendationsCard
            recommendations={recommendations}
            isLoading={recommendationsLoading}
            onViewAll={() => router.push('/decarbonization/recommendations')}
          />
        </div>

        {/* Right Column - Target & Scenarios */}
        <div className="space-y-6">
          {/* Target Progress */}
          <TargetProgressCard
            target={activeTarget}
            currentEmissions={profile?.total_co2e_tonnes}
            onSetTarget={() => setShowTargetModal(true)}
          />

          {/* Active Scenario Summary */}
          {activeScenario && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <BarChart3 className="w-5 h-5 text-foreground-muted" />
                  Active Scenario
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-foreground">{activeScenario.name}</span>
                    <Badge variant="success">Active</Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-foreground-muted">Reduction</p>
                      <p className="text-xl font-bold text-success">
                        -{activeScenario.total_reduction_tco2e.toLocaleString()} tCO2e
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-foreground-muted">Investment</p>
                      <p className="text-xl font-bold text-foreground">
                        ${(activeScenario.total_investment / 1000).toFixed(0)}K
                      </p>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-border">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-foreground-muted">Target Achievement</span>
                      <span className="font-medium text-foreground">
                        {activeScenario.target_achievement_percent.toFixed(0)}%
                      </span>
                    </div>
                    <div className="w-full h-2 bg-background-muted rounded-full overflow-hidden">
                      <div
                        className={cn(
                          "h-full rounded-full transition-all",
                          activeScenario.target_achievement_percent >= 100 ? 'bg-success' : 'bg-primary'
                        )}
                        style={{ width: `${Math.min(activeScenario.target_achievement_percent, 100)}%` }}
                      />
                    </div>
                  </div>

                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => router.push('/decarbonization/scenarios')}
                  >
                    View Scenario Details
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => router.push('/decarbonization/recommendations')}
              >
                <Lightbulb className="w-4 h-4 mr-2" />
                View All Recommendations
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => router.push('/decarbonization/scenarios')}
              >
                <BarChart3 className="w-4 h-4 mr-2" />
                Build Scenario
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => router.push('/decarbonization/roadmap')}
              >
                <Target className="w-4 h-4 mr-2" />
                View Roadmap
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Set Target Modal */}
      {showTargetModal && (
        <SetTargetModal
          isOpen={showTargetModal}
          onClose={() => setShowTargetModal(false)}
          existingTarget={activeTarget}
          baselineEmissions={profile?.total_co2e_tonnes}
          baseYear={profile ? new Date(profile.analysis_date).getFullYear() : new Date().getFullYear()}
          basePeriodId={selectedPeriodId || undefined}
        />
      )}
    </AppShell>
  );
}

function DecarbonizationLoading() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-primary animate-spin" />
    </div>
  );
}

export default function DecarbonizationPage() {
  return (
    <Suspense fallback={<DecarbonizationLoading />}>
      <DecarbonizationPageContent />
    </Suspense>
  );
}
