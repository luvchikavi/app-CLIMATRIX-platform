'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import { useSupportedRegions, useCreatePeriod, useCreateSite } from '@/hooks/useEmissions';
import { Button, Card, Input, Badge, toast } from '@/components/ui';
import { cn } from '@/lib/utils';
import { COUNTRY_OPTIONS } from '@/lib/countries';
import {
  Leaf,
  Building2,
  Globe,
  Calendar,
  Check,
  ChevronRight,
  ChevronLeft,
  Loader2,
  MapPin,
} from 'lucide-react';

interface OnboardingWizardProps {
  onComplete: () => void;
  organizationName?: string;
}

// Formal facts only — everything environmental (categories, data sources,
// uploads) lives in the Data Hub, which this wizard lands on when done.
type Step = 'welcome' | 'organization' | 'region' | 'site' | 'period' | 'complete';

const STEPS: Step[] = ['welcome', 'organization', 'region', 'site', 'period', 'complete'];

const STORAGE_KEY = 'onboarding_wizard_state';

interface WizardPersistedState {
  currentStep: Step;
  orgDetails: {
    industry_code: string;
    base_year: number;
    currency: string;
    unit_system: string;
    consolidation_approach: string;
  };
  selectedRegion: string;
  siteDetails: { name: string; country_code: string; address: string; grid_region: string };
  periodYear: number;
}

const CURRENCY_OPTIONS = ['USD', 'EUR', 'GBP', 'ILS', 'CHF', 'JPY', 'CAD', 'AUD'];

interface FieldErrors {
  [field: string]: string;
}

