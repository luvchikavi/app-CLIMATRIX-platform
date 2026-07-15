'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout';
import { LeadsPanel } from '@/components/admin/LeadsPanel';
import { useAuthStore } from '@/stores/auth';

/**
 * Standalone deep link to the lead CRM. The cockpit's Leads tab renders the
 * same panel; the rail's "Super admin" entry covers both routes. Company-
 * internal — super admins only (the API enforces this server-side too).
 */
export default function LeadsPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated && user && user.role !== 'super_admin') {
      router.push('/dashboard');
    }
  }, [isAuthenticated, user, router]);

  if (!user || user.role !== 'super_admin') return null;

  return (
    <AppShell>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-[20px] font-[650] tracking-[-0.01em] text-foreground">Leads</h1>
          <p className="text-foreground-muted mt-1">
            Track people who tried the app, left details, or came from a conference or forum.
          </p>
        </div>
      </div>
      <LeadsPanel />
    </AppShell>
  );
}
