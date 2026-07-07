/**
 * TanStack Query hooks for the Data Hub — the inventory profile + coverage matrix.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, HubProfileEntry } from '@/lib/api';

export const hubKeys = {
  overview: (periodId?: string, siteId?: string) => ['hub-overview', periodId, siteId] as const,
  profile: (siteId?: string) => ['hub-profile', siteId] as const,
};

/** The full matrix: every category with profile + live coverage. */
export function useHubOverview(periodId?: string, siteId?: string) {
  return useQuery({
    queryKey: hubKeys.overview(periodId, siteId),
    queryFn: () => api.getHubOverview(periodId, siteId),
    staleTime: 30 * 1000,
  });
}

/** Bulk-save profile rows (any subset of the matrix). */
export function useSaveHubProfile(siteId?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (entries: HubProfileEntry[]) => api.saveHubProfile(entries, siteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hub-overview'] });
      queryClient.invalidateQueries({ queryKey: ['hub-profile'] });
    },
  });
}
