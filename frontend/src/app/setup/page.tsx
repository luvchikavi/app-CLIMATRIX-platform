'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { OnboardingWizard } from '@/components/onboarding';
import { Loader2 } from 'lucide-react';

/**
 * The required organization-setup gate. Renders the wizard full-screen (no AppShell/sidebar)
 * so a new client cannot reach the rest of the app until setup is complete.
 */
export default function SetupPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, organization } = useAuthStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- pre-existing intentional state sync on mount/deps change; no behavior change
    setMounted(true);
  }, []);

  // Not signed in -> landing
  useEffect(() => {
    if (mounted && !isLoading && !isAuthenticated) {
      router.push('/');
    }
  }, [mounted, isLoading, isAuthenticated, router]);

  // Already set up -> straight to the app
  useEffect(() => {
    if (mounted && organization?.setup_complete) {
      router.push('/dashboard');
    }
  }, [mounted, organization, router]);

  if (!mounted || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <OnboardingWizard
      onComplete={() => { /* handleComplete routes to /import */ }}
      organizationName={organization?.name}
    />
  );
}
