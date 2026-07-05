'use client';

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Sparkles, Lock } from 'lucide-react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui';

/** Persistent trial countdown shown at the top of the app while a trial is active. */
export function TrialBanner() {
  const { data } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => api.getSubscription(),
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  if (!data?.is_trialing || !data.trial_ends_at) return null;

  const days = Math.max(
    0,
    Math.ceil((new Date(data.trial_ends_at).getTime() - Date.now()) / 86_400_000)
  );
  const urgent = days <= 3;

  return (
    <div
      className={cn(
        'flex items-center justify-between gap-3 px-4 py-2 rounded-lg border text-sm mb-4',
        urgent
          ? 'bg-error/10 border-error/30 text-error'
          : 'bg-primary/10 border-primary/20 text-foreground'
      )}
    >
      <span className="flex items-center gap-2">
        <Sparkles className="w-4 h-4 shrink-0" />
        {days > 0
          ? `${days} day${days === 1 ? '' : 's'} left in your free trial`
          : 'Your free trial has ended'}
      </span>
      <Link href="/pricing" className="font-semibold underline shrink-0">
        Upgrade
      </Link>
    </div>
  );
}

/** Listens for 402 "limit reached" events (dispatched by the API client) and shows
 *  a targeted upgrade modal instead of a generic error. */
export function UpgradePrompt() {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail || {};
      setMessage(detail.message || 'Upgrade to unlock this feature.');
    };
    window.addEventListener('climatrix:limit-reached', handler as EventListener);
    return () =>
      window.removeEventListener('climatrix:limit-reached', handler as EventListener);
  }, []);

  if (!message) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={() => setMessage(null)} />
      <div className="relative bg-background-elevated border border-border rounded-2xl shadow-xl max-w-md w-full p-6 text-center">
        <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
          <Lock className="w-6 h-6 text-primary" />
        </div>
        <h3 className="text-lg font-semibold text-foreground mb-2">Upgrade to continue</h3>
        <p className="text-sm text-foreground-muted mb-6">{message}</p>
        <div className="flex gap-3 justify-center">
          <Button variant="outline" onClick={() => setMessage(null)}>
            Not now
          </Button>
          <Button
            variant="primary"
            onClick={() => {
              setMessage(null);
              router.push('/pricing');
            }}
          >
            See plans
          </Button>
        </div>
      </div>
    </div>
  );
}
