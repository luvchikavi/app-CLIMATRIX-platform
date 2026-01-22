import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface KPICardProps extends HTMLAttributes<HTMLDivElement> {
  title: string;
  value: string | number;
  unit?: string;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  variant?: 'default' | 'scope1' | 'scope2' | 'scope3';
  size?: 'sm' | 'md' | 'lg';
}

export const KPICard = forwardRef<HTMLDivElement, KPICardProps>(
  (
    {
      className,
      title,
      value,
      unit,
      change,
      changeLabel,
      icon,
      variant = 'default',
      size = 'md',
      ...props
    },
    ref
  ) => {
    const variantStyles = {
      default: 'border-border-muted',
      scope1: 'border-l-4 border-l-scope1',
      scope2: 'border-l-4 border-l-scope2',
      scope3: 'border-l-4 border-l-scope3',
    };

    const sizes = {
      sm: { padding: 'p-4', value: 'text-2xl', title: 'text-xs' },
      md: { padding: 'p-6', value: 'text-3xl', title: 'text-sm' },
      lg: { padding: 'p-8', value: 'text-4xl', title: 'text-base' },
    };

    const getTrendIcon = () => {
      if (change === undefined) return null;
      if (change > 0) return <TrendingUp className="w-4 h-4" />;
      if (change < 0) return <TrendingDown className="w-4 h-4" />;
      return <Minus className="w-4 h-4" />;
    };

    const getTrendColor = () => {
      if (change === undefined) return '';
      // For emissions, DOWN is good (green), UP is bad (red)
      if (change < 0) return 'text-success';
      if (change > 0) return 'text-error';
      return 'text-foreground-muted';
    };

    return (
      <div
        ref={ref}
        className={cn(
          'bg-background-elevated rounded-xl border shadow-card',
          variantStyles[variant],
          sizes[size].padding,
          className
        )}
        {...props}
      >
        <div className="flex items-start justify-between mb-2">
          <p className={cn('font-medium text-foreground-muted uppercase tracking-wide', sizes[size].title)}>
            {title}
          </p>
          {icon && <div className="text-foreground-muted">{icon}</div>}
        </div>

        <div className="flex items-baseline gap-2">
          <span className={cn('font-bold text-foreground tracking-tight', sizes[size].value)}>
            {typeof value === 'number' ? value.toLocaleString() : value}
          </span>
          {unit && (
            <span className="text-sm text-foreground-muted">{unit}</span>
          )}
        </div>

        {change !== undefined && (
          <div className={cn('flex items-center gap-1 mt-2', getTrendColor())}>
            {getTrendIcon()}
            <span className="text-sm font-medium">
              {change > 0 ? '+' : ''}
              {change.toFixed(1)}%
            </span>
            {changeLabel && (
              <span className="text-xs text-foreground-muted ml-1">
                {changeLabel}
              </span>
            )}
          </div>
        )}
      </div>
    );
  }
);

KPICard.displayName = 'KPICard';

// Scope KPI - Specialized for scope totals
export interface ScopeKPIProps extends HTMLAttributes<HTMLDivElement> {
  scope: 1 | 2 | 3;
  value: number;
  percentage?: number;
  activityCount?: number;
}

const scopeLabels = {
  1: 'Scope 1 - Direct',
  2: 'Scope 2 - Energy',
  3: 'Scope 3 - Value Chain',
};

const scopeDescriptions = {
  1: 'Direct emissions from owned or controlled sources',
  2: 'Indirect emissions from purchased energy',
  3: 'All other indirect emissions in value chain',
};

export const ScopeKPI = forwardRef<HTMLDivElement, ScopeKPIProps>(
  ({ className, scope, value, percentage, activityCount, ...props }, ref) => {
    const scopeColors = {
      1: 'border-l-scope1',
      2: 'border-l-scope2',
      3: 'border-l-scope3',
    };

    const scopeBg = {
      1: 'bg-[var(--color-scope1-light)]',
      2: 'bg-[var(--color-scope2-light)]',
      3: 'bg-[var(--color-scope3-light)]',
    };

    const formatValue = (v: number) => {
      if (v >= 1000000) return `${(v / 1000000).toFixed(1)} kt`;
      if (v >= 1000) return `${(v / 1000).toFixed(1)} t`;
      return `${v.toFixed(0)} kg`;
    };

    return (
      <div
        ref={ref}
        className={cn(
          'bg-background-elevated rounded-xl border-l-4 p-6 shadow-card',
          scopeColors[scope],
          className
        )}
        {...props}
      >
        <div className="flex items-start justify-between mb-1">
          <p className="text-sm font-medium text-foreground-muted">
            {scopeLabels[scope]}
          </p>
          {percentage !== undefined && (
            <span className={cn('px-2 py-0.5 rounded-full text-xs font-semibold', scopeBg[scope])}>
              {percentage.toFixed(0)}%
            </span>
          )}
        </div>

        <p className="text-3xl font-bold text-foreground tracking-tight">
          {formatValue(value)}
        </p>
        <p className="text-xs text-foreground-muted mt-0.5">CO2e</p>

        {activityCount !== undefined && (
          <p className="text-xs text-foreground-muted mt-3">
            {activityCount} {activityCount === 1 ? 'activity' : 'activities'}
          </p>
        )}
      </div>
    );
  }
);

ScopeKPI.displayName = 'ScopeKPI';
