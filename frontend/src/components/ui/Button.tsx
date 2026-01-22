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
    const baseStyles = cn(
      'inline-flex items-center justify-center gap-2 font-medium rounded-lg',
      'transition-all duration-150 ease-in-out',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
      'disabled:opacity-50 disabled:cursor-not-allowed'
    );

    const variants = {
      primary: cn(
        'bg-primary text-white',
        'hover:bg-primary-hover',
        'active:bg-[var(--color-primary-700)]',
        'focus-visible:ring-primary'
      ),
      secondary: cn(
        'bg-secondary text-white',
        'hover:bg-secondary-hover',
        'active:bg-[var(--color-secondary-700)]',
        'focus-visible:ring-secondary'
      ),
      outline: cn(
        'border border-primary text-primary bg-transparent',
        'hover:bg-primary-light',
        'active:bg-[var(--color-primary-100)]',
        'focus-visible:ring-primary'
      ),
      ghost: cn(
        'text-foreground bg-transparent',
        'hover:bg-background-muted',
        'active:bg-[var(--color-neutral-200)]',
        'focus-visible:ring-foreground-muted'
      ),
      danger: cn(
        'bg-error text-white',
        'hover:bg-[var(--color-error-600)]',
        'active:bg-[var(--color-error-700)]',
        'focus-visible:ring-error'
      ),
    };

    const sizes = {
      sm: 'px-3 py-1.5 text-xs',
      md: 'px-4 py-2 text-sm',
      lg: 'px-6 py-3 text-base',
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
