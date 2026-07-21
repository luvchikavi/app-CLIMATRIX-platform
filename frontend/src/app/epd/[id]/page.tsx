'use client';

/**
 * EPD project wizard/detail — the declaration workbench.
 *
 * One page walks the whole preparation: declaration details (draft-editable),
 * readiness checklist (the data-gaps list), the frozen/live EN 15804 results
 * matrix, document downloads (EN 15804 PDF + ILCD+EPD XML, export-gated),
 * the verification tab (VerifierAccess reuse) and the one-step ISO 14025
 * status machine.
 */

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { AppShell } from '@/components/layout';
import { useEntitlementFlags } from '@/components/layout/TeaserGate';
import { Surface, PanelLabel, PageHead } from '@/components/canopy';
import { Button, Input, toast } from '@/components/ui';
import {
  useEpd,
  useUpdateEpd,
  useDeleteEpd,
  useTransitionEpd,
  useEpdVerifierAccess,
  useInviteEpdVerifier,
  useRevokeEpdVerifier,
} from '@/hooks/useEpd';
import { api } from '@/lib/api';
import type { EpdDetail, EpdResults, EpdStatus } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import { EPD_STATUS_ORDER, EPD_STATUS_META, TRANSITION_LABEL, PROGRAM_OPERATORS } from '@/lib/epd';
import { EN15804_MODULE_OPTIONS, STAGE_META, UNIT_SHORT } from '@/lib/pcf';
import { cn, num } from '@/lib/utils';
import {
  ArrowLeft,
  Check,
  CheckCircle2,
  Circle,
  Copy,
  FileText,
  FileCode2,
  Loader2,
  Lock,
  ShieldCheck,
  Snowflake,
  Trash2,
} from 'lucide-react';

function fmtVal(v: number): string {
  if (v === 0) return '—';
  const a = Math.abs(v);
  if (a >= 100) return v.toFixed(1);
  if (a >= 0.01) return v.toFixed(3);
  return v.toExponential(2);
}

/** The ISO 14025 workflow strip — where this declaration stands. */
function StatusStepper({ status }: { status: EpdStatus }) {
  const expired = status === 'expired';
  const currentIdx = expired ? EPD_STATUS_ORDER.length - 1 : EPD_STATUS_ORDER.indexOf(status);
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {EPD_STATUS_ORDER.map((s, i) => {
        const meta = EPD_STATUS_META[s];
        const done = i < currentIdx;
        const current = i === currentIdx && !expired;
        return (
          <div key={s} className="flex items-center gap-1.5">
            {i > 0 && <div className={cn('h-px w-4', done || current ? 'bg-cy-accent' : 'bg-cy-row')} />}
            <span
              className={cn(
                'flex items-center gap-1 rounded-full px-2.5 py-1 text-[11.5px] font-semibold',
                current ? meta.className : done ? 'bg-cy-accent-soft text-cy-accent' : 'bg-cy-row text-cy-faint'
              )}
              title={meta.hint}
            >
              {done ? <Check className="h-3 w-3" /> : <Circle className="h-2 w-2" />}
              {meta.label}
            </span>
          </div>
        );
      })}
      {expired && (
        <span className={cn('rounded-full px-2.5 py-1 text-[11.5px] font-semibold', EPD_STATUS_META.expired.className)}>
          Expired
        </span>
      )}
    </div>
  );
}

/** Readiness checklist — the wizard's data-gaps view. */
function Checklist({ items }: { items: EpdDetail['checklist'] }) {
  return (
    <Surface padding="panel">
      <PanelLabel>Readiness checklist</PanelLabel>
      <ul className="mt-2 space-y-2">
        {items.map((c) => (
          <li key={c.key} className="flex items-start gap-2.5 text-[12.5px]">
            {c.ok ? (
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-cy-accent" />
            ) : (
              <Circle className="mt-0.5 h-4 w-4 shrink-0 text-cy-warn" />
            )}
            <div>
              <span className={cn('font-semibold', c.ok ? 'text-cy-ink' : 'text-cy-warn')}>{c.label}</span>
              <div className="text-[11.5px] text-cy-muted">{c.detail}</div>
            </div>
          </li>
        ))}
      </ul>
    </Surface>
  );
}

