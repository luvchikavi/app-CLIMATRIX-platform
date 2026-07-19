'use client';

import { Fragment, useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

/**
 * The journey rail — the app chrome (design contract §0.1). Permanent left
 * rail on desktop: logo → "Your journey" steps → page nav pinned to the
 * bottom. Below lg it collapses to a top strip with a disclosure menu.
 * Presentational: journey states arrive via props (useJourney provides them).
 */
export type JourneyStepState = 'done' | 'now' | 'todo' | 'locked';

export interface RailJourneyStep {
  title: string;
  status: string;
  state: JourneyStepState;
  /** Soft-lock (decision #3): locked steps stay clickable when href is set. */
  href?: string;
}

export interface RailNavItem {
  label: string;
  href: string;
  active?: boolean;
  /** small chip after the label, e.g. "Beta", "AI" */
  badge?: string;
  /** renders faint with a "Soon" chip and doesn't navigate */
  disabled?: boolean;
  /** hairline above this item — separates nav sections */
  separatorBefore?: boolean;
}

export interface RailNavGroup {
  label: string;
  items: RailNavItem[];
  /** hairline above this group — separates nav sections */
  separatorBefore?: boolean;
  /** start expanded — for groups used as always-visible sections */
  defaultOpen?: boolean;
}

export interface RailProps {
  steps: RailJourneyStep[];
  nav: (RailNavItem | RailNavGroup)[];
  /** renders a quiet "Sign out" at the very bottom of the rail */
  onSignOut?: () => void;
  className?: string;
}

function isGroup(item: RailNavItem | RailNavGroup): item is RailNavGroup {
  return 'items' in item;
}

function StepMarker({ state }: { state: JourneyStepState }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        'mt-px flex h-4 w-4 flex-none items-center justify-center rounded-full border-[1.5px]',
        state === 'done' && 'border-cy-rail-accent bg-cy-rail-accent',
        state === 'now' && 'border-cy-rail-accent',
        (state === 'todo' || state === 'locked') && 'border-cy-rail-faint'
      )}
    >
      {state === 'done' && (
        <span className="text-[9px] font-extrabold leading-none text-cy-rail">✓</span>
      )}
      {state === 'now' && <span className="h-1.5 w-1.5 rounded-full bg-cy-rail-accent" />}
    </span>
  );
}

function JourneyStep({ step }: { step: RailJourneyStep }) {
  const body = (
    <>
      <StepMarker state={step.state} />
      <span className="min-w-0">
        <span
          className={cn(
            'block text-[13px] font-semibold',
            step.state === 'now' && 'text-cy-rail-accent',
            step.state === 'locked' && 'text-cy-rail-faint'
          )}
        >
          {step.title}
        </span>
        <span
          className={cn(
            'mt-0.5 block text-[11px] leading-[1.4]',
            step.state === 'locked' ? 'text-cy-rail-faint' : 'text-cy-rail-muted'
          )}
        >
          {step.status}
        </span>
      </span>
    </>
  );
  const cls = cn(
    'mb-1 flex gap-[11px] rounded-[10px] px-2 py-2',
    step.state === 'now' && 'bg-cy-rail-soft'
  );
  if (step.href) {
    return (
      <Link href={step.href} className={cls}>
        {body}
      </Link>
    );
  }
  return <div className={cls}>{body}</div>;
}

function NavBadge({ children }: { children: string }) {
  return (
    <span className="ml-2 rounded-full bg-cy-rail-soft px-1.5 py-px align-[1px] text-[9.5px] font-bold tracking-[0.04em] text-cy-rail-accent">
      {children}
    </span>
  );
}

function NavLink({ item, onNavigate }: { item: RailNavItem; onNavigate?: () => void }) {
  if (item.disabled) {
    return (
      <span className="block cursor-not-allowed text-cy-rail-faint">
        {item.label}
        <span className="ml-2 rounded-full bg-cy-rail-soft px-1.5 py-px align-[1px] text-[9.5px] font-bold tracking-[0.04em] text-cy-rail-faint">
          Soon
        </span>
      </span>
    );
  }
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      className={cn(
        'block hover:text-cy-rail-ink',
        item.active ? 'font-semibold text-cy-rail-ink' : 'text-cy-rail-muted'
      )}
    >
      {item.label}
      {item.badge && <NavBadge>{item.badge}</NavBadge>}
    </Link>
  );
}

/** A collapsible sub-tab group: closed by default, opens on click; stays open
 *  while one of its children is the active page. */
