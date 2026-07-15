import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

/**
 * A journey/stepper row: number, title, description, right action. The open
 * step ("now") sits on an accent-soft pill row; done steps show their result;
 * locked steps recede. Children render under the description (e.g. measure
 * rows with provenance chips — Phase 4 uses this heavily).
 */
export interface StepRowProps {
  num: number | string;
  title: string;
  description?: ReactNode;
  state?: 'done' | 'now' | 'todo' | 'locked';
  /** right column, e.g. <CanopyButton>, <StepDoneText/>, <StepLockedText> */
  action?: ReactNode;
  children?: ReactNode;
  className?: string;
}

export function StepRow({
  num,
  title,
  description,
  state = 'todo',
  action,
  children,
  className,
}: StepRowProps) {
  return (
    <div
      className={cn(
        'grid grid-cols-[26px_1fr_auto] items-baseline gap-x-3.5 rounded-[12px] px-3.5 py-[15px]',
        state === 'now' && 'bg-cy-accent-soft',
        className
      )}
    >
      <span
        className={cn(
          'text-[12px] tabular-nums',
          state === 'done' || state === 'now'
            ? 'font-bold text-cy-accent'
            : 'font-semibold text-cy-faint'
        )}
      >
        {num}
      </span>
      <div className="min-w-0">
        <p
          className={cn(
            'text-[13.5px] font-semibold',
            state === 'locked' ? 'text-cy-faint' : 'text-cy-ink'
          )}
        >
          {title}
        </p>
        {description && (
          <p
            className={cn(
              'mt-[3px] max-w-[58ch] text-[12.5px]',
              state === 'locked' ? 'text-cy-faint' : 'text-cy-muted'
            )}
          >
            {description}
          </p>
        )}
        {children}
      </div>
      <span className="whitespace-nowrap text-[12.5px]">{action}</span>
    </div>
  );
}

/** "Done ✓" for a StepRow action slot. */
export function StepDoneText({ children = 'Done ✓' }: { children?: ReactNode }) {
  return <span className="font-semibold text-cy-accent">{children}</span>;
}

/** "Locked" / "After target" for a StepRow action slot. */
export function StepLockedText({ children = 'Locked' }: { children?: ReactNode }) {
  return <span className="text-cy-faint">{children}</span>;
}

/** Bold value inside a StepRow description ("64,468 t CO₂e"). */
export function StepValue({ children }: { children: ReactNode }) {
  return <b className="font-semibold tabular-nums text-cy-ink">{children}</b>;
}