/** The EN 15804 results matrix the declaration renders (frozen or live). */
function ResultsMatrix({ results, frozen }: { results: EpdResults; frozen: boolean }) {
  const lca = results.lca;
  const unitShort = UNIT_SHORT[results.declared_unit] ?? results.declared_unit;
  return (
    <Surface padding="panel">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div>
          <PanelLabel>EN 15804 results</PanelLabel>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-[24px] font-[650] tabular-nums text-cy-ink">
              {results.pcf.total_kgco2e_per_unit.toFixed(2)}
            </span>
            <span className="text-[12.5px] text-cy-muted">
              kg CO2e / {results.declared_unit_amount} {unitShort} (A1-A3)
            </span>
          </div>
        </div>
        <span
          className={cn(
            'flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold',
            frozen ? 'bg-cy-accent-soft text-cy-accent' : 'bg-cy-warn-soft text-cy-warn'
          )}
          title={
            frozen
              ? 'These results froze when the EPD left draft — later recomputes on the product do not change this declaration'
              : 'Live preview from the pinned footprint — freezes when you send the EPD to internal review'
          }
        >
          <Snowflake className="h-3 w-3" />
          {frozen ? 'Frozen snapshot' : 'Live preview'}
        </span>
      </div>
      {results.pcf.primary_data_share != null && (
        <p className="mb-2 text-[12px] text-cy-muted">
          Primary data share:{' '}
          <span className="font-semibold tabular-nums text-cy-accent">
            {results.pcf.primary_data_share.toFixed(1)}%
          </span>
        </p>
      )}
      {lca ? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-[12.5px]">
            <thead>
              <tr>
                <th className="py-2 pr-3 text-left text-[10.5px] font-bold uppercase tracking-[0.07em] text-cy-faint">
                  Indicator
                </th>
                {lca.modules.map((m) => (
                  <th
                    key={m}
                    className="py-2 pr-3 text-right text-[10.5px] font-bold uppercase tracking-[0.07em] text-cy-faint"
                    title={STAGE_META[m]?.label ?? m}
                  >
                    {m}
                  </th>
                ))}
                <th className="py-2 pr-3 text-right text-[10.5px] font-bold uppercase tracking-[0.07em] text-cy-faint">
                  Total
                </th>
                <th className="py-2 text-left text-[10.5px] font-bold uppercase tracking-[0.07em] text-cy-faint">
                  Unit
                </th>
              </tr>
            </thead>
            <tbody>
              {lca.rows.map((row) => (
                <tr key={row.code} className="border-t border-cy-row">
                  <td className="max-w-[14rem] py-1.5 pr-3 font-semibold text-cy-ink">{row.name}</td>
                  {lca.modules.map((m) => (
                    <td key={m} className="py-1.5 pr-3 text-right tabular-nums text-cy-muted">
                      {fmtVal(row.by_module[m] ?? 0)}
                    </td>
                  ))}
                  <td className="py-1.5 pr-3 text-right tabular-nums font-semibold text-cy-ink">{fmtVal(row.total)}</td>
                  <td className="py-1.5 text-[11px] text-cy-faint">{row.unit}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-[12.5px] text-cy-muted">No LCA matrix on the pinned footprint — recompute it.</p>
      )}
      {lca?.note && <p className="mt-2 text-[11px] text-cy-faint">{lca.note}</p>}
    </Surface>
  );
}

function VerificationPanel({ epdId, canManage }: { epdId: string; canManage: boolean }) {
  const { data: invites } = useEpdVerifierAccess(epdId);
  const invite = useInviteEpdVerifier(epdId);
  const revoke = useRevokeEpdVerifier(epdId);
  const [email, setEmail] = useState('');
  const [firm, setFirm] = useState('');
  const [copied, setCopied] = useState<string | null>(null);

  const copyLink = (url: string, id: string) => {
    navigator.clipboard.writeText(url).then(() => {
      setCopied(id);
      setTimeout(() => setCopied(null), 1500);
    });
  };

  return (
    <Surface padding="panel">
      <div className="flex items-center gap-2">
        <ShieldCheck className="h-4 w-4 text-cy-accent" />
        <PanelLabel>Third-party verification</PanelLabel>
      </div>
      <p className="mt-1 text-[12px] text-cy-muted">
        The verifier gets a read-only portal link scoped to this EPD only — declaration, frozen results and every
        line&apos;s derivation. No login, no write access, revocable any time.
      </p>
      {canManage && (
        <div className="mt-3 flex flex-wrap gap-2">
          <Input
            placeholder="verifier@firm.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="min-w-[200px] flex-1"
          />
          <Input
            placeholder="Firm (e.g. SII)"
            value={firm}
            onChange={(e) => setFirm(e.target.value)}
            className="w-36"
          />
          <Button
            size="sm"
            disabled={!email.trim() || invite.isPending}
            isLoading={invite.isPending}
            onClick={() =>
              invite.mutate(
                { verifier_email: email.trim(), verifier_name: firm.trim() || undefined },
                {
                  onSuccess: () => {
                    setEmail('');
                    setFirm('');
                    toast.success('Verifier invited — copy the portal link below');
                  },
                  onError: (e: Error) => toast.error(e.message || 'Could not invite'),
                }
              )
            }
          >
            Invite verifier
          </Button>
        </div>
      )}
      {!!invites?.length && (
        <ul className="mt-3 space-y-2">
          {invites.map((a) => (
            <li key={a.id} className="flex flex-wrap items-center justify-between gap-2 rounded-[10px] bg-cy-row/60 px-3 py-2 text-[12.5px]">
              <div>
                <span className="font-semibold text-cy-ink">{a.verifier_email}</span>
                {a.verifier_name && <span className="text-cy-muted"> · {a.verifier_name}</span>}
                <span className={cn('ml-2 rounded-full px-2 py-0.5 text-[10.5px] font-semibold', a.status === 'active' ? 'bg-cy-accent-soft text-cy-accent' : 'bg-cy-row text-cy-faint')}>
                  {a.status}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {a.status === 'active' && (
                  <>
                    <button
                      type="button"
                      onClick={() => copyLink(a.portal_url, a.id)}
                      className="flex cursor-pointer items-center gap-1 text-[12px] font-semibold text-cy-accent hover:underline"
                    >
                      {copied === a.id ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                      {copied === a.id ? 'Copied' : 'Copy portal link'}
                    </button>
                    {canManage && (
                      <button
                        type="button"
                        onClick={() => revoke.mutate(a.id, { onSuccess: () => toast.success('Access revoked') })}
                        className="cursor-pointer text-cy-faint hover:text-error"
                        aria-label="Revoke access"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Surface>
  );
}

function EpdDetailContent() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const epdId = params.id;

  const { data: epd, isLoading } = useEpd(epdId);
  const update = useUpdateEpd(epdId);
  const del = useDeleteEpd();
  const transition = useTransitionEpd(epdId);
  const { isTrialing } = useEntitlementFlags();
  const { user } = useAuthStore();
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

  const isDraft = epd?.status === 'draft';
  const [form, setForm] = useState({
    name: '',
    program_operator: '',
    functional_unit: '',
    rsl_years: '',
    registration_number: '',
    scope_modules: [] as string[],
  });
  useEffect(() => {
    if (epd) {
      setForm({
        name: epd.name,
        program_operator: epd.program_operator ?? '',
        functional_unit: epd.functional_unit ?? '',
        rsl_years: epd.rsl_years != null ? String(epd.rsl_years) : '',
        registration_number: epd.registration_number ?? '',
        scope_modules: epd.scope_modules,
      });
    }
  }, [epd]);
  const [downloading, setDownloading] = useState<string | null>(null);

  if (isLoading || !epd) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-cy-accent" />
      </div>
    );
  }

  const saveDetails = () => {
    const payload: Parameters<typeof update.mutate>[0] = {
      program_operator: form.program_operator.trim() || null,
      registration_number: form.registration_number.trim() || null,
    };
    if (isDraft) {
      payload.name = form.name.trim() || epd.name;
      payload.functional_unit = form.functional_unit.trim() || null;
      payload.rsl_years = form.rsl_years ? Number(form.rsl_years) : null;
      payload.scope_modules = form.scope_modules;
    }
    update.mutate(payload, {
      onSuccess: () => toast.success('Saved'),
      onError: (e: Error) => toast.error(e.message || 'Could not save'),
    });
  };

  const toggleModule = (m: string) => {
    if (!isDraft) return;
    setForm((f) => ({
      ...f,
      scope_modules: f.scope_modules.includes(m)
        ? f.scope_modules.filter((x) => x !== m)
        : [...f.scope_modules, m],
    }));
  };

  const runDownload = async (format: 'pdf' | 'ilcd') => {
    setDownloading(format);
    try {
      const safe = epd.name.replace(/\s+/g, '-');
      await api.downloadEpdExport(epdId, format, format === 'pdf' ? `epd_${safe}.pdf` : `epd_${safe}_ilcd.xml`);
    } catch {
      // 402 surfaces via the global limit-reached modal
    } finally {
      setDownloading(null);
    }
  };

  const meta = EPD_STATUS_META[epd.status];

  return (
    <>
      <Link href="/epd" className="mb-3 inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-cy-muted hover:text-cy-ink">
        <ArrowLeft className="h-3.5 w-3.5" /> EPD registry
      </Link>
      <PageHead
        title={epd.name}
        subtitle={`${epd.product_name} · ${epd.pcr} · per ${num(epd.declared_unit_amount)} ${UNIT_SHORT[epd.declared_unit] ?? epd.declared_unit} · version ${epd.version}`}
      />

      {/* Workflow strip + transitions */}
      <Surface padding="panel" className="mb-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <StatusStepper status={epd.status} />
          <div className="flex flex-wrap items-center gap-2">
            {epd.allowed_transitions.map((t) => (
              <Button
                key={t}
                size="sm"
                variant={t === 'draft' ? 'secondary' : 'primary'}
                isLoading={transition.isPending}
                onClick={() =>
                  transition.mutate(t, {
                    onSuccess: () => toast.success(`Moved to ${EPD_STATUS_META[t as EpdStatus]?.label ?? t}`),
                    onError: (e: Error) => toast.error(e.message),
                  })
                }
              >
                {TRANSITION_LABEL[t] ?? t}
              </Button>
            ))}
            {isDraft && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() =>
                  del.mutate(epdId, {
                    onSuccess: () => {
                      toast.success('Draft deleted');
                      router.push('/epd');
                    },
                    onError: (e: Error) => toast.error(e.message),
                  })
                }
                leftIcon={<Trash2 className="h-3.5 w-3.5" />}
              >
                Delete draft
              </Button>
            )}
          </div>
        </div>
        <p className="mt-2 text-[12px] text-cy-muted">{meta.hint}</p>
        {epd.valid_until && (
          <p className="mt-1 text-[12px] text-cy-muted">
            Valid until <span className="font-semibold tabular-nums">{epd.valid_until.slice(0, 10)}</span>
            {epd.days_until_expiry != null && (
              <span className={cn('ml-1.5', epd.days_until_expiry < 180 ? 'font-semibold text-cy-warn' : 'text-cy-faint')}>
                ({epd.days_until_expiry < 0 ? `${-epd.days_until_expiry} days overdue` : `${epd.days_until_expiry} days left`})
              </span>
            )}
          </p>
        )}
      </Surface>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          {/* Declaration details */}
          <Surface padding="panel">
            <div className="mb-3 flex items-center justify-between">
              <PanelLabel>Declaration details</PanelLabel>
              {!isDraft && (
                <span className="flex items-center gap-1 text-[11.5px] text-cy-faint" title="Reopen to draft to edit declaration content">
                  <Lock className="h-3 w-3" /> Content locked after draft
                </span>
              )}
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <Input label="Declaration name" value={form.name} disabled={!isDraft}
                onChange={(e) => setForm({ ...form, name: e.target.value })} />
              <div>
                <Input
                  label="Program operator"
                  list="epd-operators"
                  placeholder="e.g. EPD International"
                  value={form.program_operator}
                  onChange={(e) => setForm({ ...form, program_operator: e.target.value })}
                />
                <datalist id="epd-operators">
                  {PROGRAM_OPERATORS.map((o) => (
                    <option key={o} value={o} />
                  ))}
                </datalist>
              </div>
              <Input label="Functional unit (optional)" value={form.functional_unit} disabled={!isDraft}
                placeholder="e.g. 1 m² of wall, 50 years"
                onChange={(e) => setForm({ ...form, functional_unit: e.target.value })} />
              <Input label="Reference service life (years)" type="number" value={form.rsl_years} disabled={!isDraft}
                placeholder="Required if B modules declared"
                onChange={(e) => setForm({ ...form, rsl_years: e.target.value })} />
              <Input label="Registration number" value={form.registration_number}
                placeholder="Assigned by the program operator"
                onChange={(e) => setForm({ ...form, registration_number: e.target.value })} />
            </div>
            <div className="mt-3">
              <p className="mb-1.5 text-[11.5px] font-semibold text-cy-muted">Declared modules (EN 15804)</p>
              <div className="flex flex-wrap gap-1.5">
                {EN15804_MODULE_OPTIONS.map(({ value }) => {
                  const on = form.scope_modules.includes(value);
                  return (
                    <button
                      key={value}
                      type="button"
                      onClick={() => toggleModule(value)}
                      disabled={!isDraft}
                      title={STAGE_META[value]?.label ?? value}
                      className={cn(
                        'rounded-full px-2.5 py-1 text-[11.5px] font-semibold transition-colors',
                        on ? 'bg-cy-accent text-white' : 'bg-cy-row text-cy-faint',
                        isDraft ? 'cursor-pointer hover:opacity-80' : 'cursor-default opacity-70'
                      )}
                    >
                      {value}
                    </button>
                  );
                })}
              </div>
            </div>
            <div className="mt-4 flex justify-end">
              <Button size="sm" onClick={saveDetails} isLoading={update.isPending}>
                Save details
              </Button>
            </div>
          </Surface>

          {/* Results */}
          {epd.results ? (
            <ResultsMatrix results={epd.results} frozen={epd.results_are_frozen} />
          ) : (
            <Surface padding="panel">
              <PanelLabel>EN 15804 results</PanelLabel>
              <p className="mt-2 text-[13px] text-cy-muted">
                No footprint pinned yet. Go to{' '}
                <Link href={`/products/${epd.product_id}`} className="font-semibold text-cy-accent hover:underline">
                  {epd.product_name}
                </Link>
                , compute + finalize a footprint — it pins to this EPD from the product page.
              </p>
            </Surface>
          )}

          {/* Documents */}
          <Surface padding="panel">
            <PanelLabel>Declaration documents</PanelLabel>
            <p className="mt-1 text-[12px] text-cy-muted">
              The EN 15804-structured declaration PDF and the ILCD+EPD digital dataset (the machine-readable EPD
              building-LCA tools ingest).
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button
                size="sm"
                onClick={() => runDownload('pdf')}
                isLoading={downloading === 'pdf'}
                disabled={!epd.results}
                leftIcon={isTrialing ? <Lock className="h-3.5 w-3.5" /> : <FileText className="h-3.5 w-3.5" />}
                title={isTrialing ? 'Document exports unlock on a plan' : 'EN 15804-structured PDF'}
              >
                {isTrialing ? 'EPD PDF (locked)' : 'Download EPD PDF'}
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => runDownload('ilcd')}
                isLoading={downloading === 'ilcd'}
                disabled={!epd.results}
                leftIcon={isTrialing ? <Lock className="h-3.5 w-3.5" /> : <FileCode2 className="h-3.5 w-3.5" />}
                title={isTrialing ? 'Document exports unlock on a plan' : 'ILCD+EPD XML dataset'}
              >
                {isTrialing ? 'ILCD+EPD XML (locked)' : 'Download ILCD+EPD XML'}
              </Button>
            </div>
          </Surface>
        </div>

        <div className="space-y-4">
          <Checklist items={epd.checklist} />
          <VerificationPanel epdId={epdId} canManage={isAdmin} />
        </div>
      </div>
    </>
  );
}

export default function EpdDetailPage() {
  return (
    <AppShell>
      <EpdDetailContent />
    </AppShell>
  );
}
