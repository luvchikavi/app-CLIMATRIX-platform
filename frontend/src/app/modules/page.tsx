'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { AppShell } from '@/components/layout';
import { Card, Button } from '@/components/ui';
import { cn } from '@/lib/utils';
import { ArrowRight, Bell, Loader2 } from 'lucide-react';
import {
  MODULE_REGISTRY,
  STATUS_META,
  isEnterable,
  recommendedModules,
  type ModuleDef,
} from '@/lib/modules';

export default function ModulesPage() {
  const router = useRouter();
  const { isAuthenticated, organization } = useAuthStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isAuthenticated) {
      router.push('/');
    }
  }, [mounted, isAuthenticated, router]);

  if (!mounted || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  const recommended = recommendedModules(organization ?? undefined);

  const ModuleCard = ({ m }: { m: ModuleDef }) => {
    const Icon = m.icon;
    const enterable = isEnterable(m.status);
    const meta = STATUS_META[m.status];

    return (
      <Card
        padding="lg"
        className={cn(
          'relative overflow-hidden transition-all duration-300 hover:shadow-lg flex flex-col',
          enterable ? 'cursor-pointer' : 'opacity-90'
        )}
        onClick={() => enterable && router.push(m.href)}
      >
        {/* Status badge */}
        <div className="absolute top-4 right-4">
          <span className={cn('px-2.5 py-0.5 text-xs font-semibold rounded-full', meta.className)}>
            {meta.label}
          </span>
        </div>

        {/* Icon */}
        <div
          className={cn(
            'w-12 h-12 rounded-xl flex items-center justify-center mb-4',
            enterable ? 'bg-primary' : 'bg-muted'
          )}
        >
          <Icon className={cn('w-6 h-6', enterable ? 'text-white' : 'text-foreground-muted')} />
        </div>

        <h3 className="text-lg font-semibold text-foreground mb-2">{m.name}</h3>
        <p className="text-sm text-foreground-muted mb-4">{m.blurb}</p>

        <ul className="space-y-2 mb-6 flex-1">
          {m.features.slice(0, 3).map((feature, i) => (
            <li key={i} className="flex items-center gap-2 text-sm text-foreground-muted">
              <div className={cn('w-1.5 h-1.5 rounded-full', enterable ? 'bg-primary' : 'bg-foreground-muted/40')} />
              {feature}
            </li>
          ))}
        </ul>

        {enterable ? (
          <Button
            variant="primary"
            size="sm"
            rightIcon={<ArrowRight className="w-4 h-4" />}
            onClick={(e) => {
              e.stopPropagation();
              router.push(m.href);
            }}
          >
            Open Module
          </Button>
        ) : (
          <Button
            variant="outline"
            size="sm"
            leftIcon={<Bell className="w-4 h-4" />}
            onClick={(e) => {
              e.stopPropagation();
              router.push(m.href);
            }}
          >
            Notify Me
          </Button>
        )}
      </Card>
    );
  };

  return (
    <AppShell>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Modules</h1>
        <p className="text-foreground-muted mt-1">
          Find the right service for your organization. Start with GHG Inventory — it powers every
          other module.
        </p>
      </div>

      {/* Recommended for you */}
      <div className="mb-10">
        <h2 className="text-sm font-semibold text-foreground-muted uppercase tracking-wider mb-3">
          Recommended for you
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recommended.map((m) => (
            <ModuleCard key={m.id} m={m} />
          ))}
        </div>
      </div>

      {/* All modules */}
      <div>
        <h2 className="text-sm font-semibold text-foreground-muted uppercase tracking-wider mb-3">
          All modules
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {MODULE_REGISTRY.map((m) => (
            <ModuleCard key={m.id} m={m} />
          ))}
        </div>
      </div>
    </AppShell>
  );
}
