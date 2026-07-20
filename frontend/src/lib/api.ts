/**
 * API Client for CLIMATRIX backend
 *
 * Uses explicit activity_key system - no fuzzy matching.
 * All endpoints are typed with TypeScript interfaces.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// ============================================================================
// Types
// ============================================================================

/**
 * Backend fields typed as Python Decimal arrive as JSON STRINGS ("67.44"),
 * not numbers — pydantic v2 serializes Decimal to string. Anything typed
 * ApiDecimal must go through num() (lib/utils) before math or formatting;
 * calling .toFixed on it is the crash that took down /decarbonization.
 */
export type ApiDecimal = number | string;

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
  organization?: Organization;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  organization_name: string;
  country_code?: string;
}

export interface RegisterResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
  organization: Organization;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  organization_id: string;
  role: string;
  onboarding_completed?: boolean;
}

export interface Organization {
  id: string;
  name: string;
  country_code: string;
  subscription_plan?: 'free' | 'starter' | 'professional' | 'enterprise';
  default_region?: string;
  industry_code?: string | null;
  base_year?: number | null;
  setup_complete?: boolean;
}

export type PeriodStatus = "draft" | "review" | "submitted" | "audit" | "verified" | "locked";
export type AssuranceLevel = "limited" | "reasonable";

export interface ReportingPeriod {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_locked: boolean;
  // Verification workflow fields
  status: PeriodStatus;
  assurance_level?: AssuranceLevel;
  submitted_at?: string;
  submitted_by_id?: string;
  verified_at?: string;
  verified_by?: string;
  verification_statement?: string;
  /** Period was created by "Load sample data" (shows a DEMO badge). */
  is_demo?: boolean;
}

export interface StatusHistory {
  period_id: string;
  current_status: PeriodStatus;
  is_locked: boolean;
  timeline: {
    created_at?: string;
    submitted_at?: string;
    submitted_by_id?: string;
    verified_at?: string;
    verified_by?: string;
  };
  verification: {
    assurance_level?: AssuranceLevel;
    verification_statement?: string;
  };
  valid_transitions: PeriodStatus[];
}

export interface ActivityCreate {
  scope: 1 | 2 | 3;
  category_code: string;
  activity_key: string;
  description: string;
  quantity: number;
  unit: string;
  activity_date: string;
  site_id?: string;
  // For Supplier-Specific method (3.1, 3.2): user provides their own emission factor
  supplier_ef?: number;
  // Data quality fields (PCAF: 1=best, 5=worst)
  data_quality_score?: number;
  data_quality_justification?: string;
  supporting_document_url?: string;
}

export interface Activity {
  id: string;
  scope: number;
  category_code: string;
  activity_key: string;
  description: string;
  quantity: number;
  unit: string;
  activity_date: string;
  site_id: string | null;
  created_at: string;
  import_batch_id?: string | null;
  // Data quality fields
  data_quality_score: number;
  data_quality_justification?: string | null;
  supporting_document_url?: string | null;
  /** Row was seeded by "Load sample data" (shows a DEMO badge). */
  is_demo?: boolean;
}

export interface Emission {
  id: string;
  activity_id: string;
  co2e_kg: number;
  co2_kg: number | null;
  ch4_kg: number | null;
  n2o_kg: number | null;
  wtt_co2e_kg: number | null;
  formula: string;
  confidence: 'high' | 'medium' | 'low';
  resolution_strategy: string;
  factor_used: string;
  factor_source: string;
  factor_value: number | null;
  factor_unit: string | null;
  warnings: string[];
}

export interface ActivityWithEmission {
  activity: Activity;
  emission: Emission | null;
}

// Sample data (the "Load sample data" button)
export interface SampleDataStatus {
  loaded: boolean;
  period_id: string | null;
  activities: number;
}

export interface SampleDataLoadResult {
  period_id: string;
  site_id: string;
  activities_created: number;
  rows_skipped: number;
  total_co2e_tonnes: number;
  target_created: boolean;
  scenarios_created: number;
}

export interface SampleDataRemoveResult {
  removed_activities: number;
  removed_scenarios: number;
  removed_targets: number;
  period_removed: boolean;
  periods_kept: number;
}

export interface EmissionFactor {
  id?: string;
  activity_key: string;
  display_name: string;
  activity_unit?: string;
  unit?: string; // For activity options
  scope: number;
  category_code: string;
  co2e_factor?: ApiDecimal;
  factor_unit?: string;
  source?: string;
  region?: string;
  year?: number;
}

// Power Producer (for market-based Scope 2)
export interface PowerProducer {
  id: string;
  producer_name_he: string | null;
  producer_name_en: string;
  country_code: string;
  region: string | null;
  co2e_per_kwh: number;
  source: string;
  source_type: string;
  year: number;
  is_active: boolean;
}

// Market Factor Response (for Scope 2 market-based)
export interface MarketFactorResponse {
  country: string;
  subregion: string | null;
  factor: number;
  source: string;
  source_type: string;
  year: number;
}

// Transport Route (for Cat 3.4/3.9)
export interface TransportRoute {
  origin: string;
  destination: string;
  origin_land_km: number;
  sea_distance_km: number;
  destination_land_km: number;
  total_distance_km: number;
  transport_mode: string;
  source: string;
}

// Transport Distance Response
export interface TransportDistanceResponse {
  origin: string;
  destination: string;
  origin_land_km: number;
  sea_distance_km: number;
  destination_land_km: number;
  total_distance_km: number;
  transport_mode: string;
  source: string;
}

// Fuel Prices (for spend-to-quantity conversion)
export interface FuelPrice {
  id: string;
  fuel_type: string;
  price_per_unit: number;
  currency: string;
  unit: string;
  region: string;
  source: string;
  source_url: string | null;
  valid_from: string;
  valid_until: string | null;
}

export interface SpendConversionRequest {
  fuel_type: string;
  spend_amount: number;
  currency: string;
  region?: string;
}

export interface SpendConversionResult {
  fuel_type: string;
  spend_amount: number;
  currency: string;
  fuel_price: number;
  price_unit: string;
  price_source: string;
  calculated_quantity: number;
  quantity_unit: string;
  formula: string;
}

// Airport and Flight Distance Types
export interface Airport {
  iata_code: string;
  name: string;
  city: string;
  country: string;
  latitude: number;
  longitude: number;
}

export interface FlightDistanceResult {
  origin: Airport;
  destination: Airport;
  distance_km: number;
  haul_type: 'short' | 'medium' | 'long';
  suggested_activity_key: string;
  emission_factor_info: string;
}

// Import Batch tracking
export interface ImportBatch {
  id: string;
  file_name: string;
  file_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'partial';
  total_rows: number;
  successful_rows: number;
  failed_rows: number;
  uploaded_at: string;
  completed_at: string | null;
}

export interface ImportBatchDetail extends ImportBatch {
  file_size_bytes: number | null;
  skipped_rows: number;
  error_message: string | null;
  row_errors: Array<{ row: number; errors: string[] }> | null;
}

export interface ReportSummary {
  period_id: string;
  period_name: string;
  total_co2e_kg: number;
  total_co2e_tonnes: number;
  scope_1_co2e_kg: number;
  scope_2_co2e_kg: number;
  scope_2_location_based_co2e_kg: number;
  scope_2_market_based_co2e_kg: number | null;
  scope_3_co2e_kg: number;
  scope_3_wtt_co2e_kg: number;
  by_scope: ScopeSummary[];
  by_category: CategorySummary[];
}

// Data Quality Report Types
export interface DataQualityBreakdown {
  score: number;
  score_label: string;
  activity_count: number;
  total_co2e_kg: number;
  percentage: number;
}

export interface DataQualitySummary {
  period_id: string;
  period_name: string;
  total_activities: number;
  weighted_average_score: number;
  score_interpretation: string;
  by_score: DataQualityBreakdown[];
}

// ISO 14064-1 GHG Inventory Report Types
export interface OrganizationInfo {
  name: string;
  country?: string;
  industry?: string;
  base_year?: number;
}

export interface ReportingBoundary {
  consolidation_approach: string;
  included_facilities: number;
  reporting_period_start: string;
  reporting_period_end: string;
}

export interface EmissionSourceDetail {
  activity_key: string;
  display_name: string;
  category_code: string;
  activity_count: number;
  total_quantity: number;
  unit: string;
  total_co2e_kg: number;
  total_co2e_tonnes: number;
  emission_factor: number;
  factor_source: string;
  factor_unit: string;
  avg_data_quality: number;
}

export interface ScopeDetail {
  scope: number;
  scope_name: string;
  total_co2e_kg: number;
  total_co2e_tonnes: number;
  percentage_of_total: number;
  activity_count: number;
  avg_data_quality: number;
  sources: EmissionSourceDetail[];
}

export interface MethodologySection {
  calculation_approach: string;
  emission_factor_sources: string[];
  gwp_values: string;
  exclusions: string[];
  assumptions: string[];
}

export interface BaseYearComparison {
  base_year: number;
  base_year_emissions_tonnes: number;
  current_emissions_tonnes: number;
  absolute_change_tonnes: number;
  percentage_change: number;
}

export interface VerificationInfo {
  status: string;
  assurance_level?: string;
  verified_by?: string;
  verified_at?: string;
  verification_statement?: string;
}

export interface GHGInventoryReport {
  report_title: string;
  report_date: string;
  reporting_period: string;
  organization: OrganizationInfo;
  boundaries: ReportingBoundary;
  executive_summary: {
    total_emissions_tonnes: number;
    scope_1_tonnes: number;
    scope_2_tonnes: number;
    scope_3_tonnes: number;
    scope_1_percentage: number;
    scope_2_percentage: number;
    scope_3_percentage: number;
    total_activities: number;
    data_quality_score: number;
    top_emission_sources: string[];
  };
  scope_1: ScopeDetail;
  scope_2: ScopeDetail;
  scope_3: ScopeDetail;
  total_emissions_kg: number;
  total_emissions_tonnes: number;
  overall_data_quality_score: number;
  data_quality_interpretation: string;
  methodology: MethodologySection;
  base_year_comparison?: BaseYearComparison;
  verification: VerificationInfo;
}

// Audit Package Types (Phase 1.4)
export interface ActivityAuditRecord {
  activity_id: string;
  scope: number;
  category_code: string;
  category_name: string;
  activity_key: string;
  display_name: string;
  description: string;
  quantity: number;
  unit: string;
  activity_date: string;
  calculation_method: string;
  data_source: string;
  import_batch_id: string | null;
  import_file_name: string | null;
  data_quality_score: number;
  data_quality_label: string;
  data_quality_justification: string | null;
  supporting_document_url: string | null;
  co2e_kg: number;
  co2e_tonnes: number;
  co2_kg: number | null;
  ch4_kg: number | null;
  n2o_kg: number | null;
  wtt_co2e_kg: number | null;
  emission_factor_id: string;
  emission_factor_value: number;
  emission_factor_unit: string;
  converted_quantity: number | null;
  converted_unit: string | null;
  calculation_formula: string | null;
  confidence_level: string;
  created_at: string;
  created_by: string | null;
}

export interface EmissionFactorAuditRecord {
  factor_id: string;
  activity_key: string;
  display_name: string;
  scope: number;
  category_code: string;
  subcategory: string | null;
  co2e_factor: number;
  co2_factor: number | null;
  ch4_factor: number | null;
  n2o_factor: number | null;
  activity_unit: string;
  factor_unit: string;
  source: string;
  region: string;
  year: number;
  valid_from: string | null;
  valid_until: string | null;
  usage_count: number;
  total_co2e_kg: number;
}

export interface ImportBatchAuditRecord {
  batch_id: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number | null;
  status: string;
  total_rows: number;
  successful_rows: number;
  failed_rows: number;
  skipped_rows: number;
  error_message: string | null;
  uploaded_at: string;
  uploaded_by: string | null;
  completed_at: string | null;
}

