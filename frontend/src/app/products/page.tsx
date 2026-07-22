'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { AppShell } from '@/components/layout';
import { Surface, PanelLabel, PageHead } from '@/components/canopy';
import { Button, Input, Select, EmptyState } from '@/components/ui';
import { LoadSampleDataButton } from '@/components/LoadSampleDataButton';
import {
  useProducts,
  useCreateProduct,
  useSupplierPcfs,
  useCreateSupplierPcf,
  useUploadSupplierPact,
  useDeleteSupplierPcf,
} from '@/hooks/useProducts';
import { num, cn, formatQty } from '@/lib/utils';
import { DECLARED_UNITS, UNIT_SHORT } from '@/lib/pcf';
import { Package, Plus, Loader2, Upload, Trash2, X, FileCheck2 } from 'lucide-react';

function NewProductModal({ onClose }: { onClose: () => void }) {
  const router = useRouter();
  const createProduct = useCreateProduct();
  const [form, setForm] = useState({
    name: '',
    sku: '',
    declared_unit: 'kilogram',
    cn_code: '',
    category: '',
  });

  const submit = async () => {
    if (!form.name.trim()) return;
    const product = await createProduct.mutateAsync({
      name: form.name.trim(),
      sku: form.sku.trim() || null,
      declared_unit: form.declared_unit,
      cn_code: form.cn_code.trim() || null,
      category: form.category.trim() || null,
    });
    onClose();
    router.push(`/products/${product.id}`);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Surface padding="panel" className="w-full max-w-md">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-[16px] font-[650] text-cy-ink">New product</h2>
          <button onClick={onClose} className="cursor-pointer text-cy-faint hover:text-cy-ink" aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="space-y-3">
          <Input
            label="Product name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="e.g. Hot-rolled steel coil"
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="SKU (optional)"
              value={form.sku}
              onChange={(e) => setForm({ ...form, sku: e.target.value })}
              placeholder="HRC-1000"
            />
            <Select
              label="Declared unit"
              value={form.declared_unit}
              onChange={(e) => setForm({ ...form, declared_unit: e.target.value })}
              options={DECLARED_UNITS}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="CN code (CBAM link, optional)"
              value={form.cn_code}
              onChange={(e) => setForm({ ...form, cn_code: e.target.value })}
              placeholder="72083900"
            />
            <Input
              label="Category (optional)"
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
              placeholder="Steel products"
            />
          </div>
          <p className="text-[12px] text-cy-faint">
            The footprint is computed per declared unit (cradle-to-gate, ISO 14067 / PACT v3).
          </p>
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="ghost" onClick={onClose}>Cancel</Button>
            <Button
              onClick={submit}
              disabled={!form.name.trim() || createProduct.isPending}
              isLoading={createProduct.isPending}
            >
              Create product
            </Button>
          </div>
        </div>
      </Surface>
    </div>
  );
}

