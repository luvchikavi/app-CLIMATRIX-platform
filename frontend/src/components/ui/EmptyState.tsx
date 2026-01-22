import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { FileX, Inbox, Search, AlertCircle, Plus } from 'lucide-react';
import { Button } from './Button';

export interface EmptyStateProps extends HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
  };
  variant?: 'default' | 'search' | 'error' | 'minimal';
}

export const EmptyState = forwardRef<HTMLDivElement, EmptyStateProps>(
  (
    {
      className,
      icon,
      title,
      description,
      action,
      variant = 'default',
      ...props
    },
    ref
  ) => {
    const defaultIcons = {
      default: <Inbox className="w-12 h-12" />,
      search: <Search className="w-12 h-12" />,
      error: <AlertCircle className="w-12 h-12" />,
      minimal: <FileX className="w-10 h-10" />,
    };

    const sizes = {
      default: 'py-16',
      search: 'py-12',
      error: 'py-12',
      minimal: 'py-8',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'flex flex-col items-center justify-center text-center',
          sizes[variant],
          className
        )}
        {...props}
      >
        <div className="mb-4 text-foreground-muted">
          {icon || defaultIcons[variant]}
        </div>

        <h3 className={cn(
          'font-semibold text-foreground',
          variant === 'minimal' ? 'text-base' : 'text-lg'
        )}>
          {title}
        </h3>

        {description && (
          <p className="mt-1 text-sm text-foreground-muted max-w-sm">
            {description}
          </p>
        )}

        {action && (
          <Button
            onClick={action.onClick}
            variant="primary"
            className="mt-4"
            leftIcon={action.icon || <Plus className="w-4 h-4" />}
          >
            {action.label}
          </Button>
        )}
      </div>
    );
  }
);

EmptyState.displayName = 'EmptyState';

// Pre-configured empty states for common use cases
export function NoActivitiesEmpty({ onAdd }: { onAdd: () => void }) {
  return (
    <EmptyState
      title="No activities yet"
      description="Start tracking your emissions by adding your first activity or importing data from a file."
      action={{
        label: 'Add Activity',
        onClick: onAdd,
      }}
    />
  );
}

export function NoSearchResultsEmpty({ query }: { query: string }) {
  return (
    <EmptyState
      variant="search"
      title="No results found"
      description={`We couldn't find any activities matching "${query}". Try adjusting your search or filters.`}
    />
  );
}

export function ErrorEmpty({ onRetry }: { onRetry: () => void }) {
  return (
    <EmptyState
      variant="error"
      title="Something went wrong"
      description="We couldn't load the data. Please try again."
      action={{
        label: 'Try Again',
        onClick: onRetry,
        icon: undefined,
      }}
    />
  );
}
