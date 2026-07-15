import { forwardRef, ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    // Canopy skin: accent fill / soft pill / quiet — no borders anywhere.
    const baseStyles = cn(
      'inline-flex items-center justify-center gap-2 font-semibold rounded-[10px]',
      'transition-colors duration-150 ease-in-out',
      'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cy-accent',
      'disabled:opacity-50 disabled:cursor-not-allowed'
    );

    const variants = {
      primary: cn(
        'bg-cy-accent text-white',
        'hover:bg-[color-mix(in_srgb,var(--cy-accent)_88%,#000)]'
      ),
      secondary: cn(
        'bg-cy-accent-soft text-cy-accent',
        'hover:bg-cy-row'
      ),
      outline: cn(
        'bg-cy-accent-soft text-cy-accent',
        'hover:bg-cy-row'
      ),
      ghost: cn(
        'text-cy-muted bg-transparent',
        'hover:bg-cy-row hover:text-cy-ink'
      ),
      danger: cn(
        'bg-error text-white',
        'hover:bg-[var(--color-error-600)]',
        'focus-visible:outline-error'
      ),
    };

    const sizes = {
      sm: 'px-3 py-1.5 text-xs',
      md: 'px-[18px] py-2.5 text-[13px] leading-none',
      lg: 'px-6 py-3 text-[14px] leading-none',
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          leftIcon
        )}
        {children}
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = 'Button';
