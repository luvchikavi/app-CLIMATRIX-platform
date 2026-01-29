/**
 * API Client for CLIMATRIX backend
 *
 * Uses explicit activity_key system - no fuzzy matching.
 * All endpoints are typed with TypeScript interfaces.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';

// ============================================================================
// Types
// ============================================================================

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
}

export interface Organization {
  id: string;
  name: string;
  country_code: string;
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

export interface EmissionFactor {
  id?: string;
  activity_key: string;
  display_name: string;
  activity_unit?: string;
  unit?: string; // For activity options
  scope: number;
  category_code: string;
  co2e_factor?: number;
  factor_unit?: string;
  source?: string;
  region?: string;
  year?: number;
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
  scope_1_methodology: Record<string, any>;
  scope_2_methodology: Record<string, any>;
  scope_3_methodology: Record<string, any>;
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
}

export interface Region {
  code: string;
  name: string;
  description: string;
}

export interface Site {
  id: string;
  name: string;
  country_code: string | null;
  address: string | null;
  grid_region: string | null;
  is_active: boolean;
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

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
    return this.token;
  }

  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const token = this.getToken();
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));

      // If 401 Unauthorized, clear the token
      if (response.status === 401) {
        this.setToken(null);
        // Dispatch event to notify auth store
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('auth-expired'));
        }
      }

      throw new Error(error.detail || `API Error: ${response.status}`);
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
    return result;
  }

  logout() {
    this.setToken(null);
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
    filters?: { scope?: number; category_code?: string }
  ): Promise<ActivityWithEmission[]> {
    const params = new URLSearchParams();
    if (filters?.scope) params.append('scope', String(filters.scope));
    if (filters?.category_code) params.append('category_code', filters.category_code);

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
  async getReportSummary(periodId: string): Promise<ReportSummary> {
    return this.fetch<ReportSummary>(`/periods/${periodId}/report/summary`);
  }

  async getReportByScope(periodId: string): Promise<any> {
    return this.fetch(`/periods/${periodId}/report/by-scope`);
  }

  async getWTTReport(periodId: string): Promise<any> {
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

  // Recalculate
  async recalculatePeriod(periodId: string): Promise<any> {
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

  async getSupportedRegions(): Promise<Region[]> {
    return this.fetch<Region[]>('/organization/regions');
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

  async deleteSite(siteId: string): Promise<void> {
    await this.fetch(`/organization/sites/${siteId}`, { method: 'DELETE' });
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
        const activities = (scopeData as { activities?: any[] }).activities || [];
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
        errors: (data.errors || []).map((e: any) => ({
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
      data.errors = data.errors.map((e: any) => ({
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

  async generateCBAMAnnualDeclaration(year: number): Promise<CBAMAnnualDeclaration> {
    return this.fetch<CBAMAnnualDeclaration>(`/cbam/reports/annual/${year}`, {
      method: 'POST',
    });
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
    cancelUrl: string
  ): Promise<CheckoutResponse> {
    return this.fetch<CheckoutResponse>('/billing/checkout', {
      method: 'POST',
      body: JSON.stringify({
        plan,
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
  CBAMCNCode,
  CBAMEmissionCalculationRequest,
  CBAMEmissionCalculationResult,
  CBAMDashboard,
  CBAMQuarterlyReportEUFormat,
} from './types';

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
  sample_data: Record<string, any>[];
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
    scope_1: { total_co2e_kg: number; activity_count: number; activities: any[] };
    scope_2: { total_co2e_kg: number; activity_count: number; activities: any[] };
    scope_3: { total_co2e_kg: number; activity_count: number; activities: any[] };
  };
}

// ============================================================================
// Billing Types
// ============================================================================

export type SubscriptionPlan = 'free' | 'starter' | 'professional' | 'enterprise';
export type SubscriptionStatus = 'active' | 'trialing' | 'past_due' | 'canceled' | 'incomplete' | 'unpaid';

export interface PlanLimits {
  activities_per_month: number;
  users: number;
  periods: number;
  sites: number;
  ai_extractions: number;
  export_formats: string[];
}

export interface SubscriptionInfo {
  plan: SubscriptionPlan;
  status: SubscriptionStatus | null;
  current_period_end: string | null;
  is_trialing: boolean;
  plan_limits: PlanLimits;
}

export interface PlanInfo {
  id: SubscriptionPlan;
  name: string;
  limits: PlanLimits;
  price_monthly: number | null;
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

export const api = new ApiClient();
