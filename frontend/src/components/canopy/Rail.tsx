import Link from 'next/link';
import { cn } from '@/lib/utils';

/**
 * The journey rail — the app chrome (design contract §0.1). Permanent left
 * rail on desktop: logo → "Your journey" steps → page nav pinned to the
 * bottom. Collapses to a top strip below lg (finalized in batch 2.1).
 * Phase 1 is presentational: states arrive as props; Phase 3's useJourney()
 * becomes the single source for them.
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
}

export interface RailNavGroup {
  label: string;
  items: RailNavItem[];
}

export interface RailProps {
  steps: RailJourneyStep[];
  nav: (RailNavItem | RailNavGroup)[];
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

function NavLink({ item }: { item: RailNavItem }) {
  return (
    <Link
      href={item.href}
      className={cn(
        'block hover:text-cy-rail-ink',
        item.active ? 'font-semibold text-cy-rail-ink' : 'text-cy-rail-muted'
      )}
    >
      {item.label}
    </Link>
  );
}

export function Logo({ className }: { className?: string }) {
  return (
    <p className={cn('text-[14px] font-bold tracking-[0.01em]', className)}>
      climatri<span className="text-cy-rail-accent">x</span>
    </p>
  );
}

export function Rail({ steps, nav, className }: RailProps) {
  return (
    <>
      {/* Desktop: the permanent rail */}
      <aside
        className={cn(
          'hidden bg-cy-rail px-[18px] py-[22px] text-cy-rail-ink lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col lg:overflow-y-auto',
          className
        )}
      >
        <Logo className="mx-1 mt-0.5 mb-[30px]" />
        <p className="mx-1 mb-3 text-[10px] font-bold tracking-[0.1em] uppercase text-cy-rail-faint">
          Your journey
        </p>
        {steps.map((step) => (
          <JourneyStep key={step.title} step={step} />
        ))}
        <nav className="mt-auto flex flex-col gap-3 border-t border-cy-rail-divider px-1 pt-[18px] pb-0.5 text-[12.5px]">
          {nav.map((item) =>
            isGroup(item) ? (
              <div key={item.label}>
                <p className="text-cy-rail-faint">{item.label} ▸</p>
                <div className="mt-2 flex flex-col gap-2 pl-3">
                  {item.items.map((sub) => (
                    <NavLink key={sub.label} item={sub} />
                  ))}
                </div>
              </div>
            ) : (
              <NavLink key={item.label} item={item} />
            )
          )}
        </nav>
      </aside>

      {/* Mobile: slim top journey strip */}
      <div className="flex items-center gap-4 overflow-x-auto bg-cy-rail px-4 py-3 text-cy-rail-ink lg:hidden">
        <Logo />
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
      </div>
    </>
  );
}
