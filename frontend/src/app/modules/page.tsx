'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { AppShell } from '@/components/layout';
import { Card, CardContent, Button, Badge } from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  Leaf,
  Coins,
  Scale,
  Microscope,
  FileStack,
  ArrowRight,
  Check,
  Lock,
  Loader2,
} from 'lucide-react';

interface Module {
  id: string;
  name: string;
  description: string;
  icon: React.ElementType;
  color: string;
  href: string;
  status: 'active' | 'coming_soon' | 'locked';
  features: string[];
}

const MODULES: Module[] = [
  {
    id: 'ghg',
    name: 'GHG Inventory',
    description: 'Complete greenhouse gas emissions tracking across Scope 1, 2, and 3 categories.',
    icon: Leaf,
    color: 'bg-primary',
    href: '/modules/ghg',
    status: 'active',
    features: [
      'Scope 1 Direct Emissions',
      'Scope 2 Indirect Energy',
      'Scope 3 Value Chain',
      'Auto WTT (Category 3.3)',
      'Multi-region Factors',
    ],
  },
  {
    id: 'pcaf',
    name: 'PCAF',
    description: 'Partnership for Carbon Accounting Financials - financed emissions tracking for financial institutions.',
    icon: Coins,
    color: 'bg-amber-500',
    href: '/modules/pcaf',
    status: 'coming_soon',
    features: [
      'Asset Class Attribution',
      'Financed Emissions',
      'Portfolio Carbon Footprint',
      'PCAF Data Quality Scores',
      'Regulatory Reporting',
    ],
  },
  {
    id: 'cbam',
    name: 'CBAM',
    description: 'Carbon Border Adjustment Mechanism - EU carbon compliance for importers.',
    icon: Scale,
    color: 'bg-blue-600',
    href: '/modules/cbam',
    status: 'coming_soon',
    features: [
      'Embedded Emissions',
      'Supplier Data Collection',
      'CBAM Reports',
      'EU Compliance',
      'Certificate Management',
    ],
  },
  {
    id: 'lca',
    name: 'LCA',
    description: 'Life Cycle Assessment - comprehensive environmental impact analysis for products.',
    icon: Microscope,
    color: 'bg-purple-600',
    href: '/modules/lca',
    status: 'coming_soon',
    features: [
      'Cradle-to-Gate Analysis',
      'Product Footprinting',
      'Impact Categories',
      'Database Integration',
      'ISO 14040/14044 Compliant',
    ],
  },
  {
    id: 'epd',
    name: 'EPD Reports',
    description: 'Environmental Product Declarations - standardized environmental performance reports.',
    icon: FileStack,
    color: 'bg-teal-600',
    href: '/modules/epd',
    status: 'coming_soon',
    features: [
      'EPD Generation',
      'Third-party Verification',
      'Multiple Standards',
      'Product Categories',
      'Public Registry Ready',
    ],
  },
];

export default function ModulesPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [mounted, setMounted] = useState(false);

  // Handle client-side mounting
  useEffect(() => {
    setMounted(true);
  }, []);

  // Redirect if not authenticated (client-side only)
  useEffect(() => {
    if (mounted && !isAuthenticated) {
      router.push('/');
    }
  }, [mounted, isAuthenticated, router]);

  // Don't render until mounted and authenticated
  if (!mounted || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <AppShell>
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Modules</h1>
        <p className="text-foreground-muted mt-1">
          Explore and manage your sustainability modules
        </p>
      </div>

      {/* Modules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {MODULES.map((module) => {
          const Icon = module.icon;
          const isActive = module.status === 'active';
          const isComingSoon = module.status === 'coming_soon';

          return (
            <Card
              key={module.id}
              padding="lg"
              className={cn(
                'relative overflow-hidden transition-all duration-300 hover:shadow-lg cursor-pointer',
                isComingSoon && 'opacity-90'
              )}
              onClick={() => router.push(module.href)}
            >
              {/* Status Badge */}
              <div className="absolute top-4 right-4">
                {isActive && (
                  <Badge variant="success">
                    <Check className="w-3 h-3 mr-1" />
                    Active
                  </Badge>
                )}
                {isComingSoon && (
                  <Badge variant="secondary">
                    Coming Soon
                  </Badge>
                )}
                {module.status === 'locked' && (
                  <Badge variant="secondary">
                    <Lock className="w-3 h-3 mr-1" />
                    Locked
                  </Badge>
                )}
              </div>

              {/* Icon */}
              <div className={cn('w-12 h-12 rounded-xl flex items-center justify-center mb-4', module.color)}>
                <Icon className="w-6 h-6 text-white" />
              </div>

              {/* Content */}
              <h3 className="text-lg font-semibold text-foreground mb-2">{module.name}</h3>
              <p className="text-sm text-foreground-muted mb-4">{module.description}</p>

              {/* Features */}
              <ul className="space-y-2 mb-6">
                {module.features.slice(0, 3).map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-foreground-muted">
                    <div className={cn('w-1.5 h-1.5 rounded-full', module.color)} />
                    {feature}
                  </li>
                ))}
                {module.features.length > 3 && (
                  <li className="text-xs text-foreground-muted">
                    +{module.features.length - 3} more features
                  </li>
                )}
              </ul>

              {/* Action */}
              {isActive && (
                <Button
                  variant="primary"
                  size="sm"
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push(module.href);
                  }}
                >
                  Open Module
                </Button>
              )}

              {isComingSoon && (
                <Button
                  variant="outline"
                  size="sm"
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push(module.href);
                  }}
                >
                  Learn More
                </Button>
              )}
            </Card>
          );
        })}
      </div>

      {/* Enterprise CTA */}
      <Card padding="lg" className="mt-8 bg-gradient-to-r from-primary/5 to-secondary/5">
        <CardContent>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-foreground">Need a Custom Module?</h3>
              <p className="text-foreground-muted mt-1">
                Contact our team to discuss custom sustainability solutions for your organization.
              </p>
            </div>
            <Button variant="primary">
              Contact Sales
            </Button>
          </div>
        </CardContent>
      </Card>
    </AppShell>
  );
}
