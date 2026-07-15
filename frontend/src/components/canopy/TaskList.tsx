import { ReactNode } from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

/**
 * "What needs you" rows: amber-open / green-done dot + text + inline action.
 */
export interface TaskItem {
  state: 'open' | 'done';
  text: ReactNode;
  hint?: string;
  action?: { label: string; href: string };
}

export function TaskList({ items, className }: { items: TaskItem[]; className?: string }) {
  return (
    <div className={className}>
      {items.map((item, index) => (
        <div key={index} className="flex items-baseline gap-2.5 py-[9px] text-[13px]">
          <span
            aria-hidden="true"
            className={cn(
              'relative top-px h-2 w-2 flex-none rounded-full',
              item.state === 'done' ? 'bg-cy-accent' : 'border-[1.5px] border-cy-warn'
            )}
          />
          <p className="text-cy-ink">
            {item.text}
            {item.hint && <span className="text-[12px] text-cy-muted"> — {item.hint}</span>}
            {item.action && (
              <>
                {' '}
                <Link href={item.action.href} className="font-semibold text-cy-accent">
                  {item.action.label}
                </Link>
              </>
            )}
          </p>
        </div>
      ))}
    </div>
  );
}
