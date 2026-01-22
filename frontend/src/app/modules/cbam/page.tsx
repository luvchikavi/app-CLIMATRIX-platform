'use client';

import { ComingSoonModule } from '@/components/modules/ComingSoonModule';
import { Scale } from 'lucide-react';

export default function CBAMModulePage() {
  return (
    <ComingSoonModule
      name="CBAM"
      description="Carbon Border Adjustment Mechanism"
      icon={Scale}
      color="bg-blue-600"
      features={[
        'Embedded Emissions Calculation - Track carbon content of imported goods',
        'Supplier Data Collection - Collect and verify supplier emission data',
        'CBAM Declaration Reports - Generate quarterly reports for EU authorities',
        'EU Compliance Tracking - Monitor compliance deadlines and requirements',
        'Certificate Management - Track CBAM certificates and carbon price adjustments',
      ]}
      expectedDate="Q2 2026"
    />
  );
}
