export interface Plan {
  name: string;
  description: string;
  icon: string;
  monthlyPrice: number;
  annualPrice: number;
  features: string[];
  limitations: string[];
  cta: string;
  popular: boolean;
}

export interface AddOn {
  name: string;
  description: string;
  price: number;
  features: string[];
}

export const plans: Plan[] = [
  {
    name: 'Starter',
    description: 'Perfect for small businesses beginning their sustainability journey',
    icon: 'Zap',
    monthlyPrice: 349,
    annualPrice: 299,
    features: [
      'Scope 1 & 2 emissions',
      'Up to 5 sites',
      '3 users',
      '200+ emission factors',
      'Basic dashboard',
      'PDF export',
      'Email support (48hr)',
    ],
    limitations: [
      'No Scope 3',
      'No decarbonization planning',
      'No scenario modeling',
    ],
    cta: 'Start Free Trial',
    popular: false,
  },
  {
    name: 'Professional',
    description: 'Ideal for mid-size companies with comprehensive reporting needs',
    icon: 'Building2',
    monthlyPrice: 799,
    annualPrice: 699,
    features: [
      'Scope 1, 2 & 3 (all 15 categories)',
      'Up to 25 sites',
      '10 users',
      '401+ emission factors',
      'AI-powered data import',
      'ISO 14064-1 reports',
      'CDP export',
      'SBTi-aligned targets',
      'AI recommendations',
      'Up to 5 scenarios',
      'Full audit trail',
      'Priority support (24hr)',
    ],
    limitations: [],
    cta: 'Start Free Trial',
    popular: true,
  },
  {
    name: 'Enterprise',
    description: 'For large organizations with complex compliance requirements',
    icon: 'Rocket',
    monthlyPrice: 1799,
    annualPrice: 1499,
    features: [
      'Everything in Professional',
      'Unlimited sites & users',
      'Custom emission factors',
      'CSRD/ESRS E1 reports',
      'Unlimited scenarios',
      'Advanced financial modeling',
      'Auditor portal',
      'SSO/SAML',
      'Full API access',
      'Dedicated account manager',
      '99.9% SLA guarantee',
    ],
    limitations: [],
    cta: 'Contact Sales',
    popular: false,
  },
];

export const addOns: AddOn[] = [
  {
    name: 'CBAM Module',
    description: 'EU Carbon Border Adjustment Mechanism compliance',
    price: 299,
    features: [
      'CBAM-covered goods classification',
      'Embedded emissions calculation',
      'Quarterly report generation',
      'Certificate cost estimation',
    ],
  },
  {
    name: 'PCAF Module',
    description: 'Financed emissions for financial institutions',
    price: 399,
    features: [
      'All asset classes supported',
      'Portfolio emissions tracking',
      'PCAF data quality scoring',
      'TCFD-aligned reporting',
    ],
  },
  {
    name: 'LCA Module',
    description: 'Product-level carbon footprints',
    price: 499,
    features: [
      'Cradle-to-gate analysis',
      'Hotspot identification',
      'ecoinvent database access',
      'ISO 14040/14044 aligned',
    ],
  },
  {
    name: 'EPD Module',
    description: 'Environmental Product Declarations',
    price: 399,
    features: [
      'ISO 14025 aligned',
      'PCR library access',
      'EPD document generation',
      'Registry publication support',
    ],
  },
];
