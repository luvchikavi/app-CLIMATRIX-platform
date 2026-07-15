'use client';

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Lock } from 'lucide-react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui';

/** Quiet one-line trial notice — a dot and a sentence, never a box (Canopy). */
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
    // eslint-disable-next-line react-hooks/purity -- day-granularity countdown; stable within a render
    Math.ceil((new Date(data.trial_ends_at).getTime() - Date.now()) / 86_400_000)
  );
  const urgent = days <= 3;

  return (
    <div className="flex items-center gap-2 text-[12.5px] text-cy-muted">
      <span
        className={cn('w-[7px] h-[7px] rounded-full shrink-0', urgent ? 'bg-error' : 'bg-cy-warn')}
        aria-hidden="true"
      />
      <span>
        {days > 0
          ? `Trial · ${days} day${days === 1 ? '' : 's'} left — full results unlock on a plan`
          : 'Your free trial has ended'}
      </span>
      <span className="text-cy-faint" aria-hidden="true">·</span>
      <Link href="/pricing" className="font-bold text-cy-accent shrink-0">
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
      <div className="absolute inset-0 bg-black/40" onClick={() => setMessage(null)} />
      <div className="relative bg-background-elevated rounded-cy shadow-xl max-w-md w-full p-6 text-center">
        <div className="w-11 h-11 rounded-full bg-cy-accent-soft flex items-center justify-center mx-auto mb-4">
          <Lock className="w-5 h-5 text-cy-accent" strokeWidth={1.75} />
        </div>
        <h3 className="text-[16px] font-bold text-foreground mb-2 tracking-[-0.01em]">Upgrade to continue</h3>
        <p className="text-[12.5px] text-foreground-muted mb-6">{message}</p>
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
