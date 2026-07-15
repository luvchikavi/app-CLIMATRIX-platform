import { ButtonHTMLAttributes } from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

/**
 * Canopy button. One primary style (accent fill), a quiet text style for
 * skip links, and a pill style for export/secondary actions.
 * Renders a Link when href is given, a button otherwise.
 */
export interface CanopyButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'quiet' | 'pill';
  href?: string;
}

const variants = {
  primary:
    'inline-block rounded-[10px] bg-cy-accent px-[18px] py-2.5 text-[13px] font-semibold leading-none text-white',
  quiet: 'inline-block text-[12.5px] text-cy-muted hover:text-cy-ink',
  pill: 'inline-block rounded-full bg-cy-accent-soft px-3 py-1.5 text-[12px] font-semibold leading-none text-cy-accent',
};

export function CanopyButton({
  variant = 'primary',
  href,
  className,
  children,
  type,
  ...rest
}: CanopyButtonProps) {
  const cls = cn(
    'cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cy-accent',
    variants[variant],
    className
  );
  if (href) {
    return (
      <Link href={href} className={cls}>
        {children}
      </Link>
    );
  }
  return (
    <button type={type ?? 'button'} className={cls} {...rest}>
      {children}
    </button>
  );
}
