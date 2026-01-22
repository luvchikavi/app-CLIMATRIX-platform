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
  Sparkles,
  TrendingUp,
  Globe,
  Shield,
  ArrowRight,
  Check,
  Clock,
  Calendar,
  Loader2,
} from 'lucide-react';

interface RoadmapItem {
  id: string;
  quarter: string;
  year: number;
  items: {
    name: string;
    description: string;
    icon: React.ElementType;
    color: string;
    status: 'completed' | 'in_progress' | 'planned';
    href?: string;
  }[];
}

const ROADMAP: RoadmapItem[] = [
  {
    id: 'q1-2026',
    quarter: 'Q1',
    year: 2026,
    items: [
      {
        name: 'GHG Inventory Module',
        description: 'Complete Scope 1, 2, 3 emissions tracking with auto-WTT calculation',
        icon: Leaf,
        color: 'bg-primary',
        status: 'completed',
        href: '/modules/ghg',
      },
      {
        name: 'Multi-Region Emission Factors',
        description: 'Support for UK, US, EU, Israel, and Global emission factors',
        icon: Globe,
        color: 'bg-blue-500',
        status: 'completed',
      },
      {
        name: 'Modern Dashboard',
        description: 'Real-time KPIs, scope breakdown charts, and activity timeline',
        icon: TrendingUp,
        color: 'bg-emerald-500',
        status: 'completed',
        href: '/dashboard',
      },
    ],
  },
  {
    id: 'q2-2026',
    quarter: 'Q2',
    year: 2026,
    items: [
      {
        name: 'CBAM Module',
        description: 'EU Carbon Border Adjustment Mechanism compliance and reporting',
        icon: Scale,
        color: 'bg-blue-600',
        status: 'in_progress',
        href: '/modules/cbam',
      },
      {
        name: 'AI Smart Import',
        description: 'Intelligent data extraction from invoices, bills, and documents',
        icon: Sparkles,
        color: 'bg-purple-500',
        status: 'in_progress',
      },
      {
        name: 'Enhanced Security',
        description: 'SOC 2 compliance, SSO integration, and audit logging',
        icon: Shield,
        color: 'bg-slate-600',
        status: 'planned',
      },
    ],
  },
  {
    id: 'q3-2026',
    quarter: 'Q3',
    year: 2026,
    items: [
      {
        name: 'PCAF Module',
        description: 'Financed emissions tracking for financial institutions',
        icon: Coins,
        color: 'bg-amber-500',
        status: 'planned',
        href: '/modules/pcaf',
      },
      {
        name: 'API & Integrations',
        description: 'Public API for ERP, accounting, and sustainability software integration',
        icon: Globe,
        color: 'bg-indigo-500',
        status: 'planned',
      },
    ],
  },
  {
    id: 'q4-2026',
    quarter: 'Q4',
    year: 2026,
    items: [
      {
        name: 'LCA Module',
        description: 'Life Cycle Assessment for product carbon footprinting',
        icon: Microscope,
        color: 'bg-purple-600',
        status: 'planned',
        href: '/modules/lca',
      },
      {
        name: 'EPD Reports',
        description: 'Environmental Product Declaration generation and verification',
        icon: FileStack,
        color: 'bg-teal-600',
        status: 'planned',
        href: '/modules/epd',
      },
    ],
  },
];

const statusConfig = {
  completed: {
    label: 'Completed',
    variant: 'success' as const,
    icon: Check,
  },
  in_progress: {
    label: 'In Progress',
    variant: 'warning' as const,
    icon: Clock,
  },
  planned: {
    label: 'Planned',
    variant: 'secondary' as const,
    icon: Calendar,
  },
};

export default function RoadmapPage() {
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
        <h1 className="text-2xl font-bold text-foreground">Product Roadmap</h1>
        <p className="text-foreground-muted mt-1">
          See what we're building and what's coming next
        </p>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mb-8">
        {Object.entries(statusConfig).map(([key, config]) => {
          const Icon = config.icon;
          return (
            <div key={key} className="flex items-center gap-2">
              <Badge variant={config.variant}>
                <Icon className="w-3 h-3 mr-1" />
                {config.label}
              </Badge>
            </div>
          );
        })}
      </div>

      {/* Roadmap Timeline */}
      <div className="space-y-8">
        {ROADMAP.map((quarter, quarterIndex) => (
          <div key={quarter.id} className="relative">
            {/* Timeline Line */}
            {quarterIndex < ROADMAP.length - 1 && (
              <div className="absolute left-6 top-14 bottom-0 w-0.5 bg-border-light" />
            )}

            {/* Quarter Header */}
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center text-white font-bold text-sm">
                {quarter.quarter}
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">
                  {quarter.quarter} {quarter.year}
                </h2>
                <p className="text-sm text-foreground-muted">
                  {quarter.items.length} items
                </p>
              </div>
            </div>

            {/* Quarter Items */}
            <div className="ml-16 grid gap-4">
              {quarter.items.map((item, itemIndex) => {
                const Icon = item.icon;
                const StatusIcon = statusConfig[item.status].icon;
                const statusVariant = statusConfig[item.status].variant;

                return (
                  <Card
                    key={itemIndex}
                    padding="md"
                    className={cn(
                      'transition-all duration-300',
                      item.href && 'hover:shadow-md cursor-pointer'
                    )}
                    onClick={() => item.href && router.push(item.href)}
                  >
                    <div className="flex items-start gap-4">
                      <div className={cn('p-3 rounded-lg', item.color)}>
                        <Icon className="w-5 h-5 text-white" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <h3 className="font-semibold text-foreground">{item.name}</h3>
                          <Badge variant={statusVariant} className="text-xs">
                            <StatusIcon className="w-3 h-3 mr-1" />
                            {statusConfig[item.status].label}
                          </Badge>
                        </div>
                        <p className="text-sm text-foreground-muted">{item.description}</p>
                      </div>
                      {item.href && (
                        <ArrowRight className="w-5 h-5 text-foreground-muted" />
                      )}
                    </div>
                  </Card>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Request Feature CTA */}
      <Card padding="lg" className="mt-8 bg-gradient-to-r from-primary/5 to-secondary/5">
        <CardContent>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-foreground">Have a Feature Request?</h3>
              <p className="text-foreground-muted mt-1">
                We'd love to hear your ideas. Contact us to suggest new features or modules.
              </p>
            </div>
            <Button variant="primary">
              Request Feature
            </Button>
          </div>
        </CardContent>
      </Card>
    </AppShell>
  );
}
