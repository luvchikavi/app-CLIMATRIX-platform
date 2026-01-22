import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { colors } from '@/lib/design-tokens';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md';
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => {
    const variants = {
      default: 'bg-background-muted text-foreground-muted',
      primary: 'bg-primary-light text-primary',
      secondary: 'bg-secondary-light text-secondary',
      success: 'bg-success-50 text-success',
      warning: 'bg-warning-50 text-warning',
      error: 'bg-error-50 text-error',
      info: 'bg-info-50 text-info',
    };

    const sizes = {
      sm: 'px-1.5 py-0.5 text-[10px]',
      md: 'px-2 py-0.5 text-xs',
    };

    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center font-semibold rounded-full uppercase tracking-wide',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      />
    );
  }
);

Badge.displayName = 'Badge';

// Scope Badge - Specific component for GHG scopes
export interface ScopeBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  scope: 1 | 2 | 3;
  size?: 'sm' | 'md';
  showLabel?: boolean;
}

export const ScopeBadge = forwardRef<HTMLSpanElement, ScopeBadgeProps>(
  ({ className, scope, size = 'md', showLabel = true, ...props }, ref) => {
    const scopeColors = {
      1: 'bg-[var(--color-scope1-light)] text-[var(--color-scope1)]',
      2: 'bg-[var(--color-scope2-light)] text-[var(--color-scope2)]',
      3: 'bg-[var(--color-scope3-light)] text-[var(--color-scope3)]',
    };

    const sizes = {
      sm: 'px-1.5 py-0.5 text-[10px]',
      md: 'px-2 py-0.5 text-xs',
    };

    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center font-semibold rounded-full uppercase tracking-wide',
          scopeColors[scope],
          sizes[size],
          className
        )}
        {...props}
      >
        {showLabel ? `Scope ${scope}` : scope}
      </span>
    );
  }
);

ScopeBadge.displayName = 'ScopeBadge';

// Status Badge
export interface StatusBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  status: 'active' | 'pending' | 'completed' | 'failed' | 'locked';
}

export const StatusBadge = forwardRef<HTMLSpanElement, StatusBadgeProps>(
  ({ className, status, ...props }, ref) => {
    const statusConfig = {
      active: { variant: 'success' as const, label: 'Active' },
      pending: { variant: 'warning' as const, label: 'Pending' },
      completed: { variant: 'primary' as const, label: 'Completed' },
      failed: { variant: 'error' as const, label: 'Failed' },
      locked: { variant: 'default' as const, label: 'Locked' },
    };

    const config = statusConfig[status];

    return (
      <Badge
        ref={ref}
        variant={config.variant}
        className={className}
        {...props}
      >
        {config.label}
      </Badge>
    );
  }
);

StatusBadge.displayName = 'StatusBadge';

// Confidence Badge
export interface ConfidenceBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  level: 'high' | 'medium' | 'low';
}

export const ConfidenceBadge = forwardRef<HTMLSpanElement, ConfidenceBadgeProps>(
  ({ className, level, ...props }, ref) => {
    const config = {
      high: { variant: 'success' as const, label: 'High' },
      medium: { variant: 'warning' as const, label: 'Medium' },
      low: { variant: 'error' as const, label: 'Low' },
    };

    return (
      <Badge
        ref={ref}
        variant={config[level].variant}
        className={className}
        {...props}
      >
        {config[level].label}
      </Badge>
    );
  }
);

ConfidenceBadge.displayName = 'ConfidenceBadge';
