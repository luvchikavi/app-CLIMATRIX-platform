'use client';

import { useState, useEffect, Suspense } from 'react';
import { useAuthStore } from '@/stores/auth';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api, SubscriptionPlan, PlanInfo } from '@/lib/api';
import { AppShell } from '@/components/layout';
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Badge,
  toast,
} from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  CreditCard,
  Check,
  Loader2,
  Zap,
  Building2,
  Sparkles,
  Crown,
  ExternalLink,
} from 'lucide-react';

function BillingPageContent() {
  const { user, isAuthenticated } = useAuthStore();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [mounted, setMounted] = useState(false);

  // Check for success/cancel from Stripe checkout
  const checkoutStatus = searchParams.get('checkout');

  // Fetch current subscription
  const { data: subscription, isLoading: subscriptionLoading, refetch: refetchSubscription } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => api.getSubscription(),
    enabled: isAuthenticated,
  });

  // Fetch available plans
  const { data: plansData, isLoading: plansLoading } = useQuery({
    queryKey: ['plans'],
    queryFn: () => api.getPlans(),
  });

  // Create checkout session mutation
  const createCheckout = useMutation({
    mutationFn: (plan: SubscriptionPlan) =>
      api.createCheckout(
        plan,
        `${window.location.origin}/billing?checkout=success`,
        `${window.location.origin}/billing?checkout=canceled`
      ),
    onSuccess: (data) => {
      window.location.href = data.url;
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create checkout session');
    },
  });

  // Create portal session mutation
  const createPortal = useMutation({
    mutationFn: () => api.createPortal(`${window.location.origin}/billing`),
    onSuccess: (data) => {
      window.location.href = data.url;
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to open subscription management');
    },
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isAuthenticated) {
      router.push('/');
    }
  }, [mounted, isAuthenticated, router]);

  // Refetch subscription after successful checkout
  useEffect(() => {
    if (checkoutStatus === 'success') {
      refetchSubscription();
      toast.success('Subscription updated successfully!');
    } else if (checkoutStatus === 'canceled') {
      toast.warning('Checkout was canceled. No changes were made.');
    }
  }, [checkoutStatus, refetchSubscription]);

  if (!mounted || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  const isLoading = subscriptionLoading || plansLoading;
  const plans = plansData?.plans || [];
  const currentPlan = subscription?.plan || 'free';

  // Compute trial info
  const trialEndsAt = subscription?.trial_ends_at ? new Date(subscription.trial_ends_at) : null;
  const trialDaysRemaining = trialEndsAt
    ? // eslint-disable-next-line react-hooks/purity -- day-granularity countdown; stable within a render
      Math.max(0, Math.ceil((trialEndsAt.getTime() - Date.now()) / (1000 * 60 * 60 * 24)))
    : 0;

  const getPlanIcon = (planId: string) => {
    switch (planId) {
      case 'free':
        return Zap;
      case 'starter':
        return Sparkles;
      case 'professional':
        return Building2;
      case 'enterprise':
        return Crown;
      default:
        return Zap;
    }
  };

  const getPlanColor = (planId: string) => {
    switch (planId) {
      case 'free':
        return 'text-foreground-muted';
      case 'starter':
        return 'text-primary';
      case 'professional':
        return 'text-success';
      case 'enterprise':
        return 'text-warning';
      default:
        return 'text-foreground-muted';
    }
  };

  const handleUpgrade = (plan: SubscriptionPlan) => {
    if (plan === 'enterprise') {
      // eslint-disable-next-line react-hooks/immutability -- intentional navigation side effect inside an event handler
      window.location.href = 'mailto:sales@climatrix.co?subject=Enterprise Plan Inquiry';
      return;
    }
    createCheckout.mutate(plan);
  };

  const handleManageSubscription = () => {
    createPortal.mutate();
  };

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-[20px] font-[650] tracking-[-0.01em] text-cy-ink">Billing &amp; plans</h1>
          <p className="mt-[3px] text-[13px] text-cy-muted">
            Manage your subscription and billing details
          </p>
        </div>
      </div>

      {/* Checkout Status Messages */}
      {checkoutStatus === 'success' && (
        <div className="mb-6 flex items-center gap-2.5 rounded-[12px] bg-cy-accent-soft p-3.5">
          <span className="h-[7px] w-[7px] shrink-0 rounded-full bg-cy-accent" aria-hidden="true" />
          <p className="text-[12.5px] font-semibold text-cy-accent">
            Subscription updated — thank you!
          </p>
        </div>
      )}

      {checkoutStatus === 'canceled' && (
        <div className="mb-6 flex items-center gap-2.5 rounded-[12px] bg-cy-warn-soft p-3.5">
          <span className="h-[7px] w-[7px] shrink-0 rounded-full bg-cy-warn" aria-hidden="true" />
          <p className="text-[12.5px] font-semibold text-cy-warn">
            Checkout was canceled — no changes were made to your subscription.
          </p>
        </div>
      )}

      {/* Trial Status Banner */}
      {subscription?.is_trialing && trialEndsAt && (
        <div className="mb-6 flex items-center justify-between gap-4 rounded-[12px] bg-cy-warn-soft p-3.5">
          <div className="flex items-center gap-2.5">
            <span className="h-[7px] w-[7px] shrink-0 rounded-full bg-cy-warn" aria-hidden="true" />
            <div>
              <p className="text-[12.5px] font-bold text-cy-warn">
                Trial · {trialDaysRemaining} day{trialDaysRemaining !== 1 ? 's' : ''} remaining
              </p>
              <p className="text-[12px] text-cy-muted mt-0.5">
                Your trial ends on {trialEndsAt.toLocaleDateString()}. Upgrade to a paid plan to keep full access.
              </p>
            </div>
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              const plansSection = document.getElementById('available-plans');
              plansSection?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            Upgrade Now
          </Button>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-foreground-muted">Loading billing information...</span>
        </div>
      )}

      {/* Content */}
      {!isLoading && (
        <div className="space-y-8">
          {/* Current Plan Card */}
          <Card padding="lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-foreground-muted" />
                Current Subscription
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex items-center gap-4">
                  {(() => {
                    const Icon = getPlanIcon(currentPlan);
                    return (
                      <div className={cn('p-3 rounded-xl bg-background-muted', getPlanColor(currentPlan))}>
                        <Icon className="w-6 h-6" />
                      </div>
                    );
                  })()}
                  <div>
                    <h3 className="text-[15px] font-bold text-foreground capitalize tracking-[-0.01em]">
                      {currentPlan} plan
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      {subscription?.status && (
                        <Badge
                          variant={
                            subscription.status === 'active'
                              ? 'success'
                              : subscription.status === 'trialing'
                              ? 'primary'
                              : 'warning'
                          }
                        >
                          {subscription.status}
                        </Badge>
                      )}
                      {subscription?.is_trialing && (
                        <span className="text-sm text-foreground-muted">
                          Trial ends {subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : 'soon'}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {currentPlan !== 'free' && (
                  <Button
                    variant="outline"
                    onClick={handleManageSubscription}
                    disabled={createPortal.isPending}
                    rightIcon={<ExternalLink className="w-4 h-4" />}
                  >
                    {createPortal.isPending ? 'Loading...' : 'Manage Subscription'}
                  </Button>
                )}
              </div>

              {/* Current Plan Limits */}
              {subscription?.plan_limits && (
                <div className="mt-6">
                  <h4 className="mb-3.5 text-[11px] font-bold uppercase tracking-[0.08em] text-cy-faint">Your plan limits</h4>
                  <div className="flex flex-wrap gap-x-11 gap-y-2.5">
                    <div>
                      <p className="text-[16px] font-[650] tabular-nums text-cy-ink">
                        {subscription.plan_limits.activities_per_month === -1
                          ? 'Unlimited'
                          : subscription.plan_limits.activities_per_month.toLocaleString()}
                      </p>
                      <p className="mt-0.5 text-[11.5px] text-cy-muted">Activities / month</p>
                    </div>
                    <div>
                      <p className="text-[16px] font-[650] tabular-nums text-cy-ink">
                        {subscription.plan_limits.users === -1
                          ? 'Unlimited'
                          : subscription.plan_limits.users}
                      </p>
                      <p className="mt-0.5 text-[11.5px] text-cy-muted">Team members</p>
                    </div>
                    <div>
                      <p className="text-[16px] font-[650] tabular-nums text-cy-ink">
                        {subscription.plan_limits.sites === -1
                          ? 'Unlimited'
                          : subscription.plan_limits.sites}
                      </p>
                      <p className="mt-0.5 text-[11.5px] text-cy-muted">Sites</p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Available Plans */}
          <div id="available-plans">
            <h2 className="text-xl font-bold text-foreground mb-4">Available Plans</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {plans.map((plan: PlanInfo) => {
                const Icon = getPlanIcon(plan.id);
                const isCurrentPlan = plan.id === currentPlan;
                const isPopular = plan.id === 'professional';

                return (
                  <Card
                    key={plan.id}
                    padding="lg"
                    className={cn(
                      'relative',
                      isPopular && 'ring-2 ring-cy-accent'
                    )}
                  >
                    {isPopular && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                        <Badge variant="primary">Most Popular</Badge>
                      </div>
                    )}

                    <div className="text-center mb-6">
                      <div className={cn('inline-flex p-3 rounded-xl bg-background-muted mb-4', getPlanColor(plan.id))}>
                        <Icon className="w-6 h-6" />
                      </div>
                      <h3 className="text-[14px] font-bold text-foreground">{plan.name}</h3>
                      <div className="mt-2">
                        {plan.price_monthly !== null ? (
                          <>
                            <span className="text-[20px] font-[650] tabular-nums text-foreground">${plan.price_monthly}</span>
                            <span className="text-[12.5px] text-cy-muted"> /month</span>
                          </>
                        ) : (
                          <span className="text-[14px] font-semibold text-foreground">Custom pricing</span>
                        )}
                      </div>
                    </div>

                    <ul className="space-y-3 mb-6">
                      {plan.features.map((feature, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <Check className="w-4 h-4 text-success mt-0.5 flex-shrink-0" />
                          <span className="text-foreground-muted">{feature}</span>
                        </li>
                      ))}
                    </ul>

                    <div className="mt-auto">
                      {isCurrentPlan ? (
                        <Button variant="outline" className="w-full" disabled>
                          Current Plan
                        </Button>
                      ) : (
                        <Button
                          variant={isPopular ? 'primary' : 'outline'}
                          className="w-full"
                          onClick={() => handleUpgrade(plan.id)}
                          disabled={createCheckout.isPending}
                        >
                          {plan.id === 'enterprise'
                            ? 'Contact Sales'
                            : plan.id === 'free'
                            ? 'Downgrade'
                            : 'Upgrade'}
                        </Button>
                      )}
                    </div>
                  </Card>
                );
              })}
            </div>
          </div>

          {/* FAQ Section */}
          <Card padding="lg">
            <CardHeader>
              <CardTitle>Frequently Asked Questions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <h4 className="font-semibold text-foreground mb-2">Can I change plans at any time?</h4>
                  <p className="text-foreground-muted">
                    Yes, you can upgrade or downgrade your plan at any time. When upgrading, you&apos;ll be charged the prorated difference. When downgrading, your current plan continues until the end of the billing period.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold text-foreground mb-2">What payment methods do you accept?</h4>
                  <p className="text-foreground-muted">
                    We accept all major credit cards (Visa, MasterCard, American Express) through our secure payment provider Stripe.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold text-foreground mb-2">Is there a free trial?</h4>
                  <p className="text-foreground-muted">
                    Yes! All paid plans come with a 14-day free trial. You won&apos;t be charged until the trial ends, and you can cancel anytime.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold text-foreground mb-2">What happens if I exceed my plan limits?</h4>
                  <p className="text-foreground-muted">
                    If you approach your limits, we&apos;ll notify you so you can upgrade. We never delete your data - you can always view your existing data, but adding new activities may be restricted until you upgrade.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </AppShell>
  );
}

function BillingLoading() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-primary animate-spin" />
    </div>
  );
}

export default function BillingPage() {
  return (
    <Suspense fallback={<BillingLoading />}>
      <BillingPageContent />
    </Suspense>
  );
}
