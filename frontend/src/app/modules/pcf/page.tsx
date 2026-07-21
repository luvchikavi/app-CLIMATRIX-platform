'use client';

import { ComingSoonModule } from '@/components/modules/ComingSoonModule';
import { Package } from 'lucide-react';

export default function PCFModulePage() {
  return (
    <ComingSoonModule
      moduleId="pcf"
      name="PCF"
      description="Product Carbon Footprint"
      icon={Package}
      color="bg-emerald-700"
      features={[
        'Cradle-to-Gate per Product - ISO 14067 footprint per declared unit',
        'BOM Modeling - Materials, energy and transport per product, grounded in the factor library',
        'PACT v3 Exchange - Machine-readable PCF data your customers’ systems ingest directly',
        'Supplier PCF Ingestion - Replace secondary factors with real supplier data',
        'CBAM Synergy - Shares CN codes and embedded-emissions math with the CBAM module',
      ]}
      expectedDate="Q4 2026"
    />
  );
}