export function OnboardingWizard({ onComplete, organizationName }: OnboardingWizardProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { organization, setOrganization } = useAuthStore();
  const [currentStep, setCurrentStep] = useState<Step>('welcome');
  const [orgDetails, setOrgDetails] = useState({
    industry_code: '',
    base_year: new Date().getFullYear() - 1,
    currency: 'USD',
    unit_system: 'metric',
    consolidation_approach: 'operational_control',
  });
  const [selectedRegion, setSelectedRegion] = useState<string>('Global');
  const [siteDetails, setSiteDetails] = useState({
    name: '',
    country_code: '',
    address: '',
    grid_region: '',
  });
  const [periodYear, setPeriodYear] = useState<number>(new Date().getFullYear());
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [createdSites, setCreatedSites] = useState<string[]>([]);

  const { data: regions } = useSupportedRegions();
  const createPeriod = useCreatePeriod();
  const createSite = useCreateSite();

  const updateOrg = useMutation({
    mutationFn: (data: {
      default_region?: string;
      industry_code?: string;
      base_year?: number;
      currency?: string;
      unit_system?: string;
      consolidation_approach?: string;
    }) => api.updateOrganization(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organization'] });
    },
  });

  // ---- Persistence helpers ----
  const saveProgress = useCallback(
    (step: Step) => {
      const state: WizardPersistedState = {
        currentStep: step,
        orgDetails,
        selectedRegion,
        siteDetails,
        periodYear,
      };
      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      } catch {
        // Storage full or unavailable -- silently ignore
      }
    },
    [orgDetails, selectedRegion, siteDetails, periodYear],
  );

  const clearProgress = () => {
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
  };

  // Restore persisted state on mount
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) {
        const saved: WizardPersistedState = JSON.parse(raw);
        if (saved.currentStep && STEPS.includes(saved.currentStep)) {
          setCurrentStep(saved.currentStep);
        }
        if (saved.orgDetails) setOrgDetails(saved.orgDetails);
        if (saved.selectedRegion) setSelectedRegion(saved.selectedRegion);
        if (saved.siteDetails) setSiteDetails(saved.siteDetails);
        if (saved.periodYear) setPeriodYear(saved.periodYear);
      }
    } catch {
      // Corrupt data -- start fresh
    }
    // Only run on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Persist whenever the step changes
  useEffect(() => {
    saveProgress(currentStep);
  }, [currentStep, saveProgress]);

  const currentStepIndex = STEPS.indexOf(currentStep);
  const progress = ((currentStepIndex + 1) / STEPS.length) * 100;
  const nextStep = () => {
    const nextIndex = currentStepIndex + 1;
    if (nextIndex < STEPS.length) {
      setFieldErrors({});
      setCurrentStep(STEPS[nextIndex]);
    }
  };

  const prevStep = () => {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      setFieldErrors({});
      setCurrentStep(STEPS[prevIndex]);
    }
  };

  // ---- Validation helpers ----
  const clearError = (field: string) => {
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  };

  const handleSaveOrganization = async () => {
    try {
      await updateOrg.mutateAsync({
        industry_code: orgDetails.industry_code || undefined,
        base_year: orgDetails.base_year || undefined,
        currency: orgDetails.currency || undefined,
        unit_system: orgDetails.unit_system || undefined,
        consolidation_approach: orgDetails.consolidation_approach || undefined,
      });
      toast.success('Organization details saved');
      nextStep();
    } catch {
      toast.error('Failed to save organization details');
    }
  };

  const handleSaveRegion = async () => {
    try {
      await updateOrg.mutateAsync({ default_region: selectedRegion });
      toast.success('Region saved');
      nextStep();
    } catch {
      toast.error('Failed to save region');
    }
  };

  // Many organizations report across several sites — the wizard lets them add
  // as many as they need before moving on ("Save & add another").
  const saveSite = async (): Promise<boolean> => {
    if (!siteDetails.name.trim()) {
      setFieldErrors({ site_name: 'Site name is required' });
      return false;
    }
    try {
      await createSite.mutateAsync({
        name: siteDetails.name.trim(),
        country_code: siteDetails.country_code || undefined,
        address: siteDetails.address.trim() || undefined,
        grid_region: siteDetails.grid_region || undefined,
      });
      setCreatedSites((prev) => [...prev, siteDetails.name.trim()]);
      // Keep country/grid — sibling sites usually share them; clear the rest.
      setSiteDetails((prev) => ({ ...prev, name: '', address: '' }));
      return true;
    } catch {
      toast.error('Failed to create site');
      return false;
    }
  };

  const handleAddAnotherSite = async () => {
    if (await saveSite()) toast.success('Site added — enter the next one');
  };

  const handleSiteContinue = async () => {
    if (siteDetails.name.trim()) {
      if (await saveSite()) nextStep();
      return;
    }
    if (createdSites.length > 0) {
      nextStep();
      return;
    }
    setFieldErrors({ site_name: 'Add at least one site' });
  };

  const handleCreatePeriod = async () => {
    try {
      await createPeriod.mutateAsync({
        name: `FY ${periodYear}`,
        start_date: `${periodYear}-01-01`,
        end_date: `${periodYear}-12-31`,
      });
      toast.success('Reporting period created');
      nextStep();
    } catch {
      toast.error('Failed to create reporting period');
    }
  };

  const handleComplete = async () => {
    localStorage.setItem('onboarding_completed', 'true');
    // Personal "seen the tour" flag — non-blocking.
    try { await api.completeOnboarding(); } catch { /* non-blocking */ }
    // The real gate: server validates org is set up, then flips setup_complete.
    try {
      const org = await api.completeSetup();
      if (organization) {
        setOrganization({
          ...organization,
          setup_complete: true,
          default_region: org.default_region,
          industry_code: org.industry_code,
          base_year: org.base_year,
        });
      }
      clearProgress();
      onComplete();
      // Land in the Data Hub — mapping the inventory is the natural next step.
      router.push('/hub');
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Please complete all required steps first.';
      toast.error(msg);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-secondary/5 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-2xl">
        {/* Progress bar */}
        <div className="mb-8">
          <div className="h-2 bg-background-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="flex justify-between mt-2 text-sm text-foreground-muted">
            <span>Step {currentStepIndex + 1} of {STEPS.length}</span>
            <span>{Math.round(progress)}% complete</span>
          </div>
        </div>

        {/* Step Content */}
        <Card padding="lg" className="animate-fade-in max-h-[85vh] overflow-y-auto p-8">
          {/* Welcome Step */}
          {currentStep === 'welcome' && (
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-6 rounded-2xl gradient-primary flex items-center justify-center">
                <Leaf className="w-10 h-10 text-white" />
              </div>
              <h1 className="text-[20px] font-[650] tracking-[-0.01em] text-foreground mb-4">
                Welcome to CLIMATRIX
              </h1>
              <p className="text-lg text-foreground-muted mb-8 max-w-md mx-auto">
                Let&apos;s set up your organization for carbon accounting in just a few minutes.
              </p>
              {organizationName && (
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-light rounded-full text-primary font-medium mb-8">
                  <Building2 className="w-4 h-4" />
                  {organizationName}
                </div>
              )}
              <Button variant="primary" size="lg" onClick={nextStep}>
                Get Started
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
            </div>
          )}

          {/* Organization Details Step */}
          {currentStep === 'organization' && (
            <div>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 rounded-xl bg-primary-light">
                  <Building2 className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-foreground">Organization Details</h2>
                  <p className="text-foreground-muted">Help us customize your experience</p>
                </div>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Industry / Sector (Optional)
                  </label>
                  <select
                    value={orgDetails.industry_code}
                    onChange={(e) => setOrgDetails({ ...orgDetails, industry_code: e.target.value })}
                    className="w-full rounded-[10px] border-0 bg-cy-row px-4 py-2.5 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent"
                  >
                    <option value="">Select your industry</option>
                    <option value="manufacturing">Manufacturing</option>
                    <option value="technology">Technology</option>
                    <option value="retail">Retail & Consumer Goods</option>
                    <option value="finance">Financial Services</option>
                    <option value="healthcare">Healthcare</option>
                    <option value="energy">Energy & Utilities</option>
                    <option value="transportation">Transportation & Logistics</option>
                    <option value="construction">Construction & Real Estate</option>
                    <option value="agriculture">Agriculture & Food</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Base Year for Emissions Tracking
                  </label>
                  <select
                    value={orgDetails.base_year}
                    onChange={(e) => setOrgDetails({ ...orgDetails, base_year: parseInt(e.target.value) })}
                    className="w-full rounded-[10px] border-0 bg-cy-row px-4 py-2.5 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent"
                  >
                    {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i).map(year => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
                  <p className="mt-1.5 text-sm text-foreground-muted">
                    The base year is used to track emissions reductions over time
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Currency
                    </label>
                    <select
                      value={orgDetails.currency}
                      onChange={(e) => setOrgDetails({ ...orgDetails, currency: e.target.value })}
                      className="w-full rounded-[10px] border-0 bg-cy-row px-4 py-2.5 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent"
                    >
                      {CURRENCY_OPTIONS.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                    <p className="mt-1.5 text-sm text-foreground-muted">
                      For any spend-based data you upload
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Units
                    </label>
                    <select
                      value={orgDetails.unit_system}
                      onChange={(e) => setOrgDetails({ ...orgDetails, unit_system: e.target.value })}
                      className="w-full rounded-[10px] border-0 bg-cy-row px-4 py-2.5 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent"
                    >
                      <option value="metric">Metric (liters, km, kg)</option>
                      <option value="imperial">Imperial (gallons, miles, lbs)</option>
                    </select>
                    <p className="mt-1.5 text-sm text-foreground-muted">
                      So &quot;gal&quot; and &quot;ton&quot; are never ambiguous
                    </p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Reporting Boundary
                  </label>
                  <select
                    value={orgDetails.consolidation_approach}
                    onChange={(e) =>
                      setOrgDetails({ ...orgDetails, consolidation_approach: e.target.value })
                    }
                    className="w-full rounded-[10px] border-0 bg-cy-row px-4 py-2.5 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent"
                  >
                    <option value="operational_control">
                      Operational control (most common) — what you operate
                    </option>
                    <option value="financial_control">Financial control — what you control financially</option>
                    <option value="equity_share">Equity share — your ownership percentage</option>
                  </select>
                  <p className="mt-1.5 text-sm text-foreground-muted">
                    The GHG Protocol consolidation approach — keep the default if unsure
                  </p>
                </div>
              </div>

              <div className="sticky bottom-0 -mx-8 -mb-8 mt-8 flex justify-between bg-background-elevated shadow-[0_-1px_0_var(--cy-row)] px-8 py-4">
                <Button variant="outline" onClick={prevStep}>
                  <ChevronLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
                <div className="flex gap-3">
                  <Button
                    variant="primary"
                    onClick={handleSaveOrganization}
                    disabled={updateOrg.isPending}
                    isLoading={updateOrg.isPending}
                  >
                    Continue
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Region Step */}
          {currentStep === 'region' && (
            <div>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 rounded-xl bg-primary-light">
                  <Globe className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-foreground">Select Your Region</h2>
                  <p className="text-foreground-muted">For region-specific emission factors</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 max-h-80 overflow-y-auto">
                {regions?.map((region) => (
                  <button
                    key={region.code}
                    onClick={() => setSelectedRegion(region.code)}
                    className={cn(
                      'p-4 rounded-[12px] text-left transition-colors',
                      selectedRegion === region.code
                        ? 'bg-cy-accent-soft'
                        : 'bg-cy-row/50 hover:bg-cy-row'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-foreground">{region.name}</h3>
                        <p className="text-sm text-foreground-muted mt-0.5">{region.description}</p>
                      </div>
                      {selectedRegion === region.code && (
                        <span className="shrink-0 text-[13px] font-bold text-cy-accent" aria-hidden="true">✓</span>
                      )}
                    </div>
                  </button>
                ))}
              </div>

              <div className="sticky bottom-0 -mx-8 -mb-8 mt-8 flex justify-between bg-background-elevated shadow-[0_-1px_0_var(--cy-row)] px-8 py-4">
                <Button variant="outline" onClick={prevStep}>
                  <ChevronLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
                <Button
                  variant="primary"
                  onClick={handleSaveRegion}
                  disabled={updateOrg.isPending}
                  isLoading={updateOrg.isPending}
                >
                  Continue
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {/* Site Creation Step */}
          {currentStep === 'site' && (
            <div>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 rounded-xl bg-primary-light">
                  <MapPin className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-foreground">Add Your First Site</h2>
                  <p className="text-foreground-muted">Where does your organization operate?</p>
                </div>
              </div>

              {createdSites.length > 0 && (
                <div className="mb-5 flex flex-wrap items-center gap-2">
                  {createdSites.map((name, i) => (
                    <span
                      key={`${name}-${i}`}
                      className="inline-flex items-center gap-1.5 rounded-full bg-primary-light px-3 py-1 text-sm font-medium text-primary"
                    >
                      <Building2 className="w-3.5 h-3.5" />
                      {name}
                    </span>
                  ))}
                  <span className="text-sm text-foreground-muted">
                    {createdSites.length} site{createdSites.length > 1 ? 's' : ''} added
                  </span>
                </div>
              )}

              <div className="space-y-5">
                {/* Site Name (required) */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Site Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Headquarters, Main Office, Factory A"
                    value={siteDetails.name}
                    onChange={(e) => {
                      setSiteDetails({ ...siteDetails, name: e.target.value });
                      if (fieldErrors.site_name) clearError('site_name');
                    }}
                    className={cn(
                      'w-full rounded-[10px] border-0 bg-cy-row px-4 py-2.5 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2',
                      fieldErrors.site_name
                        ? 'ring-2 ring-error/50 focus:ring-error'
                        : 'focus:ring-cy-accent'
                    )}
                  />
                  {fieldErrors.site_name && (
                    <p className="mt-1.5 text-sm text-red-500">{fieldErrors.site_name}</p>
                  )}
                </div>

                {/* Country */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Country
                  </label>
                  <select
                    value={siteDetails.country_code}
                    onChange={(e) => setSiteDetails({ ...siteDetails, country_code: e.target.value })}
                    className="w-full rounded-[10px] border-0 bg-cy-row px-4 py-2.5 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent"
                  >
                    {COUNTRY_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Address (optional) */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Address (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="Street address, city, postal code"
                    value={siteDetails.address}
                    onChange={(e) => setSiteDetails({ ...siteDetails, address: e.target.value })}
                    className="w-full rounded-[10px] border-0 bg-cy-row px-4 py-2.5 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent"
                  />
                </div>

                {/* Grid Region */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Grid Region
                  </label>
                  {regions && regions.length > 0 ? (
                    <select
                      value={siteDetails.grid_region}
                      onChange={(e) => setSiteDetails({ ...siteDetails, grid_region: e.target.value })}
                      className="w-full rounded-[10px] border-0 bg-cy-row px-4 py-2.5 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent"
                    >
                      <option value="">Select grid region...</option>
                      {regions.map((r) => (
                        <option key={r.code} value={r.code}>
                          {r.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      placeholder="e.g. ERCOT, PJM, CAISO"
                      value={siteDetails.grid_region}
                      onChange={(e) => setSiteDetails({ ...siteDetails, grid_region: e.target.value })}
                      className="w-full rounded-[10px] border-0 bg-cy-row px-4 py-2.5 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent"
                    />
                  )}
                  <p className="mt-1.5 text-sm text-foreground-muted">
                    Used to determine electricity emission factors for this site
                  </p>
                </div>
              </div>

              <div className="sticky bottom-0 -mx-8 -mb-8 mt-8 flex justify-between bg-background-elevated shadow-[0_-1px_0_var(--cy-row)] px-8 py-4">
                <Button variant="outline" onClick={prevStep}>
                  <ChevronLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    onClick={handleAddAnotherSite}
                    disabled={createSite.isPending}
                  >
                    Save & add another
                  </Button>
                  <Button
                    variant="primary"
                    onClick={handleSiteContinue}
                    disabled={createSite.isPending}
                    isLoading={createSite.isPending}
                  >
                    Continue
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Period Step */}
          {currentStep === 'period' && (
            <div>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 rounded-xl bg-primary-light">
                  <Calendar className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-foreground">Create Reporting Period</h2>
                  <p className="text-foreground-muted">Start tracking your emissions</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-3">
                  Which year do you want to track?
                </label>
                <div className="flex flex-wrap gap-2">
                  {[new Date().getFullYear() - 2, new Date().getFullYear() - 1, new Date().getFullYear()].map((year) => (
                    <button
                      key={year}
                      onClick={() => setPeriodYear(year)}
                      className={cn(
                        'cursor-pointer rounded-full px-5 py-2.5 text-[13px] font-semibold transition-colors',
                        periodYear === year
                          ? 'bg-cy-accent text-white'
                          : 'bg-cy-row text-cy-muted hover:text-cy-ink'
                      )}
                    >
                      FY {year}
                    </button>
                  ))}
                </div>
                <p className="mt-4 text-sm text-foreground-muted">
                  This will create a reporting period from January 1 to December 31, {periodYear}.
                  You can create additional periods later.
                </p>
              </div>

              <div className="sticky bottom-0 -mx-8 -mb-8 mt-8 flex justify-between bg-background-elevated shadow-[0_-1px_0_var(--cy-row)] px-8 py-4">
                <Button variant="outline" onClick={prevStep}>
                  <ChevronLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
                <Button
                  variant="primary"
                  onClick={handleCreatePeriod}
                  disabled={createPeriod.isPending}
                  isLoading={createPeriod.isPending}
                >
                  Create Period
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {/* Complete Step */}
          {currentStep === 'complete' && (
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-success/10 flex items-center justify-center">
                <Check className="w-10 h-10 text-success" />
              </div>
              <h2 className="text-[18px] font-bold tracking-[-0.01em] text-foreground mb-4">
                You&apos;re All Set!
              </h2>
              <p className="text-lg text-foreground-muted mb-8 max-w-md mx-auto">
                Your organization is ready. Next: map your inventory in the Data Hub —
                mark what&apos;s relevant, then start dropping in your data.
              </p>

              <div className="flex justify-center">
                <Button variant="primary" onClick={handleComplete}>
                  Open the Data Hub
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