export interface CalculationMethodologySection {
  overview: string;
  ghg_protocol_alignment: string;
  calculation_approach: string;
  scope_1_methodology: Record<string, unknown>;
  scope_2_methodology: Record<string, unknown>;
  scope_3_methodology: Record<string, unknown>;
  unit_conversion_approach: string;
  wtt_calculation_method: string;
  data_validation_rules: string[];
  confidence_level_criteria: Record<string, string>;
}

export interface AuditPackageSummary {
  period_id: string;
  period_name: string;
  organization_name: string;
  reporting_period_start: string;
  reporting_period_end: string;
  verification_status: string;
  assurance_level: string | null;
  total_activities: number;
  total_emissions_kg: number;
  total_emissions_tonnes: number;
  scope_1_emissions_tonnes: number;
  scope_2_emissions_tonnes: number;
  scope_3_emissions_tonnes: number;
  overall_data_quality_score: number;
  data_quality_interpretation: string;
  total_import_batches: number;
  generated_at: string;
  generated_by: string;
}

export interface AuditPackage {
  package_version: string;
  summary: AuditPackageSummary;
  methodology: CalculationMethodologySection;
  activities: ActivityAuditRecord[];
  emission_factors: EmissionFactorAuditRecord[];
  import_batches: ImportBatchAuditRecord[];
}

// CDP Export Types (Phase 1.5)
export interface CDPScope1Breakdown {
  source_category: string;
  emissions_metric_tonnes: number;
  methodology: string;
  source_of_emission_factors: string;
}

export interface CDPScope2Breakdown {
  country: string;
  grid_region: string | null;
  purchased_electricity_mwh: number;
  location_based_emissions_tonnes: number;
  market_based_emissions_tonnes: number | null;
}

export interface CDPScope3Category {
  category_number: number;
  category_name: string;
  emissions_metric_tonnes: number;
  calculation_methodology: string;
  percentage_calculated_using_primary_data: number;
  explanation: string;
}

export interface CDPEmissionsTotals {
  scope_1_metric_tonnes: number;
  scope_2_location_based_metric_tonnes: number;
  scope_2_market_based_metric_tonnes: number | null;
  scope_3_metric_tonnes: number;
  total_metric_tonnes: number;
}

export interface CDPTargetsAndPerformance {
  base_year: number | null;
  base_year_emissions_tonnes: number | null;
  target_year: number | null;
  target_reduction_percentage: number | null;
  current_year_emissions_tonnes: number;
  progress_percentage: number | null;
}

export interface CDPDataQuality {
  overall_data_quality_score: number;
  percentage_verified_data: number;
  percentage_primary_data: number;
  percentage_estimated_data: number;
  verification_status: string;
  assurance_level: string | null;
}

export interface CDPExport {
  export_version: string;
  export_date: string;
  reporting_year: number;
  organization_name: string;
  country: string | null;
  primary_industry: string | null;
  reporting_boundary: string;
  targets: CDPTargetsAndPerformance;
  emissions_totals: CDPEmissionsTotals;
  scope_1_breakdown: CDPScope1Breakdown[];
  scope_2_breakdown: CDPScope2Breakdown[];
  scope_3_categories: CDPScope3Category[];
  data_quality: CDPDataQuality;
  emission_factor_sources: string[];
  global_warming_potential_source: string;
}

// ESRS E1 Export Types (Phase 1.5)
export interface ESRSE1GrossEmissions {
  scope_1_tonnes: number;
  scope_2_location_based_tonnes: number;
  scope_2_market_based_tonnes: number | null;
  scope_3_tonnes: number;
  total_ghg_emissions_tonnes: number;
}

export interface ESRSE1Scope3Detail {
  category: string;
  emissions_tonnes: number;
  percentage_of_scope_3: number;
}

export interface ESRSE1IntensityMetric {
  metric_name: string;
  numerator_tonnes: number;
  denominator_value: number;
  denominator_unit: string;
  intensity_value: number;
  intensity_unit: string;
}

export interface ESRSE1TargetInfo {
  target_type: string;
  target_scope: string;
  base_year: number;
  base_year_value: number;
  target_year: number;
  target_value: number;
  target_reduction_percentage: number;
}

export interface ESRSE1TransitionPlan {
  has_transition_plan: boolean;
  plan_aligned_with: string | null;
  key_decarbonization_levers: string[];
  locked_in_emissions_tonnes: number | null;
}

export interface ESRSE1DataQuality {
  data_quality_approach: string;
  percentage_estimated_scope_3: number;
  significant_assumptions: string[];
  verification_statement: string | null;
}

export interface ESRSE1Export {
  export_version: string;
  export_date: string;
  reporting_period_start: string;
  reporting_period_end: string;
  undertaking_name: string;
  country_of_domicile: string | null;
  nace_sector: string | null;
  consolidation_scope: string;
  transition_plan: ESRSE1TransitionPlan;
  climate_targets: ESRSE1TargetInfo[];
  gross_emissions: ESRSE1GrossEmissions;
  scope_3_breakdown: ESRSE1Scope3Detail[];
  intensity_metrics: ESRSE1IntensityMetric[];
  data_quality: ESRSE1DataQuality;
  ghg_accounting_standard: string;
  emission_factor_sources: string[];
  gwp_values_source: string;
}

export interface ScopeSummary {
  scope: number;
  total_co2e_kg: number;
  total_wtt_co2e_kg: number;
  activity_count: number;
}

export interface CategorySummary {
  scope: number;
  category_code: string;
  total_co2e_kg: number;
  activity_count: number;
}

// Scope 2 Location vs Market Comparison
export interface Scope2ActivityComparison {
  activity_id: string;
  description: string;
  country_code: string;
  country_name: string;
  quantity_kwh: number;
  location_factor: number;
  market_factor: number | null;
  location_co2e_kg: number;
  market_co2e_kg: number | null;
  difference_kg: number | null;
  difference_percent: number | null;
}

export interface Scope2ComparisonResponse {
  period_id: string;
  period_name: string;
  total_activities: number;
  total_location_co2e_kg: number;
  total_market_co2e_kg: number | null;
  total_difference_kg: number | null;
  total_difference_percent: number | null;
  activities: Scope2ActivityComparison[];
  countries_without_market_factor: string[];
}

export interface OrganizationSettings {
  id: string;
  name: string;
  country_code: string | null;
  industry_code: string | null;
  base_year: number | null;
  default_region: string;
  setup_complete?: boolean;
  currency?: string | null;
  unit_system?: string;
  consolidation_approach?: string;
}

// ============================================================================
// Data Hub — inventory profile + coverage matrix
// ============================================================================

export type HubRelevance = 'relevant' | 'not_relevant' | 'not_sure';

export interface HubProfileEntry {
  category_code: string;
  relevance: HubRelevance;
  exclusion_reason?: string | null;
  calculate_this_period?: boolean;
  data_owner?: string | null;
  expected_form?: string | null;
  details?: Record<string, unknown> | null;
}

export interface HubProfileEntryResponse extends HubProfileEntry {
  scope: number;
  site_id: string | null;
  updated_at: string | null;
}

export interface HubCoverage {
  committed_count: number;
  total_co2e_kg: number;
  staged_count: number;
  staged_by_tier: Record<string, number>;
  open_questions: number;
}

export interface HubCategory {
  scope: number;
  code: string;
  name: string;
  description: string;
  profile: HubProfileEntryResponse | null;
  coverage: HubCoverage;
}

export interface HubStats {
  total_categories: number;
  relevant: number;
  not_relevant: number;
  not_sure: number;
  with_data: number;
  open_questions: number;
}

export interface HubOverview {
  categories: HubCategory[];
  stats: HubStats;
}

export interface HubQuestion {
  id: string;
  session_id: string;
  filename: string;
  question: string;
  field: string | null;
  choices: { value: string; label: string }[] | null;
  applies_count: number;
}

export interface Region {
  code: string;
  name: string;
  description: string;
}

export interface FactorRegion {
  code: string;
  name: string;
}

export interface Site {
  id: string;
  name: string;
  country_code: string | null;
  address: string | null;
  grid_region: string | null;
  is_active: boolean;
}

export interface SiteDetail extends Site {
  activity_count: number;
  total_co2e_kg: number;
  total_co2e_tonnes: number;
  scope_1_co2e_kg: number;
  scope_2_co2e_kg: number;
  scope_3_co2e_kg: number;
}

export interface SiteEmissionSummary {
  site_id: string;
  site_name: string;
  total_co2e_kg: number;
  total_co2e_tonnes: number;
  scope_1_co2e_kg: number;
  scope_2_co2e_kg: number;
  scope_3_co2e_kg: number;
  activity_count: number;
}

export interface ImportRow {
  row_number: number;
  scope: number | null;
  category_code: string | null;
  activity_key: string | null;
  description: string | null;
  quantity: number | null;
  unit: string | null;
  activity_date: string | null;
  errors: string[];
  warnings: string[];
  is_valid: boolean;
}

export interface ImportPreview {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  rows: ImportRow[];
  columns_found: string[];
  columns_missing: string[];
}

/** Raw per-row error payload returned by the import endpoints (shape varies by endpoint). */
interface ImportErrorPayload {
  row?: number;
  activity_key?: string;
  errors?: string | string[];
  error?: string | string[];
  message?: string;
}

export interface ImportResult {
  total_rows: number;
  imported: number;
  failed: number;
  errors: {
    row?: number;
    activity_key?: string;
    category_code?: string;
    quantity?: number;
    unit?: string;
    errors: string[];
  }[];
  import_batch_id?: string;
}

// ============================================================================
// API Client
// ============================================================================

class ApiClient {
  private token: string | null = null;
  private refreshToken: string | null = null;
  private refreshPromise: Promise<boolean> | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  getToken(): string | null {
    return this.token;
  }

  setRefreshToken(token: string | null) {
    this.refreshToken = token;
    if (typeof window !== 'undefined') {
      if (token) localStorage.setItem('climatrix_refresh', token);
      else localStorage.removeItem('climatrix_refresh');
    }
  }

  private getRefreshToken(): string | null {
    if (!this.refreshToken && typeof window !== 'undefined') {
      this.refreshToken = localStorage.getItem('climatrix_refresh');
    }
    return this.refreshToken;
  }

  /** Exchange the stored refresh token for a fresh access token. Deduped so a burst
   *  of concurrent 401s triggers only one refresh call. Returns true on success. */
  private async tryRefresh(): Promise<boolean> {
    const rt = this.getRefreshToken();
    if (!rt) return false;
    if (!this.refreshPromise) {
      this.refreshPromise = this.doRefresh(rt).finally(() => {
        this.refreshPromise = null;
      });
    }
    return this.refreshPromise;
  }

