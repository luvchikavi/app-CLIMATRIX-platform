import { HTMLAttributes, TdHTMLAttributes, ThHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

// Table Root
export type TableProps = HTMLAttributes<HTMLTableElement>;

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
export type TableHeaderProps = HTMLAttributes<HTMLTableSectionElement>;

export const TableHeader = forwardRef<HTMLTableSectionElement, TableHeaderProps>(
  ({ className, ...props }, ref) => (
    <thead ref={ref} className={className} {...props} />
  )
);

TableHeader.displayName = 'TableHeader';

// Table Body
export type TableBodyProps = HTMLAttributes<HTMLTableSectionElement>;

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
export type TableFooterProps = HTMLAttributes<HTMLTableSectionElement>;

export const TableFooter = forwardRef<HTMLTableSectionElement, TableFooterProps>(
  ({ className, ...props }, ref) => (
    <tfoot
      ref={ref}
      className={cn(
        'border-t border-cy-row font-semibold',
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
        'border-b border-cy-row transition-colors',
        'hover:bg-cy-row/40',
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
        'px-4 pb-2.5 pt-1 text-left align-middle text-[10.5px] font-bold uppercase tracking-[0.07em] text-cy-faint',
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
export type TableCellProps = TdHTMLAttributes<HTMLTableCellElement>;

export const TableCell = forwardRef<HTMLTableCellElement, TableCellProps>(
  ({ className, ...props }, ref) => (
    <td
      ref={ref}
      className={cn(
        'px-4 py-[9px] align-middle text-[13px] [&:has([role=checkbox])]:pr-0',
        className
      )}
      {...props}
    />
  )
);

TableCell.displayName = 'TableCell';

// Table Caption
export type TableCaptionProps = HTMLAttributes<HTMLTableCaptionElement>;

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
          <h3 className="text-[14px] font-bold text-foreground mb-1">{title}</h3>
          {description && (
            <p className="text-[12.5px] text-foreground-muted mb-4 max-w-sm">{description}</p>
          )}
          {action}
        </div>
      </td>
    </tr>
  )
);

TableEmpty.displayName = 'TableEmpty';
