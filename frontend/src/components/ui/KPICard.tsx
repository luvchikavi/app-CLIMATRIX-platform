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
    // Canopy: quiet stat cell on a surface — a scope dot, never a border stripe;
    // numbers cap at 16px (design contract §0.2).
    const variantDots: Record<string, string | null> = {
      default: null,
      scope1: 'bg-cy-scope1',
      scope2: 'bg-cy-scope2',
      scope3: 'bg-cy-scope3',
    };

    const sizes = {
      sm: { padding: 'p-4', value: 'text-[15px]', title: 'text-[10.5px]' },
      md: { padding: 'px-6 py-5', value: 'text-[16px]', title: 'text-[11px]' },
      lg: { padding: 'px-6 py-5', value: 'text-[16px]', title: 'text-[11px]' },
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
          'bg-background-elevated rounded-cy shadow-card',
          sizes[size].padding,
          className
        )}
        {...props}
      >
        <div className="flex items-start justify-between mb-1.5">
          <p className={cn('flex items-center gap-1.5 font-bold text-cy-faint uppercase tracking-[0.08em]', sizes[size].title)}>
            {variantDots[variant] && (
              <span
                aria-hidden="true"
                className={cn('inline-block h-[7px] w-[7px] rounded-full', variantDots[variant])}
              />
            )}
            {title}
          </p>
          {icon && <div className="text-cy-faint">{icon}</div>}
        </div>

        <div className="flex items-baseline gap-1.5">
          <span className={cn('font-[650] tabular-nums text-foreground', sizes[size].value)}>
            {typeof value === 'number' ? value.toLocaleString() : value}
          </span>
          {unit && (
            <span className="text-[11.5px] text-cy-muted">{unit}</span>
          )}
        </div>

        {change !== undefined && (
          <div className={cn('flex items-center gap-1 mt-1.5 text-[12px]', getTrendColor())}>
            {getTrendIcon()}
            <span className="font-semibold tabular-nums">
              {change > 0 ? '+' : ''}
              {change.toFixed(1)}%
            </span>
            {changeLabel && (
              <span className="text-[11.5px] text-cy-muted ml-1">
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
  onClick?: () => void;
  label?: string;
  subtitle?: string;
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
  ({ className, scope, value, percentage, activityCount, onClick, label, subtitle, ...props }, ref) => {
    const scopeDots = {
      1: 'bg-cy-scope1',
      2: 'bg-cy-scope2',
      3: 'bg-cy-scope3',
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

    const isClickable = !!onClick;

    return (
      <div
        ref={ref}
        className={cn(
          'bg-background-elevated rounded-cy px-6 py-5 shadow-card',
          isClickable && 'cursor-pointer hover:bg-cy-row/40 transition-colors',
          className
        )}
        onClick={onClick}
        role={isClickable ? 'button' : undefined}
        tabIndex={isClickable ? 0 : undefined}
        onKeyDown={isClickable ? (e) => e.key === 'Enter' && onClick() : undefined}
        {...props}
      >
        <div className="flex items-start justify-between mb-1">
          <p className="flex items-center gap-1.5 text-[11.5px] text-cy-muted">
            <span
              aria-hidden="true"
              className={cn('inline-block h-[7px] w-[7px] rounded-full', scopeDots[scope])}
            />
            {label || scopeLabels[scope]}
          </p>
          {percentage !== undefined && (
            <span className={cn('px-2 py-0.5 rounded-full text-[11px] font-semibold', scopeBg[scope])}>
              {percentage.toFixed(0)}%
            </span>
          )}
        </div>

        <p className="text-[16px] font-[650] tabular-nums text-foreground">
          {formatValue(value)}
          <small className="ml-1 text-[11.5px] font-medium text-cy-muted">CO₂e</small>
        </p>

        {activityCount !== undefined && (
          <p className="text-[11.5px] text-cy-muted mt-2">
            {activityCount} {activityCount === 1 ? 'activity' : 'activities'}
          </p>
        )}

        {isClickable && activityCount && activityCount > 0 && (
          <p className="text-[12px] text-cy-accent mt-1.5 font-semibold">
            Breakdown →
          </p>
        )}
      </div>
    );
  }
);

ScopeKPI.displayName = 'ScopeKPI';
