/**
 * TanStack Query hooks for the PCF module (products, BOM, supplier PCFs,
 * footprints). Mirrors the useEmissions.ts conventions: central query keys,
 * targeted invalidation on mutations.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  api,
  type PcfInputCreate,
  type PcfProductCreate,
  type SupplierPcfCreate,
} from '@/lib/api';

export const pcfKeys = {
  products: ['pcf-products'] as const,
  product: (id: string) => ['pcf-product', id] as const,
  supplierPcfs: ['supplier-pcfs'] as const,
};

export function useProducts() {
  return useQuery({
    queryKey: pcfKeys.products,
    queryFn: () => api.getProducts(),
    staleTime: 2 * 60 * 1000,
  });
}

export function useProduct(productId: string | undefined) {
  return useQuery({
    queryKey: pcfKeys.product(productId ?? ''),
    queryFn: () => api.getProduct(productId!),
    enabled: !!productId,
    staleTime: 60 * 1000,
  });
}

export function useSupplierPcfs() {
  return useQuery({
    queryKey: pcfKeys.supplierPcfs,
    queryFn: () => api.getSupplierPcfs(),
    staleTime: 2 * 60 * 1000,
  });
}

function useInvalidateProduct(productId?: string) {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: pcfKeys.products });
    if (productId) qc.invalidateQueries({ queryKey: pcfKeys.product(productId) });
  };
}

export function useCreateProduct() {
  const invalidate = useInvalidateProduct();
  return useMutation({
    mutationFn: (data: PcfProductCreate) => api.createProduct(data),
    onSuccess: invalidate,
  });
}

export function useUpdateProduct(productId: string) {
  const invalidate = useInvalidateProduct(productId);
  return useMutation({
    mutationFn: (data: Partial<PcfProductCreate> & { is_active?: boolean }) =>
      api.updateProduct(productId, data),
    onSuccess: invalidate,
  });
}

export function useDeleteProduct() {
  const invalidate = useInvalidateProduct();
  return useMutation({
    mutationFn: (productId: string) => api.deleteProduct(productId),
    onSuccess: invalidate,
  });
}

export function useCreateProductInput(productId: string) {
  const invalidate = useInvalidateProduct(productId);
  return useMutation({
    mutationFn: (data: PcfInputCreate) => api.createProductInput(productId, data),
    onSuccess: invalidate,
  });
}

export function useUpdateProductInput(productId: string) {
  const invalidate = useInvalidateProduct(productId);
  return useMutation({
    mutationFn: ({ inputId, data }: { inputId: string; data: Partial<PcfInputCreate> }) =>
      api.updateProductInput(productId, inputId, data),
    onSuccess: invalidate,
  });
}

export function useDeleteProductInput(productId: string) {
  const invalidate = useInvalidateProduct(productId);
  return useMutation({
    mutationFn: (inputId: string) => api.deleteProductInput(productId, inputId),
    onSuccess: invalidate,
  });
}

export function useComputeFootprint(productId: string) {
  const invalidate = useInvalidateProduct(productId);
  return useMutation({
    mutationFn: (periodId: string) => api.computeProductFootprint(productId, periodId),
    onSuccess: invalidate,
  });
}

export function useFinalizeFootprint(productId: string) {
  const invalidate = useInvalidateProduct(productId);
  return useMutation({
    mutationFn: (footprintId: string) => api.finalizeProductFootprint(productId, footprintId),
    onSuccess: invalidate,
  });
}

export function useCreateSupplierPcf() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SupplierPcfCreate) => api.createSupplierPcf(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: pcfKeys.supplierPcfs }),
  });
}

export function useUploadSupplierPact() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.uploadSupplierPactJson(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: pcfKeys.supplierPcfs }),
  });
}

export function useDeleteSupplierPcf() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (supplierPcfId: string) => api.deleteSupplierPcf(supplierPcfId),
    onSuccess: () => qc.invalidateQueries({ queryKey: pcfKeys.supplierPcfs }),
  });
}
