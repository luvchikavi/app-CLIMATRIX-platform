'use client';

import { useAuthStore } from '@/stores/auth';
import { ComingSoonModule } from '@/components/modules/ComingSoonModule';
import { LockedModule } from '@/components/modules/LockedModule';
import { Microscope } from 'lucide-react';

const PLAN_LEVELS: Record<string, number> = {
  free: 0,
  starter: 1,
  professional: 2,
  enterprise: 3,
};

export default function LCAModulePage() {
  return (
    <ComingSoonModule
      moduleId="lca"
      name="LCA"
      description="Life Cycle Assessment"
      icon={Microscope}
      color="bg-purple-600"
      features={[
        'ISO 14040/14044 Compliant - Methodology aligned with international standards',
        'EF 3.1 Impact Method - 16 impact categories beyond carbon (acidification, water, resources)',
        'Lifecycle Modules A1-D - Production through end-of-life per EN 15804 structure',
        'Builds on PCF - Your product models extend into full life-cycle assessment',
        'Feeds EPD Generation - Results matrix ready for EN 15804+A2 declarations',
      ]}
      expectedDate="Q4 2026"
    />
  );
}