function SupplierPcfPanel() {
  const { data: supplierPcfs, isLoading } = useSupplierPcfs();
  const createSupplierPcf = useCreateSupplierPcf();
  const uploadPact = useUploadSupplierPact();
  const deleteSupplierPcf = useDeleteSupplierPcf();
  const [showAdd, setShowAdd] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [form, setForm] = useState({ supplier_name: '', product_name: '', pcf_value: '', unit: 'kilogram' });

  const handleFile = async (file: File) => {
    setUploadError(null);
    try {
      const payload = JSON.parse(await file.text());
      await uploadPact.mutateAsync(payload);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Could not read that file');
    }
  };

  const submitManual = async () => {
    await createSupplierPcf.mutateAsync({
      supplier_name: form.supplier_name.trim(),
      product_name: form.product_name.trim(),
      pcf_value: form.pcf_value,
      unit: form.unit,
    });
    setForm({ supplier_name: '', product_name: '', pcf_value: '', unit: 'kilogram' });
    setShowAdd(false);
  };

  return (
    <Surface padding="panel">
      <div className="mb-3 flex items-center justify-between">
        <PanelLabel>Supplier PCFs — primary data</PanelLabel>
        <div className="flex items-center gap-2">
          <label className="flex cursor-pointer items-center gap-1.5 rounded-full bg-cy-accent-soft px-3 py-1.5 text-[12.5px] font-semibold text-cy-accent hover:opacity-90">
            <Upload className="h-3.5 w-3.5" />
            Upload PACT JSON
            <input
              type="file"
              accept="application/json,.json"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
                e.target.value = '';
              }}
            />
          </label>
          <button
            onClick={() => setShowAdd((v) => !v)}
            className="cursor-pointer rounded-full px-3 py-1.5 text-[12.5px] font-semibold text-cy-muted hover:bg-cy-row hover:text-cy-ink"
          >
            {showAdd ? 'Close' : 'Add manually'}
          </button>
        </div>
      </div>
      <p className="mb-3 text-[12.5px] text-cy-muted">
        Footprints your suppliers hand you (PACT Data Exchange files or declared values). BOM lines
        that reference one count as primary data and lift your primary-data share.
      </p>
      {uploadError && <p className="mb-2 text-[12.5px] text-error">{uploadError}</p>}
      {showAdd && (
        <div className="mb-3 grid grid-cols-2 gap-2 rounded-[10px] bg-cy-row/60 p-3 sm:grid-cols-5">
          <Input placeholder="Supplier" value={form.supplier_name} onChange={(e) => setForm({ ...form, supplier_name: e.target.value })} />
          <Input placeholder="Their product" value={form.product_name} onChange={(e) => setForm({ ...form, product_name: e.target.value })} />
          <Input placeholder="kg CO2e per unit" type="number" value={form.pcf_value} onChange={(e) => setForm({ ...form, pcf_value: e.target.value })} />
          <Input placeholder="Unit (e.g. kilogram)" value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} />
          <Button
            size="sm"
            onClick={submitManual}
            disabled={!form.supplier_name.trim() || !form.product_name.trim() || !form.pcf_value || createSupplierPcf.isPending}
            isLoading={createSupplierPcf.isPending}
          >
            Save
          </Button>
        </div>
      )}
      {isLoading ? (
        <Loader2 className="h-4 w-4 animate-spin text-cy-accent" />
      ) : !supplierPcfs?.length ? (
        <p className="text-[12.5px] text-cy-faint">None yet — ask suppliers for their PACT PCF files.</p>
      ) : (
        <table className="w-full text-[13px]">
          <thead>
            <tr>
              {['Supplier', 'Product', 'PCF', 'Source', ''].map((h) => (
                <th key={h} className="py-2 pr-3 text-left text-[10.5px] font-bold uppercase tracking-[0.07em] text-cy-faint">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {supplierPcfs.map((s) => (
              <tr key={s.id} className="border-t border-cy-row">
                <td className="py-2.5 pr-3 font-semibold text-cy-ink">{s.supplier_name}</td>
                <td className="py-2.5 pr-3 text-cy-muted">{s.product_name}</td>
                <td className="py-2.5 pr-3 tabular-nums text-cy-muted">
                  {formatQty(s.pcf_value)} kg CO2e/{s.unit}
                </td>
                <td className="py-2.5 pr-3">
                  <span className={cn(
                    'rounded-full px-2 py-0.5 text-[11px] font-semibold',
                    s.source === 'pact_json' ? 'bg-cy-accent-soft text-cy-accent' : 'bg-cy-row text-cy-muted'
                  )}>
                    {s.source === 'pact_json' ? 'PACT file' : 'Declared'}
                  </span>
                </td>
                <td className="py-2.5 text-right">
                  <button
                    onClick={() => deleteSupplierPcf.mutate(s.id)}
                    className="cursor-pointer text-cy-faint hover:text-error"
                    aria-label={`Delete ${s.product_name}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Surface>
  );
}

export default function ProductsPage() {
  const { data: products, isLoading } = useProducts();
  const [showNew, setShowNew] = useState(false);

  return (
    <AppShell>
      <PageHead
        title="Products — Product Carbon Footprint"
        subtitle="Cradle-to-gate footprints per ISO 14067, exchanged in the PACT v3 format"
      />
      <div className="mb-4 flex items-center justify-between">
        <span className="rounded-full bg-primary/10 px-2.5 py-1 text-[11px] font-semibold text-primary">Beta</span>
        <Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => setShowNew(true)}>
          New product
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-cy-accent" />
        </div>
      ) : !products?.length ? (
        <Surface padding="panel">
          <EmptyState
            icon={<Package className="h-8 w-8" />}
            title="Model your first product"
            description="Define the product and its declared unit, add the bill of materials, and Climatrix computes the cradle-to-gate footprint from the same factor library that powers your corporate inventory."
            action={{ label: 'New product', onClick: () => setShowNew(true) }}
          />
          <div className="flex flex-col items-center pb-2 text-center">
            <LoadSampleDataButton caption="Not ready with your own BOM? Sample data includes a computed steel coil — PCF, full LCA matrix and an EPD draft — plus a draft product to try Compute on." />
          </div>
        </Surface>
      ) : (
        <Surface padding="tight">
          <table className="w-full text-[13px]">
            <thead>
              <tr>
                {['Product', 'Declared unit', 'BOM lines', 'Latest PCF', 'Primary data', 'Status'].map((h) => (
                  <th key={h} className="px-3 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-[0.07em] text-cy-faint">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {products.map((p) => {
                const fp = p.latest_footprint;
                return (
                  <tr key={p.id} className="border-t border-cy-row hover:bg-cy-row/40">
                    <td className="px-3 py-3">
                      <Link href={`/products/${p.id}`} className="font-semibold text-cy-ink hover:text-cy-accent">
                        {p.name}
                      </Link>
                      {p.sku && <div className="text-[11.5px] text-cy-faint">{p.sku}</div>}
                    </td>
                    <td className="px-3 py-3 text-cy-muted">
                      {formatQty(p.declared_unit_amount)} {UNIT_SHORT[p.declared_unit] ?? p.declared_unit}
                    </td>
                    <td className="px-3 py-3 tabular-nums text-cy-muted">{p.input_count}</td>
                    <td className="px-3 py-3 tabular-nums text-cy-ink">
                      {fp ? (
                        <span className="font-semibold">
                          {num(fp.total_kgco2e_per_unit).toFixed(2)}{' '}
                          <span className="font-normal text-cy-faint">
                            kg CO2e/{UNIT_SHORT[p.declared_unit] ?? p.declared_unit}
                          </span>
                        </span>
                      ) : (
                        <span className="text-cy-faint">Not computed</span>
                      )}
                    </td>
                    <td className="px-3 py-3 tabular-nums text-cy-muted">
                      {fp?.primary_data_share != null ? `${fp.primary_data_share.toFixed(0)}%` : '—'}
                    </td>
                    <td className="px-3 py-3">
                      {fp ? (
                        <span className={cn(
                          'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold',
                          fp.status === 'final' ? 'bg-cy-accent-soft text-cy-accent' : 'bg-cy-warn-soft text-cy-warn'
                        )}>
                          {fp.status === 'final' && <FileCheck2 className="h-3 w-3" />}
                          {fp.status === 'final' ? 'Final' : 'Draft'}
                        </span>
                      ) : (
                        <span className="text-[11px] text-cy-faint">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Surface>
      )}

      <div className="mt-4">
        <SupplierPcfPanel />
      </div>

      {showNew && <NewProductModal onClose={() => setShowNew(false)} />}
    </AppShell>
  );
}
