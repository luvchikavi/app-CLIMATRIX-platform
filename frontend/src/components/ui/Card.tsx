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

    // Canopy: every card is a Surface — radius 16, soft shadow, never a border.
    const variants = {
      default: 'bg-background-elevated shadow-card',
      bordered: 'bg-background-elevated shadow-card',
      elevated: 'bg-background-elevated shadow-card',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'rounded-cy',
          variants[variant],
          paddings[padding],
          interactive && 'cursor-pointer hover:bg-cy-row/40 transition-colors',
          className
        )}
        {...props}
      />
    );
  }
);

Card.displayName = 'Card';

// Card Header
export type CardHeaderProps = HTMLAttributes<HTMLDivElement>;

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center justify-between pb-3.5', className)}
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
      className={cn('text-[11px] font-bold tracking-[0.08em] uppercase text-cy-faint', className)}
      {...props}
    />
  )
);

CardTitle.displayName = 'CardTitle';

// Card Description
export type CardDescriptionProps = HTMLAttributes<HTMLParagraphElement>;

export const CardDescription = forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-[12.5px] text-foreground-muted', className)}
      {...props}
    />
  )
);

CardDescription.displayName = 'CardDescription';

// Card Content
export type CardContentProps = HTMLAttributes<HTMLDivElement>;

export const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('pt-0', className)} {...props} />
  )
);

CardContent.displayName = 'CardContent';

// Card Footer
export type CardFooterProps = HTMLAttributes<HTMLDivElement>;

export const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center justify-end gap-3 pt-4', className)}
      {...props}
    />
  )
);

CardFooter.displayName = 'CardFooter';
