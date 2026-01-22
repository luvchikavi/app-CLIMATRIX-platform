'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { usePeriods } from '@/hooks/useEmissions';
import { cn } from '@/lib/utils';
import {
  Menu,
  Bell,
  User,
  LogOut,
  Settings,
  ChevronDown,
  Calendar,
  Plus,
  Search,
  HelpCircle,
} from 'lucide-react';

interface HeaderProps {
  onMenuClick?: () => void;
  sidebarCollapsed?: boolean;
}

export function Header({ onMenuClick, sidebarCollapsed }: HeaderProps) {
  const router = useRouter();
  const { user, organization, logout } = useAuthStore();
  const { data: periods } = usePeriods();

  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showPeriodMenu, setShowPeriodMenu] = useState(false);
  const [selectedPeriodId, setSelectedPeriodId] = useState<string>('');

  const userMenuRef = useRef<HTMLDivElement>(null);
  const periodMenuRef = useRef<HTMLDivElement>(null);

  // Close menus when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
      if (periodMenuRef.current && !periodMenuRef.current.contains(event.target as Node)) {
        setShowPeriodMenu(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Set default period
  useEffect(() => {
    if (periods?.length && !selectedPeriodId) {
      setSelectedPeriodId(periods[0].id);
    }
  }, [periods, selectedPeriodId]);

  const selectedPeriod = periods?.find(p => p.id === selectedPeriodId);

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  return (
    <header
      className={cn(
        'fixed top-0 right-0 z-30 h-16 bg-background-elevated border-b border-border',
        'flex items-center justify-between px-4 transition-all duration-300',
        sidebarCollapsed ? 'left-[72px]' : 'left-[280px]'
      )}
    >
      {/* Left side - Menu toggle (mobile) and Search */}
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-lg hover:bg-background-muted transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Search (placeholder for now) */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-2 bg-background-muted rounded-lg">
          <Search className="w-4 h-4 text-foreground-muted" />
          <input
            type="text"
            placeholder="Search activities..."
            className="bg-transparent text-sm focus:outline-none w-48 placeholder:text-foreground-muted"
          />
          <kbd className="hidden md:inline-flex px-1.5 py-0.5 text-xs text-foreground-muted bg-background rounded border border-border">
            /
          </kbd>
        </div>
      </div>

      {/* Right side - Period selector, notifications, user menu */}
      <div className="flex items-center gap-3">
        {/* Period Selector */}
        <div ref={periodMenuRef} className="relative">
          <button
            onClick={() => setShowPeriodMenu(!showPeriodMenu)}
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-lg border border-border',
              'hover:border-primary transition-colors text-sm'
            )}
          >
            <Calendar className="w-4 h-4 text-primary" />
            <span className="hidden sm:inline font-medium">
              {selectedPeriod?.name || 'Select Period'}
            </span>
            <ChevronDown className="w-4 h-4 text-foreground-muted" />
          </button>

          {showPeriodMenu && (
            <div className="absolute right-0 mt-2 w-64 bg-background-elevated rounded-xl shadow-lg border border-border py-2 animate-fade-in-down">
              <div className="px-3 py-2 border-b border-border">
                <p className="text-xs font-semibold text-foreground-muted uppercase">
                  Reporting Period
                </p>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {periods?.map((period) => (
                  <button
                    key={period.id}
                    onClick={() => {
                      setSelectedPeriodId(period.id);
                      setShowPeriodMenu(false);
                    }}
                    className={cn(
                      'w-full text-left px-3 py-2 hover:bg-background-muted transition-colors',
                      selectedPeriodId === period.id && 'bg-primary-light'
                    )}
                  >
                    <p className="font-medium text-sm">{period.name}</p>
                    <p className="text-xs text-foreground-muted">
                      {new Date(period.start_date).toLocaleDateString()} -{' '}
                      {new Date(period.end_date).toLocaleDateString()}
                    </p>
                  </button>
                ))}
              </div>
              <div className="px-3 py-2 border-t border-border">
                <button
                  onClick={() => {
                    router.push('/settings?tab=periods');
                    setShowPeriodMenu(false);
                  }}
                  className="flex items-center gap-2 text-sm text-primary hover:text-primary-hover"
                >
                  <Plus className="w-4 h-4" />
                  Create New Period
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Help */}
        <button className="p-2 rounded-lg hover:bg-background-muted transition-colors">
          <HelpCircle className="w-5 h-5 text-foreground-muted" />
        </button>

        {/* Notifications */}
        <button className="relative p-2 rounded-lg hover:bg-background-muted transition-colors">
          <Bell className="w-5 h-5 text-foreground-muted" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-accent rounded-full" />
        </button>

        {/* User Menu */}
        <div ref={userMenuRef} className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className={cn(
              'flex items-center gap-2 px-2 py-1.5 rounded-lg',
              'hover:bg-background-muted transition-colors'
            )}
          >
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <span className="text-white text-sm font-medium">
                {user?.email?.charAt(0).toUpperCase() || 'U'}
              </span>
            </div>
            <div className="hidden md:block text-left">
              <p className="text-sm font-medium text-foreground">
                {user?.email?.split('@')[0] || 'User'}
              </p>
              <p className="text-xs text-foreground-muted">
                {organization?.name || 'Organization'}
              </p>
            </div>
            <ChevronDown className="w-4 h-4 text-foreground-muted hidden md:block" />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-background-elevated rounded-xl shadow-lg border border-border py-2 animate-fade-in-down">
              <div className="px-4 py-3 border-b border-border">
                <p className="text-sm font-medium text-foreground">{user?.email}</p>
                <p className="text-xs text-foreground-muted">{organization?.name}</p>
              </div>
              <div className="py-1">
                <button
                  onClick={() => {
                    router.push('/settings?tab=profile');
                    setShowUserMenu(false);
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-foreground hover:bg-background-muted transition-colors"
                >
                  <User className="w-4 h-4" />
                  Profile Settings
                </button>
                <button
                  onClick={() => {
                    router.push('/settings');
                    setShowUserMenu(false);
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-foreground hover:bg-background-muted transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  Organization Settings
                </button>
              </div>
              <div className="py-1 border-t border-border">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-error hover:bg-error-50 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
