import { forwardRef, HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

/**
 * Canopy Surface — the only container. Radius 16, soft shadow, no border;
 * hierarchy comes from space and tint, never from lines (design contract §0.1).
 */
export interface SurfaceProps extends HTMLAttributes<HTMLDivElement> {
  /** soft = accent-tinted (active/current), warn = amber-tinted notices */
  tint?: 'none' | 'soft' | 'warn';
  /** panel = 20/24px (the default panel), tight = 12px (stepper wrappers) */
  padding?: 'panel' | 'tight' | 'none';
}

const tints = {
  none: 'bg-cy-surface',
  soft: 'bg-cy-accent-soft',
  warn: 'bg-cy-warn-soft',
};

const paddings = {
  panel: 'px-6 py-5',
  tight: 'p-3',
  none: '',
};

export const Surface = forwardRef<HTMLDivElement, SurfaceProps>(
  ({ className, tint = 'none', padding = 'panel', ...props }, ref) => (
    <div
      ref={ref}
      className={cn('rounded-cy shadow-cy-surface', tints[tint], paddings[padding], className)}
      {...props}
    />
  )
);
Surface.displayName = 'Surface';

/** The quiet 11px uppercase panel label ("Footprint · FY2025"). */
export const PanelLabel = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn(
        'mb-3.5 text-[11px] font-bold tracking-[0.08em] uppercase text-cy-faint',
        className
      )}
      {...props}
    />
  )
);
PanelLabel.displayName = 'PanelLabel';
