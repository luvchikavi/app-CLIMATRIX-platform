'use client';

import { ComingSoonModule } from '@/components/modules/ComingSoonModule';
import { Coins } from 'lucide-react';

export default function PCAFModulePage() {
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
