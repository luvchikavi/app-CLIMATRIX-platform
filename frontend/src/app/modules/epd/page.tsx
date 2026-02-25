'use client';

import { useAuthStore } from '@/stores/auth';
import { ComingSoonModule } from '@/components/modules/ComingSoonModule';
import { LockedModule } from '@/components/modules/LockedModule';
import { FileStack } from 'lucide-react';

const PLAN_LEVELS: Record<string, number> = {
  free: 0,
  starter: 1,
  professional: 2,
  enterprise: 3,
};

export default function EPDModulePage() {
  const { organization } = useAuthStore();
  const currentPlan = organization?.subscription_plan || 'free';
  const isLocked = (PLAN_LEVELS[currentPlan] ?? 0) < PLAN_LEVELS['enterprise'];

  if (isLocked) {
    return (
      <LockedModule
        moduleName="EPD Reports"
        description="Environmental Product Declarations - standardized environmental performance reports."
        icon={FileStack}
        color="bg-teal-600"
        features={[
          'Automated EPD Generation',
          'Third-party Verification Support',
          'Multiple PCR Standards',
          'Product Category Management',
          'Public Registry Ready',
        ]}
        requiredPlan="Enterprise"
        price="$299/mo"
      />
    );
  }

  return (
    <ComingSoonModule
      name="EPD Reports"
      description="Environmental Product Declarations"
      icon={FileStack}
      color="bg-teal-600"
      features={[
        'Automated EPD Generation - Create declarations from LCA data',
        'Third-party Verification Support - Streamlined verification workflow',
        'Multiple PCR Standards - Support for various Product Category Rules',
        'Product Category Management - Organize products by environmental category',
        'Public Registry Ready - Export formats compatible with major EPD registries',
      ]}
      expectedDate="Q4 2026"
    />
  );
}
