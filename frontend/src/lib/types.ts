/**
 * CLIMATRIX Shared TypeScript Types
 */

// =============================================================================
// GHG TYPES
// =============================================================================

export type Scope = 1 | 2 | 3;

export type CategoryCode =
  | "1.1"
  | "1.2"
  | "1.3"
  | "2"
  | "2.1"
  | "2.2"
  | "3.1"
  | "3.2"
  | "3.3"
  | "3.4"
  | "3.5"
  | "3.6"
  | "3.7"
  | "3.8"
  | "3.9"
  | "3.10"
  | "3.11"
  | "3.12"
  | "3.13"
  | "3.14"
  | "3.15";

export type CalculationMethod = "activity" | "spend" | "distance" | "supplier";

export type DataSource = "manual" | "import" | "api";

export type ConfidenceLevel = "high" | "medium" | "low";

// Data Quality Score (PCAF methodology: 1=best, 5=worst)
export type DataQualityScore = 1 | 2 | 3 | 4 | 5;

export const DATA_QUALITY_LABELS: Record<DataQualityScore, string> = {
  1: "Verified Data",
  2: "Primary Data",
  3: "Activity Average",
  4: "Spend-Based",
  5: "Estimated",
};

export const DATA_QUALITY_DESCRIPTIONS: Record<DataQualityScore, string> = {
  1: "Audited/verified data from primary sources (e.g., audited energy bills)",
  2: "Non-audited data from primary sources (e.g., utility bills, invoices)",
  3: "Physical activity data with average emission factors",
  4: "Economic activity-based modeling (e.g., spend-based calculations)",
  5: "Estimated data with high uncertainty (e.g., industry averages)",
};

// =============================================================================
// ENTITY TYPES
// =============================================================================

export type SubscriptionPlan = 'free' | 'starter' | 'professional' | 'enterprise';

export interface Organization {
  id: string;
  name: string;
  country_code?: string;
  industry_code?: string;
  base_year?: number;
  subscription_plan?: SubscriptionPlan;
  created_at: string;
  modules?: ModuleConfig;
}

