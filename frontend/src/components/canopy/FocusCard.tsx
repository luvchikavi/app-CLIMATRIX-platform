import { Surface } from './Surface';
import { CanopyButton } from './Button';

/**
 * The one call-to-action a page opens with (design contract §0.1: one focus
 * per page). Progress ring + kicker + title + body + ONE button + skip link.
 * Phase 3's next-best-action selector decides what it says.
 */
export interface FocusCardProps {
  kicker: string;
  title: string;
  body: string;
  action: { label: string; href?: string; onClick?: () => void };
  skip?: { label: string; href?: string; onClick?: () => void };
  /** e.g. { fraction: 1 / 3, label: '1/3' } */
  progress?: { fraction: number; label: string };
  className?: string;
}

const RADIUS = 33;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function ProgressRing({ fraction, label }: { fraction: number; label: string }) {
  const clamped = Math.max(0, Math.min(1, fraction));
  return (
    <span className="relative block h-[78px] w-[78px] flex-none" aria-hidden="true">
      <svg width="78" height="78" viewBox="0 0 78 78" fill="none" className="-rotate-90">
        <circle cx="39" cy="39" r={RADIUS} strokeWidth="6.5" className="stroke-cy-row" />
        <circle
          cx="39"
          cy="39"
          r={RADIUS}
          strokeWidth="6.5"
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={CIRCUMFERENCE * (1 - clamped)}
          className="stroke-cy-accent motion-safe:transition-[stroke-dashoffset] motion-safe:duration-700"
        />
      </svg>
      <b className="absolute inset-0 flex items-center justify-center text-[12.5px] font-bold text-cy-accent">
        {label}
      </b>
    </span>
  );
}

export function FocusCard({
  kicker,
  title,
  body,
  action,
  skip,
  progress,
  className,
}: FocusCardProps) {
  return (
    <Surface
      padding="none"
      className={`mb-4 flex flex-col items-start gap-5 px-7 py-6 sm:flex-row sm:items-center sm:gap-[26px] ${className ?? ''}`}
    >
      {progress && <ProgressRing fraction={progress.fraction} label={progress.label} />}
      <div>
        <p className="mb-[5px] text-[11px] font-bold tracking-[0.08em] uppercase text-cy-accent">
          {kicker}
        </p>
        <h4 className="mb-[5px] text-[17px] font-[650] tracking-[-0.01em] text-cy-ink">{title}</h4>
        <p className="mb-3.5 max-w-[46ch] text-[13px] text-cy-muted">{body}</p>
        <CanopyButton href={action.href} onClick={action.onClick}>
          {action.label}
        </CanopyButton>
        {skip && (
          <CanopyButton variant="quiet" href={skip.href} onClick={skip.onClick} className="ml-[13px]">
            {skip.label}
          </CanopyButton>
        )}
      </div>
    </Surface>
  );
}
