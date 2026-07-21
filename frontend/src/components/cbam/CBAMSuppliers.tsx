'use client';

/**
 * CBAM Suppliers tab (Phase 3 — supplier portal, importer side).
 *
 * Lists the org's non-EU installations with a per-installation "Request
 * data" action (magic-link email to the supplier), plus the data-requests
 * table: supplier, installation, status, sent date, remind button and a
 * summary of the submitted SEE rows.
 */

import { useCallback, useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableEmpty,
} from '@/components/ui/Table';
import { toast } from '@/components/ui';
import { api } from '@/lib/api';
import { formatQty } from '@/lib/utils';
import type { CBAMDataRequest, CBAMInstallation } from '@/lib/types';
import { Factory, Globe, Mail, Send, X, CheckCircle2, ShieldCheck } from 'lucide-react';

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-cy-warn-soft text-cy-warn',
  submitted: 'bg-cy-accent-soft text-cy-accent',
  expired: 'bg-cy-row text-cy-ink',
};

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString();
}

export function CBAMSuppliers() {
  const [installations, setInstallations] = useState<CBAMInstallation[]>([]);
  const [requests, setRequests] = useState<CBAMDataRequest[]>([]);
  const [loading, setLoading] = useState(true);

  // "Request data" form state (opened per installation)
  const [formInstallation, setFormInstallation] = useState<CBAMInstallation | null>(null);
  const [supplierEmail, setSupplierEmail] = useState('');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [remindingId, setRemindingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [inst, reqs] = await Promise.all([
        api.getCBAMInstallations(),
        api.getCBAMDataRequests(),
      ]);
      setInstallations(inst);
      setRequests(reqs);
    } catch (err) {
      console.error('Failed to load supplier data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const openForm = (installation: CBAMInstallation) => {
    setFormInstallation(installation);
    setSupplierEmail(installation.contact_email || '');
    setMessage('');
  };

  const sendRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formInstallation || !supplierEmail.includes('@')) return;
    try {
      setSending(true);
      await api.createCBAMDataRequest({
        installation_id: formInstallation.id,
        supplier_email: supplierEmail.trim(),
        message: message.trim() || undefined,
      });
      toast.success(`Data request emailed to ${supplierEmail.trim()}`);
      setFormInstallation(null);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to send the request');
    } finally {
      setSending(false);
    }
  };

  const remind = async (req: CBAMDataRequest) => {
    try {
      setRemindingId(req.id);
      await api.remindCBAMDataRequest(req.id);
      toast.success(`Reminder sent to ${req.supplier_email}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to send the reminder');
    } finally {
      setRemindingId(null);
    }
  };

  const summarizeRows = (req: CBAMDataRequest) => {
    if (req.rows.length === 0) return <span className="text-foreground-muted">—</span>;
    return (
      <div className="space-y-0.5">
        {req.rows.map((row) => (
          <div key={row.id} className="flex items-center gap-1.5 text-xs">
            <span className="font-mono">{row.cn_code}</span>
            <span>
              {formatQty(row.direct_see_tco2e_per_t)}
              {row.indirect_see_tco2e_per_t != null &&
                ` + ${formatQty(row.indirect_see_tco2e_per_t)}`}{' '}
              tCO₂e/t
            </span>
            {row.verified && (
              <span className="inline-flex items-center gap-0.5 text-cy-accent">
                <ShieldCheck className="w-3 h-3" /> verified
              </span>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-foreground">Suppliers</h2>
        <p className="text-foreground-muted">
          Ask installation operators for actual embedded-emissions data — supplier actuals replace
          penalised default values (no markup) in your annual declaration.
        </p>
      </div>

      {/* Request-data form */}
      {formInstallation && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Request data — {formInstallation.name}</span>
              <Button variant="ghost" size="sm" onClick={() => setFormInstallation(null)}>
                <X className="w-4 h-4" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={sendRequest} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Supplier email *"
                  type="email"
                  value={supplierEmail}
                  onChange={(e) => setSupplierEmail(e.target.value)}
                  placeholder="operator@supplier.com"
                  required
                />
                <Input
                  label="Message (optional)"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="e.g. Please provide 2026 production data"
                />
              </div>
              <p className="text-xs text-foreground-muted">
                The supplier receives a secure form link (valid 60 days, no account needed) to
                submit specific embedded emissions per CN code.
              </p>
              <div className="flex justify-end gap-3">
                <Button type="button" variant="ghost" onClick={() => setFormInstallation(null)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  isLoading={sending}
                  leftIcon={<Send className="w-4 h-4" />}
                  disabled={!supplierEmail.includes('@')}
                >
                  Send request
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Installations */}
      <Card>
        <CardHeader>
          <CardTitle>Installations</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Installation</TableHead>
              <TableHead>Country</TableHead>
              <TableHead>Contact</TableHead>
              <TableHead className="w-40">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto"></div>
                </TableCell>
              </TableRow>
            ) : installations.length === 0 ? (
              <TableEmpty
                colSpan={4}
                icon={<Factory className="w-12 h-12" />}
                title="No installations yet"
                description="Add a non-EU production facility in the Installations tab first"
              />
            ) : (
              installations.map((inst) => (
                <TableRow key={inst.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Factory className="w-4 h-4 text-foreground-muted" />
                      <span className="font-medium">{inst.name}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Globe className="w-4 h-4 text-foreground-muted" />
                      {inst.country_code}
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-foreground-muted">
                      {inst.contact_email || '—'}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      variant="secondary"
                      leftIcon={<Mail className="w-4 h-4" />}
                      onClick={() => openForm(inst)}
                    >
                      Request data
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Data requests */}
      <Card>
        <CardHeader>
          <CardTitle>Data requests</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Supplier</TableHead>
              <TableHead>Installation</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Sent</TableHead>
              <TableHead>Submitted values</TableHead>
              <TableHead className="w-28">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto"></div>
                </TableCell>
              </TableRow>
            ) : requests.length === 0 ? (
              <TableEmpty
                colSpan={6}
                icon={<Mail className="w-12 h-12" />}
                title="No data requests yet"
                description="Send your first request from the installations list above"
              />
            ) : (
              requests.map((req) => (
                <TableRow key={req.id}>
                  <TableCell>
                    <span className="text-sm">{req.supplier_email}</span>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm">
                      {req.installation_name}{' '}
                      <span className="text-foreground-muted">({req.installation_country})</span>
                    </span>
                  </TableCell>
                  <TableCell>
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        STATUS_COLORS[req.status] || 'bg-cy-row text-cy-ink'
                      }`}
                    >
                      {req.status}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm">{formatDate(req.created_at)}</span>
                  </TableCell>
                  <TableCell>{summarizeRows(req)}</TableCell>
                  <TableCell>
                    {req.status === 'pending' ? (
                      <Button
                        size="sm"
                        variant="ghost"
                        isLoading={remindingId === req.id}
                        onClick={() => remind(req)}
                        leftIcon={<Send className="w-4 h-4" />}
                      >
                        Remind
                      </Button>
                    ) : req.status === 'submitted' ? (
                      <span className="inline-flex items-center gap-1 text-xs text-cy-accent">
                        <CheckCircle2 className="w-4 h-4" /> {formatDate(req.submitted_at)}
                      </span>
                    ) : (
                      <span className="text-xs text-foreground-muted">expired</span>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
