import { forwardRef, HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'bordered' | 'elevated';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  interactive?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', padding = 'md', interactive = false, ...props }, ref) => {
    const paddings = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    };

    const variants = {
      default: 'bg-background-elevated border border-border-muted shadow-card',
      bordered: 'bg-background-elevated border border-border',
      elevated: 'bg-background-elevated shadow-lg',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'rounded-xl',
          variants[variant],
          paddings[padding],
          interactive && 'cursor-pointer hover:shadow-card-hover hover:border-primary/20 transition-all',
          className
        )}
        {...props}
      />
    );
  }
);

Card.displayName = 'Card';

// Card Header
export interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {}

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center justify-between pb-4 border-b border-border-muted', className)}
      {...props}
    />
  )
);

CardHeader.displayName = 'CardHeader';

// Card Title
export interface CardTitleProps extends HTMLAttributes<HTMLHeadingElement> {
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}

export const CardTitle = forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className, as: Tag = 'h3', ...props }, ref) => (
    <Tag
      ref={ref as React.Ref<HTMLHeadingElement>}
      className={cn('text-lg font-semibold text-foreground', className)}
      {...props}
    />
  )
);

CardTitle.displayName = 'CardTitle';

// Card Description
export interface CardDescriptionProps extends HTMLAttributes<HTMLParagraphElement> {}

export const CardDescription = forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-foreground-muted', className)}
      {...props}
    />
  )
);

CardDescription.displayName = 'CardDescription';

// Card Content
export interface CardContentProps extends HTMLAttributes<HTMLDivElement> {}

export const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('pt-4', className)} {...props} />
  )
);

CardContent.displayName = 'CardContent';

// Card Footer
export interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {}

export const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center justify-end gap-3 pt-4 border-t border-border-muted', className)}
      {...props}
    />
  )
);

CardFooter.displayName = 'CardFooter';
