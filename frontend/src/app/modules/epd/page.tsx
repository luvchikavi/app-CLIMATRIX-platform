'use client';

import { ComingSoonModule } from '@/components/modules/ComingSoonModule';
import { FileStack } from 'lucide-react';

export default function EPDModulePage() {
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
