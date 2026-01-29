'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/auth';
import {
  LayoutDashboard,
  PlusCircle,
  Upload,
  Building2,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  Leaf,
  Map,
  Coins,
  Scale,
  Microscope,
  FileStack,
  Lock,
  Shield,
  CreditCard,
} from 'lucide-react';

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
  disabled?: boolean;
  comingSoon?: boolean;
  superAdminOnly?: boolean;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const navigation: NavGroup[] = [
  {
    title: 'Main',
    items: [
      { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
      { label: 'Add Activity', href: '/dashboard?wizard=true', icon: PlusCircle },
      { label: 'Import Data', href: '/import', icon: Upload },
    ],
  },
  {
    title: 'Organization',
    items: [
      { label: 'Sites & Locations', href: '/sites', icon: Building2 },
      { label: 'Reports', href: '/reports', icon: FileText },
      { label: 'Billing', href: '/billing', icon: CreditCard },
      { label: 'Settings', href: '/settings', icon: Settings },
      { label: 'Roadmap', href: '/roadmap', icon: Map },
    ],
  },
  {
    title: 'Modules',
    items: [
      { label: 'GHG Inventory', href: '/modules/ghg', icon: Leaf, badge: 'Active' },
      { label: 'PCAF', href: '/modules/pcaf', icon: Coins, comingSoon: true },
      { label: 'CBAM', href: '/modules/cbam', icon: Scale, badge: 'Active' },
      { label: 'LCA', href: '/modules/lca', icon: Microscope, comingSoon: true },
      { label: 'EPD/Reports', href: '/modules/epd', icon: FileStack, comingSoon: true },
    ],
  },
  {
    title: 'Admin',
    items: [
      { label: 'Admin Dashboard', href: '/admin', icon: Shield, badge: 'Super', superAdminOnly: true },
    ],
  },
];

interface SidebarProps {
  collapsed?: boolean;
  onToggle?: () => void;
}

export function Sidebar({ collapsed = false, onToggle }: SidebarProps) {
  const pathname = usePathname();
  const { user } = useAuthStore();
  const isSuperAdmin = user?.role === 'super_admin';

  // Filter navigation to hide super admin items from non-super admins
  const filteredNavigation = navigation
    .map(group => ({
      ...group,
      items: group.items.filter(item => !item.superAdminOnly || isSuperAdmin)
    }))
    .filter(group => group.items.length > 0);

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 h-screen bg-background-elevated border-r border-border',
        'flex flex-col transition-all duration-300 ease-in-out',
        collapsed ? 'w-[72px]' : 'w-[280px]'
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-border">
        {!collapsed && (
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
              <Leaf className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-semibold text-foreground">CLIMATRIX</span>
          </Link>
        )}
        {collapsed && (
          <Link href="/dashboard" className="mx-auto">
            <div className="w-10 h-10 rounded-lg gradient-primary flex items-center justify-center">
              <Leaf className="w-6 h-6 text-white" />
            </div>
          </Link>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3">
        {filteredNavigation.map((group) => (
          <div key={group.title} className="mb-6">
            {!collapsed && (
              <h3 className="px-3 mb-2 text-xs font-semibold text-foreground-muted uppercase tracking-wider">
                {group.title}
              </h3>
            )}
            <ul className="space-y-1">
              {group.items.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
                const Icon = item.icon;
                const isDisabled = item.disabled || item.comingSoon;

                return (
                  <li key={item.href}>
                    <Link
                      href={isDisabled ? '#' : item.href}
                      className={cn(
                        'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
                        'group relative',
                        isActive
                          ? 'bg-primary text-white'
                          : 'text-foreground hover:bg-background-muted',
                        isDisabled && 'opacity-50 cursor-not-allowed',
                        collapsed && 'justify-center'
                      )}
                      onClick={(e) => isDisabled && e.preventDefault()}
                    >
                      <Icon className={cn('w-5 h-5 flex-shrink-0', isActive && 'text-white')} />
                      {!collapsed && (
                        <>
                          <span className="flex-1 text-sm font-medium">{item.label}</span>
                          {item.badge && (
                            <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-secondary text-white">
                              {item.badge}
                            </span>
                          )}
                          {item.comingSoon && (
                            <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-background-muted text-foreground-muted">
                              Soon
                            </span>
                          )}
                        </>
                      )}

                      {/* Tooltip for collapsed state */}
                      {collapsed && (
                        <div className="absolute left-full ml-2 px-2 py-1 bg-neutral-900 text-white text-sm rounded opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all whitespace-nowrap z-50">
                          {item.label}
                          {item.comingSoon && ' (Coming Soon)'}
                        </div>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Collapse Toggle */}
      <div className="p-3 border-t border-border">
        <button
          onClick={onToggle}
          className={cn(
            'w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg',
            'text-foreground-muted hover:bg-background-muted transition-colors'
          )}
        >
          {collapsed ? (
            <ChevronRight className="w-5 h-5" />
          ) : (
            <>
              <ChevronLeft className="w-5 h-5" />
              <span className="text-sm">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
