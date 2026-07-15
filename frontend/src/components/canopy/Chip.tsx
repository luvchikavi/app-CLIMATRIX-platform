import { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

/**
 * Provenance chip: where a number comes from. Default = quiet row tint
 * ("IL price", "IEA", "AI assumption"); `you` = accent-soft ("your data").
 * Phase 4's economics rows use these heavily.
 */
export interface ChipProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'you';
}

export function Chip({ variant = 'default', className, ...props }: ChipProps) {
  return (
    <span
      className={cn(
        'inline-block rounded-full px-2 py-[2.5px] text-[10px] font-semibold tracking-[0.03em]',
        variant === 'you' ? 'bg-cy-accent-soft text-cy-accent' : 'bg-cy-row text-cy-muted',
        className
      )}
      {...props}
    />
  );
}

/** Inline chip cluster after a measure name. */
export function ChipGroup({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn('ml-2 inline-flex gap-[5px] align-[1px]', className)}
      {...props}
    />
  );
}
