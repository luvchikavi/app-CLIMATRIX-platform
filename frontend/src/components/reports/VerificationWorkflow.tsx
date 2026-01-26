'use client';

import { useState } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  PeriodStatusBadge,
  Input,
  Textarea,
  Select,
} from '@/components/ui';
import { cn, formatDate } from '@/lib/utils';
import {
  Shield,
  Clock,
  CheckCircle,
  AlertCircle,
  Lock,
  Send,
  RotateCcw,
  FileSearch,
  Award,
  ChevronRight,
  Loader2,
  X,
} from 'lucide-react';
import type { ReportingPeriod, StatusHistory, PeriodStatus, AssuranceLevel } from '@/lib/api';

interface VerificationWorkflowProps {
  period: ReportingPeriod;
  statusHistory?: StatusHistory;
  userRole?: 'admin' | 'editor' | 'viewer';
  onTransition: (newStatus: PeriodStatus) => Promise<void>;
  onVerify: (data: { assurance_level: AssuranceLevel; verified_by: string; verification_statement: string }) => Promise<void>;
  onLock: () => Promise<void>;
}

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

  const getStatusIcon = (status: PeriodStatus) => {
    switch (status) {
      case 'draft':
        return <Clock className="w-5 h-5" />;
      case 'review':
        return <FileSearch className="w-5 h-5" />;
      case 'submitted':
        return <Send className="w-5 h-5" />;
      case 'audit':
        return <Shield className="w-5 h-5" />;
      case 'verified':
        return <Award className="w-5 h-5" />;
      case 'locked':
        return <Lock className="w-5 h-5" />;
      default:
        return <Clock className="w-5 h-5" />;
    }
  };

  const statusSteps: PeriodStatus[] = ['draft', 'review', 'submitted', 'audit', 'verified', 'locked'];
  const currentStepIndex = statusSteps.indexOf(period.status);

  return (
    <div className="space-y-6">
      {/* Current Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-foreground-muted" />
            Verification Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <PeriodStatusBadge status={period.status} />
              {period.is_locked && (
                <Badge variant="primary">
                  <Lock className="w-3 h-3 mr-1" />
                  Locked
                </Badge>
              )}
            </div>
            {period.assurance_level && (
              <Badge variant="secondary" className="capitalize">
                {period.assurance_level} Assurance
              </Badge>
            )}
          </div>

          {/* Verification Info */}
          {period.verified_by && (
            <div className="mt-4 p-4 bg-success/10 rounded-lg border border-success/20">
              <div className="flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-success mt-0.5" />
                <div>
                  <p className="font-medium text-foreground">Verified</p>
                  <p className="text-sm text-foreground-muted">
                    By {period.verified_by}
                    {period.verified_at && ` on ${formatDate(period.verified_at)}`}
                  </p>
                  {period.verification_statement && (
                    <p className="text-sm text-foreground-muted mt-2 italic">
                      "{period.verification_statement}"
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Status Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Workflow Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between relative">
            {/* Progress Line */}
            <div className="absolute top-5 left-0 right-0 h-1 bg-border -z-10" />
            <div
              className="absolute top-5 left-0 h-1 bg-primary -z-10 transition-all duration-500"
              style={{ width: `${(currentStepIndex / (statusSteps.length - 1)) * 100}%` }}
            />

            {statusSteps.map((status, index) => {
              const isComplete = index < currentStepIndex;
              const isCurrent = index === currentStepIndex;
              const isPending = index > currentStepIndex;

              return (
                <div key={status} className="flex flex-col items-center">
                  <div
                    className={cn(
                      'w-10 h-10 rounded-full flex items-center justify-center transition-colors',
                      isComplete && 'bg-primary text-white',
                      isCurrent && 'bg-primary text-white ring-4 ring-primary/20',
                      isPending && 'bg-background border-2 border-border text-foreground-muted'
                    )}
                  >
                    {isComplete ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : (
                      getStatusIcon(status)
                    )}
                  </div>
                  <p
                    className={cn(
                      'text-xs mt-2 capitalize',
                      (isComplete || isCurrent) && 'text-foreground font-medium',
                      isPending && 'text-foreground-muted'
                    )}
                  >
                    {status}
                  </p>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Status Actions */}
      {!period.is_locked && (
        <Card>
          <CardHeader>
            <CardTitle>Available Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Draft -> Review */}
              {period.status === 'draft' && validTransitions.includes('review') && (
                <div className="flex items-center justify-between p-4 bg-background-muted rounded-lg">
                  <div>
                    <p className="font-medium text-foreground">Submit for Review</p>
                    <p className="text-sm text-foreground-muted">
                      Send this period for internal review before submission.
                    </p>
                  </div>
                  <Button
                    variant="primary"
                    onClick={() => handleTransition('review')}
                    disabled={loading}
                    leftIcon={loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  >
                    Submit for Review
                  </Button>
                </div>
              )}

              {/* Review -> Draft or Submitted */}
              {period.status === 'review' && (
                <>
                  {validTransitions.includes('draft') && (
                    <div className="flex items-center justify-between p-4 bg-background-muted rounded-lg">
                      <div>
                        <p className="font-medium text-foreground">Return to Draft</p>
                        <p className="text-sm text-foreground-muted">
                          Return this period to draft status for edits.
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        onClick={() => handleTransition('draft')}
                        disabled={loading}
                        leftIcon={<RotateCcw className="w-4 h-4" />}
                      >
                        Return to Draft
                      </Button>
                    </div>
                  )}
                  {validTransitions.includes('submitted') && (
                    <div className="flex items-center justify-between p-4 bg-background-muted rounded-lg">
                      <div>
                        <p className="font-medium text-foreground">Submit for Verification</p>
                        <p className="text-sm text-foreground-muted">
                          Submit this period for third-party verification.
                        </p>
                      </div>
                      <Button
                        variant="primary"
                        onClick={() => handleTransition('submitted')}
                        disabled={loading}
                        leftIcon={loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                      >
                        Submit
                      </Button>
                    </div>
                  )}
                </>
              )}

              {/* Submitted -> Audit (Admin only) */}
              {period.status === 'submitted' && validTransitions.includes('audit') && isAdmin && (
                <div className="flex items-center justify-between p-4 bg-background-muted rounded-lg">
                  <div>
                    <p className="font-medium text-foreground">Start Audit</p>
                    <p className="text-sm text-foreground-muted">
                      Begin the third-party audit process. Admin only.
                    </p>
                  </div>
                  <Button
                    variant="primary"
                    onClick={() => handleTransition('audit')}
                    disabled={loading}
                    leftIcon={loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileSearch className="w-4 h-4" />}
                  >
                    Start Audit
                  </Button>
                </div>
              )}

              {/* Audit -> Verified (Admin only) */}
              {period.status === 'audit' && validTransitions.includes('verified') && isAdmin && (
                <div className="flex items-center justify-between p-4 bg-background-muted rounded-lg">
                  <div>
                    <p className="font-medium text-foreground">Mark as Verified</p>
                    <p className="text-sm text-foreground-muted">
                      Complete audit and mark this period as verified. Admin only.
                    </p>
                  </div>
                  <Button
                    variant="primary"
                    onClick={() => setShowVerifyModal(true)}
                    disabled={loading}
                    leftIcon={<Award className="w-4 h-4" />}
                  >
                    Mark Verified
                  </Button>
                </div>
              )}

              {/* Verified -> Locked (Admin only) */}
              {period.status === 'verified' && !period.is_locked && isAdmin && (
                <div className="flex items-center justify-between p-4 bg-warning/10 rounded-lg border border-warning/20">
                  <div>
                    <p className="font-medium text-foreground flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-warning" />
                      Lock Period
                    </p>
                    <p className="text-sm text-foreground-muted">
                      Lock this period to prevent any further changes. This action cannot be undone.
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    onClick={handleLock}
                    disabled={loading}
                    leftIcon={loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                  >
                    Lock Period
                  </Button>
                </div>
              )}

              {/* No actions available */}
              {validTransitions.length === 0 && !period.is_locked && (
                <div className="text-center py-4">
                  <p className="text-foreground-muted">
                    No actions available for your role at this status.
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Locked Message */}
      {period.is_locked && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="py-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-primary/10">
                <Lock className="w-6 h-6 text-primary" />
              </div>
              <div>
                <p className="font-semibold text-foreground">Period is Locked</p>
                <p className="text-sm text-foreground-muted">
                  This reporting period has been locked and cannot be modified.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Status History Timeline */}
      {statusHistory && (
        <Card>
          <CardHeader>
            <CardTitle>Status History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {statusHistory.timeline.created_at && (
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-foreground-muted mt-2" />
                  <div>
                    <p className="font-medium text-foreground">Period Created</p>
                    <p className="text-sm text-foreground-muted">
                      {formatDate(statusHistory.timeline.created_at)}
                    </p>
                  </div>
                </div>
              )}
              {statusHistory.timeline.submitted_at && (
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-warning mt-2" />
                  <div>
                    <p className="font-medium text-foreground">Submitted</p>
                    <p className="text-sm text-foreground-muted">
                      {formatDate(statusHistory.timeline.submitted_at)}
                    </p>
                  </div>
                </div>
              )}
              {statusHistory.timeline.verified_at && (
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-success mt-2" />
                  <div>
                    <p className="font-medium text-foreground">Verified</p>
                    <p className="text-sm text-foreground-muted">
                      {formatDate(statusHistory.timeline.verified_at)}
                      {statusHistory.timeline.verified_by && ` by ${statusHistory.timeline.verified_by}`}
                    </p>
                    {statusHistory.verification.assurance_level && (
                      <Badge variant="secondary" size="sm" className="mt-1 capitalize">
                        {statusHistory.verification.assurance_level} Assurance
                      </Badge>
                    )}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Verification Modal */}
      {showVerifyModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-lg mx-4">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Mark Period as Verified</CardTitle>
                <button
                  onClick={() => setShowVerifyModal(false)}
                  className="p-2 hover:bg-background-muted rounded-lg"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Assurance Level
                  </label>
                  <Select
                    value={verifyForm.assurance_level}
                    onChange={(e) =>
                      setVerifyForm({ ...verifyForm, assurance_level: e.target.value as AssuranceLevel })
                    }
                    options={[
                      { value: 'limited', label: 'Limited Assurance' },
                      { value: 'reasonable', label: 'Reasonable Assurance' },
                    ]}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Verified By
                  </label>
                  <Input
                    placeholder="Name of verifier or verification body"
                    value={verifyForm.verified_by}
                    onChange={(e) => setVerifyForm({ ...verifyForm, verified_by: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Verification Statement
                  </label>
                  <Textarea
                    placeholder="Enter verification statement or notes..."
                    value={verifyForm.verification_statement}
                    onChange={(e) =>
                      setVerifyForm({ ...verifyForm, verification_statement: e.target.value })
                    }
                    rows={4}
                  />
                </div>
              </div>
            </CardContent>
            <div className="px-6 py-4 border-t border-border flex justify-end gap-3">
              <Button variant="outline" onClick={() => setShowVerifyModal(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleVerify}
                disabled={loading || !verifyForm.verified_by || !verifyForm.verification_statement}
                leftIcon={loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
              >
                Confirm Verification
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
