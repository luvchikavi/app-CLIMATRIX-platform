/**
 * TanStack Query hooks for sample data — the "Load sample data" button.
 *
 * Loading seeds the user's own org with the flagged Galil Steel demo dataset
 * and switches the period selector to the sample period; removing deletes
 * exactly that flagged set. Both touch nearly every server-state domain
 * (periods, activities, reports, hub, decarbonization), so on success we
 * invalidate the whole cache rather than enumerating keys.
 *
 * Toasts live HERE, not at the call sites: success unmounts both triggers
 * (the empty-state button and the banner), and TanStack drops mutate-level
 * callbacks of unmounted components.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, SampleDataStatus } from '@/lib/api';
import { toast } from '@/components/ui';
import { usePeriodStore } from '@/stores/period';

export const sampleDataKeys = {
  status: ['sample-data-status'] as const,
};

export function useSampleDataStatus() {
  return useQuery({
    queryKey: sampleDataKeys.status,
    queryFn: () => api.getSampleDataStatus(),
    staleTime: 60 * 1000,
  });
}

export function useLoadSampleData() {
  const queryClient = useQueryClient();
  const setSelectedPeriodId = usePeriodStore((s) => s.setSelectedPeriodId);

  return useMutation({
    mutationFn: () => api.loadSampleData(),
    onSuccess: async (result) => {
      toast.success(
        `Sample data loaded — ${result.activities_created} activities, a full report and ${result.scenarios_created} reduction scenarios to explore.`
      );
      // The Header heals a selected period id it can't find in the cached
      // periods list — refresh that list BEFORE switching to the sample
      // period, or the switch gets reverted to the user's first period.
      await queryClient.refetchQueries({ queryKey: ['periods'] });
      setSelectedPeriodId(result.period_id);
      queryClient.invalidateQueries();
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : '';
      toast.error(
        message.includes('already')
          ? 'Sample data is already loaded.'
          : 'Could not load sample data — please try again.'
      );
    },
  });
}

export function useRemoveSampleData() {
  const queryClient = useQueryClient();
  const { selectedPeriodId, setSelectedPeriodId } = usePeriodStore();

  return useMutation({
    mutationFn: () => api.removeSampleData(),
    onSuccess: (result) => {
      toast.success(
        `Sample data removed (${result.removed_activities} activities). Your own data was not touched.`
      );
      // If the user was parked on the (now deleted) sample period, let the
      // period picker fall back to their own first period.
      const status = queryClient.getQueryData<SampleDataStatus>(sampleDataKeys.status);
      if (result.period_removed && selectedPeriodId && selectedPeriodId === status?.period_id) {
        setSelectedPeriodId(null);
      }
      queryClient.invalidateQueries();
    },
    onError: () => toast.error('Could not remove sample data — please try again.'),
  });
}
