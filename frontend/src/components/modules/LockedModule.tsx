'use client';

import { useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout';
import { Card, CardContent, Button, Badge } from '@/components/ui';
import { cn } from '@/lib/utils';
import { ArrowLeft, Lock, ArrowUpRight, Check } from 'lucide-react';

interface LockedModuleProps {
  moduleName: string;
  description: string;
  icon: React.ElementType;
  color: string;
  features: string[];
  requiredPlan: string;
  price: string;
}

export function LockedModule({
  moduleName,
  description,
  icon: Icon,
  color,
  features,
  requiredPlan,
  price,
}: LockedModuleProps) {
  const router = useRouter();

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex items-center gap-4 mb-8">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/modules')}
          leftIcon={<ArrowLeft className="w-4 h-4" />}
        >
          Modules
        </Button>
        <div className="flex items-center gap-3">
          <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center relative', color)}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">{moduleName}</h1>
            <p className="text-foreground-muted">{description}</p>
          </div>
        </div>
        <Badge variant="warning" className="ml-auto">
          <Lock className="w-3 h-3 mr-1" />
          Locked
        </Badge>
      </div>

      {/* Locked Content */}
      <div className="max-w-2xl mx-auto">
        <Card padding="lg" className="text-center mb-8 relative overflow-hidden">
          {/* Lock overlay */}
          <div className="absolute inset-0 bg-background/30 backdrop-blur-[1px] z-10 flex items-center justify-center">
            <div className="w-16 h-16 rounded-full bg-background-elevated border border-border flex items-center justify-center">
              <Lock className="w-8 h-8 text-foreground-muted" />
            </div>
          </div>

          <CardContent className="opacity-60">
            <div className={cn('w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6', color)}>
              <Icon className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-foreground mb-4">{moduleName}</h2>
            <p className="text-foreground-muted mb-6 max-w-md mx-auto">{description}</p>
          </CardContent>
        </Card>

        {/* Upgrade CTA */}
        <Card padding="lg" className="mb-8 border-primary/30 bg-gradient-to-br from-primary/5 to-transparent">
          <CardContent>
            <div className="text-center">
              <Badge variant="primary" className="mb-4">
                Available with {requiredPlan} plan
              </Badge>
              <h3 className="text-xl font-bold text-foreground mb-2">
                Unlock {moduleName}
              </h3>
              <p className="text-foreground-muted mb-4 max-w-md mx-auto">
                Upgrade your plan to access {moduleName} and all its powerful features.
              </p>
              <p className="text-sm text-foreground-muted mb-6">
                Starting at <span className="text-foreground font-semibold">{price}</span>
              </p>
              <Button
                variant="primary"
                rightIcon={<ArrowUpRight className="w-4 h-4" />}
                onClick={() => router.push('/billing')}
              >
                Upgrade Plan
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Features Preview */}
        <Card padding="lg" className="mb-8">
          <CardContent>
            <h3 className="font-semibold text-foreground mb-4">What You Get with {moduleName}</h3>
            <ul className="space-y-3">
              {features.map((feature, i) => (
                <li key={i} className="flex items-center gap-3">
                  <div className={cn('w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0', color)}>
                    <Check className="w-3 h-3 text-white" />
                  </div>
                  <span className="text-foreground-muted">{feature}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        {/* Contact Sales */}
        <Card padding="lg" className="text-center">
          <CardContent>
            <h3 className="font-semibold text-foreground mb-2">Have questions?</h3>
            <p className="text-sm text-foreground-muted mb-4">
              Contact our sales team to discuss the right plan for your organization.
            </p>
            <Button variant="outline">
              Contact Sales
            </Button>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
