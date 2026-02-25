'use client';

import { useAuthStore } from '@/stores/auth';
import { ComingSoonModule } from '@/components/modules/ComingSoonModule';
import { LockedModule } from '@/components/modules/LockedModule';
import { Coins } from 'lucide-react';

const PLAN_LEVELS: Record<string, number> = {
  free: 0,
  starter: 1,
  professional: 2,
  enterprise: 3,
};

export default function PCAFModulePage() {
  const { organization } = useAuthStore();
  const currentPlan = organization?.subscription_plan || 'free';
  const isLocked = (PLAN_LEVELS[currentPlan] ?? 0) < PLAN_LEVELS['enterprise'];

  if (isLocked) {
    return (
      <LockedModule
        moduleName="PCAF"
        description="Partnership for Carbon Accounting Financials - financed emissions tracking for financial institutions."
        icon={Coins}
        color="bg-amber-500"
        features={[
          'Asset Class Attribution',
          'Financed Emissions Tracking',
          'Portfolio Carbon Footprint',
          'PCAF Data Quality Scores',
          'Regulatory Reporting',
        ]}
        requiredPlan="Enterprise"
        price="$299/mo"
      />
    );
  }

  return (
    <ComingSoonModule
      name="PCAF"
      description="Partnership for Carbon Accounting Financials"
      icon={Coins}
      color="bg-amber-500"
      features={[
        'Asset Class Attribution - Calculate financed emissions by investment type',
        'Financed Emissions Tracking - Monitor carbon footprint of lending and investment portfolios',
        'Portfolio Carbon Footprint - Aggregate emissions across all holdings',
        'PCAF Data Quality Scores - Track data quality from estimated to verified',
        'Regulatory Reporting - Generate TCFD and EU Taxonomy aligned reports',
      ]}
      expectedDate="Q3 2026"
    />
  );
}
