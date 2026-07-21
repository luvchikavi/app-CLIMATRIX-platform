'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import { usePeriods } from '@/hooks/useEmissions';
import { cn } from '@/lib/utils';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { HelpCircle } from 'lucide-react';

/**
 * The quiet top-right cluster: period selector + theme toggle + user menu.
 * Replaces the fixed Header — the page heading owns the top of the canvas,
 * this recedes (design contract §0.1: one focus per page).
 */
export function TopBar({ className }: { className?: string }) {
  const router = useRouter();
  const { user, organization, logout } = useAuthStore();
  const { selectedPeriodId, setSelectedPeriodId } = usePeriodStore();
  const { data: periods } = usePeriods();

  const [openMenu, setOpenMenu] = useState<'period' | 'user' | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpenMenu(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Default / heal the persisted period id (same behavior as the old Header).
  useEffect(() => {
    if (!periods?.length) return;
    if (!selectedPeriodId || !periods.some((p) => p.id === selectedPeriodId)) {
      setSelectedPeriodId(periods[0].id);
    }
  }, [periods, selectedPeriodId, setSelectedPeriodId]);

  const selectedPeriod = periods?.find((p) => p.id === selectedPeriodId);

  const pillCls =
    'flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[12.5px] font-semibold text-cy-muted hover:bg-cy-row hover:text-cy-ink cursor-pointer';

  return (
    <div ref={rootRef} className={cn('flex items-center justify-end gap-1', className)}>
      {/* Period selector */}
      <div className="relative">
        <button
          type="button"
          onClick={() => setOpenMenu(openMenu === 'period' ? null : 'period')}
          className={pillCls}
          aria-expanded={openMenu === 'period'}
        >
          {selectedPeriod?.name || 'Select period'}
          <span aria-hidden="true" className="text-[10px] text-cy-faint">▾</span>
        </button>
        {openMenu === 'period' && (
          <div className="absolute right-0 z-40 mt-2 w-64 rounded-[14px] bg-cy-surface py-2 shadow-cy-surface">
            <p className="px-4 pt-1 pb-2 text-[10.5px] font-bold tracking-[0.07em] uppercase text-cy-faint">
              Reporting period
            </p>
            <div className="max-h-64 overflow-y-auto">
              {periods?.map((period) => (
                <button
                  key={period.id}
                  type="button"
                  onClick={() => {
                    setSelectedPeriodId(period.id);
                    setOpenMenu(null);
                  }}
                  className={cn(
                    'block w-full px-4 py-2 text-left text-[13px] hover:bg-cy-row',
                    selectedPeriodId === period.id
                      ? 'bg-cy-accent-soft font-semibold text-cy-accent'
                      : 'text-cy-ink'
                  )}
                >
                  {period.name}
                  <span className="mt-0.5 block text-[11.5px] font-normal text-cy-muted">
                    {new Date(period.start_date).toLocaleDateString()} –{' '}
                    {new Date(period.end_date).toLocaleDateString()}
                  </span>
                </button>
              ))}
            </div>
            <button
              type="button"
              onClick={() => {
                router.push('/settings?tab=periods');
                setOpenMenu(null);
              }}
              className="mt-1 block w-full px-4 py-2 text-left text-[12.5px] font-semibold text-cy-accent hover:bg-cy-row"
            >
              + Create new period
            </button>
          </div>
        )}
      </div>

      {/* Help center */}
      <button
        type="button"
        onClick={() => router.push('/help')}
        className={pillCls}
        title="Help & support"
      >
        <HelpCircle className="h-4 w-4" strokeWidth={1.75} />
        <span className="hidden sm:inline">Help</span>
      </button>

      <ThemeToggle />

      {/* User menu */}
      <div className="relative">
        <button
          type="button"
          onClick={() => setOpenMenu(openMenu === 'user' ? null : 'user')}
          className={pillCls}
          aria-expanded={openMenu === 'user'}
        >
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-cy-accent-soft text-[11px] font-bold text-cy-accent">
            {user?.email?.charAt(0).toUpperCase() || 'U'}
          </span>
          <span className="hidden sm:inline">{user?.email?.split('@')[0] || 'Account'}</span>
          <span aria-hidden="true" className="text-[10px] text-cy-faint">▾</span>
        </button>
        {openMenu === 'user' && (
          <div className="absolute right-0 z-40 mt-2 w-60 rounded-[14px] bg-cy-surface py-2 shadow-cy-surface">
            <div className="px-4 pt-1 pb-2.5">
              <p className="truncate text-[13px] font-semibold text-cy-ink">{user?.email}</p>
              <p className="truncate text-[11.5px] text-cy-muted">{organization?.name}</p>
            </div>
            {(
              [
                { label: 'Profile settings', to: '/settings?tab=profile' },
                { label: 'Organization settings', to: '/settings' },
              ] as const
            ).map((item) => (
              <button
                key={item.label}
                type="button"
                onClick={() => {
                  router.push(item.to);
                  setOpenMenu(null);
                }}
                className="block w-full px-4 py-2 text-left text-[13px] text-cy-ink hover:bg-cy-row"
              >
                {item.label}
              </button>
            ))}
            <button
              type="button"
              onClick={() => {
                logout();
                router.push('/');
              }}
              className="mt-1 block w-full px-4 py-2 text-left text-[13px] font-semibold text-error hover:bg-cy-row"
            >
              Sign out
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
