/**
 * TanStack Query hooks for emissions data
 *
 * Benefits:
 * - Automatic caching (user switches tabs, data stays)
 * - Background refetching
 * - Optimistic updates
 * - Loading/error states
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  api,
  ActivityCreate,
  ActivityWithEmission,
  EmissionFactor,
  ReportSummary,
  ReportingPeriod,
  OrganizationSettings,
  Region,
  Site,
  Airport,
  FlightDistanceResult,
  Scope2ComparisonResponse,
} from '@/lib/api';

// ============================================================================
// Query Keys
// ============================================================================

export const queryKeys = {
  periods: ['periods'] as const,
  activities: (periodId: string, filters?: { scope?: number; category_code?: string }) =>
    ['activities', periodId, filters] as const,
  emissionFactors: (categoryCode?: string) => ['emission-factors', categoryCode] as const,
  activityOptions: (categoryCode: string) => ['activity-options', categoryCode] as const,
  reportSummary: (periodId: string) => ['report-summary', periodId] as const,
  reportByScope: (periodId: string) => ['report-by-scope', periodId] as const,
  wttReport: (periodId: string) => ['wtt-report', periodId] as const,
  scope2Comparison: (periodId: string) => ['scope-2-comparison', periodId] as const,
  organization: ['organization'] as const,
  regions: ['regions'] as const,
  sites: ['sites'] as const,
};

// ============================================================================
// Hooks
// ============================================================================

/**
 * Fetch all reporting periods
 */
export function usePeriods() {
  return useQuery({
    queryKey: queryKeys.periods,
    queryFn: () => api.getPeriods(),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}

/**
 * Create a new reporting period
 */
export function useCreatePeriod() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<ReportingPeriod>) => api.createPeriod(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.periods });
    },
  });
}

/**
 * Fetch activities for a reporting period
 */
export function useActivities(
  periodId: string,
  filters?: { scope?: number; category_code?: string }
) {
  return useQuery({
    queryKey: queryKeys.activities(periodId, filters),
    queryFn: () => api.getActivities(periodId, filters),
    enabled: !!periodId,
    staleTime: 2 * 60 * 1000, // Cache for 2 minutes
  });
}

/**
 * Create a new activity
 */
export function useCreateActivity(periodId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ActivityCreate) => api.createActivity(periodId, data),
    onSuccess: () => {
      // Invalidate activities list
      queryClient.invalidateQueries({
        queryKey: ['activities', periodId],
      });
      // Invalidate report summary
      queryClient.invalidateQueries({
        queryKey: queryKeys.reportSummary(periodId),
      });
    },
  });
}

/**
 * Delete an activity
 */
export function useDeleteActivity(periodId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (activityId: string) => api.deleteActivity(activityId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['activities', periodId],
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.reportSummary(periodId),
      });
    },
  });
}

/**
 * Fetch emission factors (reference data)
 * Cached indefinitely since reference data rarely changes
 */
export function useEmissionFactors(categoryCode?: string) {
  return useQuery({
    queryKey: queryKeys.emissionFactors(categoryCode),
    queryFn: () => api.getEmissionFactors(categoryCode),
    staleTime: 10 * 60 * 1000, // Cache for 10 minutes
  });
}

/**
 * Fetch activity options for a category
 * Used in wizard dropdown
 */
export function useActivityOptions(categoryCode: string) {
  return useQuery({
    queryKey: queryKeys.activityOptions(categoryCode),
    queryFn: () => api.getActivityOptions(categoryCode),
    enabled: !!categoryCode,
    staleTime: 10 * 60 * 1000, // Cache for 10 minutes, then refetch
  });
}

/**
 * Fetch report summary
 */
export function useReportSummary(periodId: string) {
  return useQuery({
    queryKey: queryKeys.reportSummary(periodId),
    queryFn: () => api.getReportSummary(periodId),
    enabled: !!periodId,
    staleTime: 1 * 60 * 1000, // Cache for 1 minute
  });
}

/**
 * Fetch detailed report by scope
 */
export function useReportByScope(periodId: string) {
  return useQuery({
    queryKey: queryKeys.reportByScope(periodId),
    queryFn: () => api.getReportByScope(periodId),
    enabled: !!periodId,
  });
}

/**
 * Fetch WTT (Scope 3.3) report
 */
export function useWTTReport(periodId: string) {
  return useQuery({
    queryKey: queryKeys.wttReport(periodId),
    queryFn: () => api.getWTTReport(periodId),
    enabled: !!periodId,
  });
}

/**
 * Fetch Scope 2 Location vs Market comparison
 */
export function useScope2Comparison(periodId: string) {
  return useQuery({
    queryKey: queryKeys.scope2Comparison(periodId),
    queryFn: () => api.getScope2Comparison(periodId),
    enabled: !!periodId,
    staleTime: 1 * 60 * 1000, // Cache for 1 minute
  });
}

/**
 * Recalculate all emissions for a period
 */
export function useRecalculatePeriod(periodId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.recalculatePeriod(periodId),
    onSuccess: () => {
      // Invalidate all period-related queries
      queryClient.invalidateQueries({
        queryKey: ['activities', periodId],
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.reportSummary(periodId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.reportByScope(periodId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.wttReport(periodId),
      });
    },
  });
}

// ============================================================================
// Organization Hooks
// ============================================================================

/**
 * Fetch organization settings
 */
export function useOrganization() {
  return useQuery({
    queryKey: queryKeys.organization,
    queryFn: () => api.getOrganization(),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Update organization settings
 */
export function useUpdateOrganization() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<OrganizationSettings>) => api.updateOrganization(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.organization });
    },
  });
}

/**
 * Fetch supported regions
 */
export function useSupportedRegions() {
  return useQuery({
    queryKey: queryKeys.regions,
    queryFn: () => api.getSupportedRegions(),
    staleTime: Infinity, // Static data
  });
}

/**
 * Fetch organization sites
 */
export function useSites() {
  return useQuery({
    queryKey: queryKeys.sites,
    queryFn: () => api.getSites(),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Create a new site
 */
export function useCreateSite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { name: string; country_code?: string; address?: string; grid_region?: string }) =>
      api.createSite(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.sites });
    },
  });
}

/**
 * Delete a site
 */
export function useDeleteSite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (siteId: string) => api.deleteSite(siteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.sites });
    },
  });
}

// ============================================================================
// Flight Distance Hooks
// ============================================================================

/**
 * Calculate flight distance between two airports
 */
export function useFlightDistance() {
  return useMutation({
    mutationFn: ({
      origin,
      destination,
      cabinClass = 'economy',
    }: {
      origin: string;
      destination: string;
      cabinClass?: string;
    }) => api.calculateFlightDistance(origin, destination, cabinClass),
  });
}

/**
 * Search airports by name, city, or IATA code
 */
export function useAirportSearch(query: string) {
  return useQuery({
    queryKey: ['airports', query],
    queryFn: () => api.searchAirports(query),
    enabled: query.length >= 2,
    staleTime: Infinity, // Airport data doesn't change
  });
}