  private async doRefresh(rt: string): Promise<boolean> {
    try {
      const resp = await fetch(
        `${API_BASE}/auth/refresh?refresh_token=${encodeURIComponent(rt)}`,
        { method: 'POST' }
      );
      if (!resp.ok) return false;
      const data = await resp.json();
      this.setToken(data.access_token);
      if (data.refresh_token) this.setRefreshToken(data.refresh_token);
      if (typeof window !== 'undefined') {
        // Let the auth store persist the new access token.
        window.dispatchEvent(
          new CustomEvent('climatrix:token-refreshed', {
            detail: { access_token: data.access_token },
          })
        );
      }
      return true;
    } catch {
      return false;
    }
  }

  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {},
    timeoutMs: number = 30000,
    _retry: boolean = false
  ): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const token = this.getToken();
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    let response: Response;
    try {
      response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
        signal: options.signal || controller.signal,
      });
    } catch (err: unknown) {
      clearTimeout(timeoutId);
      if (err instanceof Error && err.name === 'AbortError') {
        throw new Error('Request timed out. Please check your connection and try again.');
      }
      throw err;
    } finally {
      clearTimeout(timeoutId);
    }

    // On a 401, try to silently refresh the access token once and retry the request
    // before giving up — so a 30-min access token expiring mid-session is invisible.
    if (response.status === 401 && !_retry) {
      const refreshed = await this.tryRefresh();
      if (refreshed) {
        return this.fetch<T>(endpoint, options, timeoutMs, true);
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));

      // Refresh failed (or already retried): now it's a real auth expiry.
      if (response.status === 401) {
        this.setToken(null);
        this.setRefreshToken(null);
        // Dispatch event to notify auth store
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('auth-expired'));
        }
      }

      // 402 = plan limit reached. Surface a targeted upgrade prompt.
      if (response.status === 402) {
        const d =
          error.detail && typeof error.detail === 'object' ? error.detail : {};
        if (typeof window !== 'undefined') {
          window.dispatchEvent(
            new CustomEvent('climatrix:limit-reached', { detail: d })
          );
        }
        throw new Error(d.message || 'Upgrade required to use this feature.');
      }

      // detail can be a string or a structured object — never render "[object Object]"
      const message =
        typeof error.detail === 'string'
          ? error.detail
          : error.detail?.message || `API Error: ${response.status}`;
      throw new Error(message);
    }

    return response.json();
  }

  // Validate current token by calling /auth/me
  async validateToken(): Promise<boolean> {
    const token = this.getToken();
    if (!token) return false;

    try {
      await this.fetch<User>('/auth/me');
      return true;
    } catch {
      return false;
    }
  }

  async completeOnboarding(): Promise<User> {
    return this.fetch<User>('/auth/me/onboarding-complete', { method: 'PATCH' });
  }

  // Auth
  async login(data: LoginRequest): Promise<LoginResponse> {
    const formData = new URLSearchParams();
    formData.append('username', data.email);
    formData.append('password', data.password);

    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail || 'Login failed');
    }

    const result = await response.json();
    this.setToken(result.access_token);
    this.setRefreshToken(result.refresh_token ?? null);
    return result;
  }

  logout() {
    this.setToken(null);
    this.setRefreshToken(null);
  }

  // Google OAuth
  async googleLogin(idToken: string): Promise<LoginResponse> {
    const response = await fetch(`${API_BASE}/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_token: idToken }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Google login failed' }));
      throw new Error(error.detail || 'Google login failed');
    }

    const result = await response.json();
    this.setToken(result.access_token);
    this.setRefreshToken(result.refresh_token ?? null);
    return result;
  }

  // Registration
  async register(data: RegisterRequest): Promise<RegisterResponse> {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(error.detail || 'Registration failed');
    }

    const result = await response.json();
    this.setToken(result.access_token);
    this.setRefreshToken(result.refresh_token ?? null);
    return result;
  }

  // Reporting Periods
  async getPeriods(): Promise<ReportingPeriod[]> {
    return this.fetch<ReportingPeriod[]>('/periods');
  }

  async createPeriod(data: Partial<ReportingPeriod>): Promise<ReportingPeriod> {
    return this.fetch<ReportingPeriod>('/periods', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getPeriod(periodId: string): Promise<ReportingPeriod> {
    return this.fetch<ReportingPeriod>(`/periods/${periodId}`);
  }

  // Verification Workflow
  async transitionPeriodStatus(periodId: string, newStatus: PeriodStatus): Promise<ReportingPeriod> {
    return this.fetch<ReportingPeriod>(`/periods/${periodId}/transition`, {
      method: 'POST',
      body: JSON.stringify({ new_status: newStatus }),
    });
  }

  async verifyPeriod(
    periodId: string,
    data: { assurance_level: AssuranceLevel; verified_by: string; verification_statement: string }
  ): Promise<ReportingPeriod> {
    return this.fetch<ReportingPeriod>(`/periods/${periodId}/verify`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async lockPeriod(periodId: string): Promise<ReportingPeriod> {
    return this.fetch<ReportingPeriod>(`/periods/${periodId}/lock`, {
      method: 'POST',
    });
  }

  async getPeriodStatusHistory(periodId: string): Promise<StatusHistory> {
    return this.fetch<StatusHistory>(`/periods/${periodId}/status-history`);
  }

  // Activities
  async getActivities(
    periodId: string,
    filters?: { scope?: number; category_code?: string; site_id?: string }
  ): Promise<ActivityWithEmission[]> {
    const params = new URLSearchParams();
    if (filters?.scope) params.append('scope', String(filters.scope));
    if (filters?.category_code) params.append('category_code', filters.category_code);
    if (filters?.site_id) params.append('site_id', filters.site_id);

    const query = params.toString() ? `?${params}` : '';
    return this.fetch<ActivityWithEmission[]>(`/periods/${periodId}/activities${query}`);
  }

  async createActivity(
    periodId: string,
    data: ActivityCreate
  ): Promise<ActivityWithEmission> {
    return this.fetch<ActivityWithEmission>(`/periods/${periodId}/activities`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateActivity(activityId: string, data: {
    description?: string;
    quantity?: number;
    unit?: string;
    activity_key?: string;
    data_quality_score?: number;
    data_quality_justification?: string;
    supporting_document_url?: string;
  }): Promise<ActivityWithEmission> {
    return this.fetch<ActivityWithEmission>(`/activities/${activityId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteActivity(activityId: string): Promise<void> {
    await this.fetch(`/activities/${activityId}`, { method: 'DELETE' });
  }

  // Emission Factors (Reference Data)
  async getEmissionFactors(categoryCode?: string): Promise<EmissionFactor[]> {
    const query = categoryCode ? `?category_code=${categoryCode}` : '';
    return this.fetch<EmissionFactor[]>(`/reference/emission-factors${query}`);
  }

  async getActivityOptions(categoryCode: string): Promise<EmissionFactor[]> {
    return this.fetch<EmissionFactor[]>(`/reference/activity-options/${categoryCode}`);
  }

  // Power Producers (for market-based Scope 2)
  async getPowerProducers(country: string, year?: number): Promise<PowerProducer[]> {
    const params = new URLSearchParams({ country });
    if (year) params.append('year', year.toString());
    return this.fetch<PowerProducer[]>(`/reference/power-producers?${params}`);
  }

  // Fuel Prices (for spend-to-quantity conversion)
  async getFuelPrices(fuelType?: string, region?: string): Promise<FuelPrice[]> {
    const params = new URLSearchParams();
    if (fuelType) params.append('fuel_type', fuelType);
    if (region) params.append('region', region);
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.fetch<FuelPrice[]>(`/reference/fuel-prices${query}`);
  }

  async getFuelPrice(fuelType: string, region?: string): Promise<FuelPrice> {
    const query = region ? `?region=${region}` : '';
    return this.fetch<FuelPrice>(`/reference/fuel-prices/${fuelType}${query}`);
  }

  // Methodology — the rules every number is computed under (GWP set, ladder,
  // method hierarchy, biogenic policy). Rendered on /methodology.
  async getMethodology(): Promise<MethodologyReference> {
    return this.fetch<MethodologyReference>('/reference/methodology');
  }

  async convertSpendToQuantity(request: SpendConversionRequest): Promise<SpendConversionResult> {
    return this.fetch<SpendConversionResult>('/reference/convert-spend', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Flight Distance Calculator
  async calculateFlightDistance(
    origin: string,
    destination: string,
    cabinClass: string = 'economy'
  ): Promise<FlightDistanceResult> {
    return this.fetch<FlightDistanceResult>(
      `/reference/flight-distance?origin=${origin}&destination=${destination}&cabin_class=${cabinClass}`
    );
  }

  async searchAirports(query: string, limit: number = 10): Promise<Airport[]> {
    return this.fetch<Airport[]>(`/reference/airports/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  }

  async getAirport(iataCode: string): Promise<Airport> {
    return this.fetch<Airport>(`/reference/airports/${iataCode}`);
  }

  // Reports
  async getReportSummary(periodId: string, siteId?: string): Promise<ReportSummary> {
    const query = siteId ? `?site_id=${siteId}` : '';
    return this.fetch<ReportSummary>(`/periods/${periodId}/report/summary${query}`);
  }

  async getReportByScope(periodId: string): Promise<unknown> {
    return this.fetch(`/periods/${periodId}/report/by-scope`);
  }

  async getWTTReport(periodId: string): Promise<unknown> {
    return this.fetch(`/periods/${periodId}/report/scope-3-3-wtt`);
  }

  async getScope2Comparison(periodId: string): Promise<Scope2ComparisonResponse> {
    return this.fetch<Scope2ComparisonResponse>(`/periods/${periodId}/report/scope-2-comparison`);
  }

  async getDataQualitySummary(periodId: string): Promise<DataQualitySummary> {
    return this.fetch<DataQualitySummary>(`/periods/${periodId}/report/data-quality`);
  }

  async getGHGInventoryReport(periodId: string): Promise<GHGInventoryReport> {
    return this.fetch<GHGInventoryReport>(`/periods/${periodId}/report/ghg-inventory`);
  }

  async getAuditPackage(periodId: string): Promise<AuditPackage> {
    return this.fetch<AuditPackage>(`/periods/${periodId}/report/audit-package`);
  }

  async exportCDP(periodId: string): Promise<CDPExport> {
    return this.fetch<CDPExport>(`/periods/${periodId}/export/cdp`);
  }

  async exportESRSE1(periodId: string): Promise<ESRSE1Export> {
    return this.fetch<ESRSE1Export>(`/periods/${periodId}/export/esrs-e1`);
  }

  getReportExportUrl(format: 'csv' | 'pdf', periodId: string, siteId?: string): string {
    let url = `${API_BASE}/reports/export/${format}?period_id=${periodId}`;
    if (siteId) url += `&site_id=${siteId}`;
    return url;
  }

  async downloadReportExport(format: 'csv' | 'pdf', periodId: string, siteId?: string): Promise<void> {
    const token = this.getToken();
    const url = this.getReportExportUrl(format, periodId, siteId);

    const response = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Export failed' }));
      throw new Error(error.detail || `Export failed: ${response.status}`);
    }

    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition');
    const filenameMatch = disposition?.match(/filename="?([^"]+)"?/);
    const filename = filenameMatch?.[1] || `ghg_report.${format}`;

    const blobUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(blobUrl);
  }

  // Recalculate
  async recalculatePeriod(periodId: string): Promise<unknown> {
    return this.fetch(`/periods/${periodId}/emissions/recalculate`, {
      method: 'POST',
    });
  }

  // Organization
  async getOrganization(): Promise<OrganizationSettings> {
    return this.fetch<OrganizationSettings>('/organization');
  }

  async updateOrganization(data: Partial<OrganizationSettings>): Promise<OrganizationSettings> {
    return this.fetch<OrganizationSettings>('/organization', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  /** Mark org setup complete (server validates industry, base year, region, >=1 site, >=1 period). */
  async completeSetup(): Promise<OrganizationSettings> {
    return this.fetch<OrganizationSettings>('/organization/complete-setup', {
      method: 'PATCH',
    });
  }

  /** Join the 'Notify Me' waitlist for a Coming Soon module (captures a lead). */
  async joinModuleWaitlist(moduleId: string, email?: string): Promise<{ ok: boolean; module_id: string }> {
    return this.fetch<{ ok: boolean; module_id: string }>('/modules/waitlist', {
      method: 'POST',
      body: JSON.stringify({ module_id: moduleId, email }),
    });
  }

  // ============ Sample data (the "Load sample data" button) ============

  /** Whether this org currently has the flagged sample dataset loaded. */
  async getSampleDataStatus(): Promise<SampleDataStatus> {
    return this.fetch<SampleDataStatus>('/sample-data');
  }

  /** Seed the org with the Galil Steel sample dataset (site, period, activities, target + scenarios). */
  async loadSampleData(): Promise<SampleDataLoadResult> {
    return this.fetch<SampleDataLoadResult>('/sample-data', { method: 'POST' });
  }

  /** Remove every sample record (never touches the user's own data). */
  async removeSampleData(): Promise<SampleDataRemoveResult> {
    return this.fetch<SampleDataRemoveResult>('/sample-data', { method: 'DELETE' });
  }

  async getSupportedRegions(): Promise<Region[]> {
    return this.fetch<Region[]>('/organization/regions');
  }

  // Every region the factor library actually covers — richer than the 5 org-level
  // regions; feeds the site grid-region picker.
  async getFactorRegions(): Promise<FactorRegion[]> {
    return this.fetch<FactorRegion[]>('/reference/factor-regions');
  }

  async getSites(): Promise<Site[]> {
    return this.fetch<Site[]>('/organization/sites');
  }

  async createSite(data: { name: string; country_code?: string; address?: string; grid_region?: string }): Promise<Site> {
    return this.fetch<Site>('/organization/sites', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateSite(
    siteId: string,
    data: { name?: string; country_code?: string; address?: string; grid_region?: string; is_active?: boolean }
  ): Promise<Site> {
    return this.fetch<Site>(`/organization/sites/${siteId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteSite(siteId: string): Promise<void> {
    await this.fetch(`/organization/sites/${siteId}`, { method: 'DELETE' });
  }

  async getSiteDetail(siteId: string, periodId?: string): Promise<SiteDetail> {
    const query = periodId ? `?period_id=${periodId}` : '';
    return this.fetch<SiteDetail>(`/organization/sites/${siteId}${query}`);
  }

  // Data Hub
  async getHubOverview(periodId?: string, siteId?: string): Promise<HubOverview> {
    const params = new URLSearchParams();
    if (periodId) params.set('period_id', periodId);
    if (siteId) params.set('site_id', siteId);
    const query = params.size ? `?${params.toString()}` : '';
    return this.fetch<HubOverview>(`/hub/overview${query}`);
  }

  async getHubProfile(siteId?: string): Promise<HubProfileEntryResponse[]> {
    const query = siteId ? `?site_id=${siteId}` : '';
    return this.fetch<HubProfileEntryResponse[]>(`/hub/profile${query}`);
  }

  async saveHubProfile(
    entries: HubProfileEntry[],
    siteId?: string
  ): Promise<HubProfileEntryResponse[]> {
    return this.fetch<HubProfileEntryResponse[]>('/hub/profile', {
      method: 'PUT',
      body: JSON.stringify({ site_id: siteId ?? null, entries }),
    });
  }

  async getHubQuestions(categoryCode: string, periodId?: string): Promise<HubQuestion[]> {
    const params = new URLSearchParams({ category_code: categoryCode });
    if (periodId) params.set('period_id', periodId);
    return this.fetch<HubQuestion[]>(`/hub/questions?${params.toString()}`);
  }

  /** Download the auditor punch-list (verification pack) as CSV. */
  async downloadPunchList(periodId?: string): Promise<void> {
    const token = this.getToken();
    const params = new URLSearchParams({ format: 'csv' });
    if (periodId) params.set('period_id', periodId);
    const response = await fetch(`${API_BASE}/hub/punch-list?${params.toString()}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Export failed' }));
      throw new Error(error.detail || `Export failed: ${response.status}`);
    }
    const blob = await response.blob();
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = 'climatrix-punch-list.csv';
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(blobUrl);
    document.body.removeChild(a);
  }

  async getSitesBreakdown(periodId?: string): Promise<SiteEmissionSummary[]> {
    const query = periodId ? `?period_id=${periodId}` : '';
    return this.fetch<SiteEmissionSummary[]>(`/organization/sites-breakdown${query}`);
  }

  // Import
  async previewImport(periodId: string, file: File): Promise<ImportPreview> {
    const formData = new FormData();
    formData.append('file', file);

    // Use template endpoint for Excel files (client's GHG template format)
    const isExcel = file.name.toLowerCase().endsWith('.xlsx');
    const endpoint = isExcel
      ? `${API_BASE}/periods/${periodId}/import/template/preview`
      : `${API_BASE}/periods/${periodId}/import/preview`;

    const token = this.getToken();
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Import preview failed' }));
      throw new Error(error.detail || 'Import preview failed');
    }

    const data = await response.json();

    // Transform template preview response to standard format
    if (isExcel && data.total_activities !== undefined) {
      // Build rows from sheets data
      const rows: ImportRow[] = [];
      let rowNum = 1;

      // Collect activities from each scope
      for (const [scopeNum, scopeData] of Object.entries(data.by_scope || {})) {
        const scope = parseInt(scopeNum);
        const activities =
          (scopeData as {
            activities?: {
              category_code: string;
              activity_key: string;
              description: string;
              quantity: number;
              unit: string;
              activity_date?: string;
              warnings?: string[];
            }[];
          }).activities || [];
        for (const act of activities) {
          rows.push({
            row_number: rowNum++,
            is_valid: true,
            scope,
            category_code: act.category_code,
            activity_key: act.activity_key,
            description: act.description,
            quantity: act.quantity,
            unit: act.unit,
            activity_date: act.activity_date || new Date().toISOString().split('T')[0],
            errors: [],
            warnings: act.warnings || [],
          });
        }
      }

      // If no detailed rows, create summary rows from sheets
      if (rows.length === 0 && data.sheets) {
        for (const sheet of data.sheets) {
          if (sheet.parsed_rows > 0) {
            rows.push({
              row_number: rowNum++,
              is_valid: true,
              scope: sheet.scope,
              category_code: sheet.category_code,
              activity_key: sheet.sheet_name,
              description: `${sheet.parsed_rows} activities from ${sheet.sheet_name}`,
              quantity: sheet.parsed_rows,
              unit: 'activities',
              activity_date: new Date().toISOString().split('T')[0],
              errors: sheet.errors || [],
              warnings: sheet.warnings || [],
            });
          }
        }
      }

      return {
        total_rows: data.total_activities,
        valid_rows: data.total_activities,
        invalid_rows: 0,
        rows,
        columns_found: ['scope', 'category_code', 'activity_key', 'quantity', 'unit', 'description'],
        columns_missing: [],
      };
    }

    return data;
  }

  async importActivities(periodId: string, file: File, siteId?: string): Promise<ImportResult> {
    const formData = new FormData();
    formData.append('file', file);

    // Use template endpoint for Excel files (client's GHG template format)
    const isExcel = file.name.toLowerCase().endsWith('.xlsx');
    let endpoint = isExcel
      ? `${API_BASE}/periods/${periodId}/import/template`
      : `${API_BASE}/periods/${periodId}/import`;

    // Add site_id as query parameter if provided
    if (siteId) {
      endpoint += `?site_id=${siteId}`;
    }

    const token = this.getToken();
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Import failed' }));
      throw new Error(error.detail || 'Import failed');
    }

    const data = await response.json();

    // Transform template import response to standard format
    if (isExcel && (data.total_activities !== undefined || data.activities_created !== undefined)) {
      return {
        total_rows: data.total_activities || data.activities_created,
        imported: data.imported || data.activities_created,
        failed: data.failed || data.activities_failed || 0,
        import_batch_id: data.import_batch_id,
        errors: (data.errors || []).map((e: ImportErrorPayload) => ({
          row: e.row,
          activity_key: e.activity_key,
          // Backend returns 'errors' (array) or 'error' (string) depending on endpoint
          errors: Array.isArray(e.errors) ? e.errors :
                  Array.isArray(e.error) ? e.error :
                  [e.errors || e.error || e.message || 'Unknown error'],
        })),
      };
    }

    // For CSV import or other endpoints, normalize the error format
    if (data.errors) {
      data.errors = data.errors.map((e: ImportErrorPayload) => ({
        row: e.row,
        activity_key: e.activity_key,
        errors: Array.isArray(e.errors) ? e.errors :
                Array.isArray(e.error) ? e.error :
                [e.errors || e.error || e.message || 'Unknown error'],
      }));
    }

    return data;
  }

  async getImportTemplate(): Promise<{ filename: string; content: string; columns: Record<string, string> }> {
    return this.fetch('/import/template?scope=csv');
  }

  async downloadTemplate(scope: '1-2' | '3'): Promise<void> {
    // For Excel templates, fetch as blob
    const headers: HeadersInit = {};
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}/import/template?scope=${scope}`, {
      headers,
    });

    if (!response.ok) {
      throw new Error(`Failed to download template: ${response.statusText}`);
    }

    const blob = await response.blob();
    const filename = scope === '3' ? 'climatrix_scope3_template.xlsx' : 'climatrix_scope1and2_template.xlsx';
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }

  // ============================================================================
  // Import Batch Tracking
  // ============================================================================

  async getImportBatches(periodId?: string, limit = 20): Promise<ImportBatch[]> {
    const params = new URLSearchParams();
    if (periodId) params.append('period_id', periodId);
    params.append('limit', String(limit));
    return this.fetch<ImportBatch[]>(`/import/batches?${params}`);
  }

  async getImportBatch(batchId: string): Promise<ImportBatchDetail> {
    return this.fetch<ImportBatchDetail>(`/import/batches/${batchId}`);
  }

  async getImportBatchActivities(batchId: string): Promise<{
    batch_id: string;
    file_name: string;
    activity_count: number;
    activities: Array<{
      id: string;
      scope: number;
      category_code: string;
      activity_key: string;
      description: string;
      quantity: number;
      unit: string;
      activity_date: string | null;
      emission: {
        co2e_kg: number | null;
        factor_value: number | null;
        factor_unit: string | null;
        factor_source: string | null;
        formula: string | null;
      } | null;
    }>;
  }> {
    return this.fetch(`/import/batches/${batchId}/activities`);
  }

  async deleteImportBatch(batchId: string, deleteActivities = false): Promise<{
    message: string;
    batch_id: string;
    deleted_activities: number;
  }> {
    return this.fetch(`/import/batches/${batchId}?delete_activities=${deleteActivities}`, {
      method: 'DELETE',
    });
  }

  // ============================================================================
  // Bulk Delete Methods
  // ============================================================================

  /**
   * Delete ALL activities for a specific reporting period.
   * Also deletes associated emissions and import batches.
   */
  async deletePeriodActivities(periodId: string): Promise<{
    deleted_activities: number;
    deleted_emissions: number;
    message: string;
  }> {
    return this.fetch(`/periods/${periodId}/activities`, {
      method: 'DELETE',
    });
  }

  /**
   * Delete ALL activities for the organization (across all periods).
   * Requires confirm=true parameter as safety measure.
   */
  async deleteOrganizationActivities(confirm = false): Promise<{
    deleted_activities: number;
    deleted_emissions: number;
    message: string;
  }> {
    return this.fetch(`/organization/activities?confirm=${confirm}`, {
      method: 'DELETE',
    });
  }

  // ============================================================================
  // Admin Methods (Super Admin Only)
  // ============================================================================

  async getAdminStats(): Promise<AdminStats> {
    return this.fetch<AdminStats>('/admin/stats');
  }

  async getAdminCockpit(): Promise<CockpitData> {
    return this.fetch<CockpitData>('/admin/cockpit');
  }

  async getAdminOrganizations(skip = 0, limit = 50): Promise<AdminOrganization[]> {
    return this.fetch<AdminOrganization[]>(`/admin/organizations?skip=${skip}&limit=${limit}`);
  }

  async getAdminOrganization(orgId: string): Promise<AdminOrganization> {
    return this.fetch<AdminOrganization>(`/admin/organizations/${orgId}`);
  }

  async getAdminUsers(skip = 0, limit = 50, orgId?: string): Promise<AdminUser[]> {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (orgId) params.append('org_id', orgId);
    return this.fetch<AdminUser[]>(`/admin/users?${params}`);
  }

  async getAdminActivities(skip = 0, limit = 100, orgId?: string, scope?: number): Promise<AdminActivity[]> {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (orgId) params.append('org_id', orgId);
    if (scope) params.append('scope', String(scope));
    return this.fetch<AdminActivity[]>(`/admin/activities?${params}`);
  }

  async getAdminOrgReport(orgId: string): Promise<AdminOrgReport> {
    return this.fetch<AdminOrgReport>(`/admin/organizations/${orgId}/report`);
  }

  // Smart Import (AI-powered)
  async smartImportPreview(periodId: string, file: File): Promise<SmartImportPreview> {
    const formData = new FormData();
    formData.append('file', file);

    const token = this.getToken();
    const response = await fetch(`${API_BASE}/periods/${periodId}/import/analyze-columns`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Smart import analysis failed' }));
      throw new Error(error.detail || 'Smart import analysis failed');
    }

    return response.json();
  }

  async smartImport(periodId: string, file: File): Promise<SmartImportResult> {
    const formData = new FormData();
    formData.append('file', file);

    const token = this.getToken();
    const response = await fetch(`${API_BASE}/periods/${periodId}/import/smart`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Smart import failed' }));
      throw new Error(error.detail || 'Smart import failed');
    }

    return response.json();
  }

  async getImportJobStatus(jobId: string): Promise<ImportJobStatus> {
    return this.fetch(`/import/jobs/${jobId}`);
  }

  // ============================================================================
  // Unified AI Import (handles ANY file type including multi-sheet Excel)
  // ============================================================================

  async unifiedImportPreview(file: File): Promise<UnifiedImportPreview> {
    const formData = new FormData();
    formData.append('file', file);

    const token = this.getToken();
    const response = await fetch(`${API_BASE}/unified/preview`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unified import preview failed' }));
      throw new Error(error.detail || 'Unified import preview failed');
    }

    return response.json();
  }

  async unifiedImport(periodId: string, file: File, siteId?: string): Promise<UnifiedImportResult> {
    const formData = new FormData();
    formData.append('file', file);

    let url = `${API_BASE}/unified/import/${periodId}`;
    if (siteId) {
      url += `?site_id=${siteId}`;
    }

    const token = this.getToken();
    const response = await fetch(url, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unified import failed' }));
      throw new Error(error.detail || 'Unified import failed');
    }

    return response.json();
  }

  // ============================================================================
  // AI Ingestion Funnel ("drop any file" → staged rows → review → commit)
  // ============================================================================

  async ingestUpload(file: File, reportingPeriodId?: string, siteId?: string): Promise<IngestionSessionDetail> {
    const formData = new FormData();
    formData.append('file', file);
    if (reportingPeriodId) formData.append('reporting_period_id', reportingPeriodId);
    if (siteId) formData.append('site_id', siteId);

    const token = this.getToken();
    // Parsing can take a while (per-sheet LLM mapping) — allow up to 5 minutes.
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000);
    let response: Response;
    try {
      response = await fetch(`${API_BASE}/ingest`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timeoutId);
    }
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(
        typeof error.detail === 'string' ? error.detail : 'Upload failed'
      );
    }
    return response.json();
  }

  async getIngestSession(sessionId: string): Promise<IngestionSessionDetail> {
    return this.fetch<IngestionSessionDetail>(`/ingest/${sessionId}`);
  }

  async listIngestSessions(): Promise<IngestionSession[]> {
    return this.fetch<IngestionSession[]>(`/ingest`);
  }

  async answerIngestQuestions(
    sessionId: string,
    answers: { question_id: string; answer: string }[]
  ): Promise<IngestionSessionDetail> {
    return this.fetch<IngestionSessionDetail>(`/ingest/${sessionId}/answers`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
    });
  }

  async patchIngestRow(
    sessionId: string,
    rowId: string,
    patch: { status?: string; activity_key?: string; quantity?: number; unit?: string }
  ): Promise<StagedRow> {
    return this.fetch<StagedRow>(`/ingest/${sessionId}/rows/${rowId}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    });
  }

  async commitIngestSession(
    sessionId: string,
    reportingPeriodId?: string,
    siteId?: string
  ): Promise<IngestionSessionDetail> {
    return this.fetch<IngestionSessionDetail>(`/ingest/${sessionId}/commit`, {
      method: 'POST',
      body: JSON.stringify({
        reporting_period_id: reportingPeriodId ?? null,
        site_id: siteId ?? null,
      }),
    });
  }

  // ============================================================================
  // CBAM Module (Phase 2) - EU Carbon Border Adjustment Mechanism
  // ============================================================================

  // CBAM Installations
  async getCBAMInstallations(filters?: {
    country_code?: string;
    sector?: string;
  }): Promise<CBAMInstallation[]> {
    const params = new URLSearchParams();
    if (filters?.country_code) params.append('country_code', filters.country_code);
    if (filters?.sector) params.append('sector', filters.sector);
    const query = params.toString() ? `?${params}` : '';
    return this.fetch<CBAMInstallation[]>(`/cbam/installations${query}`);
  }

  async createCBAMInstallation(data: CBAMInstallationCreate): Promise<CBAMInstallation> {
    return this.fetch<CBAMInstallation>('/cbam/installations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getCBAMInstallation(installationId: string): Promise<CBAMInstallation> {
    return this.fetch<CBAMInstallation>(`/cbam/installations/${installationId}`);
  }

  async updateCBAMInstallation(
    installationId: string,
    data: CBAMInstallationUpdate
  ): Promise<CBAMInstallation> {
    return this.fetch<CBAMInstallation>(`/cbam/installations/${installationId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteCBAMInstallation(installationId: string): Promise<void> {
    await this.fetch(`/cbam/installations/${installationId}`, {
      method: 'DELETE',
    });
  }

  // CBAM Imports
  async getCBAMImports(filters?: {
    installation_id?: string;
    cn_code?: string;
    sector?: string;
    year?: number;
    quarter?: number;
  }): Promise<CBAMImport[]> {
    const params = new URLSearchParams();
    if (filters?.installation_id) params.append('installation_id', filters.installation_id);
    if (filters?.cn_code) params.append('cn_code', filters.cn_code);
    if (filters?.sector) params.append('sector', filters.sector);
    if (filters?.year) params.append('year', String(filters.year));
    if (filters?.quarter) params.append('quarter', String(filters.quarter));
    const query = params.toString() ? `?${params}` : '';
    return this.fetch<CBAMImport[]>(`/cbam/imports${query}`);
  }

  async createCBAMImport(data: CBAMImportCreate): Promise<CBAMImport> {
    return this.fetch<CBAMImport>('/cbam/imports', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getCBAMImport(importId: string): Promise<CBAMImport> {
    return this.fetch<CBAMImport>(`/cbam/imports/${importId}`);
  }

  async deleteCBAMImport(importId: string): Promise<void> {
    await this.fetch(`/cbam/imports/${importId}`, {
      method: 'DELETE',
    });
  }

  // CBAM Calculation Preview
  async calculateCBAMEmissions(
    data: CBAMEmissionCalculationRequest
  ): Promise<CBAMEmissionCalculationResult> {
    return this.fetch<CBAMEmissionCalculationResult>('/cbam/calculate-emissions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // CBAM public screening (50 t exemption checker — no auth required)
  async cbamScreen(data: CBAMScreenRequest): Promise<CBAMScreenResult> {
    return this.fetch<CBAMScreenResult>('/cbam/screen', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // CBAM screening reference values (ETS price, markup, sector intensities)
  async getCBAMScreenDefaults(): Promise<CBAMScreenDefaults> {
    return this.fetch<CBAMScreenDefaults>('/cbam/screen-defaults');
  }

  // CBAM supplier portal (Phase 3) — importer side
  async getCBAMDataRequests(filters?: {
    status?: string;
    installation_id?: string;
  }): Promise<CBAMDataRequest[]> {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.installation_id) params.append('installation_id', filters.installation_id);
    const query = params.toString() ? `?${params}` : '';
    return this.fetch<CBAMDataRequest[]>(`/cbam/data-requests${query}`);
  }

  async createCBAMDataRequest(data: CBAMDataRequestCreate): Promise<CBAMDataRequest> {
    return this.fetch<CBAMDataRequest>('/cbam/data-requests', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async remindCBAMDataRequest(requestId: string): Promise<CBAMDataRequest> {
    return this.fetch<CBAMDataRequest>(`/cbam/data-requests/${requestId}/remind`, {
      method: 'POST',
    });
  }

  // CBAM certificate ledger (definitive regime)
  async getCBAMCertificates(): Promise<CBAMCertificateEntry[]> {
    return this.fetch<CBAMCertificateEntry[]>('/cbam/certificates');
  }

  async createCBAMCertificateEntry(
    data: CBAMCertificateEntryCreate
  ): Promise<CBAMCertificateEntry> {
    return this.fetch<CBAMCertificateEntry>('/cbam/certificates', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteCBAMCertificateEntry(entryId: string): Promise<void> {
    await this.fetch(`/cbam/certificates/${entryId}`, { method: 'DELETE' });
  }

  async getCBAMCertificateSummary(
    year: number
  ): Promise<CBAMCertificateSummary> {
    return this.fetch<CBAMCertificateSummary>(
      `/cbam/certificates/summary/${year}`
    );
  }

  // CBAM supplier portal — PUBLIC magic-link endpoints (no auth). These use
  // raw fetch and throw PublicApiError so the page can tell 404 from 410.
  async getCBAMSupplierRequest(token: string): Promise<CBAMSupplierRequestContext> {
    return publicJsonFetch<CBAMSupplierRequestContext>(
      `${API_BASE}/cbam/supplier-data/${encodeURIComponent(token)}`
    );
  }

  async submitCBAMSupplierData(
    token: string,
    rows: CBAMSupplierEmissionRowInput[]
  ): Promise<CBAMSupplierRequestContext> {
    return publicJsonFetch<CBAMSupplierRequestContext>(
      `${API_BASE}/cbam/supplier-data/${encodeURIComponent(token)}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rows }),
      }
    );
  }

  // CBAM CN Code Search
  async searchCBAMCNCodes(
    query: string,
    sector?: string,
    limit = 20
  ): Promise<CBAMCNCode[]> {
    const params = new URLSearchParams({ query, limit: String(limit) });
    if (sector) params.append('sector', sector);
    return this.fetch<CBAMCNCode[]>(`/cbam/cn-codes?${params}`);
  }

  // CBAM Quarterly Reports
  async getCBAMQuarterlyReports(year?: number): Promise<CBAMQuarterlyReport[]> {
    const params = year ? `?year=${year}` : '';
    return this.fetch<CBAMQuarterlyReport[]>(`/cbam/reports/quarterly${params}`);
  }

  async generateCBAMQuarterlyReport(
    year: number,
    quarter: number
  ): Promise<CBAMQuarterlyReport> {
    return this.fetch<CBAMQuarterlyReport>(`/cbam/reports/quarterly/${year}/${quarter}`, {
      method: 'POST',
    });
  }

  async submitCBAMQuarterlyReport(
    year: number,
    quarter: number
  ): Promise<{ message: string }> {
    return this.fetch<{ message: string }>(
      `/cbam/reports/quarterly/${year}/${quarter}/submit`,
      { method: 'POST' }
    );
  }

  async exportCBAMQuarterlyReportXML(year: number, quarter: number): Promise<Blob> {
    const token = this.getToken();
    const response = await fetch(
      `${API_BASE}/cbam/reports/quarterly/${year}/${quarter}/export/xml`,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }
    );
    if (!response.ok) {
      throw new Error('Failed to export quarterly report XML');
    }
    return response.blob();
  }

  async exportCBAMQuarterlyReportCSV(year: number, quarter: number): Promise<Blob> {
    const token = this.getToken();
    const response = await fetch(
      `${API_BASE}/cbam/reports/quarterly/${year}/${quarter}/export/csv`,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }
    );
    if (!response.ok) {
      throw new Error('Failed to export quarterly report CSV');
    }
    return response.blob();
  }

  async getCBAMQuarterlyReportEUFormat(
    year: number,
    quarter: number
  ): Promise<CBAMQuarterlyReportEUFormat> {
    return this.fetch<CBAMQuarterlyReportEUFormat>(
      `/cbam/reports/quarterly/${year}/${quarter}/export/eu-format`
    );
  }

  // CBAM Annual Declarations
  async getCBAMAnnualDeclarations(): Promise<CBAMAnnualDeclaration[]> {
    return this.fetch<CBAMAnnualDeclaration[]>('/cbam/reports/annual');
  }

  // Generate or regenerate the annual declaration draft (idempotent per
  // org + year: regenerating replaces the existing draft).
  async generateCBAMAnnualDeclaration(
    year: number
  ): Promise<CBAMAnnualDeclarationDetail> {
    return this.fetch<CBAMAnnualDeclarationDetail>(`/cbam/reports/annual/${year}`, {
      method: 'POST',
    });
  }

  // Full declaration draft package (lines, per-CN breakdown, data quality,
  // assumptions). 404s until a draft has been generated for the year.
  async getCBAMAnnualDeclarationDetail(
    year: number
  ): Promise<CBAMAnnualDeclarationDetail> {
    return this.fetch<CBAMAnnualDeclarationDetail>(`/cbam/reports/annual/${year}`);
  }

  // Move a declaration between 'draft' and 'ready' (submission stays on
  // hold until the CBAM Registry schema is validated).
  async updateCBAMAnnualDeclarationStatus(
    year: number,
    status: Extract<CBAMReportStatus, 'draft' | 'ready'>
  ): Promise<CBAMAnnualDeclaration> {
    return this.fetch<CBAMAnnualDeclaration>(`/cbam/reports/annual/${year}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  }

  async exportCBAMAnnualDeclarationCSV(year: number): Promise<Blob> {
    const token = this.getToken();
    const response = await fetch(
      `${API_BASE}/cbam/reports/annual/${year}/export/csv`,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }
    );
    if (!response.ok) {
      throw new Error('Failed to export annual declaration CSV');
    }
    return response.blob();
  }

  async exportCBAMAnnualDeclarationXML(year: number): Promise<Blob> {
    const token = this.getToken();
    const response = await fetch(
      `${API_BASE}/cbam/reports/annual/${year}/export/xml`,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }
    );
    if (!response.ok) {
      throw new Error('Failed to export annual declaration XML');
    }
    return response.blob();
  }

  // CBAM Dashboard
  async getCBAMDashboard(): Promise<CBAMDashboard> {
    return this.fetch<CBAMDashboard>('/cbam/dashboard');
  }

  // ============================================================================
  // Billing
  // ============================================================================

  async getSubscription(): Promise<SubscriptionInfo> {
    return this.fetch<SubscriptionInfo>('/billing/subscription');
  }

  async getPlans(): Promise<PlansResponse> {
    return this.fetch<PlansResponse>('/billing/plans');
  }

  async createCheckout(
    plan: SubscriptionPlan,
    successUrl: string,
    cancelUrl: string,
    cadence: 'monthly' | 'annual' = 'annual'
  ): Promise<CheckoutResponse> {
    return this.fetch<CheckoutResponse>('/billing/checkout', {
      method: 'POST',
      body: JSON.stringify({
        plan,
        cadence,
        success_url: successUrl,
        cancel_url: cancelUrl,
      }),
    });
  }

  async createReportPassCheckout(
    reportYear: number,
    successUrl: string,
    cancelUrl: string
  ): Promise<CheckoutResponse> {
    return this.fetch<CheckoutResponse>('/billing/report-pass/checkout', {
      method: 'POST',
      body: JSON.stringify({
        report_year: reportYear,
        success_url: successUrl,
        cancel_url: cancelUrl,
      }),
    });
  }

  async createPortal(returnUrl: string): Promise<PortalResponse> {
    return this.fetch<PortalResponse>('/billing/portal', {
      method: 'POST',
      body: JSON.stringify({ return_url: returnUrl }),
    });
  }

  async cancelSubscription(): Promise<{ message: string }> {
    return this.fetch<{ message: string }>('/billing/cancel', {
      method: 'POST',
    });
  }

  // ============================================================================
  // User Invitations
  // ============================================================================

  async inviteUser(email: string, role: string = 'editor'): Promise<Invitation> {
    return this.fetch<Invitation>('/auth/invitations', {
      method: 'POST',
      body: JSON.stringify({ email, role }),
    });
  }

  async getInvitations(): Promise<Invitation[]> {
    return this.fetch<Invitation[]>('/auth/invitations');
  }

  async checkInvitation(token: string): Promise<InvitationCheck> {
    return this.fetch<InvitationCheck>(`/auth/invitations/${token}/check`);
  }

  async acceptInvitation(
    token: string,
    fullName: string,
    password: string
  ): Promise<LoginResponse> {
    return this.fetch<LoginResponse>('/auth/invitations/accept', {
      method: 'POST',
      body: JSON.stringify({
        token,
        full_name: fullName,
        password,
      }),
    });
  }

  async resendInvitation(invitationId: string): Promise<{ message: string }> {
    return this.fetch<{ message: string }>(`/auth/invitations/${invitationId}/resend`, {
      method: 'POST',
    });
  }

  async cancelInvitation(invitationId: string): Promise<{ message: string }> {
    return this.fetch<{ message: string }>(`/auth/invitations/${invitationId}`, {
      method: 'DELETE',
    });
  }

  // ============================================================================
  // Audit Logs
  // ============================================================================

  async getAuditLogs(params?: {
    limit?: number;
    offset?: number;
    action?: AuditAction;
    resource_type?: string;
    user_id?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<AuditLogsResponse> {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.offset) queryParams.set('offset', params.offset.toString());
    if (params?.action) queryParams.set('action', params.action);
    if (params?.resource_type) queryParams.set('resource_type', params.resource_type);
    if (params?.user_id) queryParams.set('user_id', params.user_id);
    if (params?.start_date) queryParams.set('start_date', params.start_date);
    if (params?.end_date) queryParams.set('end_date', params.end_date);

    const query = queryParams.toString();
    return this.fetch<AuditLogsResponse>(`/audit/logs${query ? `?${query}` : ''}`);
  }

  async getAuditStats(): Promise<AuditStatsResponse> {
    return this.fetch<AuditStatsResponse>('/audit/stats');
  }

  async getAuditActions(): Promise<{ actions: string[] }> {
    return this.fetch<{ actions: string[] }>('/audit/actions');
  }

  async getAuditResourceTypes(): Promise<{ resource_types: string[] }> {
    return this.fetch<{ resource_types: string[] }>('/audit/resource-types');
  }

  // ============================================================================
  // Decarbonization Pathways
  // ============================================================================

  // Emission Profile Analysis
  async getEmissionProfile(periodId: string): Promise<EmissionProfileAnalysis> {
    return this.fetch<EmissionProfileAnalysis>(`/decarbonization/profile?period_id=${periodId}`);
  }

  // Personalized Recommendations
  async getRecommendations(
    periodId: string,
    params?: { limit?: number; category?: InitiativeCategory }
  ): Promise<PersonalizedRecommendation[]> {
    const queryParams = new URLSearchParams({ period_id: periodId });
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.category) queryParams.set('category', params.category);
    return this.fetch<PersonalizedRecommendation[]>(`/decarbonization/recommendations?${queryParams}`);
  }

  // Targets
  async getDecarbonizationTargets(): Promise<DecarbonizationTarget[]> {
    return this.fetch<DecarbonizationTarget[]>('/decarbonization/targets');
  }

  async createDecarbonizationTarget(data: TargetCreateRequest): Promise<DecarbonizationTarget> {
    return this.fetch<DecarbonizationTarget>('/decarbonization/targets', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateDecarbonizationTarget(
    id: string,
    data: TargetCreateRequest
  ): Promise<DecarbonizationTarget> {
    return this.fetch<DecarbonizationTarget>(`/decarbonization/targets/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async getDecarbonizationTarget(targetId: string): Promise<DecarbonizationTarget> {
    return this.fetch<DecarbonizationTarget>(`/decarbonization/targets/${targetId}`);
  }

  async getTargetTrajectory(targetId: string): Promise<TrajectoryResponse> {
    return this.fetch<TrajectoryResponse>(`/decarbonization/targets/${targetId}/trajectory`);
  }

  async getTargetProgress(targetId: string, periodId: string): Promise<TargetProgress> {
    return this.fetch<TargetProgress>(
      `/decarbonization/targets/${targetId}/progress?period_id=${periodId}`
    );
  }

  async deleteDecarbonizationTarget(targetId: string): Promise<{ message: string }> {
    return this.fetch<{ message: string }>(`/decarbonization/targets/${targetId}`, {
      method: 'DELETE',
    });
  }

  // Initiative Library
  async getInitiatives(params?: {
    category?: InitiativeCategory;
    scope?: number;
  }): Promise<Initiative[]> {
    const queryParams = new URLSearchParams();
    if (params?.category) queryParams.set('category', params.category);
    if (params?.scope) queryParams.set('scope', params.scope.toString());
    const query = queryParams.toString();
    return this.fetch<Initiative[]>(`/decarbonization/initiatives${query ? `?${query}` : ''}`);
  }

  async getInitiative(initiativeId: string): Promise<Initiative> {
    return this.fetch<Initiative>(`/decarbonization/initiatives/${initiativeId}`);
  }

  // Scenarios
  async getScenarios(targetId?: string): Promise<Scenario[]> {
    const query = targetId ? `?target_id=${targetId}` : '';
    return this.fetch<Scenario[]>(`/decarbonization/scenarios${query}`);
  }

  async createScenario(data: ScenarioCreateRequest): Promise<Scenario> {
    return this.fetch<Scenario>('/decarbonization/scenarios', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async activateScenario(scenarioId: string): Promise<{ message: string }> {
    return this.fetch<{ message: string }>(`/decarbonization/scenarios/${scenarioId}/activate`, {
      method: 'POST',
    });
  }

  async deleteScenario(scenarioId: string): Promise<{ message: string }> {
    return this.fetch<{ message: string }>(`/decarbonization/scenarios/${scenarioId}`, {
      method: 'DELETE',
    });
  }

  // Scenario Initiatives
  async getScenarioInitiatives(scenarioId: string): Promise<ScenarioInitiative[]> {
    return this.fetch<ScenarioInitiative[]>(`/decarbonization/scenarios/${scenarioId}/initiatives`);
  }

  async addInitiativeToScenario(
    scenarioId: string,
    data: ScenarioInitiativeRequest
  ): Promise<ScenarioInitiative> {
    return this.fetch<ScenarioInitiative>(`/decarbonization/scenarios/${scenarioId}/initiatives`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async removeInitiativeFromScenario(
    scenarioId: string,
    initiativeId: string
  ): Promise<{ message: string }> {
    return this.fetch<{ message: string }>(
      `/decarbonization/scenarios/${scenarioId}/initiatives/${initiativeId}`,
      { method: 'DELETE' }
    );
  }

  // Progress Tracking
  async getEmissionCheckpoints(targetId: string): Promise<EmissionCheckpoint[]> {
    return this.fetch<EmissionCheckpoint[]>(`/decarbonization/progress/checkpoints?target_id=${targetId}`);
  }

  async createEmissionCheckpoint(
    targetId: string,
    periodId: string
  ): Promise<EmissionCheckpoint> {
    return this.fetch<EmissionCheckpoint>(
      `/decarbonization/progress/checkpoints?target_id=${targetId}&period_id=${periodId}`,
      { method: 'POST' }
    );
  }

  // Leads (lightweight CRM)
  async captureLead(data: LeadCapture): Promise<Lead> {
    return this.fetch<Lead>('/leads', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getLeads(params?: { status?: LeadStatus; source?: LeadSource }): Promise<Lead[]> {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.source) query.append('source', params.source);
    const qs = query.toString();
    return this.fetch<Lead[]>(`/leads${qs ? `?${qs}` : ''}`);
  }

  async updateLead(
    leadId: string,
    data: { status?: LeadStatus; notes?: string }
  ): Promise<Lead> {
    return this.fetch<Lead>(`/leads/${leadId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async sendLeadFollowUp(leadId: string): Promise<Lead> {
    return this.fetch<Lead>(`/leads/${leadId}/follow-up`, { method: 'POST' });
  }
}

// CBAM Types for API
import type {
  CBAMInstallation,
  CBAMInstallationCreate,
  CBAMInstallationUpdate,
  CBAMImport,
  CBAMImportCreate,
  CBAMQuarterlyReport,
  CBAMAnnualDeclaration,
  CBAMAnnualDeclarationDetail,
  CBAMReportStatus,
  CBAMCNCode,
  CBAMEmissionCalculationRequest,
  CBAMEmissionCalculationResult,
  CBAMDashboard,
  CBAMQuarterlyReportEUFormat,
  CBAMScreenDefaults,
  CBAMDataRequest,
  CBAMDataRequestCreate,
  CBAMSupplierRequestContext,
  CBAMSupplierEmissionRowInput,
  CBAMCertificateEntry,
  CBAMCertificateEntryCreate,
  CBAMCertificateSummary,
} from './types';

// Error for public (no-auth) endpoints that keeps the HTTP status so pages
// can distinguish 404 (unknown link) from 410 (expired link).
export class PublicApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'PublicApiError';
    this.status = status;
  }
}

async function publicJsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const message =
      typeof error.detail === 'string' ? error.detail : `Request failed (${response.status})`;
    throw new PublicApiError(response.status, message);
  }
  return response.json();
}

// CBAM Public Screening Types (POST /cbam/screen)
export interface CBAMScreenItemInput {
  cn_code_or_sector: string;
  mass_kg: number;
  origin_country?: string;
}

export interface CBAMScreenRequest {
  items: CBAMScreenItemInput[];
  ets_price_eur?: number;
}

export interface CBAMScreenItemResult {
  cn_code_or_sector: string;
  sector: string | null;
  sector_label: string | null;
  origin_country: string | null;
  mass_kg: number;
  covered: boolean;
  counts_toward_threshold: boolean;
  estimated_emissions_tco2e: number;
  estimated_certificate_cost_eur: number;
}

export interface CBAMScreenResult {
  threshold_kg: number;
  in_threshold_mass_kg: number;
  headroom_kg: number;
  exempt: boolean;
  ets_price_eur: number;
  default_value_markup_pct: number;
  total_estimated_emissions_tco2e: number;
  total_estimated_certificate_cost_eur: number;
  items: CBAMScreenItemResult[];
  assumptions: string[];
}

// Smart Import Types
export interface SmartImportPreview {
  success: boolean;
  detected_structure: string;
  column_mappings: ColumnMapping[];
  date_column: string | null;
  description_column: string | null;
  warnings: string[];
  sample_extraction: {
    activity_key: string;
    quantity: number;
    unit: string;
    description: string;
  }[];
}

export interface ColumnMapping {
  original_header: string;
  activity_key: string | null;
  scope: number | null;
  category_code: string | null;
  detected_unit: string | null;
  column_type: string;
  confidence: number;
  notes: string | null;
}

export interface SmartImportResult {
  job_id: string;
  status: string;
  message: string;
  ai_mapping_preview: {
    detected_structure: string;
    detected_columns: {
      header: string;
      maps_to: string;
      unit: string | null;
      confidence: string;
    }[];
    date_column: string | null;
    warnings: string[];
  };
}

export interface ImportJobStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress_percent: number;
  processed_rows: number;
  total_rows: number;
  successful_rows: number;
  failed_rows: number;
  error_message: string | null;
}

// ============================================================================
// Unified AI Import Types (handles ANY file type including multi-sheet Excel)
// ============================================================================

export interface UnifiedSheetPreview {
  sheet_name: string;
  detected_scope: number | null;
  detected_category: string | null;
  header_row: number;
  total_rows: number;
  columns: string[];
  column_mappings: UnifiedColumnMapping[];
  sample_data: Record<string, unknown>[];
  activities_preview: UnifiedActivityPreview[];
  is_importable: boolean;
  skip_reason: string | null;
  warnings: string[];
}

export interface UnifiedColumnMapping {
  original_header: string;
  activity_key: string | null;
  scope: number | null;
  category_code: string | null;
  detected_unit: string | null;
  column_type: string;
  confidence: number;
  notes: string | null;
}

export interface UnifiedActivityPreview {
  scope: number;
  category_code: string;
  activity_key: string;
  description: string;
  quantity: number;
  unit: string;
  activity_date: string;
  source_sheet: string;
  source_row: number;
  confidence: number;
}

export interface UnifiedImportPreview {
  success: boolean;
  file_name: string;
  file_type: string;
  total_sheets: number;
  importable_sheets: number;
  total_activities: number;
  sheets: UnifiedSheetPreview[];
  warnings: string[];
  errors: string[];
}

export interface UnifiedImportResult {
  success: boolean;
  total_activities: number;
  imported: number;
  failed: number;
  total_co2e_kg: number;
  by_scope: Record<string, number>;
  by_category: Record<string, number>;
  errors: {
    sheet?: string;
    row?: number;
    activity_key?: string;
    error: string;
  }[];
  warnings: string[];
  import_batch_id?: string;
}

// ============================================================================
// Admin Types (Super Admin Only)
// ============================================================================

export interface AdminStats {
  total_organizations: number;
  total_users: number;
  total_activities: number;
  total_co2e_tonnes: number;
  active_organizations: number;
  activities_this_month: number;
}

export interface CockpitClient {
  id: string;
  name: string;
  contact_email: string | null;
  plan: string;
  status: string;
  trial_ends_at: string | null;
  users: number;
  activities: number;
  last_activity_at: string | null;
  total_co2e_tonnes: number;
  created_at: string;
}

export interface CockpitData {
  organizations_total: number;
  organizations_active: number;
  users_total: number;
  activities_total: number;
  total_co2e_tonnes: number;
  mrr_usd: number;
  arr_usd: number;
  revenue_note: string;
  paying_orgs: number;
  trialing_orgs: number;
  leads_total: number;
  leads_open: number;
  signups_14d: { day: string; signups: number }[];
  plans: { plan: string; orgs: number; mrr_usd: number }[];
  lead_pipeline: { status: string; count: number }[];
  lead_sources: { status: string; count: number }[];
  recent_signups: { email: string; organization_name: string; created_at: string }[];
  recent_leads: { email: string; source: string; status: string; created_at: string }[];
  clients: CockpitClient[];
  attention: {
    trials_expiring_7d: {
      organization_id: string;
      name: string;
      contact_email: string | null;
      trial_ends_at: string;
      days_left: number;
    }[];
    stuck_orgs: {
      organization_id: string;
      name: string;
      contact_email: string | null;
      days_since_signup: number;
    }[];
    failed_ingests_7d: {
      organization_name: string;
      filename: string;
      error: string | null;
      created_at: string;
    }[];
  };
}

export interface AdminOrganization {
  id: string;
  name: string;
  country_code: string | null;
  default_region: string;
  is_active: boolean;
  created_at: string;
  user_count: number;
  period_count: number;
  activity_count: number;
  total_co2e_kg: number;
}

export interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  organization_id: string;
  organization_name: string;
  created_at: string;
  last_login: string | null;
}

export interface AdminActivity {
  id: string;
  organization_name: string;
  user_email: string | null;
  scope: number;
  category_code: string;
  activity_key: string;
  description: string;
  quantity: number;
  unit: string;
  co2e_kg: number | null;
  activity_date: string;
  created_at: string;
}

export interface AdminOrgReport {
  organization: {
    id: string;
    name: string;
    country_code: string | null;
  };
  total_co2e_kg: number;
  total_co2e_tonnes: number;
  by_scope: {
    scope_1: { total_co2e_kg: number; activity_count: number; activities: AdminOrgReportActivity[] };
    scope_2: { total_co2e_kg: number; activity_count: number; activities: AdminOrgReportActivity[] };
    scope_3: { total_co2e_kg: number; activity_count: number; activities: AdminOrgReportActivity[] };
  };
}

export interface AdminOrgReportActivity {
  id: string;
  category_code: string;
  activity_key?: string;
  description: string;
  quantity: number;
  unit: string;
  co2e_kg: number | null;
  activity_date?: string;
}

// ============================================================================
// Billing Types
// ============================================================================

export type SubscriptionPlan = 'free' | 'starter' | 'professional' | 'enterprise' | 'report_pass';
export type SubscriptionStatus = 'active' | 'trialing' | 'past_due' | 'canceled' | 'incomplete' | 'unpaid';

export interface PlanLimits {
  activities_per_month: number;
  users: number;
  periods: number;
  sites: number;
  ai_extractions: number;
  export_formats: string[];
  // Scopes committable via Smart Import (Starter = [1,2]); undefined => all.
  smart_import_scopes?: number[];
}

export interface SubscriptionInfo {
  plan: SubscriptionPlan;
  status: SubscriptionStatus | null;
  current_period_end: string | null;
  trial_ends_at: string | null;
  is_trialing: boolean;
  is_expired?: boolean;
  plan_limits: PlanLimits;
  // Report Pass window + purchased add-ons
  licensed_report_year?: number | null;
  plan_expires_at?: string | null;
  extra_users?: number;
  extra_sites?: number;
}

export interface PlanInfo {
  id: SubscriptionPlan;
  name: string;
  limits: PlanLimits;
  price_monthly: number | null;
  price_annual?: number | null;
  price_one_time?: number | null;
  features: string[];
}

export interface PlansResponse {
  plans: PlanInfo[];
}

export interface CheckoutResponse {
  url: string;
}

export interface PortalResponse {
  url: string;
}

// ============================================================================
// User Invitation Types
// ============================================================================

export type InvitationStatus = 'pending' | 'accepted' | 'expired' | 'canceled';

export interface Invitation {
  id: string;
  email: string;
  role: string;
  status: InvitationStatus;
  invited_by_email: string;
  created_at: string;
  expires_at: string;
}

export interface InvitationCheck {
  email: string;
  role: string;
  organization_name: string;
  expires_at: string;
}

// ============================================================================
// Audit Log Types
// ============================================================================

export type AuditAction = 'create' | 'update' | 'delete' | 'login' | 'logout' | 'import' | 'export' | 'status_change' | 'invite' | 'permission_change';

export interface AuditLogEntry {
  id: string;
  action: AuditAction;
  resource_type: string;
  resource_id: string | null;
  description: string;
  details: string | null;
  user_email: string | null;
  ip_address: string | null;
  created_at: string;
}

export interface AuditLogsResponse {
  items: AuditLogEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuditStatsResponse {
  total_events: number;
  events_by_action: Record<string, number>;
  events_by_resource: Record<string, number>;
  recent_activity_count: number;
}

// ============================================================================
// Decarbonization Pathways Types
// ============================================================================

export type TargetType = 'absolute' | 'intensity';
export type TargetFramework = 'sbti_1_5c' | 'sbti_wb2c' | 'net_zero' | 'custom';
export type InitiativeCategory = 'energy_efficiency' | 'renewable_energy' | 'fleet_transport' | 'supply_chain' | 'process_change' | 'behavior_change' | 'waste_reduction' | 'carbon_removal';
export type ComplexityLevel = 'low' | 'medium' | 'high';
export type ScenarioType = 'aggressive' | 'moderate' | 'conservative' | 'custom';
export type InitiativeStatus = 'planned' | 'in_progress' | 'completed' | 'cancelled' | 'on_hold';

export interface EmissionSource {
  activity_key: string;
  display_name: string;
  scope: number;
  category_code: string;
  total_co2e_kg: ApiDecimal;
  total_co2e_tonnes: ApiDecimal;
  percentage_of_total: ApiDecimal;
  site_id?: string;
  site_name?: string;
  activity_count: number;
  data_quality_avg?: ApiDecimal;
}

export interface EmissionProfileAnalysis {
  organization_id: string;
  period_id: string;
  period_name: string;
  analysis_date: string;
  total_co2e_kg: ApiDecimal;
  total_co2e_tonnes: ApiDecimal;
  scope1_co2e_tonnes: ApiDecimal;
  scope2_co2e_tonnes: ApiDecimal;
  scope3_co2e_tonnes: ApiDecimal;
  emissions_by_category: Record<string, ApiDecimal>;
  emissions_by_activity_key: Record<string, ApiDecimal>;
  emissions_by_site: Record<string, ApiDecimal>;
  top_sources: EmissionSource[];
  yoy_change_percent?: ApiDecimal;
  trend_direction?: 'increasing' | 'decreasing' | 'stable';
  previous_period_total_tonnes?: ApiDecimal;
}

export interface PersonalizedRecommendation {
  initiative_id: string;
  initiative_name: string;
  initiative_category: string;
  initiative_description: string;
  target_activity_key: string;
  target_source_name: string;
  target_source_emissions_tco2e: ApiDecimal;
  target_source_percent_of_total: ApiDecimal;
  potential_reduction_tco2e: ApiDecimal;
  potential_reduction_low_tco2e: ApiDecimal;
  potential_reduction_high_tco2e: ApiDecimal;
  reduction_as_percent_of_total: ApiDecimal;
  estimated_capex?: ApiDecimal;
  estimated_annual_savings?: ApiDecimal;
  payback_years?: ApiDecimal;
  roi_percent?: ApiDecimal;
  impact_score: number;
  feasibility_score: number;
  priority_score: number;
  complexity: string;
  implementation_months_min: number;
  implementation_months_max: number;
  co_benefits?: string[];
  relevance_explanation: string;
}

export interface DecarbonizationTarget {
  id: string;
  name: string;
  description?: string;
  target_type: TargetType;
  framework: TargetFramework;
  base_year: number;
  base_year_emissions_tco2e: ApiDecimal;
  target_year: number;
  target_reduction_percent: ApiDecimal;
  target_emissions_tco2e: ApiDecimal;
  includes_scope1: boolean;
  includes_scope2: boolean;
  includes_scope3: boolean;
  scope3_categories?: string[];
  is_sbti_validated: boolean;
  is_public: boolean;
  is_active: boolean;
  created_at: string;
}

export interface TargetProgress {
  target_id: string;
  period_id: string;
  checkpoint_year: number;
  actual_emissions_tco2e: ApiDecimal;
  planned_emissions_tco2e: ApiDecimal;
  variance_tco2e: ApiDecimal;
  variance_percent: ApiDecimal;
  on_track: boolean;
  progress_percent: ApiDecimal;
  expected_progress_percent: ApiDecimal;
}

export interface TargetCreateRequest {
  name: string;
  description?: string;
  target_type?: TargetType;
  framework?: TargetFramework;
  base_year: number;
  base_year_period_id?: string;
  base_year_emissions_tco2e: number;
  target_year: number;
  target_reduction_percent?: number;
  target_emissions_tco2e?: number;
  includes_scope1?: boolean;
  includes_scope2?: boolean;
  includes_scope3?: boolean;
  scope3_categories?: string[];
}

export interface Initiative {
  id: string;
  category: InitiativeCategory;
  subcategory?: string;
  name: string;
  short_description: string;
  detailed_description?: string;
  applicable_scopes: number[];
  applicable_category_codes: string[];
  applicable_activity_keys: string[];
  typical_reduction_percent_min: ApiDecimal;
  typical_reduction_percent_max: ApiDecimal;
  typical_reduction_percent_median: ApiDecimal;
  typical_capex_per_tco2e_reduced?: ApiDecimal;
  typical_payback_years_min?: ApiDecimal;
  typical_payback_years_max?: ApiDecimal;
  complexity: ComplexityLevel;
  implementation_time_months_min: number;
  implementation_time_months_max: number;
  co_benefits?: string[];
  common_barriers?: string[];
}

export interface Scenario {
  id: string;
  name: string;
  description?: string;
  scenario_type: ScenarioType;
  is_active: boolean;
  total_reduction_tco2e: ApiDecimal;
  total_investment: ApiDecimal;
  total_annual_savings: ApiDecimal;
  weighted_payback_years?: ApiDecimal;
  target_achievement_percent: ApiDecimal;
  carbon_price_scenario: string;
  created_at: string;
  initiatives_count: number;
}

export interface ScenarioCreateRequest {
  name: string;
  description?: string;
  target_id: string;
  scenario_type?: ScenarioType;
  carbon_price_scenario?: string;
}

export interface ScenarioInitiative {
  id: string;
  scenario_id: string;
  initiative_id: string;
  initiative_name: string;
  target_activity_key: string;
  target_site_id?: string;
  expected_reduction_tco2e: ApiDecimal;
  expected_reduction_percent: ApiDecimal;
  capex: ApiDecimal;
  annual_savings: ApiDecimal;
  implementation_start?: string;
  implementation_end?: string;
  status: InitiativeStatus;
  priority_order: number;
}

export interface ScenarioInitiativeRequest {
  initiative_id: string;
  target_activity_key: string;
  target_site_id?: string;
  expected_reduction_tco2e: number;
  expected_reduction_percent: number;
  capex?: number;
  annual_opex_change?: number;
  annual_savings?: number;
  implementation_start?: string;
  implementation_end?: string;
  notes?: string;
}

export interface TrajectoryResponse {
  target_id: string;
  base_year: number;
  base_year_emissions: ApiDecimal;
  target_year: number;
  target_emissions: ApiDecimal;
  trajectory: Record<number, ApiDecimal>;
}

export interface EmissionCheckpoint {
  id: string;
  checkpoint_year: number;
  actual_emissions_tco2e: ApiDecimal;
  planned_emissions_tco2e: ApiDecimal;
  variance_tco2e: ApiDecimal;
  variance_percent: ApiDecimal;
  on_track: boolean;
  created_at: string;
}

// ============================================================================
// AI Ingestion Funnel types
// ============================================================================

export type IngestionStatus =
  | 'uploaded'
  | 'analyzing'
  | 'needs_answers'
  | 'ready_for_review'
  | 'committing'
  | 'committed'
  | 'failed';

export type RowStatus =
  | 'needs_question'
  | 'needs_review'
  | 'ready'
  | 'approved'
  | 'rejected'
  | 'committed';

export interface StagedRow {
  id: string;
  sheet: string;
  row_index: number;
  source: Record<string, unknown> | null;
  activity_key: string | null;
  scope: number | null;
  category_code: string | null;
  quantity: number | null;
  unit: string | null;
  description: string;
  confidence: number;
  band: 'green' | 'amber' | 'red';
  status: RowStatus;
  pcaf_data_quality: number | null;
  measurement_tier: MeasurementTier | null;
  reasons: string[] | null;
  provenance: StagedProvenance | null;
  committed_activity_id: string | null;
  commit_error: string | null;
}

export type MeasurementTier = 'measured' | 'calculated' | 'estimated' | 'gap';

export interface MethodologyReference {
  ghg_accounting_standard: string;
  calculation_approach: string;
  gwp_source: string;
  gwp_statement: string;
  consolidation_approaches: { value: string; label: string }[];
  data_quality_tiers: { tier: string; scores: number[]; description: string }[];
  method_hierarchy: { method: string; label: string; description: string }[];
  biogenic_policy: string;
}

export interface StagedProvenance {
  factor_source?: string | null;
  factor_year?: number | null;
  factor_region?: string | null;
  factor_name?: string | null;
  method?: string | null;
  method_label?: string | null;
  unit_kind?: string | null;
  /** Derived-quantity engine state — present when the quantity was computed
   *  (flight km, hotel nights, freight tonne-km) rather than read from the file. */
  derivation?: {
    engine?: string;
    gazetteer?: string;
    origin?: string;
    destination?: string;
    gcd_km?: number;
    uplift?: number;
    one_way_km?: number;
    round_trip?: boolean;
    rt_assumed?: boolean;
    trips?: number;
    travelers?: number;
    haul?: string;
    cabin?: string;
    cabin_assumed?: boolean;
    nights?: number;
    stay_country?: string | null;
    origin_country?: string;
    destination_country?: string;
    mode?: string;
    route_km?: number;
    mass_tonnes?: number | null;
    assumptions?: string[];
  } | null;
}

export interface QuestionChoice {
  value: string;
  label: string;
}

export interface ClarificationQuestion {
  id: string;
  staged_row_id: string | null;
  question: string;
  field: string | null;
  choices: QuestionChoice[] | null;
  answer: string | null;
  answered: boolean;
  applies_count: number;
}

export interface IngestionSession {
  id: string;
  filename: string;
  status: IngestionStatus;
  total_rows: number;
  mapped_rows: number;
  question_count: number;
  open_question_count: number;
  committed_count: number;
  summary: {
    sheets?: { sheet: string; rows: number; staged?: number; detected_scope?: number | null; error?: string }[];
    by_scope?: Record<string, number>;
    by_band?: Record<string, number>;
    by_tier?: { measured: number; calculated: number; estimated: number; gap: number };
    security?: { formula_cells_sanitised: number; injection_flags: number };
    duplicate_warning?: string;
    duplicate_of?: string;
    notice?: string;
    skipped_sheets?: string[];
  } | null;
  error_message: string | null;
  reporting_period_id: string | null;
  site_id: string | null;
  import_batch_id: string | null;
  created_at: string;
}

export interface IngestionSessionDetail extends IngestionSession {
  rows: StagedRow[];
  questions: ClarificationQuestion[];
}

// ============================================================================
// Leads (lightweight CRM) types
// ============================================================================

export type LeadSource =
  | 'website_tryit'
  | 'website_trial'
  | 'website_demo'
  | 'conference'
  | 'signup'
  | 'forum'
  | 'manual';
export type LeadStatus = 'new' | 'contacted' | 'trial' | 'customer' | 'lost';

export interface Lead {
  id: string;
  name: string | null;
  email: string;
  organization_name: string | null;
  source: LeadSource;
  status: LeadStatus;
  notes: string | null;
  what_tried: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface LeadCapture {
  email: string;
  name?: string;
  organization_name?: string;
  source: LeadSource;
  what_tried?: string;
}

// ============================================================================
// Public "Try Climatrix" demo (no auth)
// ============================================================================

export interface DemoMethodology {
  factor_value: number | null;
  factor_unit: string | null;
  factor_source: string | null;
  factor_year: number | null;
  factor_region: string | null;
  formula: string | null;
  resolution_strategy: string | null;
  confidence: string | null;
}

export interface DemoRow {
  sheet: string;
  source_description: string;
  activity_key: string | null;
  scope: number | null;
  category: string | null;
  quantity: number | null;
  unit: string | null;
  co2e_kg: number | null;
  methodology: DemoMethodology | null;
  note: string | null;
}

export interface DemoResult {
  filename: string;
  rows_read: number;
  rows_calculated: number;
  capped: boolean;
  total_tco2e: number;
  by_scope: { scope: number; tco2e: number }[];
  rows: DemoRow[];
  notice: string | null;
}

/** Public demo parse — no auth. Used by the /try landing page. */
export async function demoAnalyze(file: File): Promise<DemoResult> {
  const formData = new FormData();
  formData.append('file', file);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 120000);
  try {
    const resp = await fetch(`${API_BASE}/demo/analyze`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Analysis failed' }));
      throw new Error(
        typeof err.detail === 'string' ? err.detail : 'We could not analyze that file.'
      );
    }
    return resp.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

export const api = new ApiClient();
