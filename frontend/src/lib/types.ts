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

// =============================================================================
// ENTITY TYPES
// =============================================================================

export interface Organization {
  id: string;
  name: string;
  country_code?: string;
  industry_code?: string;
  base_year?: number;
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
