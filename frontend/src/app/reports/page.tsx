'use client';

/**
 * Reports (batch 2.5) — the locked template page: pill tabs, one summary
 * surface (footprint cells + the category table with share bars), and the
 * FinishBar as the page's finish line (status · verification · exports).
 * The deep sub-reports (GHG inventory, data quality, audit, verification)
 * keep their components inside the frame; their own re-skin is 2.5b.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/stores/auth';
import { usePeriodStore } from '@/stores/period';
import { usePeriods, useReportSummary, useActivities, useSites } from '@/hooks/useEmissions';
import Link from 'next/link';
import { AppShell } from '@/components/layout';
import {
  CellValue,
  DataTable,
  FinishBar,
  FocusCard,
  PageHead,
  PanelLabel,
  PillTabs,
  ShareBar,
  StatCells,
  Surface,
  type CanopyColumn,
} from '@/components/canopy';
import { toast } from '@/components/ui';
import {
  GHGInventoryReport,
  DataQualityReport,
  AuditPackageView,
  ExportOptions,
  VerificationWorkflow,
  VerifierInvitePanel,
} from '@/components/reports';
import { api, CategorySummary } from '@/lib/api';
import { categoryNames, downloadFile } from '@/lib/utils';
import type { PeriodStatus, AssuranceLevel } from '@/lib/api';
import { Loader2 } from 'lucide-react';

type ReportTab =
  | 'summary'
  | 'by-scope'
  | 'by-site'
  | 'inventory'
  | 'data-quality'
  | 'audit'
  | 'verification'
  | 'export';

const STATUS_META: Record<PeriodStatus, { label: string; tone: 'warn' | 'done'; line: string }> = {
  draft: { label: 'Draft', tone: 'warn', line: 'ready for internal review' },
  review: { label: 'In review', tone: 'warn', line: 'internal review in progress' },
  submitted: { label: 'Submitted', tone: 'warn', line: 'submitted for verification' },
  audit: { label: 'In audit', tone: 'warn', line: 'external audit in progress' },
  verified: { label: 'Verified ✓', tone: 'done', line: 'independently verified' },
  locked: { label: 'Locked', tone: 'done', line: 'locked for the record' },
};

/** tonnes, calm: integers once real, decimals only while tiny */
function tonnes(kg: number): string {
  const t = kg / 1000;
  if (t >= 100) return Math.round(t).toLocaleString();
  if (t >= 1) return t.toFixed(1);
  return t.toFixed(2);
}