function NavGroup({
  group,
  onNavigate,
}: {
  group: RailNavGroup;
  onNavigate?: () => void;
}) {
  const hasActive = group.items.some((sub) => sub.active);
  const [open, setOpen] = useState(hasActive || group.defaultOpen === true);

  // Navigating into a child (e.g. via a deep link) reveals the group.
  useEffect(() => {
    if (hasActive) setOpen(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasActive]);

  return (
    <div>
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          'flex w-full cursor-pointer items-center justify-between text-left hover:text-cy-rail-ink',
          hasActive ? 'font-semibold text-cy-rail-ink' : 'text-cy-rail-muted'
        )}
      >
        {group.label}
        <span
          aria-hidden="true"
          className={cn(
            'text-[10px] text-cy-rail-faint transition-transform',
            open && 'rotate-90'
          )}
        >
          ▸
        </span>
      </button>
      {open && (
        <div className="mt-2 flex flex-col gap-2 border-l border-cy-rail-divider pl-3">
          {group.items.map((sub) => (
            <NavLink key={sub.label} item={sub} onNavigate={onNavigate} />
          ))}
        </div>
      )}
    </div>
  );
}

function NavList({
  nav,
  onNavigate,
  className,
}: {
  nav: (RailNavItem | RailNavGroup)[];
  onNavigate?: () => void;
  className?: string;
}) {
  return (
    <nav className={cn('flex flex-col gap-3 text-[12.5px]', className)}>
      {nav.map((item) => (
        <Fragment key={item.label}>
          {item.separatorBefore && (
            <span aria-hidden="true" className="my-0.5 h-px bg-cy-rail-divider" />
          )}
          {isGroup(item) ? (
            <NavGroup group={item} onNavigate={onNavigate} />
          ) : (
            <NavLink item={item} onNavigate={onNavigate} />
          )}
        </Fragment>
      ))}
    </nav>
  );
}

export function Logo({ className }: { className?: string }) {
  return (
    <p className={cn('text-[14px] font-bold tracking-[0.01em]', className)}>
      climatri<span className="text-cy-rail-accent">x</span>
    </p>
  );
}

export function Rail({ steps, nav, onSignOut, className }: RailProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();

  // Close the mobile menu on navigation.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional state sync on route change
    setMenuOpen(false);
  }, [pathname]);

  return (
    <>
      {/* Desktop: the permanent rail */}
      <aside
        className={cn(
          'hidden bg-cy-rail px-[18px] py-[22px] text-cy-rail-ink lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col lg:overflow-y-auto',
          className
        )}
      >
        <Link href="/dashboard" className="mx-1 mt-0.5 mb-[30px] block">
          <Logo />
        </Link>
        <p className="mx-1 mb-3 text-[10px] font-bold tracking-[0.1em] uppercase text-cy-rail-faint">
          Your journey
        </p>
        {steps.map((step) => (
          <JourneyStep key={step.title} step={step} />
        ))}
        <NavList
          nav={nav}
          className="mt-auto border-t border-cy-rail-divider px-1 pt-[18px] pb-0.5"
        />
        {onSignOut && (
          <button
            type="button"
            onClick={onSignOut}
            className="mx-1 mt-3 cursor-pointer text-left text-[12px] text-cy-rail-faint hover:text-cy-rail-ink"
          >
            Sign out
          </button>
        )}
      </aside>

      {/* Mobile: slim top journey strip + disclosure nav */}
      <div className="bg-cy-rail text-cy-rail-ink lg:hidden">
        <div className="flex items-center gap-4 overflow-x-auto px-4 py-3">
          <Link href="/dashboard">
            <Logo />
          </Link>
          <div className="flex items-center gap-3">
            {steps.map((step) => (
              <span key={step.title} className="flex items-center gap-1.5 whitespace-nowrap">
                <StepMarker state={step.state} />
                <span
                  className={cn(
                    'text-[12px] font-semibold',
                    step.state === 'now' && 'text-cy-rail-accent',
                    step.state === 'locked' && 'text-cy-rail-faint'
                  )}
                >
                  {step.title}
                </span>
              </span>
            ))}
          </div>
          <button
            type="button"
            aria-expanded={menuOpen}
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            onClick={() => setMenuOpen((v) => !v)}
            className="ml-auto rounded-[8px] px-2.5 py-1.5 text-[12.5px] font-semibold text-cy-rail-muted hover:text-cy-rail-ink"
          >
            {menuOpen ? '✕' : 'Menu'}
          </button>
        </div>
        {menuOpen && (
          <div className="border-t border-cy-rail-divider px-5 py-4">
            <NavList nav={nav} onNavigate={() => setMenuOpen(false)} />
            {onSignOut && (
              <button
                type="button"
                onClick={onSignOut}
                className="mt-4 cursor-pointer text-left text-[12px] text-cy-rail-faint hover:text-cy-rail-ink"
              >
                Sign out
              </button>
            )}
          </div>
        )}
      </div>
    </>
  );
}
