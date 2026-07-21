'use client';

import { Fragment, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { AppShell } from '@/components/layout';
import { useEntitlementFlags } from '@/components/layout/TeaserGate';
import { Surface, PanelLabel, PageHead } from '@/components/canopy';
import { Button, Input, Select } from '@/components/ui';
import {
  useProduct,
  useCreateProductInput,
  useDeleteProductInput,
  useComputeFootprint,
  useFinalizeFootprint,
  useSupplierPcfs,
} from '@/hooks/useProducts';
import { useEmissionFactors, usePeriods } from '@/hooks/useEmissions';
import { usePeriodStore } from '@/stores/period';
import { num, cn } from '@/lib/utils';
import {
  CRADLE_TO_GATE_MODULES,
  EN15804_MODULE_OPTIONS,
  INPUT_TYPES,
  INPUT_TYPE_LABEL,
  STAGE_META,
  UNIT_SHORT,
} from '@/lib/pcf';
import type { LcaResults, PcfFootprint, PcfInputType, PcfLineItem } from '@/lib/api';
import {
  ArrowLeft,
  Calculator,
  Download,
  FileCheck2,
  Loader2,
  Lock,
  Plus,
  Trash2,
} from 'lucide-react';

const EMPTY_LINE = {
  input_type: 'purchased_material' as PcfInputType,
  name: '',
  quantity_per_unit: '',
  unit: 'kg',
  activity_key: '',
  supplier_pcf_id: '',
  region: '',
  en15804_module: '',
};

/** Values span 12 orders of magnitude (kg CO2 eq … CTUh) — format smart. */
function fmtLcaValue(v: number): string {
  if (v === 0) return '—';
  const a = Math.abs(v);
  if (a >= 100) return v.toFixed(1);
  if (a >= 0.01) return v.toFixed(3);
  return v.toExponential(2);
}

/** Stacked single-bar breakdown of the footprint by EN 15804 stage —
 * same idiom as the ingest page's InventoryQuality bar. */
function StageBar({ breakdown }: { breakdown: Record<string, number> }) {
  const total = Object.values(breakdown).reduce((a, b) => a + b, 0);
  if (!total) return null;
  const stages = Object.entries(breakdown).sort(([a], [b]) => a.localeCompare(b));
  return (
    <div>
      <div className="flex h-2.5 overflow-hidden rounded-full">
        {stages.map(([stage, value]) => (
          <div
            key={stage}
            className={cn(STAGE_META[stage]?.color ?? 'bg-cy-faint')}
            style={{ width: `${(value / total) * 100}%` }}
            title={`${STAGE_META[stage]?.label ?? stage}: ${value.toFixed(2)} kg CO2e`}
          />
        ))}
      </div>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
        {stages.map(([stage, value]) => (
          <span key={stage} className="flex items-center gap-1.5 text-[11.5px] text-cy-muted">
            <span className={cn('inline-block h-2 w-2 rounded-full', STAGE_META[stage]?.color ?? 'bg-cy-faint')} />
            {STAGE_META[stage]?.label ?? stage}
            <span className="tabular-nums text-cy-faint">
              {value.toFixed(2)} kg · {((value / total) * 100).toFixed(0)}%
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}

/** Expandable derivation story for one computed BOM line (RowStory idiom). */
function LineStory({ line }: { line: PcfLineItem }) {
  return (
    <div className="rounded-[10px] bg-cy-row/60 px-3 py-2.5 text-[12px] text-cy-muted">
      {line.factor && (
        <div className="mb-1.5 flex flex-wrap gap-x-4 gap-y-1">
          <span>
            <span className="font-semibold text-cy-ink">{line.factor.display_name}</span>
            {' · '}{line.factor.source}
            {line.factor.region ? ` · ${line.factor.region}` : ''}
            {line.factor.year ? ` · ${line.factor.year}` : ''}
          </span>
          <span className="tabular-nums">
            {line.factor.value} {line.factor.unit}
          </span>
          {line.factor.confidence && (
            <span className="capitalize">confidence: {line.factor.confidence}</span>
          )}
        </div>
      )}
      {line.formula && <div className="font-mono text-[11.5px]">{line.formula}</div>}
      {line.warnings.length > 0 && (
        <ul className="mt-1.5 list-disc pl-4 text-cy-warn">
          {line.warnings.map((w, i) => (
            <li key={i}>{w}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** LCA-lite results — EF 3.1 indicator × EN 15804 module matrix (the EN
 * 15804 results table an EPD needs, screening-grade). */
function LcaMatrix({ lca }: { lca: LcaResults }) {
  const [showCoverage, setShowCoverage] = useState(false);
  const fullCoverage = lca.rows.every((r) => r.covered_lines === r.total_lines);

  return (
    <Surface padding="panel" className="mt-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <PanelLabel>LCA-lite — environmental profile</PanelLabel>
          <p className="mt-0.5 text-[12px] text-cy-muted">
            EF 3.1 impact categories × EN 15804 lifecycle modules
            <span className="ml-2 rounded-full bg-cy-row px-2 py-0.5 text-[10.5px] font-semibold text-cy-muted">
              screening-grade
            </span>
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowCoverage(!showCoverage)}
          className="cursor-pointer text-[12px] font-semibold text-cy-accent hover:underline"
        >
          {showCoverage ? 'Hide data coverage' : 'Data coverage'}
        </button>
      </div>

      {lca.warnings.length > 0 && (
        <ul className="mb-3 list-disc pl-4 text-[12px] text-cy-warn">
          {lca.warnings.map((w, i) => (
            <li key={i}>{w}</li>
          ))}
        </ul>
      )}

      {showCoverage && (
        <div className="mb-3 rounded-[10px] bg-cy-row/60 px-3 py-2.5 text-[12px] text-cy-muted">
          {lca.line_coverage.map((c) => (
            <div key={c.input_id} className="flex flex-wrap gap-x-2 py-0.5">
              <span className="font-semibold text-cy-ink">{c.name}</span>
              <span>· {c.en15804_module}</span>
              {c.dataset ? (
                <span>
                  · {c.dataset}
                  {c.dataset_region ? ` (${c.dataset_region})` : ''} ·{' '}
                  {c.indicators_covered}/16 indicators
                </span>
              ) : (
                <span className="text-cy-warn">· {c.note ?? 'climate only'}</span>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-[12.5px]">
          <thead>
            <tr>
              <th className="py-2 pr-3 text-left text-[10.5px] font-bold uppercase tracking-[0.07em] text-cy-faint">
                Impact category
              </th>
              {lca.modules.map((m) => (
                <th
                  key={m}
                  className="py-2 pr-3 text-right text-[10.5px] font-bold uppercase tracking-[0.07em] text-cy-faint"
                  title={
                    (STAGE_META[m]?.label ?? m) +
                    (CRADLE_TO_GATE_MODULES.has(m) ? ' (cradle-to-gate)' : ' (beyond gate)')
                  }
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
              {!fullCoverage && (
                <th className="py-2 pl-3 text-right text-[10.5px] font-bold uppercase tracking-[0.07em] text-cy-faint">
                  Coverage
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {lca.rows.map((row) => {
              const partial = row.covered_lines < row.total_lines;
              return (
                <tr key={row.code} className="border-t border-cy-row">
                  <td className="max-w-[15rem] py-2 pr-3 font-semibold text-cy-ink">
                    {row.name}
                  </td>
                  {lca.modules.map((m) => (
                    <td key={m} className="py-2 pr-3 text-right tabular-nums text-cy-muted">
                      {fmtLcaValue(row.by_module[m] ?? 0)}
                    </td>
                  ))}
                  <td className="py-2 pr-3 text-right tabular-nums font-semibold text-cy-ink">
                    {fmtLcaValue(row.total)}
                  </td>
                  <td className="py-2 text-[11.5px] text-cy-faint">{row.unit}</td>
                  {!fullCoverage && (
                    <td
                      className={cn(
                        'py-2 pl-3 text-right tabular-nums text-[11.5px]',
                        partial ? 'text-cy-warn' : 'text-cy-accent'
                      )}
                      title={
                        partial
                          ? `No EF 3.1 data for: ${row.gap_lines.join(', ')}`
                          : 'All BOM lines covered'
                      }
                    >
                      {row.covered_lines}/{row.total_lines}
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="mt-3 text-[11.5px] text-cy-faint">{lca.note}</p>
    </Surface>
  );
}

function FootprintResults({
  footprint,
  declaredUnit,
  onFinalize,
  onExport,
  finalizing,
  exporting,
  isTrialing,
}: {
  footprint: PcfFootprint;
  declaredUnit: string;
  onFinalize: () => void;
  onExport: () => void;
  finalizing: boolean;
  exporting: boolean;
  isTrialing: boolean;
}) {
  const [openLine, setOpenLine] = useState<string | null>(null);
  const unitShort = UNIT_SHORT[declaredUnit] ?? declaredUnit;
  const lines = footprint.line_items ?? [];

  return (
    <Surface padding="panel">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <PanelLabel>Latest footprint</PanelLabel>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-[28px] font-[650] tabular-nums text-cy-ink">
              {num(footprint.total_kgco2e_per_unit).toFixed(2)}
            </span>
            <span className="text-[13px] text-cy-muted">kg CO2e / {unitShort}</span>
            <span
              className={cn(
                'ml-1 rounded-full px-2 py-0.5 text-[11px] font-semibold',
                footprint.status === 'final'
                  ? 'bg-cy-accent-soft text-cy-accent'
                  : 'bg-cy-warn-soft text-cy-warn'
              )}
            >
              {footprint.status === 'final' ? 'Final' : 'Draft'}
            </span>
          </div>
          <div className="mt-1 flex flex-wrap gap-x-4 text-[12px] text-cy-muted">
            <span>Boundary: cradle-to-gate</span>
            {footprint.primary_data_share != null && (
              <span>
                Primary data:{' '}
                <span className="font-semibold text-cy-accent tabular-nums">
                  {footprint.primary_data_share.toFixed(1)}%
                </span>
              </span>
            )}
            {footprint.biogenic_kgco2e_per_unit != null && (
              <span>Biogenic (reported separately): {num(footprint.biogenic_kgco2e_per_unit).toFixed(3)} kg</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {footprint.status === 'draft' && (
            <Button variant="secondary" size="sm" onClick={onFinalize} isLoading={finalizing}
              leftIcon={<FileCheck2 className="h-3.5 w-3.5" />}>
              Finalize
            </Button>
          )}
          <Button
            size="sm"
            onClick={onExport}
            isLoading={exporting}
            leftIcon={isTrialing ? <Lock className="h-3.5 w-3.5" /> : <Download className="h-3.5 w-3.5" />}
            title={isTrialing ? 'Exports unlock on a plan — results stay on screen during the trial' : 'PACT Data Exchange JSON'}
          >
            {isTrialing ? 'Export (locked)' : 'Export PACT JSON'}
          </Button>
        </div>
      </div>

      {footprint.stage_breakdown && <StageBar breakdown={footprint.stage_breakdown} />}

      {lines.length > 0 && (
        <table className="mt-4 w-full text-[13px]">
          <thead>
            <tr>
              {['', 'Input', 'Stage', 'Quantity', 'Grounding', 'kg CO2e'].map((h, i) => (
                <th key={i} className="py-2 pr-3 text-left text-[10.5px] font-bold uppercase tracking-[0.07em] text-cy-faint">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {lines.map((line) => {
              const isOpen = openLine === line.input_id;
              const gap = line.status === 'gap';
              return (
                <Fragment key={line.input_id}>
                  <tr className="border-t border-cy-row align-top">
                    <td className="py-2.5 pr-3">
                      <span
                        className={cn(
                          'inline-block h-2 w-2 rounded-full',
                          gap ? 'bg-error' : line.is_primary_data ? 'bg-cy-accent' : 'bg-cy-warn'
                        )}
                        title={gap ? 'Gap — no factor' : line.is_primary_data ? 'Primary data' : 'Secondary factor'}
                      />
                    </td>
                    <td className="max-w-[16rem] py-2.5 pr-3 text-cy-ink">
                      <div className="truncate font-semibold">{line.name}</div>
                      <button
                        type="button"
                        onClick={() => setOpenLine(isOpen ? null : line.input_id)}
                        aria-expanded={isOpen}
                        className="mt-0.5 block max-w-full cursor-pointer truncate text-left text-[11.5px] text-cy-faint hover:text-cy-ink"
                      >
                        <span aria-hidden className="mr-1 inline-block text-[9px]">{isOpen ? '▾' : '▸'}</span>
                        {gap ? line.warnings[0] ?? 'Why is this a gap?' : 'How this number was calculated'}
                      </button>
                    </td>
                    <td className="py-2.5 pr-3 text-cy-muted">{line.en15804_module}</td>
                    <td className="py-2.5 pr-3 tabular-nums text-cy-muted">
                      {line.quantity_per_unit} {line.unit}
                    </td>
                    <td className="py-2.5 pr-3 text-[12px] text-cy-muted">
                      {line.factor ? (
                        <>
                          <span className="font-mono text-[11.5px]">{line.factor.display_name}</span>
                          <div className="text-[11px] text-cy-faint">{line.factor.source}</div>
                        </>
                      ) : (
                        <span className="text-error">No factor</span>
                      )}
                    </td>
                    <td className="py-2.5 tabular-nums font-semibold text-cy-ink">
                      {line.co2e_kg.toFixed(3)}
                    </td>
                  </tr>
                  {isOpen && (
                    <tr className="border-t border-cy-row/50">
                      <td />
                      <td colSpan={5} className="pb-3 pr-3 pt-0">
                        <LineStory line={line} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      )}
    </Surface>
  );
}

function ProductDetailContent() {
  const params = useParams<{ id: string }>();
  const productId = params.id;

  const { data: product, isLoading } = useProduct(productId);
  const { data: supplierPcfs } = useSupplierPcfs();
  const { data: factors } = useEmissionFactors();
  const { data: periods } = usePeriods();
  const { selectedPeriodId } = usePeriodStore();
  const activePeriodId = periods?.find((p) => p.id === selectedPeriodId)?.id ?? periods?.[0]?.id;

  const createInput = useCreateProductInput(productId);
  const deleteInput = useDeleteProductInput(productId);
  const compute = useComputeFootprint(productId);
  const finalize = useFinalizeFootprint(productId);
  const { isTrialing } = useEntitlementFlags();

  const [line, setLine] = useState(EMPTY_LINE);
  const [computeError, setComputeError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  const factorOptions = useMemo(() => {
    const seen = new Set<string>();
    return (factors ?? []).filter((f) => {
      if (!f.activity_key || seen.has(f.activity_key)) return false;
      seen.add(f.activity_key);
      return true;
    });
  }, [factors]);

  const unitShort = product ? (UNIT_SHORT[product.declared_unit] ?? product.declared_unit) : '';
  const latest = product?.footprints?.[0] ?? null;

  const addLine = async () => {
    if (!line.name.trim() || !line.quantity_per_unit) return;
    await createInput.mutateAsync({
      input_type: line.input_type,
      name: line.name.trim(),
      quantity_per_unit: line.quantity_per_unit,
      unit: line.unit.trim() || 'kg',
      activity_key: line.input_type === 'supplier_pcf' ? null : line.activity_key.trim() || null,
      supplier_pcf_id: line.input_type === 'supplier_pcf' ? line.supplier_pcf_id || null : null,
      region: line.region.trim() || null,
      en15804_module: line.en15804_module || null,
    });
    setLine(EMPTY_LINE);
  };

  const runCompute = async () => {
    if (!activePeriodId) return;
    setComputeError(null);
    try {
      await compute.mutateAsync(activePeriodId);
    } catch (err) {
      setComputeError(err instanceof Error ? err.message : 'Computation failed');
    }
  };

  const runExport = async () => {
    if (!product || !latest) return;
    setExporting(true);
    try {
      await import('@/lib/api').then(({ api }) =>
        api.downloadPactExport(
          product.id,
          latest.id,
          `${(product.sku || product.name).replace(/\s+/g, '-')}-pcf-pact.json`
        )
      );
    } catch {
      // 402 surfaces via the global limit-reached modal
    } finally {
      setExporting(false);
    }
  };

  if (isLoading || !product) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-cy-accent" />
      </div>
    );
  }

  return (
    <>
      <Link
        href="/products"
        className="mb-3 inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-cy-muted hover:text-cy-ink"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> All products
      </Link>
      <PageHead
        title={product.name}
        subtitle={`Per ${num(product.declared_unit_amount)} ${unitShort}${product.sku ? ` · ${product.sku}` : ''}${product.cn_code ? ` · CN ${product.cn_code}` : ''}`}
      />

      {/* BOM editor */}
      <Surface padding="panel" className="mb-4">
        <div className="mb-3 flex items-center justify-between">
          <PanelLabel>Bill of materials — per {unitShort} of product</PanelLabel>
          <Button
            size="sm"
            onClick={runCompute}
            disabled={!product.inputs.length || !activePeriodId || compute.isPending}
            isLoading={compute.isPending}
            leftIcon={<Calculator className="h-3.5 w-3.5" />}
          >
            Compute footprint
          </Button>
        </div>
        {computeError && <p className="mb-2 text-[12.5px] text-error">{computeError}</p>}

        {product.inputs.length > 0 && (
          <table className="mb-3 w-full text-[13px]">
            <thead>
              <tr>
                {['Type', 'Input', 'Quantity', 'Grounding', 'Stage', ''].map((h, i) => (
                  <th key={i} className="py-2 pr-3 text-left text-[10.5px] font-bold uppercase tracking-[0.07em] text-cy-faint">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {product.inputs.map((i) => {
                const spcf = supplierPcfs?.find((s) => s.id === i.supplier_pcf_id);
                return (
                  <tr key={i.id} className="border-t border-cy-row">
                    <td className="py-2.5 pr-3 text-cy-muted">{INPUT_TYPE_LABEL[i.input_type]}</td>
                    <td className="py-2.5 pr-3 font-semibold text-cy-ink">{i.name}</td>
                    <td className="py-2.5 pr-3 tabular-nums text-cy-muted">
                      {num(i.quantity_per_unit)} {i.unit}
                    </td>
                    <td className="py-2.5 pr-3 text-[12px] text-cy-muted">
                      {i.input_type === 'supplier_pcf' ? (
                        spcf ? `${spcf.supplier_name} · ${num(spcf.pcf_value).toFixed(3)} kg CO2e/${spcf.unit}` : 'Supplier PCF'
                      ) : i.activity_key ? (
                        <span className="font-mono text-[11.5px]">{i.activity_key}</span>
                      ) : (
                        <span className="text-cy-warn">No factor yet</span>
                      )}
                      {i.region && <span className="ml-1 text-cy-faint">· {i.region}</span>}
                    </td>
                    <td className="py-2.5 pr-3 text-cy-muted">{i.en15804_module}</td>
                    <td className="py-2.5 text-right">
                      <button
                        onClick={() => deleteInput.mutate(i.id)}
                        className="cursor-pointer text-cy-faint hover:text-error"
                        aria-label={`Remove ${i.name}`}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}

        {/* Add-line row */}
        <div className="rounded-[10px] bg-cy-row/60 p-3">
          <div className="grid grid-cols-2 gap-2 lg:grid-cols-7">
            <Select
              value={line.input_type}
              onChange={(e) => setLine({ ...line, input_type: e.target.value as PcfInputType })}
              options={INPUT_TYPES.map((t) => ({ value: t.value, label: t.label }))}
            />
            <Input
              placeholder="Input name (e.g. Steel scrap)"
              value={line.name}
              onChange={(e) => setLine({ ...line, name: e.target.value })}
            />
            <Input
              placeholder="Qty per unit"
              type="number"
              value={line.quantity_per_unit}
              onChange={(e) => setLine({ ...line, quantity_per_unit: e.target.value })}
            />
            <Input
              placeholder="Unit (kg, kWh, tkm…)"
              value={line.unit}
              onChange={(e) => setLine({ ...line, unit: e.target.value })}
            />
            {line.input_type === 'supplier_pcf' ? (
              <Select
                value={line.supplier_pcf_id}
                onChange={(e) => setLine({ ...line, supplier_pcf_id: e.target.value })}
                options={[
                  { value: '', label: 'Pick supplier PCF…' },
                  ...(supplierPcfs ?? []).map((s) => ({
                    value: s.id,
                    label: `${s.supplier_name} — ${s.product_name}`,
                  })),
                ]}
              />
            ) : (
              <>
                <Input
                  placeholder="Factor key (type to search)"
                  list="pcf-factor-keys"
                  value={line.activity_key}
                  onChange={(e) => setLine({ ...line, activity_key: e.target.value })}
                />
                <datalist id="pcf-factor-keys">
                  {factorOptions.map((f) => (
                    <option key={f.activity_key} value={f.activity_key}>
                      {f.display_name}
                    </option>
                  ))}
                </datalist>
              </>
            )}
            <Select
              value={line.en15804_module}
              onChange={(e) => setLine({ ...line, en15804_module: e.target.value })}
              options={[{ value: '', label: 'Stage: auto' }, ...EN15804_MODULE_OPTIONS]}
              title="EN 15804 lifecycle module — auto picks by input type; A1-A3 = cradle-to-gate"
            />
            <Button
              size="sm"
              onClick={addLine}
              disabled={
                !line.name.trim() ||
                !line.quantity_per_unit ||
                (line.input_type === 'supplier_pcf' && !line.supplier_pcf_id) ||
                createInput.isPending
              }
              isLoading={createInput.isPending}
              leftIcon={<Plus className="h-3.5 w-3.5" />}
            >
              Add line
            </Button>
          </div>
          <p className="mt-2 text-[11.5px] text-cy-faint">
            Every line resolves through the same factor library and region precedence as your corporate
            inventory. Supplier PCF lines count as primary data. No supplier PCFs yet? Add them on the{' '}
            <Link href="/products" className="text-cy-accent hover:underline">products page</Link>.
          </p>
        </div>
      </Surface>

      {/* Results */}
      {latest ? (
        <>
          <FootprintResults
            footprint={latest}
            declaredUnit={product.declared_unit}
            onFinalize={() => finalize.mutate(latest.id)}
            onExport={runExport}
            finalizing={finalize.isPending}
            exporting={exporting}
            isTrialing={isTrialing}
          />
          {latest.lca_results && <LcaMatrix lca={latest.lca_results} />}
        </>
      ) : (
        <Surface padding="panel">
          <p className="text-[13px] text-cy-muted">
            Add BOM lines and hit <span className="font-semibold text-cy-ink">Compute footprint</span> —
            the cradle-to-gate result appears here with a full per-line derivation story.
          </p>
        </Surface>
      )}

      {/* History */}
      {product.footprints.length > 1 && (
        <Surface padding="panel" className="mt-4">
          <PanelLabel>Footprint history</PanelLabel>
          <table className="mt-2 w-full text-[13px]">
            <tbody>
              {product.footprints.map((f) => (
                <tr key={f.id} className="border-t border-cy-row first:border-t-0">
                  <td className="py-2 pr-3 text-cy-muted">
                    {new Date(f.created_at).toLocaleString()}
                  </td>
                  <td className="py-2 pr-3 tabular-nums font-semibold text-cy-ink">
                    {num(f.total_kgco2e_per_unit).toFixed(2)} kg CO2e/{unitShort}
                  </td>
                  <td className="py-2 pr-3">
                    <span
                      className={cn(
                        'rounded-full px-2 py-0.5 text-[11px] font-semibold',
                        f.status === 'final' ? 'bg-cy-accent-soft text-cy-accent' : 'bg-cy-warn-soft text-cy-warn'
                      )}
                    >
                      {f.status === 'final' ? 'Final' : 'Draft'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Surface>
      )}
    </>
  );
}

export default function ProductDetailPage() {
  return (
    <AppShell>
      <ProductDetailContent />
    </AppShell>
  );
}
