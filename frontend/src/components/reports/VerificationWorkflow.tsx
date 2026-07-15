'use client';

import { useState } from 'react';
import {
  Surface,
  PanelLabel,
  StepRow,
  StepDoneText,
  StepLockedText,
} from '@/components/canopy';
import { Button, Badge, PeriodStatusBadge, Input, Textarea, Select } from '@/components/ui';
import { formatDate } from '@/lib/utils';
import { Loader2, X } from 'lucide-react';
import type { ReportingPeriod, StatusHistory, PeriodStatus, AssuranceLevel } from '@/lib/api';

interface VerificationWorkflowProps {
  period: ReportingPeriod;
  statusHistory?: StatusHistory;
  userRole?: 'admin' | 'editor' | 'viewer';
  onTransition: (newStatus: PeriodStatus) => Promise<void>;
  onVerify: (data: { assurance_level: AssuranceLevel; verified_by: string; verification_statement: string }) => Promise<void>;
  onLock: () => Promise<void>;
}

const statusSteps: PeriodStatus[] = ['draft', 'review', 'submitted', 'audit', 'verified', 'locked'];

const stepCopy: Record<PeriodStatus, { title: string; description: string }> = {
  draft: {
    title: 'Draft',
    description: 'Everything is editable — submit when your numbers look right.',
  },
  review: {
    title: 'Internal review',
    description: 'A teammate double-checks the inventory before it leaves the building.',
  },
  submitted: {
    title: 'Submitted for verification',
    description: 'Handed to your verifier — ISO 14064-3 ready.',
  },
  audit: {
    title: 'Under audit',
    description: 'Your verifier is working through the evidence.',
  },
  verified: {
    title: 'Verified',
    description: 'The inventory carries an assurance statement.',
  },
  locked: {
    title: 'Locked',
    description: 'Frozen for the record — no further changes.',
  },
};

