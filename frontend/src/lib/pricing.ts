export interface Plan {
  id: string;
  name: string;
  description: string;
  icon: string;
  /** Per-month price when billed monthly. null = custom (Book a Demo). */
  monthlyPrice: number | null;
  /** Per-month price when billed annually (~15% off). null = custom. */
  annualPrice: number | null;
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
// Starter $99/mo ($84 annual), Professional $349/mo ($297 annual).
export const plans: Plan[] = [
  {
    id: 'free',
    name: 'Free',
    description: 'Explore your footprint. Where trials land after 14 days — keep your data.',
    icon: 'Leaf',
    monthlyPrice: 0,
    annualPrice: 0,
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
    features: [
      'Everything in Free',
      'Smart Import — the AI parser, unlimited for Scope 1 & 2',
      'Drop any file: bills, fuel cards, meter sheets',
      'Scope 3 parsed & previewed (commit unlocks on Professional)',
      '5 sites · 3 users · 5 report generations / month',
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
    description: 'Full Scope 1–3, CBAM, and unlimited audit-ready reports.',
    icon: 'Building2',
    monthlyPrice: 349,
    annualPrice: 297,
    features: [
      'Scope 1, 2 & 3 (all 15 categories)',
      'Up to 25 sites · 10 users',
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

// Advanced modules are bundled into tiers as Beta / Coming Soon — not sold as paid add-ons.
export const addOns: AddOn[] = [];
