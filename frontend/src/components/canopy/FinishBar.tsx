import { ReactNode } from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Surface } from './Surface';

/**
 * Every page's last element: status pill + one-line summary + primary link +
 * export pills. The finish line the Guide voice promises (§0.2).
 */
export interface FinishBarProps {
  status: { label: string; tone?: 'warn' | 'done' };
  summary: ReactNode;
  action?: { label: string; href: string };
  exports?: { label: string; href?: string; onClick?: () => void }[];
  className?: string;
}

const exportPill =
  'inline-block cursor-pointer rounded-full bg-cy-accent-soft px-3 py-1.5 text-[12px] font-semibold leading-none text-cy-accent';

export function FinishBar({ status, summary, action, exports, className }: FinishBarProps) {
  return (
    <Surface
      padding="none"
      className={cn(
        'flex flex-wrap items-center gap-x-[18px] gap-y-2.5 px-6 py-4 text-[12.5px] text-cy-muted',
        className
      )}
    >
      <span
        className={cn(
          'rounded-full px-2.5 py-1 text-[11px] font-bold',
          status.tone === 'done' ? 'bg-cy-accent-soft text-cy-accent' : 'bg-cy-warn-soft text-cy-warn'
        )}
      >
        {status.label}
      </span>
      <span>{summary}</span>
      {action && (
        <Link href={action.href} className="font-semibold text-cy-accent">
          {action.label} →
        </Link>
      )}
      {exports && exports.length > 0 && (
        <span className="ml-auto flex gap-2">
          {exports.map((item) =>
            item.href ? (
              <Link key={item.label} href={item.href} className={exportPill}>
                {item.label}
              </Link>
            ) : (
              <button key={item.label} type="button" onClick={item.onClick} className={exportPill}>
                {item.label}
              </button>
            )
          )}
        </span>
      )}
    </Surface>
  );
}
