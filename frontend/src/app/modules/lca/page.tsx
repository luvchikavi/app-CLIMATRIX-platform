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
      name="LCA"
      description="Life Cycle Assessment"
      icon={Microscope}
      color="bg-purple-600"
      features={[
        'Cradle-to-Gate Analysis - Full product lifecycle environmental impact',
        'Product Footprinting - Calculate carbon footprint per product unit',
        'Multiple Impact Categories - GWP, acidification, eutrophication, and more',
        'Database Integration - Connect to ecoinvent, GaBi, and other LCA databases',
        'ISO 14040/14044 Compliant - Methodology aligned with international standards',
      ]}
      expectedDate="Q4 2026"
    />
  );
}
