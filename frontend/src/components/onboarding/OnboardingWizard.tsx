'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useSupportedRegions, useCreatePeriod, useCreateSite } from '@/hooks/useEmissions';
import { Button, Card, Input, Badge, toast } from '@/components/ui';
import { cn } from '@/lib/utils';
import { COUNTRY_OPTIONS } from '@/lib/countries';
import {
  Leaf,
  Building2,
  Globe,
  Calendar,
  Upload,
  Check,
  ChevronRight,
  ChevronLeft,
  Loader2,
  Download,
  Sparkles,
  MapPin,
} from 'lucide-react';

interface OnboardingWizardProps {
  onComplete: () => void;
  organizationName?: string;
}

type Step = 'welcome' | 'organization' | 'region' | 'site' | 'period' | 'import' | 'complete';

const STEPS: Step[] = ['welcome', 'organization', 'region', 'site', 'period', 'import', 'complete'];

/** Steps that can be skipped without filling in data */
const OPTIONAL_STEPS: Step[] = ['organization', 'site', 'import'];

const STORAGE_KEY = 'onboarding_wizard_state';

interface WizardPersistedState {
  currentStep: Step;
  orgDetails: { industry_code: string; base_year: number };
  selectedRegion: string;
  siteDetails: { name: string; country_code: string; address: string; grid_region: string };
  periodYear: number;
}

interface FieldErrors {
  [field: string]: string;
}

