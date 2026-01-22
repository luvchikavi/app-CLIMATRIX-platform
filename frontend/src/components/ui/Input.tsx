import { forwardRef, InputHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, leftIcon, rightIcon, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-foreground mb-1.5"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-muted">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              'w-full px-3 py-2 rounded-lg border bg-background-elevated',
              'text-sm text-foreground placeholder:text-foreground-muted',
              'transition-colors duration-150',
              'focus:outline-none focus:ring-2 focus:ring-offset-0',
              'disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-background-muted',
              error
                ? 'border-error focus:border-error focus:ring-error/20'
                : 'border-border hover:border-neutral-300 focus:border-primary focus:ring-primary/20',
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              className
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-foreground-muted">
              {rightIcon}
            </div>
          )}
        </div>
        {(error || hint) && (
          <p
            className={cn(
              'mt-1.5 text-xs',
              error ? 'text-error' : 'text-foreground-muted'
            )}
          >
            {error || hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

// Textarea Component
export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, hint, id, ...props }, ref) => {
    const textareaId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={textareaId}
            className="block text-sm font-medium text-foreground mb-1.5"
          >
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          className={cn(
            'w-full px-3 py-2 rounded-lg border bg-background-elevated',
            'text-sm text-foreground placeholder:text-foreground-muted',
            'transition-colors duration-150 resize-y min-h-[100px]',
            'focus:outline-none focus:ring-2 focus:ring-offset-0',
            'disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-background-muted',
            error
              ? 'border-error focus:border-error focus:ring-error/20'
              : 'border-border hover:border-neutral-300 focus:border-primary focus:ring-primary/20',
            className
          )}
          {...props}
        />
        {(error || hint) && (
          <p
            className={cn(
              'mt-1.5 text-xs',
              error ? 'text-error' : 'text-foreground-muted'
            )}
          >
            {error || hint}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
