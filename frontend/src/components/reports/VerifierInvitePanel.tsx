'use client';

/**
 * Org-side control for the verifier read-only portal: invite an external
 * verifier to this reporting period, see who has access, copy their portal
 * link, and revoke. Admin-only (the backend enforces it too).
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { VerifierAccess } from '@/lib/api';
import { Surface, PanelLabel } from '@/components/canopy';
import { Button, Input, toast } from '@/components/ui';
import { ShieldCheck, Copy, Trash2, Check } from 'lucide-react';

export function VerifierInvitePanel({
  periodId,
  canManage,
}: {
  periodId: string;
  canManage: boolean;
}) {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState('');
  const [firm, setFirm] = useState('');
  const [copied, setCopied] = useState<string | null>(null);

  const { data: invites } = useQuery({
    queryKey: ['verifier-access', periodId],
    queryFn: () => api.listVerifierAccess(periodId),
    enabled: !!periodId,
  });

  const invite = useMutation({
    mutationFn: () =>
      api.inviteVerifier(periodId, {
        verifier_email: email.trim(),
        verifier_name: firm.trim() || undefined,
      }),
    onSuccess: () => {
      setEmail('');
      setFirm('');
      queryClient.invalidateQueries({ queryKey: ['verifier-access', periodId] });
      toast.success('Verifier invited — copy their read-only portal link below');
    },
    onError: (e: Error) => toast.error(e.message || 'Could not invite verifier'),
  });

  const revoke = useMutation({
    mutationFn: (id: string) => api.revokeVerifierAccess(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verifier-access', periodId] });
      toast.success('Access revoked');
    },
    onError: (e: Error) => toast.error(e.message || 'Could not revoke'),
  });

  const copyLink = (a: VerifierAccess) => {
    navigator.clipboard.writeText(a.portal_url).then(() => {
      setCopied(a.id);
      setTimeout(() => setCopied(null), 1500);
    });
  };

  const active = (invites ?? []).filter((i) => i.status === 'active');

  return (
    <Surface className="mt-4">
      <PanelLabel>External verifier access</PanelLabel>
      <p className="mb-4 text-[12.5px] text-cy-muted">
        Invite your auditor (LRQA, DEKRA, SII…) to a read-only view of this period — every
        line’s source, factor, method and result, plus the audit trail. No account needed;
        the whole engagement can run remotely (ISO 14064-5:2026).
      </p>

      {canManage && (
        <div className="mb-5 flex flex-wrap items-end gap-2">
          <div className="min-w-[200px] flex-1">
            <Input
              label="Verifier email"
              placeholder="auditor@lrqa.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="min-w-[160px] flex-1">
            <Input
              label="Firm (optional)"
              placeholder="LRQA"
              value={firm}
              onChange={(e) => setFirm(e.target.value)}
            />
          </div>
          <Button
            onClick={() => invite.mutate()}
            disabled={!email.includes('@') || invite.isPending}
            isLoading={invite.isPending}
          >
            <ShieldCheck className="mr-1.5 h-4 w-4" />
            Invite
          </Button>
        </div>
      )}

      {active.length > 0 ? (
        <div className="divide-y divide-cy-row">
          {active.map((a) => (
            <div key={a.id} className="flex flex-wrap items-center justify-between gap-2 py-2.5">
              <div className="min-w-0">
                <p className="text-[13px] font-semibold text-cy-ink">
                  {a.verifier_name ? `${a.verifier_name} · ` : ''}
                  {a.verifier_email}
                </p>
                <p className="text-[11.5px] text-cy-faint">
                  {a.last_accessed_at
                    ? `Last opened ${a.last_accessed_at.slice(0, 10)}`
                    : 'Not opened yet'}
                </p>
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => copyLink(a)}
                  className="inline-flex items-center gap-1 rounded-full bg-cy-row px-2.5 py-1 text-[11.5px] font-semibold text-cy-muted hover:text-cy-ink"
                >
                  {copied === a.id ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-cy-accent" /> Copied
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" /> Copy link
                    </>
                  )}
                </button>
                {canManage && (
                  <button
                    onClick={() => revoke.mutate(a.id)}
                    className="rounded-full p-1.5 text-cy-faint hover:bg-error-50 hover:text-error"
                    title="Revoke access"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-[12.5px] text-cy-faint">No verifier has been invited to this period.</p>
      )}
    </Surface>
  );
}