export function VerificationWorkflow({
  period,
  statusHistory,
  userRole = 'editor',
  onTransition,
  onVerify,
  onLock,
}: VerificationWorkflowProps) {
  const [loading, setLoading] = useState(false);
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [verifyForm, setVerifyForm] = useState({
    assurance_level: 'limited' as AssuranceLevel,
    verified_by: '',
    verification_statement: '',
  });

  const isAdmin = userRole === 'admin';
  const validTransitions = statusHistory?.valid_transitions || [];

  const handleTransition = async (newStatus: PeriodStatus) => {
    setLoading(true);
    try {
      await onTransition(newStatus);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!verifyForm.verified_by || !verifyForm.verification_statement) {
      return;
    }
    setLoading(true);
    try {
      await onVerify(verifyForm);
      setShowVerifyModal(false);
    } finally {
      setLoading(false);
    }
  };

  const handleLock = async () => {
    setLoading(true);
    try {
      await onLock();
    } finally {
      setLoading(false);
    }
  };

  const currentStepIndex = statusSteps.indexOf(period.status);

  /** The one action that belongs to a step row, if any. */
  const actionFor = (status: PeriodStatus): React.ReactNode => {
    if (status !== period.status || period.is_locked) return undefined;

    switch (status) {
      case 'draft':
        return validTransitions.includes('review') ? (
          <Button size="sm" onClick={() => handleTransition('review')} disabled={loading}>
            {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Submit for review
          </Button>
        ) : undefined;
      case 'review':
        return validTransitions.includes('submitted') ? (
          <Button size="sm" onClick={() => handleTransition('submitted')} disabled={loading}>
            {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Submit
          </Button>
        ) : undefined;
      case 'submitted':
        return isAdmin && validTransitions.includes('audit') ? (
          <Button size="sm" onClick={() => handleTransition('audit')} disabled={loading}>
            {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Start audit
          </Button>
        ) : undefined;
      case 'audit':
        return isAdmin && validTransitions.includes('verified') ? (
          <Button size="sm" onClick={() => setShowVerifyModal(true)} disabled={loading}>
            Mark verified
          </Button>
        ) : undefined;
      case 'verified':
        return isAdmin && !period.is_locked ? (
          <Button variant="secondary" size="sm" onClick={handleLock} disabled={loading}>
            {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Lock period
          </Button>
        ) : undefined;
      default:
        return undefined;
    }
  };

  return (
    <div className="space-y-4">
      {/* The path to a verified inventory */}
      <Surface padding="tight">
        <div className="flex flex-wrap items-center gap-2 px-3.5 pb-1 pt-2">
          <PeriodStatusBadge status={period.status} />
          {period.assurance_level && (
            <Badge variant="secondary" size="sm" className="capitalize">
              {period.assurance_level} assurance
            </Badge>
          )}
        </div>
        {statusSteps.map((status, index) => {
          const isComplete = index < currentStepIndex || (period.is_locked && status === 'locked');
          const isCurrent = index === currentStepIndex && !isComplete;
          const state = isComplete ? 'done' : isCurrent ? 'now' : 'locked';
          const action =
            actionFor(status) ??
            (isComplete ? (
              <StepDoneText />
            ) : isCurrent ? undefined : (
              <StepLockedText>Later</StepLockedText>
            ));

          const copy = stepCopy[status];
          const description =
            status === 'verified' && period.verified_by ? (
              <>
                Verified by {period.verified_by}
                {period.verified_at && ` on ${formatDate(period.verified_at)}`}
                {period.verification_statement && (
                  <span className="mt-1 block italic">
                    &quot;{period.verification_statement}&quot;
                  </span>
                )}
              </>
            ) : (
              copy.description
            );

          return (
            <StepRow
              key={status}
              num={index + 1}
              title={copy.title}
              description={description}
              state={state}
              action={action}
            >
              {/* quiet secondary action: only on review, back to draft */}
              {status === 'review' && isCurrent && validTransitions.includes('draft') && (
                <button
                  type="button"
                  onClick={() => handleTransition('draft')}
                  disabled={loading}
                  className="mt-1.5 cursor-pointer text-[12px] font-semibold text-cy-muted hover:text-cy-ink disabled:opacity-50"
                >
                  ← Return to draft for edits
                </button>
              )}
            </StepRow>
          );
        })}
      </Surface>

      {/* History */}
      {statusHistory && (
        <Surface>
          <PanelLabel>History</PanelLabel>
          <div className="space-y-2.5">
            {statusHistory.timeline.created_at && (
              <p className="flex items-baseline gap-2.5 text-[12.5px] text-cy-muted">
                <span className="relative top-px h-2 w-2 shrink-0 rounded-full bg-cy-faint" aria-hidden="true" />
                Period created · {formatDate(statusHistory.timeline.created_at)}
              </p>
            )}
            {statusHistory.timeline.submitted_at && (
              <p className="flex items-baseline gap-2.5 text-[12.5px] text-cy-muted">
                <span className="relative top-px h-2 w-2 shrink-0 rounded-full bg-cy-warn" aria-hidden="true" />
                Submitted · {formatDate(statusHistory.timeline.submitted_at)}
              </p>
            )}
            {statusHistory.timeline.verified_at && (
              <p className="flex items-baseline gap-2.5 text-[12.5px] text-cy-muted">
                <span className="relative top-px h-2 w-2 shrink-0 rounded-full bg-cy-accent" aria-hidden="true" />
                Verified · {formatDate(statusHistory.timeline.verified_at)}
                {statusHistory.timeline.verified_by && ` by ${statusHistory.timeline.verified_by}`}
                {statusHistory.verification.assurance_level && (
                  <Badge variant="secondary" size="sm" className="capitalize">
                    {statusHistory.verification.assurance_level}
                  </Badge>
                )}
              </p>
            )}
          </div>
        </Surface>
      )}

      {/* Verification modal */}
      {showVerifyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-cy bg-background-elevated p-6 shadow-xl">
            <div className="mb-4 flex items-start justify-between">
              <div>
                <p className="mb-1.5 text-[11px] font-bold uppercase tracking-[0.08em] text-cy-accent">
                  Verification
                </p>
                <h3 className="text-[16px] font-bold tracking-[-0.01em] text-foreground">
                  Mark this period as verified
                </h3>
              </div>
              <button
                onClick={() => setShowVerifyModal(false)}
                className="rounded-md p-1.5 text-cy-muted hover:bg-cy-row hover:text-foreground"
                aria-label="Close"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="space-y-4">
              <Select
                label="Assurance level"
                value={verifyForm.assurance_level}
                onChange={(e) =>
                  setVerifyForm({ ...verifyForm, assurance_level: e.target.value as AssuranceLevel })
                }
                options={[
                  { value: 'limited', label: 'Limited assurance' },
                  { value: 'reasonable', label: 'Reasonable assurance' },
                ]}
              />
              <Input
                label="Verified by"
                placeholder="Name of verifier or verification body"
                value={verifyForm.verified_by}
                onChange={(e) => setVerifyForm({ ...verifyForm, verified_by: e.target.value })}
              />
              <Textarea
                label="Verification statement"
                placeholder="Enter verification statement or notes…"
                value={verifyForm.verification_statement}
                onChange={(e) =>
                  setVerifyForm({ ...verifyForm, verification_statement: e.target.value })
                }
                rows={4}
              />
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setShowVerifyModal(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleVerify}
                disabled={loading || !verifyForm.verified_by || !verifyForm.verification_statement}
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                Confirm verification
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
