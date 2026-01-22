import { HTMLAttributes, TdHTMLAttributes, ThHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

// Table Root
export interface TableProps extends HTMLAttributes<HTMLTableElement> {}

export const Table = forwardRef<HTMLTableElement, TableProps>(
  ({ className, ...props }, ref) => (
    <div className="w-full overflow-auto">
      <table
        ref={ref}
        className={cn('w-full caption-bottom text-sm', className)}
        {...props}
      />
    </div>
  )
);

Table.displayName = 'Table';

// Table Header
export interface TableHeaderProps extends HTMLAttributes<HTMLTableSectionElement> {}

export const TableHeader = forwardRef<HTMLTableSectionElement, TableHeaderProps>(
  ({ className, ...props }, ref) => (
    <thead ref={ref} className={cn('bg-background-muted', className)} {...props} />
  )
);

TableHeader.displayName = 'TableHeader';

// Table Body
export interface TableBodyProps extends HTMLAttributes<HTMLTableSectionElement> {}

export const TableBody = forwardRef<HTMLTableSectionElement, TableBodyProps>(
  ({ className, ...props }, ref) => (
    <tbody
      ref={ref}
      className={cn('[&_tr:last-child]:border-0', className)}
      {...props}
    />
  )
);

TableBody.displayName = 'TableBody';

// Table Footer
export interface TableFooterProps extends HTMLAttributes<HTMLTableSectionElement> {}

export const TableFooter = forwardRef<HTMLTableSectionElement, TableFooterProps>(
  ({ className, ...props }, ref) => (
    <tfoot
      ref={ref}
      className={cn(
        'border-t border-border bg-background-muted font-medium',
        className
      )}
      {...props}
    />
  )
);

TableFooter.displayName = 'TableFooter';

// Table Row
export interface TableRowProps extends HTMLAttributes<HTMLTableRowElement> {
  clickable?: boolean;
}

export const TableRow = forwardRef<HTMLTableRowElement, TableRowProps>(
  ({ className, clickable, ...props }, ref) => (
    <tr
      ref={ref}
      className={cn(
        'border-b border-border-muted transition-colors',
        'hover:bg-background-muted/50',
        clickable && 'cursor-pointer',
        className
      )}
      {...props}
    />
  )
);

TableRow.displayName = 'TableRow';

// Table Head Cell
export interface TableHeadProps extends ThHTMLAttributes<HTMLTableCellElement> {
  sortable?: boolean;
  sorted?: 'asc' | 'desc' | false;
}

export const TableHead = forwardRef<HTMLTableCellElement, TableHeadProps>(
  ({ className, sortable, sorted, children, ...props }, ref) => (
    <th
      ref={ref}
      className={cn(
        'h-12 px-4 text-left align-middle font-semibold text-foreground-muted',
        '[&:has([role=checkbox])]:pr-0',
        sortable && 'cursor-pointer select-none hover:text-foreground',
        className
      )}
      {...props}
    >
      <div className="flex items-center gap-1">
        {children}
        {sortable && sorted && (
          <span className="text-xs">
            {sorted === 'asc' ? '↑' : '↓'}
          </span>
        )}
      </div>
    </th>
  )
);

TableHead.displayName = 'TableHead';

// Table Cell
export interface TableCellProps extends TdHTMLAttributes<HTMLTableCellElement> {}

export const TableCell = forwardRef<HTMLTableCellElement, TableCellProps>(
  ({ className, ...props }, ref) => (
    <td
      ref={ref}
      className={cn(
        'p-4 align-middle [&:has([role=checkbox])]:pr-0',
        className
      )}
      {...props}
    />
  )
);

TableCell.displayName = 'TableCell';

// Table Caption
export interface TableCaptionProps extends HTMLAttributes<HTMLTableCaptionElement> {}

export const TableCaption = forwardRef<HTMLTableCaptionElement, TableCaptionProps>(
  ({ className, ...props }, ref) => (
    <caption
      ref={ref}
      className={cn('mt-4 text-sm text-foreground-muted', className)}
      {...props}
    />
  )
);

TableCaption.displayName = 'TableCaption';

// Empty State for Tables
export interface TableEmptyProps extends HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  colSpan?: number;
}

export const TableEmpty = forwardRef<HTMLTableRowElement, TableEmptyProps>(
  ({ icon, title, description, action, colSpan = 1, ...props }, ref) => (
    <tr ref={ref}>
      <td colSpan={colSpan}>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          {icon && (
            <div className="mb-4 text-foreground-muted">{icon}</div>
          )}
          <h3 className="text-lg font-semibold text-foreground mb-1">{title}</h3>
          {description && (
            <p className="text-sm text-foreground-muted mb-4 max-w-sm">{description}</p>
          )}
          {action}
        </div>
      </td>
    </tr>
  )
);

TableEmpty.displayName = 'TableEmpty';
