export interface Plan {
  id: string;
  name: string;
  description: string;
  icon: string;
  /** Per-month price when billed monthly. null = not offered monthly. */
  monthlyPrice: number | null;
  /** Per-month equivalent when billed annually. null = custom (Book a Demo). */
  annualPrice: number | null;
  /** Exact yearly total (mirrors backend PLAN_PRICING annual). null = custom. */
  annualTotal: number | null;
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

// Single source of truth for displayed pricing — mirrors backend PLAN_PRICING.
// 2026-07-20 restructure: the reporting year is the unit sold. Professional is
// annual-only; the once-a-year reporter buys the Report Pass instead.
export const plans: Plan[] = [
  {
    id: 'free',
    name: 'Free',
    description: 'Explore your footprint. Where trials land after 14 days — keep your data.',
    icon: 'Leaf',
    monthlyPrice: 0,
    annualPrice: 0,
    annualTotal: 0,
    features: [
      'GHG Scope 1 & 2 inventory',
      '1 user · 1 site · 1 reporting period',
      'Dashboards & on-screen summaries',
      'CSV export',
    ],
    limitations: [
      'No new report generation (preview only)',
      'No CBAM / Decarbonization',
      'No AI data import',
    ],
    cta: 'Start Free',
    popular: false,
  },
  {
    id: 'starter',
    name: 'Starter',
    description: 'Your operations, measured properly — with the AI parser doing the reading.',
    icon: 'Zap',
    monthlyPrice: 99,
    annualPrice: 84,
    annualTotal: 1010,
    features: [
      'Everything in Free',
      'Smart Import — the AI parser, unlimited for Scope 1 & 2',
      'Drop any file: bills, fuel cards, meter sheets',
      'Scope 3 parsed & previewed (commit unlocks on Professional)',
      '2 sites · 2 users · 5 report generations / month',
      'PDF & CSV export',
      'Email support',
    ],
    limitations: ['Scope 3 commit, CBAM & Decarbonization on Professional'],
    cta: 'Start Free Trial',
    popular: false,
  },
  {
    id: 'professional',
    name: 'Professional',
    description: 'Full Scope 1–3, CBAM, and unlimited audit-ready reports. Annual license.',
    icon: 'Building2',
    monthlyPrice: null,
    annualPrice: 297,
    annualTotal: 3560,
    features: [
      'Scope 1, 2 & 3 (all 15 categories)',
      '5 sites & 2 users included — add packs & seats anytime',
      'AI-powered data import',
      'Unlimited ISO 14064-1 & CDP reports',
      'CBAM (Beta) & Decarbonization',
      'SBTi-aligned targets',
      'Priority support',
    ],
    limitations: [],
    cta: 'Start Free Trial',
    popular: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    description: 'For large or regulated organizations. Includes BDO advisory.',
    icon: 'Rocket',
    monthlyPrice: null,
    annualPrice: null,
    annualTotal: null,
    features: [
      'Everything in Professional',
      'Unlimited sites & users',
      'CSRD / ESRS E1 reporting',
      'SSO / SAML',
      'Full API access',
      'Dedicated account manager',
      'Audit support + BDO advisory',
    ],
    limitations: [],
    cta: 'Book a Demo',
    popular: false,
  },
];

// The once-a-year reporter's product: everything in Professional for 90 days,
// licensed to a single reporting year. Mirrors backend REPORT_PASS.
export const reportPass = {
  id: 'report_pass',
  name: 'Report Pass',
  price: 1790,
  windowDays: 90,
  features: [
    'Everything in Professional for 90 days',
    'Licensed to one reporting year',
    'All exports for that year — ISO 14064-1, CDP, ESRS, PDF',
    'Your data and audit trail stay after the window closes',
  ],
};

// Capacity add-ons stacked on the included caps — mirrors backend ADDON_PRICING.
export const expansionAddOns = [
  { name: 'Site pack', detail: '+5 sites', price: 490, cadence: '/year' },
  { name: 'Extra seat', detail: '+1 team member', price: 190, cadence: '/year' },
];

// Advanced modules are bundled into tiers as Beta / Coming Soon — not sold as paid add-ons.
export const addOns: AddOn[] = [];
