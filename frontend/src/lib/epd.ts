/** Shared EPD module constants — the ISO 14025 workflow + EN 15804 vocabulary. */

import type { EpdStatus } from '@/lib/api';

/** Workflow steps in order (expired is a lapse, not a step). */
export const EPD_STATUS_ORDER: EpdStatus[] = [
  'draft',
  'internal_review',
  'verification',
  'registered',
  'published',
];

export const EPD_STATUS_META: Record<
  EpdStatus,
  { label: string; className: string; hint: string }
> = {
  draft: {
    label: 'Draft',
    className: 'bg-cy-warn-soft text-cy-warn',
    hint: 'Model the product, pin a finalized footprint, close the checklist.',
  },
  internal_review: {
    label: 'Internal review',
    className: 'bg-cy-row text-cy-ink',
    hint: 'Results are frozen — review the declaration before verification.',
  },
  verification: {
    label: 'Verification',
    className: 'bg-cy-accent-soft text-cy-accent',
    hint: 'Third-party verifier reviews through the read-only portal.',
  },
  registered: {
    label: 'Registered',
    className: 'bg-cy-accent-soft text-cy-accent',
    hint: 'Registered with the program operator — awaiting publication.',
  },
  published: {
    label: 'Published',
    className: 'bg-cy-accent text-white',
    hint: 'Live declaration — valid 5 years from publication.',
  },
  expired: {
    label: 'Expired',
    className: 'bg-error/10 text-error',
    hint: 'Past its 5-year validity — prepare a renewal.',
  },
};

/** Human labels for the transition buttons. */
export const TRANSITION_LABEL: Record<string, string> = {
  draft: 'Reopen as draft',
  internal_review: 'Send to internal review',
  verification: 'Send to verification',
  registered: 'Mark registered',
  published: 'Mark published',
  expired: 'Mark expired',
};

export const PROGRAM_OPERATORS = [
  'EPD International (Environdec)',
  'IBU — Institut Bauen und Umwelt',
  'EPD Norge',
  'UL Environment',
  'SII — Standards Institution of Israel',
];
