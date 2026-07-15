'use client';

/**
 * CBAM Certificates tab (definitive regime).
 *
 * The certificate account ledger (purchases / surrenders / Commission
 * repurchases) plus the Omnibus 50% quarterly holding schedule: at each
 * quarter end the declarant must hold certificates covering at least half
 * of the embedded emissions of the year's imports so far. Holdings come
 * from the ledger; the requirement is computed from the imports register
 * exactly as the annual declaration computes it.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { KPICard } from '@/components/ui/KPICard';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableEmpty,
} from '@/components/ui/Table';
import { ConfirmDialog, toast } from '@/components/ui';
import { api } from '@/lib/api';
import type {
  CBAMCertificateEntry,
  CBAMCertificateEntryType,
  CBAMCertificateSummary,
} from '@/lib/types';
import {
  BadgeEuro,
  CalendarClock,
  Plus,
  ShieldCheck,
  Trash2,
  Wallet,
} from 'lucide-react';

const eur = new Intl.NumberFormat('en-GB', {
  style: 'currency',
  currency: 'EUR',
  maximumFractionDigits: 0,
});

const ENTRY_TYPE_LABELS: Record<CBAMCertificateEntryType, string> = {
  purchase: 'Purchase',
  surrender: 'Surrender',
  repurchase: 'Repurchase (sold back)',
};

const QUARTER_STATUS_STYLES: Record<string, string> = {
  met: 'bg-cy-accent-soft text-cy-accent',
  shortfall: 'bg-error-50 text-error',
  upcoming: 'bg-cy-row text-cy-muted',
  not_applicable: 'bg-cy-row text-cy-muted',
};

const QUARTER_STATUS_LABELS: Record<string, string> = {
  met: 'Met',
  shortfall: 'Top-up needed',
  upcoming: 'Upcoming',
  not_applicable: 'Not applicable',
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function num(value: number | string | null | undefined, digits = 0): string {
  if (value == null) return '—';
  return Number(value).toLocaleString('en-GB', {
    maximumFractionDigits: digits,
  });
}

const CURRENT_YEAR = new Date().getFullYear();
const YEARS = Array.from(
  { length: Math.max(CURRENT_YEAR + 1, 2027) - 2026 + 1 },
  (_, i) => 2026 + i
);

export function CBAMCertificates() {
  const [entries, setEntries] = useState<CBAMCertificateEntry[]>([]);
  const [summary, setSummary] = useState<CBAMCertificateSummary | null>(null);
  const [year, setYear] = useState<number>(
    Math.min(Math.max(CURRENT_YEAR, 2026), YEARS[YEARS.length - 1])
  );
  const [loading, setLoading] = useState(true);

  // Add-entry form
  const [showForm, setShowForm] = useState(false);
  const [entryType, setEntryType] = useState<CBAMCertificateEntryType>('purchase');
  const [entryDate, setEntryDate] = useState('');
  const [quantity, setQuantity] = useState('');
  const [unitPrice, setUnitPrice] = useState('');
  const [declarationYear, setDeclarationYear] = useState('');
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);

  const [confirmState, setConfirmState] = useState<{
    open: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
  }>({ open: false, title: '', message: '', onConfirm: () => {} });

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [ledger, sum] = await Promise.all([
        api.getCBAMCertificates(),
        api.getCBAMCertificateSummary(year),
      ]);
      setEntries(ledger);
      setSummary(sum);
    } catch (err) {
      console.error('Failed to load certificate data:', err);
    } finally {
      setLoading(false);
    }
  }, [year]);

  useEffect(() => {
    load();
  }, [load]);

  const resetForm = () => {
    setEntryType('purchase');
    setEntryDate('');
    setQuantity('');
    setUnitPrice('');
    setDeclarationYear('');
    setNote('');
  };

  const addEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    const qty = parseInt(quantity, 10);
    if (!entryDate || !qty || qty <= 0) return;
    try {
      setSaving(true);
      await api.createCBAMCertificateEntry({
        entry_date: entryDate,
        entry_type: entryType,
        quantity: qty,
        unit_price_eur: unitPrice ? Number(unitPrice) : null,
        declaration_year:
          entryType === 'surrender' && declarationYear
            ? Number(declarationYear)
            : null,
        note: note.trim() || null,
      });
      toast.success('Ledger entry recorded');
      setShowForm(false);
      resetForm();
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to record the entry');
    } finally {
      setSaving(false);
    }
  };

  const removeEntry = (entry: CBAMCertificateEntry) => {
    setConfirmState({
      open: true,
      title: 'Delete ledger entry',
      message: `Delete the ${ENTRY_TYPE_LABELS[entry.entry_type].toLowerCase()} of ${num(
        entry.quantity
      )} certificate(s) on ${formatDate(entry.entry_date)}? The ledger must stay consistent — deletions that would strand a later surrender are rejected.`,
      onConfirm: async () => {
        setConfirmState((s) => ({ ...s, open: false }));
        try {
          await api.deleteCBAMCertificateEntry(entry.id);
          toast.success('Entry deleted');
          await load();
        } catch (err) {
          toast.error(err instanceof Error ? err.message : 'Failed to delete the entry');
        }
      },
    });
  };

  const nextMilestone = useMemo(
    () => summary?.milestones.find((m) => !m.passed) ?? null,
    [summary]
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-foreground">Certificates</h2>
          <p className="text-foreground-muted">
            Your CBAM certificate account and the 50% quarterly holding
            schedule (certificates cover the embedded emissions of your
            imports; 1 certificate = 1 tCO₂e).
          </p>
        </div>
        <div className="flex items-end gap-3">
          <Select
            label="Compliance year"
            value={String(year)}
            onChange={(e) => setYear(Number(e.target.value))}
            options={YEARS.map((y) => ({ value: String(y), label: String(y) }))}
          />
          <Button onClick={() => setShowForm((v) => !v)}>
            <Plus className="w-4 h-4 mr-1" /> Record entry
          </Button>
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          size="sm"
          title="Certificates held"
          value={summary ? num(summary.balance) : '…'}
          icon={<Wallet className="w-5 h-5" />}
        />
        <KPICard
          size="sm"
          title={`Required for ${year} declaration`}
          value={
            summary?.certificates_required != null
              ? num(summary.certificates_required)
              : '—'
          }
          unit={
            summary?.declaration_status
              ? `declaration: ${summary.declaration_status}`
              : 'no declaration draft yet'
          }
          icon={<ShieldCheck className="w-5 h-5" />}
        />
        <KPICard
          size="sm"
          title="Total spent"
          value={summary ? eur.format(Number(summary.total_spent_eur)) : '…'}
          unit={
            summary?.weighted_avg_purchase_price_eur != null
              ? `avg ${eur.format(Number(summary.weighted_avg_purchase_price_eur))}/cert`
              : undefined
          }
          icon={<BadgeEuro className="w-5 h-5" />}
        />
        <KPICard
          size="sm"
          title="Next deadline"
          value={nextMilestone ? formatDate(nextMilestone.date) : '—'}
          unit={nextMilestone?.label}
          icon={<CalendarClock className="w-5 h-5" />}
        />
      </div>

      {/* Add-entry form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Record a certificate movement</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={addEntry} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Select
                  label="Type *"
                  value={entryType}
                  onChange={(e) =>
                    setEntryType(e.target.value as CBAMCertificateEntryType)
                  }
                  options={Object.entries(ENTRY_TYPE_LABELS).map(
                    ([value, label]) => ({ value, label })
                  )}
                />
                <Input
                  label="Date *"
                  type="date"
                  value={entryDate}
                  onChange={(e) => setEntryDate(e.target.value)}
                  required
                />
                <Input
                  label="Certificates *"
                  type="number"
                  min="1"
                  step="1"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  placeholder="e.g. 100"
                  required
                />
                <Input
                  label="Unit price (EUR, optional)"
                  type="number"
                  min="0"
                  step="0.01"
                  value={unitPrice}
                  onChange={(e) => setUnitPrice(e.target.value)}
                  placeholder="e.g. 82.50"
                />
                {entryType === 'surrender' && (
                  <Input
                    label="Declaration year (optional)"
                    type="number"
                    min="2026"
                    value={declarationYear}
                    onChange={(e) => setDeclarationYear(e.target.value)}
                    placeholder="e.g. 2026"
                  />
                )}
                <Input
                  label="Note (optional)"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="e.g. Q1 purchase on central platform"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setShowForm(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={saving}>
                  {saving ? 'Saving…' : 'Record entry'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Holding schedule */}
      <Card>
        <CardHeader>
          <CardTitle>50% quarterly holding schedule — {year}</CardTitle>
        </CardHeader>
        <CardContent>
          {summary && !summary.holding_rule_applies && (
            <p className="mb-4 text-sm text-foreground-muted bg-background-muted rounded-lg p-3">
              The quarterly holding requirement applies from 2027.
              Certificates covering 2026 imports go on sale 1 Feb 2027 and
              are surrendered with the 30 Sep 2027 declaration — the table
              below shows your cumulative embedded emissions for planning.
            </p>
          )}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Quarter</TableHead>
                <TableHead>Quarter end</TableHead>
                <TableHead className="text-right">
                  Cumulative emissions (tCO₂e)
                </TableHead>
                <TableHead className="text-right">Required (50%)</TableHead>
                <TableHead className="text-right">Held</TableHead>
                <TableHead className="text-right">Shortfall</TableHead>
                <TableHead className="text-right">Est. top-up cost</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {!summary ? (
                <TableEmpty
                  colSpan={8}
                  title={loading ? 'Loading…' : 'No data'}
                />
              ) : (
                summary.holding_schedule.map((q) => (
                  <TableRow key={q.quarter}>
                    <TableCell className="font-medium">Q{q.quarter}</TableCell>
                    <TableCell>{formatDate(q.quarter_end)}</TableCell>
                    <TableCell className="text-right">
                      {num(q.cumulative_emissions_tco2e, 1)}
                    </TableCell>
                    <TableCell className="text-right">
                      {summary.holding_rule_applies
                        ? num(q.required_certificates)
                        : '—'}
                    </TableCell>
                    <TableCell className="text-right">
                      {num(q.held_certificates)}
                    </TableCell>
                    <TableCell className="text-right">
                      {summary.holding_rule_applies && q.shortfall > 0 ? (
                        <span className="text-error font-medium">
                          {num(q.shortfall)}
                        </span>
                      ) : (
                        '—'
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      {summary.holding_rule_applies && q.shortfall > 0
                        ? eur.format(Number(q.estimated_topup_cost_eur))
                        : '—'}
                    </TableCell>
                    <TableCell>
                      <span
                        className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                          QUARTER_STATUS_STYLES[q.status] ?? ''
                        }`}
                      >
                        {QUARTER_STATUS_LABELS[q.status] ?? q.status}
                      </span>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Milestones */}
      {summary && summary.milestones.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Key dates</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {summary.milestones.map((m) => (
                <li
                  key={`${m.date}-${m.label}`}
                  className={`flex items-center gap-3 text-sm ${
                    m.passed ? 'text-foreground-muted line-through' : 'text-foreground'
                  }`}
                >
                  <CalendarClock className="w-4 h-4 shrink-0" />
                  <span className="font-medium whitespace-nowrap">
                    {formatDate(m.date)}
                  </span>
                  <span>{m.label}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Ledger */}
      <Card>
        <CardHeader>
          <CardTitle>Ledger</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Certificates</TableHead>
                <TableHead className="text-right">Unit price</TableHead>
                <TableHead className="text-right">Total</TableHead>
                <TableHead>Declaration</TableHead>
                <TableHead>Note</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.length === 0 ? (
                <TableEmpty
                  colSpan={8}
                  title={loading ? 'Loading…' : 'No certificate movements yet'}
                  description={
                    loading
                      ? undefined
                      : 'Certificate sales open on the central platform on 1 Feb 2027.'
                  }
                />
              ) : (
                entries.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell>{formatDate(entry.entry_date)}</TableCell>
                    <TableCell>{ENTRY_TYPE_LABELS[entry.entry_type]}</TableCell>
                    <TableCell className="text-right">
                      {entry.entry_type === 'purchase' ? '+' : '−'}
                      {num(entry.quantity)}
                    </TableCell>
                    <TableCell className="text-right">
                      {entry.unit_price_eur != null
                        ? eur.format(Number(entry.unit_price_eur))
                        : '—'}
                    </TableCell>
                    <TableCell className="text-right">
                      {entry.total_eur != null
                        ? eur.format(Number(entry.total_eur))
                        : '—'}
                    </TableCell>
                    <TableCell>{entry.declaration_year ?? '—'}</TableCell>
                    <TableCell className="max-w-[220px] truncate">
                      {entry.note ?? '—'}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeEntry(entry)}
                        aria-label="Delete entry"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Assumptions */}
      {summary && summary.assumptions.length > 0 && (
        <div className="text-xs text-foreground-muted space-y-1">
          {summary.assumptions.map((a, i) => (
            <p key={i}>• {a}</p>
          ))}
        </div>
      )}

      <ConfirmDialog
        isOpen={confirmState.open}
        onClose={() => setConfirmState((s) => ({ ...s, open: false }))}
        onConfirm={confirmState.onConfirm}
        title={confirmState.title}
        message={confirmState.message}
        variant="danger"
        confirmLabel="Delete"
      />
    </div>
  );
}
