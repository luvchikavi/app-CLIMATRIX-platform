'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { TrialBanner, UpgradePrompt } from './TrialStatus';
import { SampleDataBanner } from '@/components/SampleDataBanner';
import { Shell, TopBar, type RailNavGroup, type RailNavItem } from '@/components/canopy';
import { useJourney } from '@/hooks/useJourney';
import { MODULE_REGISTRY } from '@/lib/modules';
import { Loader2 } from 'lucide-react';

interface AppShellProps {
  children: React.ReactNode;
}

/**
 * The authenticated app frame (batch 2.1: Canopy). Auth redirect, setup gate,
 * trial/sample banners and the upgrade modal carry over from the old shell;
 * the chrome is now canopy/Shell — forest rail (journey + nav) and the quiet
 * top-right cluster instead of a fixed header.
 */
export function AppShell({ children }: AppShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, organization, user, logout } = useAuthStore();
  const { steps } = useJourney();

  // Wait one tick for the persisted auth store to rehydrate — redirecting on the
  // very first render bounced hard page-loads of authed routes back to login.
  const [mounted, setMounted] = useState(false);
  // eslint-disable-next-line react-hooks/set-state-in-effect -- pre-existing intentional state sync on mount; no behavior change
  useEffect(() => setMounted(true), []);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (mounted && !isLoading && !isAuthenticated) {
      router.push('/');
    }
  }, [mounted, isAuthenticated, isLoading, router]);

  // Setup gate: an authenticated user whose org isn't set up yet is sent to /setup.
  // This single check gates dashboard, import, modules, activities, reports, etc.
  useEffect(() => {
    if (
      !isLoading &&
      isAuthenticated &&
      organization &&
      organization.setup_complete === false &&
      pathname !== '/setup'
    ) {
      router.push('/setup');
    }
  }, [isAuthenticated, isLoading, organization, pathname, router]);

  const nav = useMemo<(RailNavItem | RailNavGroup)[]>(() => {
    const isActive = (href: string) => pathname === href || pathname.startsWith(href + '/');
    const isSuperAdmin = user?.role === 'super_admin';

    // Journey-ordered rail. Coming-soon modules (PCAF/LCA/EPD) are not rail
    // entries at all — they live on /roadmap and the /modules catalog.
    // Tools holds real, working tools only; Workspace holds org-level pages.
    // Both groups render expanded so nothing hides behind a closed drawer.
    const cbam = MODULE_REGISTRY.find((m) => m.id === 'cbam');

    return [
      { label: 'Dashboard', href: '/dashboard', active: isActive('/dashboard') },
      { label: 'Data hub', href: '/hub', active: isActive('/hub') || isActive('/ingest') || isActive('/import') },
      { label: 'Activities', href: '/activities', active: isActive('/activities') },
      { label: 'Plan', href: '/decarbonization', active: isActive('/decarbonization') },
      { label: 'Reports', href: '/reports', active: isActive('/reports') },
      {
        label: 'Tools',
        separatorBefore: true,
        defaultOpen: true,
        items: cbam
          ? [
              {
                label: cbam.name,
                href: cbam.href,
                active: isActive(cbam.href),
                ...(cbam.status === 'beta' ? { badge: 'Beta' } : {}),
              },
            ]
          : [],
      },
      {
        label: 'Workspace',
        separatorBefore: true,
        defaultOpen: true,
        items: [
          { label: 'Sites', href: '/sites', active: isActive('/sites') },
          { label: 'Billing', href: '/billing', active: isActive('/billing') },
          { label: 'Roadmap', href: '/roadmap', active: isActive('/roadmap') },
          ...(isSuperAdmin
            ? [{ label: 'Audit trail', href: '/audit', active: isActive('/audit') }]
            : []),
        ],
      },
      // The company cockpit (dashboard + CRM) — internal, super admins only.
      ...(isSuperAdmin
        ? [
            {
              label: 'Super admin',
              href: '/admin',
              active: isActive('/admin') || isActive('/leads'),
              separatorBefore: true,
            },
          ]
        : []),
      {
        label: 'Settings',
        href: '/settings',
        active: isActive('/settings'),
        separatorBefore: !isSuperAdmin,
      },
    ];
  }, [pathname, user?.role]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-cy-canvas">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 h-10 w-10 animate-spin text-cy-accent" />
          <p className="text-cy-muted">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render app shell if not authenticated
  if (!isAuthenticated) {
    return null;
  }

  return (
    <>
      <Shell
        rail={{
          steps,
          nav,
          onSignOut: () => {
            logout();
            router.push('/');
          },
        }}
        topbar={<TopBar />}
      >
        {/* Quiet notice cluster — one-line rows, spacing owned here */}
        <div className="mb-4 empty:mb-0 flex flex-col gap-0.5">
          <TrialBanner />
          <SampleDataBanner />
        </div>
        {children}
      </Shell>

      {/* 402 limit-reached upgrade modal (global) */}
      <UpgradePrompt />
    </>
  );
}
