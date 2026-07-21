/**
 * TanStack Query hooks for the EPD generator. Mirrors useProducts.ts
 * conventions: central query keys, targeted invalidation on mutations.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, type EpdCreate } from '@/lib/api';

export const epdKeys = {
  list: ['epd-projects'] as const,
  detail: (id: string) => ['epd-project', id] as const,
  verifiers: (id: string) => ['epd-verifier-access', id] as const,
};

export function useEpds() {
  return useQuery({
    queryKey: epdKeys.list,
    queryFn: () => api.getEpds(),
    staleTime: 60 * 1000,
  });
}

export function useEpd(epdId: string | undefined) {
  return useQuery({
    queryKey: epdKeys.detail(epdId ?? ''),
    queryFn: () => api.getEpd(epdId!),
    enabled: !!epdId,
    staleTime: 30 * 1000,
  });
}

function useInvalidateEpd(epdId?: string) {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: epdKeys.list });
    if (epdId) qc.invalidateQueries({ queryKey: epdKeys.detail(epdId) });
  };
}

export function useCreateEpd() {
  const invalidate = useInvalidateEpd();
  return useMutation({
    mutationFn: ({ productId, data }: { productId: string; data?: EpdCreate }) =>
      api.createEpd(productId, data),
    onSuccess: invalidate,
  });
}

export function useUpdateEpd(epdId: string) {
  const invalidate = useInvalidateEpd(epdId);
  return useMutation({
    mutationFn: (data: Parameters<typeof api.updateEpd>[1]) => api.updateEpd(epdId, data),
    onSuccess: invalidate,
  });
}

export function useDeleteEpd() {
  const invalidate = useInvalidateEpd();
  return useMutation({
    mutationFn: (epdId: string) => api.deleteEpd(epdId),
    onSuccess: invalidate,
  });
}

export function useTransitionEpd(epdId: string) {
  const invalidate = useInvalidateEpd(epdId);
  return useMutation({
    mutationFn: (status: string) => api.transitionEpd(epdId, status),
    onSuccess: invalidate,
  });
}

export function useEpdVerifierAccess(epdId: string | undefined) {
  return useQuery({
    queryKey: epdKeys.verifiers(epdId ?? ''),
    queryFn: () => api.listEpdVerifierAccess(epdId!),
    enabled: !!epdId,
  });
}

export function useInviteEpdVerifier(epdId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { verifier_email: string; verifier_name?: string }) =>
      api.inviteEpdVerifier(epdId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: epdKeys.verifiers(epdId) });
      qc.invalidateQueries({ queryKey: epdKeys.detail(epdId) });
    },
  });
}

export function useRevokeEpdVerifier(epdId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (accessId: string) => api.revokeVerifierAccess(accessId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: epdKeys.verifiers(epdId) });
      qc.invalidateQueries({ queryKey: epdKeys.detail(epdId) });
    },
  });
}
