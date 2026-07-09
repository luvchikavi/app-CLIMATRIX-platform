'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AppShell } from '@/components/layout';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  Badge,
  EmptyState,
  toast,
} from '@/components/ui';
import { Users, Loader2, Filter } from 'lucide-react';
import { api, Lead, LeadStatus, LeadSource } from '@/lib/api';

const STATUS_OPTIONS: LeadStatus[] = ['new', 'contacted', 'trial', 'customer', 'lost'];
const SOURCE_OPTIONS: LeadSource[] = [
  'website_tryit',
  'website_trial',
  'website_demo',
  'conference',
  'signup',
  'forum',
  'manual',
];

const STATUS_VARIANT: Record<LeadStatus, 'default' | 'info' | 'warning' | 'success' | 'error'> = {
  new: 'info',
  contacted: 'warning',
  trial: 'warning',
  customer: 'success',
  lost: 'error',
};

const SOURCE_LABEL: Record<LeadSource, string> = {
  website_tryit: 'Website (Try It)',
  website_trial: 'Website (Trial)',
  website_demo: 'Website (Demo)',
  conference: 'Conference',
  signup: 'Signup',
  forum: 'Forum',
  manual: 'Manual',
};

export default function LeadsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<LeadStatus | ''>('');
  const [sourceFilter, setSourceFilter] = useState<LeadSource | ''>('');

  const { data: leads, isLoading } = useQuery({
    queryKey: ['leads', statusFilter, sourceFilter],
    queryFn: () =>
      api.getLeads({
        status: statusFilter || undefined,
        source: sourceFilter || undefined,
      }),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: LeadStatus }) =>
      api.updateLead(id, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      toast.success('Lead updated');
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to update lead');
    },
  });

  const notesMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) =>
      api.updateLead(id, { notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      toast.success('Notes saved');
    },
    onError: (err: Error) => toast.error(err.message || 'Failed to save notes'),
  });

  const followUpMutation = useMutation({
    mutationFn: (id: string) => api.sendLeadFollowUp(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      toast.success('Follow-up email sent');
    },
    onError: (err: Error) => toast.error(err.message || 'Email failed'),
  });

  const editNotes = (id: string, current: string | null) => {
    const next = window.prompt('Notes for this lead:', current ?? '');
    if (next !== null) notesMutation.mutate({ id, notes: next });
  };

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Leads</h1>
          <p className="text-foreground-muted mt-1">
            Track people who tried the app, left details, or came from a conference or forum.
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="flex items-center gap-2 text-foreground-muted">
          <Filter className="w-4 h-4" />
          <span className="text-sm">Filters</span>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as LeadStatus | '')}
          className="text-sm bg-transparent border border-border rounded-lg px-3 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value as LeadSource | '')}
          className="text-sm bg-transparent border border-border rounded-lg px-3 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">All sources</option>
          {SOURCE_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {SOURCE_LABEL[s]}
            </option>
          ))}
        </select>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {leads ? `${leads.length} lead${leads.length === 1 ? '' : 's'}` : 'Leads'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12 text-foreground-muted">
              <Loader2 className="w-5 h-5 animate-spin mr-2" />
              Loading leads...
            </div>
          ) : !leads || leads.length === 0 ? (
            <EmptyState
              icon={<Users className="w-8 h-8" />}
              title="No leads yet"
              description="Leads captured from the website, conferences, and forums will appear here."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>Organization</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Notes</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {leads.map((lead: Lead) => (
                  <TableRow key={lead.id}>
                    <TableCell>
                      <div className="font-medium text-foreground">{lead.email}</div>
                      {lead.name && (
                        <div className="text-sm text-foreground-muted">{lead.name}</div>
                      )}
                    </TableCell>
                    <TableCell>{lead.organization_name || '—'}</TableCell>
                    <TableCell>
                      <Badge variant="default">{SOURCE_LABEL[lead.source] || lead.source}</Badge>
                      {lead.what_tried && (
                        <div className="text-xs text-foreground-muted mt-1">
                          {lead.what_tried}
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Badge variant={STATUS_VARIANT[lead.status]}>{lead.status}</Badge>
                        <select
                          value={lead.status}
                          disabled={updateMutation.isPending}
                          onChange={(e) =>
                            updateMutation.mutate({
                              id: lead.id,
                              status: e.target.value as LeadStatus,
                            })
                          }
                          className="text-sm bg-transparent border border-border rounded-lg px-2 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                        >
                          {STATUS_OPTIONS.map((s) => (
                            <option key={s} value={s}>
                              {s}
                            </option>
                          ))}
                        </select>
                      </div>
                    </TableCell>
                    <TableCell className="text-foreground-muted">
                      {formatDate(lead.created_at)}
                    </TableCell>
                    <TableCell className="max-w-xs text-foreground-muted">
                      <button
                        onClick={() => editNotes(lead.id, lead.notes)}
                        className="whitespace-pre-line text-left hover:text-foreground"
                        title="Click to edit notes"
                      >
                        {lead.notes || 'Add note…'}
                      </button>
                    </TableCell>
                    <TableCell>
                      <button
                        onClick={() => followUpMutation.mutate(lead.id)}
                        disabled={followUpMutation.isPending}
                        className="rounded-lg border border-border px-2.5 py-1 text-xs font-medium text-foreground-muted hover:border-primary hover:text-primary disabled:opacity-50"
                        title="Send the follow-up email and mark as contacted"
                      >
                        Send follow-up
                      </button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </AppShell>
  );
}