export default function ReportsPage() {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const { selectedPeriodId } = usePeriodStore();

  const [activeTab, setActiveTab] = useState<ReportTab>('summary');

  const { data: periods, isLoading: periodsLoading } = usePeriods();
  // Only trust the persisted period if it belongs to THIS org's list.
  const activePeriodId = periods?.find((p) => p.id === selectedPeriodId)?.id ?? periods?.[0]?.id ?? '';
  const activePeriod = periods?.find((p) => p.id === activePeriodId);

  const { data: summary, isLoading: summaryLoading } = useReportSummary(activePeriodId);
  const { data: activities } = useActivities(activePeriodId);
  const { data: sites } = useSites();

  // Deep-report queries — fetched only when their tab opens
  const { data: ghgInventory, isLoading: inventoryLoading } = useQuery({
    queryKey: ['ghg-inventory', activePeriodId],
    queryFn: () => api.getGHGInventoryReport(activePeriodId),
    enabled: !!activePeriodId && activeTab === 'inventory',
  });

  const { data: dataQuality, isLoading: qualityLoading } = useQuery({
    queryKey: ['data-quality', activePeriodId],
    queryFn: () => api.getDataQualitySummary(activePeriodId),
    enabled: !!activePeriodId && activeTab === 'data-quality',
  });

  const { data: auditPackage, isLoading: auditLoading } = useQuery({
    queryKey: ['audit-package', activePeriodId],
    queryFn: () => api.getAuditPackage(activePeriodId),
    enabled: !!activePeriodId && activeTab === 'audit',
  });

  const { data: cdpExport, isLoading: cdpLoading } = useQuery({
    queryKey: ['cdp-export', activePeriodId],
    queryFn: () => api.exportCDP(activePeriodId),
    enabled: !!activePeriodId && activeTab === 'export',
  });

  const { data: esrsExport, isLoading: esrsLoading } = useQuery({
    queryKey: ['esrs-export', activePeriodId],
    queryFn: () => api.exportESRSE1(activePeriodId),
    enabled: !!activePeriodId && activeTab === 'export',
  });

  const { data: statusHistory } = useQuery({
    queryKey: ['status-history', activePeriodId],
    queryFn: () => api.getPeriodStatusHistory(activePeriodId),
    enabled: !!activePeriodId && activeTab === 'verification',
  });

  // Verification workflow mutations
  const transitionMutation = useMutation({
    mutationFn: (newStatus: PeriodStatus) => api.transitionPeriodStatus(activePeriodId, newStatus),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['periods'] });
      queryClient.invalidateQueries({ queryKey: ['status-history', activePeriodId] });
    },
  });

  const verifyMutation = useMutation({
    mutationFn: (data: {
      assurance_level: AssuranceLevel;
      verified_by: string;
      verification_statement: string;
    }) => api.verifyPeriod(activePeriodId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['periods'] });
      queryClient.invalidateQueries({ queryKey: ['status-history', activePeriodId] });
    },
  });

  const lockMutation = useMutation({
    mutationFn: () => api.lockPeriod(activePeriodId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['periods'] });
      queryClient.invalidateQueries({ queryKey: ['status-history', activePeriodId] });
    },
  });

  const isLoading = periodsLoading || summaryLoading;
  const total = summary?.total_co2e_kg ?? 0;
  const pct = (kg: number) => (total > 0 ? `${Math.round((kg / total) * 100)}%` : '0%');
  const hasData = !!summary && (activities?.length ?? 0) > 0;
  const status = activePeriod ? STATUS_META[activePeriod.status] : STATUS_META.draft;

  const handleExportCSV = async () => {
    try {
      await api.downloadReportExport('csv', activePeriodId);
      toast.success('CSV report downloaded');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to export CSV');
    }
  };

  const handleExportPDF = async () => {
    try {
      await api.downloadReportExport('pdf', activePeriodId);
      toast.success('PDF report downloaded');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to export PDF');
    }
  };

  const handleExportCDP = async () => {
    if (cdpExport) {
      downloadFile(
        JSON.stringify(cdpExport, null, 2),
        `cdp-export-${activePeriod?.name?.replace(/\s+/g, '-') || 'report'}.json`,
        'application/json'
      );
    }
  };

  const handleExportESRS = async () => {
    if (esrsExport) {
      downloadFile(
        JSON.stringify(esrsExport, null, 2),
        `esrs-e1-export-${activePeriod?.name?.replace(/\s+/g, '-') || 'report'}.json`,
        'application/json'
      );
    }
  };

  const categoryColumns: CanopyColumn<CategorySummary>[] = [
    {
      key: 'category',
      header: 'Category',
      render: (c) => categoryNames[c.category_code] || c.category_code,
    },
    { key: 'scope', header: 'Scope', render: (c) => c.scope },
    { key: 'activities', header: 'Activities', align: 'right', render: (c) => c.activity_count },
    {
      key: 'tonnes',
      header: 't CO₂e',
      align: 'right',
      render: (c) => <CellValue>{tonnes(c.total_co2e_kg)}</CellValue>,
    },
    {
      key: 'share',
      header: 'Share',
      align: 'right',
      render: (c) => <ShareBar pct={total > 0 ? (c.total_co2e_kg / total) * 100 : 0} />,
    },
  ];

  const activityColumns = (withCategory: boolean): CanopyColumn<NonNullable<typeof activities>[number]>[] => [
    {
      key: 'description',
      header: 'Description',
      render: (i) => i.activity.description,
    },
    ...(withCategory
      ? [
          {
            key: 'category',
            header: 'Category',
            render: (i) => categoryNames[i.activity.category_code] || i.activity.category_code,
          } as CanopyColumn<NonNullable<typeof activities>[number]>,
        ]
      : [
          {
            key: 'scope',
            header: 'Scope',
            render: (i) => i.activity.scope,
          } as CanopyColumn<NonNullable<typeof activities>[number]>,
        ]),
    {
      key: 'quantity',
      header: 'Quantity',
      align: 'right',
      render: (i) => `${i.activity.quantity.toLocaleString()} ${i.activity.unit}`,
    },
    {
      key: 'co2e',
      header: 't CO₂e',
      align: 'right',
      render: (i) => <CellValue>{tonnes(i.emission?.co2e_kg || 0)}</CellValue>,
    },
  ];

  return (
    <AppShell>
      <PageHead
        title={`Reports — ${activePeriod?.name || '…'}`}
        subtitle="Everything here updates live from your data. Verify when you're ready."
      />
      <Link
        href="/methodology"
        className="-mt-3 mb-4 inline-block text-[12.5px] font-semibold text-cy-accent hover:underline"
      >
        How every number is calculated — methodology →
      </Link>

      {isLoading && (
        <div className="flex items-center justify-center py-20" role="status" aria-live="polite">
          <Loader2 className="h-6 w-6 animate-spin text-cy-accent" aria-hidden="true" />
          <span className="ml-3 text-[13px] text-cy-muted">Loading your report…</span>
        </div>
      )}

      {!isLoading && (
        <>
          <PillTabs
            className="mb-5"
            value={activeTab}
            onChange={(id) => setActiveTab(id as ReportTab)}
            tabs={[
              // Report views — what the numbers say
              { id: 'summary', label: 'Summary' },
              { id: 'data-quality', label: 'Data quality' },
              { id: 'by-scope', label: 'By scope' },
              { id: 'by-site', label: 'By site' },
              { id: 'inventory', label: 'GHG Inventory' },
              // Process tabs — what you do with the report
              { id: 'audit', label: 'Audit', tone: 'warn', dividerBefore: true },
              { id: 'verification', label: 'Verification', tone: 'warn' },
              { id: 'export', label: 'Export', tone: 'warn' },
            ]}
          />

          {/* No-data guide for the data tabs */}
          {!hasData && ['summary', 'by-scope', 'by-site'].includes(activeTab) && (
            <FocusCard
              kicker="Reports"
              title="No data to report yet"
              body="Your reports build themselves from your activity data. Bring data in and this page comes alive."
              action={{ label: 'Open the Data hub', href: '/hub' }}
              skip={{ label: 'or add one activity', href: '/activities?add=1' }}
            />
          )}

          {activeTab === 'summary' && hasData && summary && (
            <>
              <Surface className="mb-4">
                <PanelLabel>Footprint</PanelLabel>
                <StatCells
                  cells={[
                    { label: 'Total', value: tonnes(total), sub: 't CO₂e' },
                    {
                      label: 'Scope 1',
                      value: tonnes(summary.scope_1_co2e_kg),
                      sub: pct(summary.scope_1_co2e_kg),
                      scope: 1,
                    },
                    {
                      label: 'Scope 2',
                      value: tonnes(summary.scope_2_co2e_kg),
                      sub: pct(summary.scope_2_co2e_kg),
                      scope: 2,
                    },
                    {
                      label: 'Scope 3 (incl. WTT)',
                      value: tonnes(summary.scope_3_co2e_kg),
                      sub: pct(summary.scope_3_co2e_kg),
                      scope: 3,
                    },
                  ]}
                />
              </Surface>
              <Surface className="mb-4">
                <PanelLabel>By category</PanelLabel>
                <DataTable
                  columns={categoryColumns}
                  rows={[...summary.by_category].sort((a, b) => b.total_co2e_kg - a.total_co2e_kg)}
                  rowKey={(c) => `${c.scope}-${c.category_code}`}
                />
              </Surface>
            </>
          )}

          {activeTab === 'by-scope' && hasData && (
            <div className="space-y-4">
              {[1, 2, 3].map((scope) => {
                const scopeActivities = (activities ?? []).filter((i) => i.activity.scope === scope);
                const scopeTotal = scopeActivities.reduce(
                  (sum, i) => sum + (i.emission?.co2e_kg || 0),
                  0
                );
                return (
                  <Surface key={scope}>
                    <PanelLabel>
                      Scope {scope} · {tonnes(scopeTotal)} t CO₂e
                    </PanelLabel>
                    {scopeActivities.length === 0 ? (
                      <p className="text-[12.5px] text-cy-muted">
                        No Scope {scope} activities recorded.
                      </p>
                    ) : (
                      <DataTable
                        columns={activityColumns(true)}
                        rows={scopeActivities}
                        rowKey={(i) => i.activity.id}
                      />
                    )}
                  </Surface>
                );
              })}
            </div>
          )}

          {activeTab === 'by-site' && hasData && (
            <div className="space-y-4">
              {Object.entries(
                (activities ?? []).reduce(
                  (acc, item) => {
                    const siteId = item.activity.site_id || 'unassigned';
                    (acc[siteId] ??= []).push(item);
                    return acc;
                  },
                  {} as Record<string, NonNullable<typeof activities>>
                )
              ).map(([siteId, siteActivities]) => {
                const site = sites?.find((s) => s.id === siteId);
                const siteTotal = siteActivities.reduce(
                  (sum, i) => sum + (i.emission?.co2e_kg || 0),
                  0
                );
                return (
                  <Surface key={siteId}>
                    <PanelLabel>
                      {site?.name || 'Unassigned'}
                      {site?.country_code ? ` · ${site.country_code}` : ''} · {tonnes(siteTotal)} t CO₂e
                    </PanelLabel>
                    <DataTable
                      columns={activityColumns(false)}
                      rows={siteActivities}
                      rowKey={(i) => i.activity.id}
                    />
                  </Surface>
                );
              })}
            </div>
          )}

          {activeTab === 'inventory' &&
            (inventoryLoading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="h-6 w-6 animate-spin text-cy-accent" />
                <span className="ml-3 text-[13px] text-cy-muted">Building the GHG inventory…</span>
              </div>
            ) : ghgInventory ? (
              <GHGInventoryReport report={ghgInventory} />
            ) : (
              <Surface tint="warn" className="max-w-[560px]">
                <p className="text-[13.5px] text-cy-ink">
                  The GHG inventory report didn’t generate — try again in a moment.
                </p>
              </Surface>
            ))}

          {activeTab === 'data-quality' &&
            (qualityLoading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="h-6 w-6 animate-spin text-cy-accent" />
                <span className="ml-3 text-[13px] text-cy-muted">Scoring your data quality…</span>
              </div>
            ) : dataQuality ? (
              <DataQualityReport report={dataQuality} />
            ) : (
              <Surface tint="warn" className="max-w-[560px]">
                <p className="text-[13.5px] text-cy-ink">
                  The data quality report didn’t generate — try again in a moment.
                </p>
              </Surface>
            ))}

          {activeTab === 'audit' &&
            (auditLoading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="h-6 w-6 animate-spin text-cy-accent" />
                <span className="ml-3 text-[13px] text-cy-muted">Assembling the audit package…</span>
              </div>
            ) : auditPackage ? (
              <AuditPackageView auditPackage={auditPackage} />
            ) : (
              <Surface tint="warn" className="max-w-[560px]">
                <p className="text-[13.5px] text-cy-ink">
                  The audit package didn’t generate — try again in a moment.
                </p>
              </Surface>
            ))}

          {activeTab === 'export' && (
            <ExportOptions
              cdpData={cdpExport}
              esrsData={esrsExport}
              cdpLoading={cdpLoading}
              esrsLoading={esrsLoading}
              onExportCDP={handleExportCDP}
              onExportESRS={handleExportESRS}
            />
          )}

          {activeTab === 'verification' && activePeriod && (
            <>
              <VerificationWorkflow
                period={activePeriod}
                statusHistory={statusHistory}
                userRole={user?.role as 'admin' | 'editor' | 'viewer' | undefined}
                onTransition={async (newStatus) => {
                  await transitionMutation.mutateAsync(newStatus);
                }}
                onVerify={async (data) => {
                  await verifyMutation.mutateAsync(data);
                }}
                onLock={async () => {
                  await lockMutation.mutateAsync();
                }}
              />
              <VerifierInvitePanel
                periodId={activePeriodId}
                canManage={
                  user?.role === 'admin' || user?.role === 'super_admin'
                }
              />
            </>
          )}

          {/* The finish line — on every tab */}
          {activePeriod && (
            <FinishBar
              className="mt-4"
              status={{ label: status.label, tone: status.tone }}
              summary={`${activities?.length ?? 0} activities · ${status.line}`}
              action={
                activeTab !== 'verification' && !['verified', 'locked'].includes(activePeriod.status)
                  ? { label: 'Start verification', onClick: () => setActiveTab('verification') }
                  : undefined
              }
              exports={[
                { label: 'PDF', onClick: handleExportPDF },
                { label: 'CSV', onClick: handleExportCSV },
              ]}
            />
          )}
        </>
      )}
    </AppShell>
  );
}
