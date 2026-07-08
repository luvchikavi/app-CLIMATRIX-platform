'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { TrialBanner, UpgradePrompt } from './TrialStatus';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, organization } = useAuthStore();

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  // Wait one tick for the persisted auth store to rehydrate — redirecting on the
  // very first render bounced hard page-loads of authed routes back to login.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

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

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-primary animate-spin mx-auto mb-4" />
          <p className="text-foreground-muted">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render app shell if not authenticated
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop Sidebar */}
      <div className="hidden lg:block">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      </div>

      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-40 w-[280px] bg-background-elevated border-r border-border',
          'transform transition-transform duration-300 ease-in-out lg:hidden',
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <Sidebar onToggle={() => setMobileMenuOpen(false)} />
      </div>

      {/* Header */}
      <Header
        onMenuClick={() => setMobileMenuOpen(true)}
        sidebarCollapsed={sidebarCollapsed}
      />

      {/* Main Content */}
      <main
        id="main-content"
        className={cn(
          'pt-16 min-h-screen transition-all duration-300',
          sidebarCollapsed ? 'lg:pl-[72px]' : 'lg:pl-[280px]'
        )}
      >
        <div className="p-4 md:p-6 lg:p-8">
          <TrialBanner />
          {children}
        </div>
      </main>

      {/* 402 limit-reached upgrade modal (global) */}
      <UpgradePrompt />
    </div>
  );
}