export interface User {
  id: string;
  organization_id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export type UserRole = "admin" | "editor" | "viewer";

export interface Site {
  id: string;
  organization_id: string;
  name: string;
  country_code?: string;
  grid_region?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  is_active: boolean;
  created_at: string;
}

// Verification workflow status for reporting periods
export type PeriodStatus = "draft" | "review" | "submitted" | "audit" | "verified" | "locked";

// Assurance level for verified reports
export type AssuranceLevel = "limited" | "reasonable";

export interface ReportingPeriod {
  id: string;
  organization_id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_locked: boolean;
  created_at: string;
  // Verification workflow fields
  status: PeriodStatus;
  assurance_level?: AssuranceLevel;
  submitted_at?: string;
  submitted_by_id?: string;
  verified_at?: string;
  verified_by?: string;
  verification_statement?: string;
}

export interface StatusTransitionRequest {
  new_status: PeriodStatus;
}

export interface VerificationRequest {
  assurance_level: AssuranceLevel;
  verified_by: string;
  verification_statement: string;
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

// =============================================================================
// ACTIVITY & EMISSION TYPES
// =============================================================================

export interface Activity {
  id: string;
  organization_id: string;
  reporting_period_id: string;
  site_id?: string;
  scope: Scope;
  category_code: CategoryCode;
  activity_key: string;
  description: string;
  quantity: number;
  unit: string;
  calculation_method: CalculationMethod;
  activity_date: string;
  data_source: DataSource;
  import_batch_id?: string;
  created_by?: string;
  created_at: string;
  updated_at?: string;
  emission?: Emission;
  // Data quality fields (PCAF: 1=best, 5=worst)
  data_quality_score: DataQualityScore;
  data_quality_justification?: string;
  supporting_document_url?: string;
}

export interface ActivityCreate {
  scope: Scope;
  category_code: string;
  activity_key: string;
  description: string;
  quantity: number;
  unit: string;
  activity_date: string;
  site_id?: string;
  calculation_method?: CalculationMethod;
  // Data quality fields (optional, defaults to 5)
  data_quality_score?: DataQualityScore;
  data_quality_justification?: string;
  supporting_document_url?: string;
}

export interface Emission {
  id: string;
  activity_id: string;
  emission_factor_id: string;
  co2_kg?: number;
  ch4_kg?: number;
  n2o_kg?: number;
  co2e_kg: number;
  wtt_co2e_kg?: number;
  converted_quantity?: number;
  converted_unit?: string;
  formula?: string;
  confidence: ConfidenceLevel;
  needs_review: boolean;
  warnings?: string[];
  calculated_at: string;
  emission_factor?: EmissionFactorSummary;
}

export interface EmissionFactorSummary {
  activity_key: string;
  display_name: string;
  co2e_factor: number;
  activity_unit: string;
  source: string;
  region: string;
  year: number;
}

// =============================================================================
// REFERENCE DATA TYPES
// =============================================================================

export interface EmissionFactor {
  id: string;
  scope: Scope;
  category_code: string;
  subcategory?: string;
  activity_key: string;
  display_name: string;
  co2_factor?: number;
  ch4_factor?: number;
  n2o_factor?: number;
  co2e_factor: number;
  activity_unit: string;
  factor_unit: string;
  source: string;
  region: string;
  year: number;
  wtt_factor_id?: string;
  is_active: boolean;
}

export interface ActivityOption {
  activity_key: string;
  display_name: string;
  unit: string;
  scope: Scope;
  category_code: string;
}

export interface UnitConversion {
  id: string;
  from_unit: string;
  to_unit: string;
  multiplier: number;
  category?: string;
}

// =============================================================================
// REPORT TYPES
// =============================================================================

export interface EmissionsSummary {
  total_co2e_kg: number;
  scope1_co2e_kg: number;
  scope2_co2e_kg: number;
  scope3_co2e_kg: number;
  scope1_percentage: number;
  scope2_percentage: number;
  scope3_percentage: number;
  activity_count: number;
  period: ReportingPeriod;
}

export interface CategoryBreakdown {
  category_code: CategoryCode;
  category_name: string;
  scope: Scope;
  co2e_kg: number;
  percentage: number;
  activity_count: number;
}

export interface SiteBreakdown {
  site_id: string;
  site_name: string;
  co2e_kg: number;
  percentage: number;
  activity_count: number;
}

export interface MonthlyTrend {
  month: string;
  scope1_co2e_kg: number;
  scope2_co2e_kg: number;
  scope3_co2e_kg: number;
  total_co2e_kg: number;
}

export interface YearOverYearComparison {
  current_period: EmissionsSummary;
  previous_period?: EmissionsSummary;
  change_percentage?: number;
  change_absolute?: number;
}

// =============================================================================
// IMPORT TYPES
// =============================================================================

export interface ImportBatch {
  id: string;
  organization_id: string;
  reporting_period_id: string;
  filename: string;
  status: ImportStatus;
  total_rows: number;
  successful_rows: number;
  failed_rows: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export type ImportStatus = "pending" | "processing" | "completed" | "failed";

export interface ImportPreview {
  columns: string[];
  sample_rows: Record<string, string>[];
  detected_mapping?: ColumnMapping[];
  total_rows: number;
}

export interface ColumnMapping {
  source_column: string;
  target_field: string;
  confidence: number;
  sample_values?: string[];
}

export interface ImportValidationResult {
  is_valid: boolean;
  row_number: number;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  corrected_data?: Record<string, unknown>;
}

export interface ValidationError {
  field: string;
  message: string;
  value?: string;
}

export interface ValidationWarning {
  field: string;
  message: string;
  suggestion?: string;
}

// =============================================================================
// MODULE SYSTEM TYPES
// =============================================================================

export type ModuleType = "ghg" | "pcaf" | "cbam" | "lca" | "epd";

export interface ModuleConfig {
  ghg: boolean;
  pcaf: boolean;
  cbam: boolean;
  lca: boolean;
  epd: boolean;
}

export interface ModuleInfo {
  id: ModuleType;
  name: string;
  description: string;
  icon: string;
  status: "active" | "coming_soon" | "beta";
  features: string[];
}

// =============================================================================
// UI STATE TYPES
// =============================================================================

export interface PaginationParams {
  page: number;
  limit: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface SortParams {
  field: string;
  direction: "asc" | "desc";
}

export interface FilterParams {
  scope?: Scope;
  category_code?: string;
  site_id?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface TableColumn<T> {
  key: keyof T | string;
  label: string;
  sortable?: boolean;
  width?: string;
  align?: "left" | "center" | "right";
  render?: (value: unknown, row: T) => React.ReactNode;
}

// =============================================================================
// API RESPONSE TYPES
// =============================================================================

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
  errors?: Record<string, string[]>;
}

// =============================================================================
// FORM TYPES
// =============================================================================

export type FormStatus = "idle" | "loading" | "success" | "error";

export interface FormState<T> {
  data: T;
  status: FormStatus;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
}

// =============================================================================
// WIZARD TYPES
// =============================================================================

export type WizardStep = "scope" | "category" | "activity" | "details" | "review";

export interface WizardState {
  step: WizardStep;
  selectedScope: Scope | null;
  selectedCategory: string | null;
  selectedActivityKey: string | null;
  formData: Partial<ActivityCreate>;
  previewEmission: Emission | null;
}

// =============================================================================
// CALCULATION TYPES
// =============================================================================

export interface CalculationRequest {
  activity_key: string;
  quantity: number;
  unit: string;
  region?: string;
}

export interface CalculationResult {
  co2e_kg: number;
  co2_kg?: number;
  ch4_kg?: number;
  n2o_kg?: number;
  wtt_co2e_kg?: number;
  emission_factor: EmissionFactorSummary;
  formula: string;
  confidence: ConfidenceLevel;
  resolution_strategy: "exact" | "regional" | "global" | "proxy";
  warnings: string[];
}

// =============================================================================
// AUTH TYPES
// =============================================================================

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthState {
  user: User | null;
  organization: Organization | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// =============================================================================
// AUDIT PACKAGE TYPES (Phase 1.4)
// =============================================================================

export interface ActivityAuditRecord {
  activity_id: string;
  scope: Scope;
  category_code: string;
  category_name: string;
  activity_key: string;
  display_name: string;
  description: string;
  quantity: number;
  unit: string;
  activity_date: string;
  calculation_method: CalculationMethod;
  data_source: DataSource;
  import_batch_id?: string;
  import_file_name?: string;
  data_quality_score: DataQualityScore;
  data_quality_label: string;
  data_quality_justification?: string;
  supporting_document_url?: string;
  co2e_kg: number;
  co2e_tonnes: number;
  co2_kg?: number;
  ch4_kg?: number;
  n2o_kg?: number;
  wtt_co2e_kg?: number;
  emission_factor_id: string;
  emission_factor_value: number;
  emission_factor_unit: string;
  converted_quantity?: number;
  converted_unit?: string;
  calculation_formula?: string;
  confidence_level: ConfidenceLevel;
  created_at: string;
  created_by?: string;
}

export interface EmissionFactorAuditRecord {
  factor_id: string;
  activity_key: string;
  display_name: string;
  scope: Scope;
  category_code: string;
  subcategory?: string;
  co2e_factor: number;
  co2_factor?: number;
  ch4_factor?: number;
  n2o_factor?: number;
  activity_unit: string;
  factor_unit: string;
  source: string;
  region: string;
  year: number;
  valid_from?: string;
  valid_until?: string;
  usage_count: number;
  total_co2e_kg: number;
}

export interface ImportBatchAuditRecord {
  batch_id: string;
  file_name: string;
  file_type: string;
  file_size_bytes?: number;
  status: string;
  total_rows: number;
  successful_rows: number;
  failed_rows: number;
  skipped_rows: number;
  error_message?: string;
  uploaded_at: string;
  uploaded_by?: string;
  completed_at?: string;
}

export interface CalculationMethodologySection {
  overview: string;
  ghg_protocol_alignment: string;
  calculation_approach: string;
  scope_1_methodology: {
    description: string;
    categories: Record<string, string>;
    calculation: string;
  };
  scope_2_methodology: {
    description: string;
    approach: string;
    categories: Record<string, string>;
    calculation: string;
  };
  scope_3_methodology: {
    description: string;
    categories_covered: string[];
    calculation: string;
    wtt_note: string;
  };
  unit_conversion_approach: string;
  wtt_calculation_method: string;
  data_validation_rules: string[];
  confidence_level_criteria: Record<ConfidenceLevel, string>;
}

export interface AuditPackageSummary {
  period_id: string;
  period_name: string;
  organization_name: string;
  reporting_period_start: string;
  reporting_period_end: string;
  verification_status: PeriodStatus;
  assurance_level?: AssuranceLevel;
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

// =============================================================================
// CDP EXPORT TYPES (Phase 1.5)
// =============================================================================

export interface CDPScope1Breakdown {
  source_category: string;
  emissions_metric_tonnes: number;
  methodology: string;
  source_of_emission_factors: string;
}

export interface CDPScope2Breakdown {
  country: string;
  grid_region?: string;
  purchased_electricity_mwh: number;
  location_based_emissions_tonnes: number;
  market_based_emissions_tonnes?: number;
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
  scope_2_market_based_metric_tonnes?: number;
  scope_3_metric_tonnes: number;
  total_metric_tonnes: number;
}

export interface CDPTargetsAndPerformance {
  base_year?: number;
  base_year_emissions_tonnes?: number;
  target_year?: number;
  target_reduction_percentage?: number;
  current_year_emissions_tonnes: number;
  progress_percentage?: number;
}

export interface CDPDataQuality {
  overall_data_quality_score: number;
  percentage_verified_data: number;
  percentage_primary_data: number;
  percentage_estimated_data: number;
  verification_status: string;
  assurance_level?: string;
}

export interface CDPExport {
  export_version: string;
  export_date: string;
  reporting_year: number;
  organization_name: string;
  country?: string;
  primary_industry?: string;
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

// =============================================================================
// ESRS E1 EXPORT TYPES (Phase 1.5)
// =============================================================================

export interface ESRSE1GrossEmissions {
  scope_1_tonnes: number;
  scope_2_location_based_tonnes: number;
  scope_2_market_based_tonnes?: number;
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
  plan_aligned_with?: string;
  key_decarbonization_levers: string[];
  locked_in_emissions_tonnes?: number;
}

export interface ESRSE1DataQuality {
  data_quality_approach: string;
  percentage_estimated_scope_3: number;
  significant_assumptions: string[];
  verification_statement?: string;
}

export interface ESRSE1Export {
  export_version: string;
  export_date: string;
  reporting_period_start: string;
  reporting_period_end: string;
  undertaking_name: string;
  country_of_domicile?: string;
  nace_sector?: string;
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

// =============================================================================
// CBAM TYPES (Phase 2)
// =============================================================================

/**
 * CBAM (Carbon Border Adjustment Mechanism) Types
 * EU Regulation 2023/956
 */

// CBAM Sectors covered by the regulation
export type CBAMSector =
  | "cement"
  | "iron_steel"
  | "aluminium"
  | "fertilisers"
  | "electricity"
  | "hydrogen"
  | "other";

export const CBAM_SECTOR_LABELS: Record<CBAMSector, string> = {
  cement: "Cement",
  iron_steel: "Iron & Steel",
  aluminium: "Aluminium",
  fertilisers: "Fertilisers",
  electricity: "Electricity",
  hydrogen: "Hydrogen",
  other: "Other",
};

// Calculation method for embedded emissions
export type CBAMCalculationMethod = "actual" | "default" | "fallback";

export const CBAM_CALCULATION_METHOD_LABELS: Record<CBAMCalculationMethod, string> = {
  actual: "Actual Installation Data",
  default: "EU Default Values",
  fallback: "Fallback Values",
};

// Report status
export type CBAMReportStatus = "draft" | "review" | "submitted" | "accepted" | "rejected";

// Installation verification status
export type CBAMInstallationStatus = "pending" | "verified" | "rejected" | "expired";

// CBAM Installation (non-EU production facility)
export interface CBAMInstallation {
  id: string;
  organization_id: string;
  name: string;
  country_code: string;
  address?: string;
  contact_name?: string;
  contact_email?: string;
  sectors: CBAMSector[];
  verification_status: CBAMInstallationStatus;
  created_at: string;
  updated_at: string;
}

export interface CBAMInstallationCreate {
  name: string;
  country_code: string;
  address?: string;
  contact_name?: string;
  contact_email?: string;
  sectors?: CBAMSector[];
  verification_status?: CBAMInstallationStatus;
}

export interface CBAMInstallationUpdate {
  name?: string;
  country_code?: string;
  address?: string;
  contact_name?: string;
  contact_email?: string;
  sectors?: CBAMSector[];
  verification_status?: CBAMInstallationStatus;
}

// CBAM Import record
export interface CBAMImport {
  id: string;
  organization_id: string;
  installation_id: string;
  cn_code: string;
  sector: CBAMSector;
  product_description?: string;
  import_date: string;
  mass_tonnes: number;
  calculation_method: CBAMCalculationMethod;
  direct_see: number;
  indirect_see: number;
  total_see: number;
  direct_emissions_tco2e: number;
  indirect_emissions_tco2e: number;
  total_emissions_tco2e: number;
  foreign_carbon_price_eur?: number;
  created_at: string;
}

export interface CBAMImportCreate {
  installation_id: string;
  cn_code: string;
  product_description?: string;
  import_date: string;
  mass_tonnes: number;
  customs_procedure?: string;
  customs_declaration_number?: string;
  actual_direct_see?: number;
  actual_indirect_see?: number;
  electricity_consumption_mwh?: number;
  foreign_carbon_price_eur?: number;
  foreign_carbon_price_currency?: string;
}

// CBAM Quarterly Report (transitional period 2024-2025)
export interface CBAMQuarterlyReport {
  id: string;
  organization_id: string;
  year: number;
  quarter: number;
  status: CBAMReportStatus;
  total_imports: number;
  total_mass_tonnes: number;
  total_emissions_tco2e: number;
  by_sector: Record<string, CBAMSectorSummary>;
  by_cn_code: Record<string, CBAMCNCodeSummary>;
  submitted_at?: string;
  created_at: string;
}

export interface CBAMSectorSummary {
  mass_tonnes: number;
  direct_emissions_tco2e: number;
  indirect_emissions_tco2e: number;
  total_emissions_tco2e: number;
  import_count: number;
  cn_codes: string[];
  countries: string[];
}

export interface CBAMCNCodeSummary {
  mass_tonnes: number;
  total_emissions_tco2e: number;
  import_count: number;
  countries: string[];
}

// CBAM Annual Declaration (definitive phase 2026+)
export interface CBAMAnnualDeclaration {
  id: string;
  organization_id: string;
  year: number;
  status: CBAMReportStatus;
  total_imports: number;
  total_mass_tonnes: number;
  gross_emissions_tco2e: number;
  deductions_tco2e: number;
  net_emissions_tco2e: number;
  certificates_required: number;
  estimated_cost_eur: number;
  by_sector: Record<string, CBAMAnnualSectorSummary>;
  submitted_at?: string;
  created_at: string;
}

export interface CBAMAnnualSectorSummary {
  gross_emissions_tco2e: number;
  net_emissions_tco2e: number;
  certificates_required: number;
  estimated_cost_eur: number;
}

// CN Code search result
export interface CBAMCNCode {
  cn_code: string;
  description: string;
  sector: CBAMSector;
}

// Emissions calculation preview
export interface CBAMEmissionCalculationRequest {
  cn_code: string;
  mass_tonnes: number;
  country_code: string;
  actual_direct_see?: number;
  actual_indirect_see?: number;
  electricity_consumption_mwh?: number;
  foreign_carbon_price_eur?: number;
}

export interface CBAMEmissionCalculationResult {
  summary: {
    cn_code: string;
    sector: CBAMSector;
    mass_tonnes: number;
    country_code: string;
    total_emissions_tco2e: number;
    net_emissions_tco2e: number;
    net_cbam_cost_eur: number;
    calculation_method: CBAMCalculationMethod;
    is_definitive_phase: boolean;
  };
  embedded_emissions: {
    cn_code: string;
    mass_tonnes: number;
    country_code: string;
    calculation_method: CBAMCalculationMethod;
    direct_see: number;
    indirect_see: number;
    total_see: number;
    direct_emissions_tco2e: number;
    indirect_emissions_tco2e: number;
    total_emissions_tco2e: number;
    warnings: string[];
  };
  carbon_price_deduction: {
    total_emissions_tco2e: number;
    foreign_carbon_price_eur: number;
    deduction_tco2e: number;
    net_emissions_tco2e: number;
    gross_cbam_cost_eur: number;
    deduction_eur: number;
    net_cbam_cost_eur: number;
  };
  certificate_requirement?: {
    net_emissions_tco2e: number;
    certificates_required: number;
    fractional_certificates: number;
    eu_ets_price_eur: number;
    estimated_cost_eur: number;
  };
  warnings: string[];
}

// CBAM Dashboard
export interface CBAMDashboard {
  year: number;
  installations: {
    total: number;
    by_country: Record<string, number>;
  };
  imports: {
    total_count: number;
    total_mass_tonnes: number;
    total_emissions_tco2e: number;
  };
  by_sector: Array<{
    sector: CBAMSector;
    import_count: number;
    total_emissions_tco2e: number;
  }>;
  quarterly_reports: Array<{
    quarter: number;
    status: CBAMReportStatus;
    total_emissions_tco2e: number;
  }>;
  phase: "transitional" | "definitive";
}

// EU Commission format for quarterly reports
export interface CBAMQuarterlyReportEUFormat {
  report_type: string;
  regulation_reference: string;
  reporting_period: {
    year: number;
    quarter: number;
    start_date: string;
    end_date: string;
    phase: "transitional" | "definitive";
  };
  reporting_declarant: {
    name: string;
    eori_number: string;
    address: string;
    member_state: string;
  };
  summary: {
    total_imports: number;
    total_mass_tonnes: number;
    total_embedded_emissions_tco2e: number;
    direct_emissions_tco2e: number;
    indirect_emissions_tco2e: number;
  };
  emissions_by_sector: Record<string, {
    mass_tonnes: number;
    direct_emissions_tco2e: number;
    indirect_emissions_tco2e: number;
    total_emissions_tco2e: number;
    import_count: number;
    cn_codes: string[];
    source_countries: string[];
  }>;
  installations: Array<{
    id: string;
    name: string;
    country: string;
    sectors: string[];
    verification_status: CBAMInstallationStatus;
  }>;
  data_quality_notes: {
    calculation_methods_used: CBAMCalculationMethod[];
    default_values_used: boolean;
    actual_values_available: boolean;
  };
  submission_metadata: {
    generated_at: string;
    status: CBAMReportStatus;
    submitted_at?: string;
  };
}