export function OnboardingWizard({ onComplete, organizationName }: OnboardingWizardProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [currentStep, setCurrentStep] = useState<Step>('welcome');
  const [orgDetails, setOrgDetails] = useState({
    industry_code: '',
    base_year: new Date().getFullYear() - 1,
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

  const { data: regions } = useSupportedRegions();
  const createPeriod = useCreatePeriod();
  const createSite = useCreateSite();

  const updateOrg = useMutation({
    mutationFn: (data: { default_region?: string; industry_code?: string; base_year?: number }) =>
      api.updateOrganization(data),
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

  const skipStep = () => {
    setFieldErrors({});
    nextStep();
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

  const handleCreateSite = async () => {
    // Validate required fields
    const errors: FieldErrors = {};
    if (!siteDetails.name.trim()) {
      errors.site_name = 'Site name is required';
    }
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    try {
      await createSite.mutateAsync({
        name: siteDetails.name.trim(),
        country_code: siteDetails.country_code || undefined,
        address: siteDetails.address.trim() || undefined,
        grid_region: siteDetails.grid_region || undefined,
      });
      toast.success('Site created successfully');
      nextStep();
    } catch {
      toast.error('Failed to create site');
    }
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

  const handleDownloadTemplate = async (scope: '1-2' | '3') => {
    try {
      await api.downloadTemplate(scope);
    } catch (error) {
      console.error('Failed to download template:', error);
      toast.error('Failed to download template');
    }
  };

  const handleComplete = () => {
    clearProgress();
    localStorage.setItem('onboarding_completed', 'true');
    onComplete();
    router.push('/dashboard');
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
        <Card padding="lg" className="animate-fade-in p-8">
          {/* Welcome Step */}
          {currentStep === 'welcome' && (
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-6 rounded-2xl gradient-primary flex items-center justify-center">
                <Leaf className="w-10 h-10 text-white" />
              </div>
              <h1 className="text-3xl font-bold text-foreground mb-4">
                Welcome to CLIMATRIX
              </h1>
              <p className="text-lg text-foreground-muted mb-8 max-w-md mx-auto">
                Let's set up your organization for carbon accounting in just a few minutes.
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
                    className="w-full px-4 py-2.5 rounded-lg border border-border bg-background text-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary"
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
                    className="w-full px-4 py-2.5 rounded-lg border border-border bg-background text-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  >
                    {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i).map(year => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
                  <p className="mt-1.5 text-sm text-foreground-muted">
                    The base year is used to track emissions reductions over time
                  </p>
                </div>
              </div>

              <div className="flex justify-between mt-8">
                <Button variant="outline" onClick={prevStep}>
                  <ChevronLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
                <div className="flex gap-3">
                  <Button variant="ghost" onClick={skipStep}>
                    Skip
                  </Button>
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
                      'p-4 rounded-xl border-2 text-left transition-all',
                      selectedRegion === region.code
                        ? 'border-primary bg-primary-light'
                        : 'border-border hover:border-primary/50'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-foreground">{region.name}</h3>
                        <p className="text-sm text-foreground-muted mt-0.5">{region.description}</p>
                      </div>
                      {selectedRegion === region.code && (
                        <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                          <Check className="w-3 h-3 text-white" />
                        </div>
                      )}
                    </div>
                  </button>
                ))}
              </div>

              <div className="flex justify-between mt-8">
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
                      'w-full px-4 py-2.5 rounded-lg border bg-background text-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary',
                      fieldErrors.site_name
                        ? 'border-red-500 focus:ring-red-200 focus:border-red-500'
                        : 'border-border'
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
                    className="w-full px-4 py-2.5 rounded-lg border border-border bg-background text-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary"
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
                    className="w-full px-4 py-2.5 rounded-lg border border-border bg-background text-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary"
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
                      className="w-full px-4 py-2.5 rounded-lg border border-border bg-background text-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary"
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
                      className="w-full px-4 py-2.5 rounded-lg border border-border bg-background text-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    />
                  )}
                  <p className="mt-1.5 text-sm text-foreground-muted">
                    Used to determine electricity emission factors for this site
                  </p>
                </div>
              </div>

              <div className="flex justify-between mt-8">
                <Button variant="outline" onClick={prevStep}>
                  <ChevronLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
                <div className="flex gap-3">
                  <Button variant="ghost" onClick={skipStep}>
                    Skip
                  </Button>
                  <Button
                    variant="primary"
                    onClick={handleCreateSite}
                    disabled={createSite.isPending}
                    isLoading={createSite.isPending}
                  >
                    Create Site
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
                        'px-6 py-3 rounded-lg border-2 font-medium transition-all',
                        periodYear === year
                          ? 'border-primary bg-primary text-white'
                          : 'border-border hover:border-primary/50 text-foreground'
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

              <div className="flex justify-between mt-8">
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

          {/* Import Step */}
          {currentStep === 'import' && (
            <div>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 rounded-xl bg-primary-light">
                  <Upload className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-foreground">Import Your Data</h2>
                  <p className="text-foreground-muted">Get started with our templates</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="p-4 rounded-xl border border-border bg-background-muted">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-primary/10">
                        <Download className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-foreground">Scope 1 & 2 Template</h4>
                        <p className="text-sm text-foreground-muted">Direct emissions and purchased energy</p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadTemplate('1-2')}
                    >
                      Download
                    </Button>
                  </div>
                </div>

                <div className="p-4 rounded-xl border border-border bg-background-muted">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-secondary/10">
                        <Download className="w-5 h-5 text-secondary" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-foreground">Scope 3 Template</h4>
                        <p className="text-sm text-foreground-muted">Value chain emissions</p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadTemplate('3')}
                    >
                      Download
                    </Button>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-primary-light border border-primary/20">
                  <div className="flex items-start gap-3">
                    <Sparkles className="w-5 h-5 text-primary mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-primary">AI-Powered Import</h4>
                      <p className="text-sm text-primary/80 mt-1">
                        Don't have the exact template format? No problem! Our AI can analyze
                        any Excel or CSV file and automatically map your data to emission factors.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-between mt-8">
                <Button variant="outline" onClick={prevStep}>
                  <ChevronLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
                <div className="flex gap-3">
                  <Button variant="ghost" onClick={skipStep}>
                    Skip
                  </Button>
                  <Button variant="primary" onClick={nextStep}>
                    Continue
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Complete Step */}
          {currentStep === 'complete' && (
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-success/10 flex items-center justify-center">
                <Check className="w-10 h-10 text-success" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-4">
                You're All Set!
              </h2>
              <p className="text-lg text-foreground-muted mb-8 max-w-md mx-auto">
                Your organization is ready for carbon accounting. Start by importing your
                emission data or adding activities manually.
              </p>

              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Button variant="outline" onClick={() => router.push('/import')}>
                  <Upload className="w-4 h-4 mr-2" />
                  Import Data
                </Button>
                <Button variant="primary" onClick={handleComplete}>
                  Go to Dashboard
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
