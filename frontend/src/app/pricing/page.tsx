'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  Check,
  X,
  Zap,
  Building2,
  Rocket,
  Shield,
  Globe,
  FileText,
  Target,
  Users,
  BarChart3,
  Leaf,
  ArrowRight,
  HelpCircle,
} from 'lucide-react';

type BillingPeriod = 'monthly' | 'annual';

interface PlanFeature {
  name: string;
  starter: boolean | string;
  professional: boolean | string;
  enterprise: boolean | string;
}

const plans = [
  {
    name: 'Starter',
    description: 'Perfect for small businesses beginning their sustainability journey',
    icon: Zap,
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
    icon: Building2,
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
    icon: Rocket,
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

const addOns = [
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

const comparisonFeatures: { category: string; features: PlanFeature[] }[] = [
  {
    category: 'Carbon Accounting',
    features: [
      { name: 'Scope 1 Emissions', starter: true, professional: true, enterprise: true },
      { name: 'Scope 2 (Location-based)', starter: true, professional: true, enterprise: true },
      { name: 'Scope 2 (Market-based)', starter: false, professional: true, enterprise: true },
      { name: 'Scope 3 (All 15 categories)', starter: false, professional: true, enterprise: true },
      { name: 'Sites/Locations', starter: '5', professional: '25', enterprise: 'Unlimited' },
      { name: 'Emission Factors', starter: '200+', professional: '401+', enterprise: '401+ Custom' },
      { name: 'Custom Emission Factors', starter: false, professional: false, enterprise: true },
    ],
  },
  {
    category: 'Reporting & Compliance',
    features: [
      { name: 'Interactive Dashboard', starter: 'Basic', professional: 'Full', enterprise: 'Full' },
      { name: 'ISO 14064-1 Report', starter: false, professional: true, enterprise: true },
      { name: 'CDP Export', starter: false, professional: true, enterprise: true },
      { name: 'CSRD/ESRS E1', starter: false, professional: false, enterprise: true },
      { name: 'White-labeled Reports', starter: false, professional: false, enterprise: true },
      { name: 'Audit Trail', starter: 'Basic', professional: 'Full', enterprise: 'Full' },
      { name: 'Auditor Portal', starter: false, professional: false, enterprise: true },
    ],
  },
  {
    category: 'Decarbonization',
    features: [
      { name: 'Target Setting', starter: false, professional: true, enterprise: true },
      { name: 'SBTi Alignment', starter: false, professional: true, enterprise: true },
      { name: 'AI Recommendations', starter: false, professional: true, enterprise: true },
      { name: 'Scenario Modeling', starter: false, professional: 'Up to 5', enterprise: 'Unlimited' },
      { name: 'ROI Calculations', starter: false, professional: true, enterprise: true },
      { name: 'Financial Modeling', starter: false, professional: 'Basic', enterprise: 'Advanced' },
    ],
  },
  {
    category: 'Support & Security',
    features: [
      { name: 'Users Included', starter: '3', professional: '10', enterprise: 'Unlimited' },
      { name: 'SSO/SAML', starter: false, professional: false, enterprise: true },
      { name: 'API Access', starter: false, professional: false, enterprise: true },
      { name: 'Email Support', starter: '48hr', professional: '24hr', enterprise: '4hr' },
      { name: 'Phone Support', starter: false, professional: false, enterprise: true },
      { name: 'Dedicated Account Manager', starter: false, professional: false, enterprise: true },
      { name: 'SLA Guarantee', starter: false, professional: false, enterprise: '99.9%' },
    ],
  },
];

const faqs = [
  {
    question: 'How accurate are the calculations?',
    answer: 'CLIMATRIX uses the same emission factors and methodologies as enterprise platforms. Our calculations are aligned with GHG Protocol, ISO 14064-1, and verified by third-party auditors.',
  },
  {
    question: 'Can I upgrade my plan later?',
    answer: "Yes, you can upgrade at any time. We'll prorate the difference and your data seamlessly transfers to your new plan.",
  },
  {
    question: 'Do you offer discounts?',
    answer: 'Yes! We offer 15% discount for annual billing (already reflected in prices), 20% discount for non-profits, and custom pricing for multi-entity organizations.',
  },
  {
    question: 'What about data security?',
    answer: "Your data is encrypted at rest and in transit. We're SOC 2 Type II compliant and GDPR ready.",
  },
  {
    question: 'Can I export my data?',
    answer: 'Yes, all plans include data export in CSV/Excel format. Enterprise includes full API access for custom integrations.',
  },
  {
    question: 'What is included in the free trial?',
    answer: 'The 14-day free trial includes full access to your selected plan features. No credit card required to start.',
  },
];

export default function PricingPage() {
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>('annual');
  const [showComparison, setShowComparison] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
              <Leaf className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-semibold text-foreground">CLIMATRIX</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link href="/register">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <Badge variant="success" className="mb-4">Save 15% with annual billing</Badge>
          <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-4">
            Enterprise Carbon Accounting
            <br />
            <span className="text-primary">Without the Enterprise Price</span>
          </h1>
          <p className="text-xl text-foreground-muted mb-8 max-w-2xl mx-auto">
            The same regulatory-compliant calculations and audit-ready reports as $50K+ platforms,
            starting at just $299/month.
          </p>

          {/* Billing Toggle */}
          <div className="flex items-center justify-center gap-4 mb-12">
            <span className={cn(
              "text-sm font-medium",
              billingPeriod === 'monthly' ? 'text-foreground' : 'text-foreground-muted'
            )}>
              Monthly
            </span>
            <button
              onClick={() => setBillingPeriod(billingPeriod === 'monthly' ? 'annual' : 'monthly')}
              className={cn(
                "relative w-14 h-7 rounded-full transition-colors",
                billingPeriod === 'annual' ? 'bg-primary' : 'bg-background-muted'
              )}
            >
              <span className={cn(
                "absolute top-1 w-5 h-5 rounded-full bg-white transition-transform",
                billingPeriod === 'annual' ? 'translate-x-8' : 'translate-x-1'
              )} />
            </button>
            <span className={cn(
              "text-sm font-medium",
              billingPeriod === 'annual' ? 'text-foreground' : 'text-foreground-muted'
            )}>
              Annual <span className="text-success">(Save 15%)</span>
            </span>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="pb-16 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-3 gap-8">
            {plans.map((plan) => {
              const Icon = plan.icon;
              const price = billingPeriod === 'annual' ? plan.annualPrice : plan.monthlyPrice;

              return (
                <Card
                  key={plan.name}
                  className={cn(
                    "relative",
                    plan.popular && "border-2 border-primary shadow-lg"
                  )}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <Badge className="bg-primary text-white">Most Popular</Badge>
                    </div>
                  )}
                  <CardHeader className="text-center pb-2">
                    <div className={cn(
                      "w-12 h-12 rounded-lg mx-auto mb-4 flex items-center justify-center",
                      plan.popular ? "bg-primary/10" : "bg-background-muted"
                    )}>
                      <Icon className={cn(
                        "w-6 h-6",
                        plan.popular ? "text-primary" : "text-foreground-muted"
                      )} />
                    </div>
                    <CardTitle className="text-xl">{plan.name}</CardTitle>
                    <p className="text-sm text-foreground-muted mt-1">{plan.description}</p>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center mb-6">
                      <div className="flex items-baseline justify-center gap-1">
                        <span className="text-4xl font-bold text-foreground">${price}</span>
                        <span className="text-foreground-muted">/month</span>
                      </div>
                      {billingPeriod === 'annual' && (
                        <p className="text-sm text-foreground-muted mt-1">
                          Billed annually (${price * 12}/year)
                        </p>
                      )}
                    </div>

                    <Button
                      className="w-full mb-6"
                      variant={plan.popular ? 'primary' : 'outline'}
                    >
                      {plan.cta}
                    </Button>

                    <div className="space-y-3">
                      {plan.features.map((feature, i) => (
                        <div key={i} className="flex items-start gap-2">
                          <Check className="w-5 h-5 text-success flex-shrink-0 mt-0.5" />
                          <span className="text-sm text-foreground">{feature}</span>
                        </div>
                      ))}
                      {plan.limitations.map((limitation, i) => (
                        <div key={i} className="flex items-start gap-2">
                          <X className="w-5 h-5 text-foreground-muted flex-shrink-0 mt-0.5" />
                          <span className="text-sm text-foreground-muted">{limitation}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Add-On Modules */}
      <section className="py-16 px-4 bg-background-elevated">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-foreground mb-4">Add-On Modules</h2>
            <p className="text-foreground-muted max-w-2xl mx-auto">
              Extend your platform with specialized compliance modules for specific regulatory requirements.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {addOns.map((addon) => (
              <Card key={addon.name}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">{addon.name}</CardTitle>
                  <p className="text-sm text-foreground-muted">{addon.description}</p>
                </CardHeader>
                <CardContent>
                  <div className="mb-4">
                    <span className="text-2xl font-bold text-foreground">+${addon.price}</span>
                    <span className="text-foreground-muted">/month</span>
                  </div>
                  <div className="space-y-2">
                    {addon.features.map((feature, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <Check className="w-4 h-4 text-success flex-shrink-0 mt-0.5" />
                        <span className="text-sm text-foreground">{feature}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Feature Comparison */}
      <section className="py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-foreground mb-4">Compare Plans</h2>
            <Button
              variant="outline"
              onClick={() => setShowComparison(!showComparison)}
            >
              {showComparison ? 'Hide' : 'Show'} Detailed Comparison
            </Button>
          </div>

          {showComparison && (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-4 px-4 font-medium text-foreground">Feature</th>
                    <th className="text-center py-4 px-4 font-medium text-foreground">Starter</th>
                    <th className="text-center py-4 px-4 font-medium text-foreground bg-primary/5">Professional</th>
                    <th className="text-center py-4 px-4 font-medium text-foreground">Enterprise</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonFeatures.map((category) => (
                    <>
                      <tr key={category.category} className="bg-background-muted">
                        <td colSpan={4} className="py-3 px-4 font-semibold text-foreground">
                          {category.category}
                        </td>
                      </tr>
                      {category.features.map((feature, i) => (
                        <tr key={i} className="border-b border-border">
                          <td className="py-3 px-4 text-sm text-foreground">{feature.name}</td>
                          <td className="py-3 px-4 text-center">
                            {typeof feature.starter === 'boolean' ? (
                              feature.starter ? (
                                <Check className="w-5 h-5 text-success mx-auto" />
                              ) : (
                                <X className="w-5 h-5 text-foreground-muted mx-auto" />
                              )
                            ) : (
                              <span className="text-sm text-foreground">{feature.starter}</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-center bg-primary/5">
                            {typeof feature.professional === 'boolean' ? (
                              feature.professional ? (
                                <Check className="w-5 h-5 text-success mx-auto" />
                              ) : (
                                <X className="w-5 h-5 text-foreground-muted mx-auto" />
                              )
                            ) : (
                              <span className="text-sm text-foreground">{feature.professional}</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-center">
                            {typeof feature.enterprise === 'boolean' ? (
                              feature.enterprise ? (
                                <Check className="w-5 h-5 text-success mx-auto" />
                              ) : (
                                <X className="w-5 h-5 text-foreground-muted mx-auto" />
                              )
                            ) : (
                              <span className="text-sm text-foreground">{feature.enterprise}</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>

      {/* Trust Indicators */}
      <section className="py-16 px-4 bg-background-elevated">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <Shield className="w-10 h-10 text-primary mx-auto mb-3" />
              <h3 className="font-semibold text-foreground mb-1">SOC 2 Type II</h3>
              <p className="text-sm text-foreground-muted">Enterprise-grade security</p>
            </div>
            <div>
              <Globe className="w-10 h-10 text-primary mx-auto mb-3" />
              <h3 className="font-semibold text-foreground mb-1">GDPR Compliant</h3>
              <p className="text-sm text-foreground-muted">Data privacy guaranteed</p>
            </div>
            <div>
              <FileText className="w-10 h-10 text-primary mx-auto mb-3" />
              <h3 className="font-semibold text-foreground mb-1">GHG Protocol</h3>
              <p className="text-sm text-foreground-muted">Fully aligned methodology</p>
            </div>
            <div>
              <Target className="w-10 h-10 text-primary mx-auto mb-3" />
              <h3 className="font-semibold text-foreground mb-1">SBTi Ready</h3>
              <p className="text-sm text-foreground-muted">Science-based targets</p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-16 px-4">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-foreground text-center mb-12">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <Card key={i}>
                <CardContent className="py-4">
                  <div className="flex items-start gap-3">
                    <HelpCircle className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                    <div>
                      <h3 className="font-semibold text-foreground mb-2">{faq.question}</h3>
                      <p className="text-sm text-foreground-muted">{faq.answer}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4 bg-primary">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Start Your Carbon Journey?
          </h2>
          <p className="text-white/80 mb-8 max-w-2xl mx-auto">
            Join hundreds of companies using CLIMATRIX to measure, report, and reduce their carbon footprint.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Button variant="secondary" size="lg">
              Start Free Trial
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Button variant="ghost" size="lg" className="text-white border-white/20 hover:bg-white/10">
              Talk to Sales
            </Button>
          </div>
          <p className="text-white/60 text-sm mt-4">
            14-day free trial. No credit card required.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-border">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Leaf className="w-5 h-5 text-primary" />
            <span className="font-semibold text-foreground">CLIMATRIX</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-foreground-muted">
            <Link href="/terms" className="hover:text-foreground">Terms</Link>
            <Link href="/privacy" className="hover:text-foreground">Privacy</Link>
            <Link href="/contact" className="hover:text-foreground">Contact</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
