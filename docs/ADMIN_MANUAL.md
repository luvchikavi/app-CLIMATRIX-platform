# CLIMATRIX Platform -- Administrator Manual

**Version:** 3.1.0
**Last Updated:** 2026-02-25
**Audience:** Platform administrators, DevOps engineers, and super-admin users

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
   - 1.1 [Technology Stack](#11-technology-stack)
   - 1.2 [Service Topology](#12-service-topology)
   - 1.3 [Data Flow Diagram](#13-data-flow-diagram)
   - 1.4 [Multi-Tenancy Model](#14-multi-tenancy-model)
2. [Database Schema](#2-database-schema)
   - 2.1 [Core Tables](#21-core-tables)
   - 2.2 [Emission Tables](#22-emission-tables)
   - 2.3 [Reference Data Tables](#23-reference-data-tables)
   - 2.4 [CBAM Tables](#24-cbam-tables)
   - 2.5 [Supporting Tables](#25-supporting-tables)
   - 2.6 [Enumerations Reference](#26-enumerations-reference)
   - 2.7 [Key Relationships and Foreign Keys](#27-key-relationships-and-foreign-keys)
3. [Application Logic](#3-application-logic)
   - 3.1 [Emission Calculation Pipeline](#31-emission-calculation-pipeline)
   - 3.2 [Factor Resolution Hierarchy](#32-factor-resolution-hierarchy)
   - 3.3 [WTT (Well-to-Tank) Auto-Calculation](#33-wtt-well-to-tank-auto-calculation)
   - 3.4 [Data Quality Scoring](#34-data-quality-scoring)
   - 3.5 [Confidence Levels](#35-confidence-levels)
   - 3.6 [Import Processing Flow](#36-import-processing-flow)
   - 3.7 [Calculation Strategies](#37-calculation-strategies)
   - 3.8 [Unit Normalization](#38-unit-normalization)
   - 3.9 [Currency Conversion](#39-currency-conversion)
4. [Admin Guide](#4-admin-guide)
   - 4.1 [CLI Commands](#41-cli-commands)
   - 4.2 [User Management](#42-user-management)
   - 4.3 [Organization Setup](#43-organization-setup)
   - 4.4 [Reporting Period Management](#44-reporting-period-management)
   - 4.5 [Subscription and Billing Management](#45-subscription-and-billing-management)
   - 4.6 [Data Import (Excel Templates)](#46-data-import-excel-templates)
   - 4.7 [Emission Factor Governance](#47-emission-factor-governance)
5. [User Guide](#5-user-guide)
   - 5.1 [Registration and Onboarding](#51-registration-and-onboarding)
   - 5.2 [Entering Data via the Activity Wizard](#52-entering-data-via-the-activity-wizard)
   - 5.3 [Uploading Excel Templates](#53-uploading-excel-templates)
   - 5.4 [Viewing the Dashboard](#54-viewing-the-dashboard)
   - 5.5 [Generating Reports](#55-generating-reports)
   - 5.6 [Using the CBAM Module](#56-using-the-cbam-module)
   - 5.7 [Settings: Organization Info and Team Invitations](#57-settings-organization-info-and-team-invitations)
   - 5.8 [Decarbonization Pathways](#58-decarbonization-pathways)
6. [Emission Factor Sources](#6-emission-factor-sources)
   - 6.1 [DEFRA (UK Government)](#61-defra-uk-government)
   - 6.2 [EEA (European Environment Agency)](#62-eea-european-environment-agency)
   - 6.3 [EPA eGRID (US Electricity)](#63-epa-egrid-us-electricity)
   - 6.4 [BEIS (UK Business Energy)](#64-beis-uk-business-energy)
   - 6.5 [IEA (International Energy Agency)](#65-iea-international-energy-agency)
   - 6.6 [IPCC AR6 GWP Values](#66-ipcc-ar6-gwp-values)
   - 6.7 [USEEIO (US Environmentally-Extended Input-Output)](#67-useeio-us-environmentally-extended-input-output)
   - 6.8 [How Factors Are Structured in the Database](#68-how-factors-are-structured-in-the-database)
7. [Deployment Runbook](#7-deployment-runbook)
   - 7.1 [Railway Setup (Backend)](#71-railway-setup-backend)
   - 7.2 [Vercel Setup (Frontend)](#72-vercel-setup-frontend)
   - 7.3 [Complete Environment Variables Reference](#73-complete-environment-variables-reference)
   - 7.4 [Database Initialization](#74-database-initialization)
   - 7.5 [Creating the First Super Admin](#75-creating-the-first-super-admin)
   - 7.6 [Updating Emission Factors](#76-updating-emission-factors)
   - 7.7 [Storage Configuration](#77-storage-configuration)
8. [Troubleshooting](#8-troubleshooting)
   - 8.1 [Common Errors and Solutions](#81-common-errors-and-solutions)
   - 8.2 [CORS Issues](#82-cors-issues)
   - 8.3 [Database Connection Issues](#83-database-connection-issues)
   - 8.4 [Import Failures](#84-import-failures)
   - 8.5 [OAuth Configuration](#85-oauth-configuration)
   - 8.6 [Stripe Webhook Debugging](#86-stripe-webhook-debugging)
   - 8.7 [Sentry Error Tracking](#87-sentry-error-tracking)

---

## 1. System Architecture Overview

### 1.1 Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Backend Framework** | FastAPI | 0.115.0 | Async Python REST API |
| **Frontend Framework** | Next.js | 16.1.1 | React-based SSR/SPA |
| **UI Library** | React | 19.2.3 | Component rendering |
| **State Management** | Zustand | 5.x | Client-side state |
| **Data Fetching** | TanStack React Query | 5.x | Server state & caching |
| **CSS** | Tailwind CSS | 4.x | Utility-first styling |
| **Charts** | Recharts | 3.6.x | Dashboard visualizations |
| **Database** | PostgreSQL | 15+ | Primary data store (Railway) |
| **ORM** | SQLModel + SQLAlchemy | 0.0.22 / 2.0.35 | Async database operations |
| **Migrations** | Alembic | 1.13.0 | Schema version control |
| **Task Queue** | Arq + Redis | 0.26.0 | Async job processing (imports) |
| **Auth** | JWT (python-jose) + bcrypt | -- | Token-based authentication |
| **OAuth** | Google Auth | 2.29+ | Google SSO login |
| **Unit Conversion** | Pint | 0.24+ | Physics-grade unit math |
| **Excel Processing** | openpyxl + pandas | 3.1.2 / 2.2.0 | Import/export files |
| **PDF Generation** | ReportLab | 4.1+ | PDF report export |
| **AI Services** | Anthropic (Claude) | 0.35+ | AI-powered column mapping |
| **Billing** | Stripe | 11.0.0 | Subscription management |
| **Monitoring** | Sentry | 2.19.0 | Error tracking & performance |
| **Storage** | Local / S3 / Cloudflare R2 | -- | File uploads |
| **HTTP Client** | httpx | 0.27.0 | External API calls |
| **CLI** | Typer | 0.12.0 | Admin command-line tools |
| **Icons** | Lucide React | 0.562+ | UI icons |

### 1.2 Service Topology

```
Production Deployment Architecture
===================================

                          +--------------------+
                          |   DNS / Domain     |
                          |  climatrix.io      |
                          +--------+-----------+
                                   |
                    +--------------+--------------+
                    |                             |
            +-------v--------+          +--------v---------+
            |   Vercel CDN   |          |  Railway Service  |
            |  (Frontend)    |          |   (Backend API)   |
            |  Next.js 16    |          |   FastAPI/Uvicorn |
            |  Port: 3000    |          |   Port: 8000      |
            +----------------+          +----+----+---------+
                    |                        |    |
                    |  API calls             |    |
                    |  /api/* --------->     |    |
                    |                        |    |
                              +--------------+    +----------+
                              |                              |
                    +---------v----------+     +-------------v----+
                    | Railway PostgreSQL  |     | Railway Redis     |
                    | (Primary Database)  |     | (Task Queue)      |
                    | Port: 5432          |     | Port: 6379        |
                    +--------------------+     +------------------+
                                                        |
                                               +--------v---------+
                                               | Arq Worker        |
                                               | (Background Jobs) |
                                               +------------------+

            External Services:
            +------------------+   +------------------+   +------------------+
            |  Stripe          |   |  Google OAuth     |   |  Sentry          |
            |  (Billing)       |   |  (SSO Login)      |   |  (Error Tracking)|
            +------------------+   +------------------+   +------------------+

            Optional:
            +------------------+   +------------------+
            |  Cloudflare R2   |   |  SMTP Provider    |
            |  (File Storage)  |   |  (Transactional   |
            +------------------+   |   Emails)         |
                                   +------------------+
```

### 1.3 Data Flow Diagram

```
User Interaction Flow
======================

[User Browser] --(HTTPS)--> [Next.js Frontend (Vercel)]
       |
       |  1. Login (email+password or Google OAuth)
       |  2. JWT token returned
       |  3. All subsequent API calls include Bearer token
       v
[FastAPI Backend (Railway)]
       |
       +--> POST /api/activities (Create Activity)
       |         |
       |         v
       |    +--------------------+
       |    | Calculation        |
       |    | Pipeline           |
       |    |                    |
       |    | Stage 1: NORMALIZE |---> Pint unit conversion
       |    | Stage 2: RESOLVE   |---> Factor DB lookup (exact -> region -> global)
       |    | Stage 3: CALCULATE |---> Strategy pattern (fuel, electricity, spend, etc.)
       |    |          + WTT     |---> Auto-calculate Scope 3.3 WTT emissions
       |    +--------------------+
       |         |
       |         v
       |    [PostgreSQL]
       |    - Activity record created
       |    - Emission record created (1:1)
       |    - Audit log entry
       |
       +--> POST /api/import/upload (Bulk Import)
       |         |
       |         +--> Small file: Sync processing
       |         +--> Large file: Queue to Redis -> Arq Worker processes async
       |
       +--> GET /api/reports/summary (Dashboard/Reports)
                 |
                 v
            Aggregation queries across activities + emissions
```

### 1.4 Multi-Tenancy Model

CLIMATRIX uses a **single-database, shared-schema** multi-tenancy model. Every data-bearing table includes an `organization_id` foreign key that scopes all queries to the authenticated user's organization.

**Tenancy enforcement:**

- Every user belongs to exactly one organization (`users.organization_id -> organizations.id`).
- Every API endpoint extracts the `organization_id` from the authenticated user's JWT token.
- All database queries include `WHERE organization_id = <user's org>` to prevent cross-tenant data leakage.
- Sites, reporting periods, activities, emissions, import batches, CBAM records, and audit logs are all scoped to an organization.
- Super admins (`role = super_admin`) have cross-tenant visibility via the `/api/admin/*` endpoints.

**Isolation boundaries:**

| Resource | Tenant-Scoped | Global (Shared) |
|----------|:---:|:---:|
| Users | Yes | -- |
| Sites | Yes | -- |
| Reporting Periods | Yes | -- |
| Activities | Yes | -- |
| Emissions | Yes | -- |
| Import Batches | Yes | -- |
| CBAM Data | Yes | -- |
| Audit Logs | Yes | -- |
| Emission Factors | -- | Yes |
| Unit Conversions | -- | Yes |
| Fuel Prices | -- | Yes |
| Grid Factors | -- | Yes |
| Airport Data | -- | Yes |
| Refrigerant GWP | -- | Yes |

---

## 2. Database Schema

### 2.1 Core Tables

#### `organizations`

The root entity for multi-tenancy. All tenant data hangs off this table.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `name` | VARCHAR(255) | NOT NULL, INDEX | Organization name |
| `country_code` | VARCHAR(2) | Nullable | ISO 3166-1 alpha-2 country code |
| `industry_code` | VARCHAR(20) | Nullable | Industry classification code |
| `base_year` | INTEGER | Nullable | GHG inventory base year |
| `default_region` | VARCHAR(50) | Default: "Global" | Default region for factor resolution |
| `is_active` | BOOLEAN | Default: true | Soft delete flag |
| `created_at` | TIMESTAMP | Auto | Creation timestamp |
| `updated_at` | TIMESTAMP | Nullable | Last update timestamp |
| `stripe_customer_id` | VARCHAR(255) | Nullable, INDEX | Stripe Customer ID |
| `stripe_subscription_id` | VARCHAR(255) | Nullable | Stripe Subscription ID |
| `subscription_plan` | VARCHAR(20) | Default: "free" | Current plan: free/starter/professional/enterprise |
| `subscription_status` | VARCHAR(20) | Nullable | Stripe status: active/trialing/past_due/canceled/incomplete/unpaid |
| `subscription_current_period_end` | TIMESTAMP | Nullable | Current billing period end |
| `trial_ends_at` | TIMESTAMP | Nullable | Trial expiration date |

#### `users`

User accounts with organization membership and role-based access.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `organization_id` | UUID | FK -> organizations.id, INDEX | Tenant membership |
| `email` | VARCHAR(255) | UNIQUE, INDEX | Login email |
| `full_name` | VARCHAR(255) | Nullable | Display name |
| `role` | ENUM(UserRole) | Default: viewer | Access level |
| `is_active` | BOOLEAN | Default: true | Account status |
| `hashed_password` | VARCHAR(255) | Nullable | bcrypt hash (null for OAuth-only) |
| `google_id` | VARCHAR(255) | Nullable, INDEX | Google OAuth subject ID |
| `created_at` | TIMESTAMP | Auto | Account creation |
| `last_login` | TIMESTAMP | Nullable | Last successful login |

#### `sites`

Physical locations/facilities for location-specific emissions tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `organization_id` | UUID | FK -> organizations.id, INDEX | Tenant scope |
| `name` | VARCHAR(255) | NOT NULL | Site/facility name |
| `country_code` | VARCHAR(2) | Nullable | Site country |
| `address` | VARCHAR(500) | Nullable | Physical address |
| `grid_region` | VARCHAR(50) | Nullable | Electricity grid region (for US subgrids) |
| `is_active` | BOOLEAN | Default: true | Soft delete |
| `created_at` | TIMESTAMP | Auto | Creation timestamp |

#### `reporting_periods`

Time periods for organizing activity data. Supports verification workflow.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `organization_id` | UUID | FK -> organizations.id, INDEX | Tenant scope |
| `name` | VARCHAR(100) | NOT NULL | Display name (e.g., "FY 2024", "Q1 2024") |
| `start_date` | DATE | NOT NULL | Period start |
| `end_date` | DATE | NOT NULL | Period end |
| `is_locked` | BOOLEAN | Default: false | Prevents edits when locked |
| `status` | ENUM(PeriodStatus) | Default: DRAFT | Verification workflow status |
| `assurance_level` | ENUM(AssuranceLevel) | Nullable | Limited or reasonable assurance |
| `submitted_at` | TIMESTAMP | Nullable | When submitted for audit |
| `submitted_by_id` | UUID | FK -> users.id | Who submitted |
| `verified_at` | TIMESTAMP | Nullable | When verified by auditor |
| `verified_by` | VARCHAR(255) | Nullable | Auditor name/firm |
| `verification_statement` | TEXT | Nullable | Auditor's verification statement |
| `created_at` | TIMESTAMP | Auto | Creation timestamp |

**Verification Workflow:** `DRAFT -> REVIEW -> SUBMITTED -> AUDIT -> VERIFIED -> LOCKED`

#### `invitations`

Team member invitations. Allows admins to invite users to their organization.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `organization_id` | UUID | FK -> organizations.id, INDEX | Target organization |
| `email` | VARCHAR(255) | INDEX | Invitee email |
| `role` | ENUM(UserRole) | Default: editor | Assigned role |
| `status` | ENUM(InvitationStatus) | Default: pending | pending/accepted/expired/canceled |
| `invited_by_id` | UUID | FK -> users.id | Who sent the invitation |
| `token` | VARCHAR(255) | UNIQUE, INDEX | Secure invitation token |
| `created_at` | TIMESTAMP | Auto | When sent |
| `expires_at` | TIMESTAMP | NOT NULL | Expiration deadline |
| `accepted_at` | TIMESTAMP | Nullable | When accepted |

#### `audit_logs`

Comprehensive audit trail for compliance, debugging, and security monitoring.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `organization_id` | UUID | FK -> organizations.id, INDEX | Tenant scope |
| `user_id` | UUID | FK -> users.id, INDEX, Nullable | Acting user |
| `user_email` | VARCHAR(255) | Nullable | Email snapshot |
| `action` | ENUM(AuditAction) | INDEX | Action type (create, update, delete, login, etc.) |
| `resource_type` | VARCHAR(50) | INDEX | Affected entity type |
| `resource_id` | VARCHAR(100) | Nullable | Affected entity ID |
| `description` | VARCHAR(500) | NOT NULL | Human-readable description |
| `details` | TEXT | Nullable | JSON string with additional context |
| `ip_address` | VARCHAR(45) | Nullable | Client IP |
| `user_agent` | VARCHAR(500) | Nullable | Browser/client info |
| `created_at` | TIMESTAMP | INDEX | Event timestamp |

### 2.2 Emission Tables

#### `activities`

User-entered activity data. Each activity represents a single emission-producing event.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `organization_id` | UUID | FK -> organizations.id, INDEX | Tenant scope |
| `reporting_period_id` | UUID | FK -> reporting_periods.id, INDEX | Period assignment |
| `site_id` | UUID | FK -> sites.id, Nullable | Optional site association |
| `scope` | INTEGER | 1-3, NOT NULL | GHG Protocol scope |
| `category_code` | VARCHAR(10) | NOT NULL | GHG category (e.g., "1.1", "2", "3.6") |
| `description` | VARCHAR(500) | Default: "" | Optional description |
| `activity_key` | VARCHAR(100) | INDEX | Links to emission_factors.activity_key |
| `quantity` | DECIMAL | NOT NULL | Numeric value |
| `unit` | VARCHAR(50) | NOT NULL | Unit of measurement |
| `calculation_method` | ENUM(CalculationMethod) | Default: activity | activity/spend/distance/supplier |
| `activity_date` | DATE | NOT NULL | When the activity occurred |
| `data_source` | ENUM(DataSource) | Default: manual | manual/import/api |
| `import_batch_id` | UUID | FK -> import_batches.id, Nullable | Import tracking |
| `data_quality_score` | INTEGER | 1-5, Default: 5 | PCAF score |
| `data_quality_justification` | VARCHAR(500) | Nullable | Justification text |
| `supporting_document_url` | VARCHAR(500) | Nullable | Evidence URL |
| `created_by` | UUID | FK -> users.id, Nullable | Creator |
| `created_at` | TIMESTAMP | Auto | Creation time |
| `updated_at` | TIMESTAMP | Nullable | Last modification |

#### `emissions`

Calculated emission results. One-to-one relationship with activities.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `activity_id` | UUID | FK -> activities.id, UNIQUE, INDEX | Parent activity |
| `emission_factor_id` | UUID | FK -> emission_factors.id, Nullable | Factor used |
| `co2_kg` | DECIMAL | Nullable | CO2 component (kg) |
| `ch4_kg` | DECIMAL | Nullable | CH4 component (kg) |
| `n2o_kg` | DECIMAL | Nullable | N2O component (kg) |
| `co2e_kg` | DECIMAL | NOT NULL | Total CO2-equivalent (kg) |
| `wtt_co2e_kg` | DECIMAL | Nullable | WTT emissions for Scope 3.3 (kg) |
| `converted_quantity` | DECIMAL | Nullable | Quantity after unit conversion |
| `converted_unit` | VARCHAR(50) | Nullable | Unit after conversion |
| `formula` | VARCHAR(500) | Nullable | Human-readable calculation formula |
| `confidence` | ENUM(ConfidenceLevel) | Default: HIGH | high/medium/low |
| `resolution_strategy` | VARCHAR(50) | Default: "exact" | exact/region/global |
| `needs_review` | BOOLEAN | Default: false | Flagged for manual review |
| `warnings` | JSON | Nullable | Array of warning messages |
| `factor_year` | INTEGER | Nullable | Year of the factor used |
| `factor_region` | VARCHAR(50) | Nullable | Region of the factor used |
| `method_hierarchy` | VARCHAR(50) | Nullable | supplier/ecoinvent/defra_physical/eeio_spend |
| `calculated_at` | TIMESTAMP | Auto | Initial calculation time |
| `recalculated_at` | TIMESTAMP | Nullable | Last recalculation time |

#### `emission_factors`

Master registry of emission factors. Single source of truth with governance workflow.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `scope` | INTEGER | 1-3, INDEX | GHG scope |
| `category_code` | VARCHAR(10) | INDEX | GHG category |
| `subcategory` | VARCHAR(100) | Nullable | Sub-classification |
| `activity_key` | VARCHAR(100) | INDEX | Explicit lookup key (e.g., "natural_gas_volume") |
| `display_name` | VARCHAR(255) | NOT NULL | Human-readable name |
| `co2_factor` | DECIMAL | Nullable | CO2 per activity unit |
| `ch4_factor` | DECIMAL | Nullable | CH4 per activity unit |
| `n2o_factor` | DECIMAL | Nullable | N2O per activity unit |
| `co2e_factor` | DECIMAL | NOT NULL | Total CO2e per activity unit |
| `activity_unit` | VARCHAR(50) | NOT NULL | Expected input unit (liters, kWh, km, etc.) |
| `factor_unit` | VARCHAR(50) | NOT NULL | Display unit (kg CO2e/liter) |
| `source` | VARCHAR(100) | NOT NULL | Data source (DEFRA_2024, EPA_2024, etc.) |
| `region` | VARCHAR(50) | Default: "Global", INDEX | Geographic applicability |
| `year` | INTEGER | INDEX | Factor year |
| `notes` | VARCHAR(1000) | Nullable | Documentation |
| `is_active` | BOOLEAN | Default: true | Active/archived |
| `wtt_factor_id` | UUID | FK -> emission_factors.id, Nullable | Linked WTT factor |
| `valid_from` | DATE | Nullable | Validity start |
| `valid_until` | DATE | Nullable | Validity end |
| `status` | VARCHAR(20) | Default: "approved", INDEX | Governance: draft/pending/approved/rejected/archived |
| `version` | INTEGER | Default: 1 | Version number |
| `previous_version_id` | UUID | FK -> emission_factors.id, Nullable | Version chain |
| `change_reason` | VARCHAR(500) | Nullable | Why it was changed |
| `submitted_at` | TIMESTAMP | Nullable | Submitted for approval |
| `submitted_by_id` | UUID | FK -> users.id, Nullable | Submitter |
| `approved_at` | TIMESTAMP | Nullable | Approval timestamp |
| `approved_by_id` | UUID | FK -> users.id, Nullable | Approver |
| `rejected_at` | TIMESTAMP | Nullable | Rejection timestamp |
| `rejected_by_id` | UUID | FK -> users.id, Nullable | Rejector |
| `rejection_reason` | VARCHAR(500) | Nullable | Rejection explanation |
| `created_at` | TIMESTAMP | Auto | Creation time |
| `created_by_id` | UUID | FK -> users.id, Nullable | Creator |
| `updated_at` | TIMESTAMP | Nullable | Last update |
| `updated_by_id` | UUID | FK -> users.id, Nullable | Last updater |

#### `import_batches`

Tracks uploaded files for audit and review.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `organization_id` | UUID | FK -> organizations.id, INDEX | Tenant scope |
| `reporting_period_id` | UUID | FK -> reporting_periods.id, INDEX | Target period |
| `file_name` | VARCHAR(255) | NOT NULL | Original filename |
| `file_type` | VARCHAR(50) | NOT NULL | "excel" or "csv" |
| `file_size_bytes` | INTEGER | Nullable | File size |
| `status` | ENUM(ImportBatchStatus) | Default: pending | pending/processing/completed/failed/partial |
| `total_rows` | INTEGER | Default: 0 | Total data rows |
| `successful_rows` | INTEGER | Default: 0 | Successfully imported |
| `failed_rows` | INTEGER | Default: 0 | Failed rows |
| `skipped_rows` | INTEGER | Default: 0 | Skipped rows |
| `error_message` | VARCHAR(1000) | Nullable | Global error |
| `row_errors` | JSON | Nullable | Per-row errors [{row, error}] |
| `uploaded_by` | UUID | FK -> users.id | Uploader |
| `uploaded_at` | TIMESTAMP | Auto | Upload time |
| `completed_at` | TIMESTAMP | Nullable | Processing completion |

### 2.3 Reference Data Tables

These tables contain shared (non-tenant-scoped) reference data used across all organizations.

#### `unit_conversions`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | PK |
| `from_unit` | VARCHAR(50) | Source unit |
| `to_unit` | VARCHAR(50) | Target unit |
| `multiplier` | DECIMAL | Conversion factor |
| `category` | VARCHAR(50) | volume/mass/distance/energy |

#### `fuel_prices`

Fuel prices for converting monetary spend to physical quantity.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | PK |
| `fuel_type` | VARCHAR(50) | diesel, petrol, natural_gas, lpg, electricity |
| `price_per_unit` | DECIMAL | Price per unit in local currency |
| `currency` | VARCHAR(3) | USD, EUR, GBP, ILS |
| `unit` | VARCHAR(20) | liter, gallon, m3, kWh, therm |
| `region` | VARCHAR(50) | US, UK, IL, EU, Global |
| `valid_from` | DATE | Validity start |
| `valid_until` | DATE | Validity end (nullable) |
| `source` | VARCHAR(200) | Source citation |
| `source_url` | VARCHAR(500) | Source URL (nullable) |
| `is_active` | BOOLEAN | Active flag |

#### `grid_emission_factors`

Country-specific electricity grid emission factors for Scope 2 and T&D loss calculations.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | PK |
| `country_code` | VARCHAR(2) | ISO country code |
| `country_name` | VARCHAR(100) | Country name |
| `region` | VARCHAR(100) | Sub-region (US subgrids) |
| `location_factor` | DECIMAL | Location-based factor (kg CO2e/kWh) |
| `market_factor` | DECIMAL | Market-based factor (kg CO2e/kWh, nullable) |
| `td_loss_factor` | DECIMAL | T&D loss emission factor (nullable) |
| `td_loss_percentage` | DECIMAL | T&D loss percentage (nullable) |
| `source` | VARCHAR(100) | IEA, eGRID, DEFRA |
| `year` | INTEGER | Factor year |

#### `airports`

Airport reference data for flight distance calculations (Category 3.6).

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | PK |
| `iata_code` | VARCHAR(3) | UNIQUE, INDEX (TLV, LHR, JFK) |
| `icao_code` | VARCHAR(4) | Optional ICAO code |
| `name` | VARCHAR(255) | Airport name |
| `city` | VARCHAR(100) | City |
| `country_code` | VARCHAR(2) | ISO country code |
| `country_name` | VARCHAR(100) | Country name |
| `latitude` | DECIMAL(6) | For Haversine distance |
| `longitude` | DECIMAL(6) | For Haversine distance |

#### `transport_distance_matrix`

Default shipping distances for Category 3.4 Upstream Transportation.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | PK |
| `origin_country` | VARCHAR(2) | Origin ISO code (CN, IN, TR) |
| `destination_country` | VARCHAR(2) | Destination ISO code (IL, GB, US) |
| `origin_land_km` | INTEGER | Factory to origin port (default 500) |
| `sea_distance_km` | INTEGER | Port to port |
| `destination_land_km` | INTEGER | Destination port to company (default 100) |
| `total_distance_km` | INTEGER | Sum of all legs |
| `transport_mode` | VARCHAR(50) | sea_container, sea_bulk, air |
| `air_distance_km` | INTEGER | Air freight alternative (nullable) |
| `rail_distance_km` | INTEGER | Rail alternative (nullable) |

#### Additional reference tables

- **`refrigerant_gwp`** -- IPCC AR6 GWP values for refrigerants (R-134a, R-410A, R-32, etc.), including AR5 and AR4 legacy values.
- **`waste_disposal_factors`** -- Emission factors by waste type and disposal method (landfill, recycling, incineration, composting). Source: DEFRA, EPA WARM.
- **`hotel_emission_factors`** -- Country-specific hotel room-night emission factors for Category 3.6 Business Travel.
- **`power_producers`** -- Market-based Scope 2 factors for specific power producers (BDO Israel, AIB Europe, GreenE US, iREC).
- **`currency_conversions`** -- Exchange rates for spend-based calculations (EUR, GBP, ILS -> USD). Source: ECB, OECD annual averages.
- **`price_ranges`** -- Expected price ranges for materials, used to flag potential data entry errors.

### 2.4 CBAM Tables

The CBAM module implements EU Regulation 2023/956 for Carbon Border Adjustment Mechanism reporting.

| Table | Purpose |
|-------|---------|
| `cbam_products` | Reference: CN codes covered by CBAM (cement, iron/steel, aluminium, fertiliser, electricity, hydrogen) |
| `cbam_installations` | Non-EU production facilities with operator details, emissions intensity, and verification status |
| `cbam_imports` | Individual import declarations with embedded emission calculations and carbon price deductions |
| `cbam_quarterly_reports` | Transitional phase quarterly reports (2024-2025) with sector/country breakdowns |
| `cbam_annual_declarations` | Definitive phase annual declarations (2026+) with certificate tracking |
| `cbam_default_values` | EU Commission default specific embedded emissions per CN code |
| `cbam_grid_factors` | Third-country grid emission factors for indirect emissions |
| `eu_ets_prices` | Weekly EU ETS carbon prices for certificate cost calculations |

### 2.5 Supporting Tables

| Table | Purpose |
|-------|---------|
| `import_jobs` | Background job tracking for async file imports. Status: pending/processing/completed/failed/cancelled. Tracks progress (total_rows, processed_rows, successful_rows, failed_rows). |

### 2.6 Enumerations Reference

#### `UserRole`
| Value | Description | Capabilities |
|-------|-------------|-------------|
| `viewer` | Read-only access | View dashboard, reports |
| `editor` | Data entry | All viewer + create/edit activities, import data |
| `admin` | Organization admin | All editor + manage users, periods, org settings |
| `super_admin` | Platform admin | All admin + cross-tenant access, system config |

#### `PeriodStatus` (Verification Workflow)
| Value | Description |
|-------|-------------|
| `draft` | Initial state, data entry allowed |
| `review` | Internal review by organization |
| `submitted` | Submitted for external audit |
| `audit` | Under auditor review |
| `verified` | Auditor verified, awaiting lock |
| `locked` | Final, no further edits possible |

#### `SubscriptionPlan`
| Value | Description |
|-------|-------------|
| `free` | Basic plan, limited features |
| `starter` | Small organizations |
| `professional` | Full features for mid-size organizations |
| `enterprise` | Unlimited, custom features |

#### `SubscriptionStatus`
`active`, `trialing`, `past_due`, `canceled`, `incomplete`, `unpaid`

#### `CalculationMethod`
| Value | Description |
|-------|-------------|
| `activity` | Physical quantity-based (liters, kWh, km) |
| `spend` | Monetary spend-based (USD, EUR) |
| `distance` | Distance-based (km, miles) |
| `supplier` | Supplier-specific emission factor |

#### `DataSource`
`manual`, `import`, `api`

#### `ConfidenceLevel`
| Value | Meaning |
|-------|---------|
| `high` | Exact factor match found |
| `medium` | Regional or similar factor used |
| `low` | Global average or proxy factor |

#### `ImportBatchStatus`
`pending`, `processing`, `completed`, `failed`, `partial`

#### `EmissionFactorStatus`
`draft`, `pending` (pending_approval), `approved`, `rejected`, `archived`

#### `DataQualityScore` (PCAF 1-5)
| Score | Label | Description |
|-------|-------|-------------|
| 1 | VERIFIED | Audited/verified data from primary sources |
| 2 | PRIMARY | Non-audited data from primary sources |
| 3 | ACTIVITY_AVERAGE | Physical activity data with average emission factors |
| 4 | SPEND_BASED | Economic activity-based modeling |
| 5 | ESTIMATED | Estimated data with high uncertainty |

#### `AuditAction`
`create`, `update`, `delete`, `login`, `logout`, `import`, `export`, `status_change`, `invite`, `permission_change`

#### `InvitationStatus`
`pending`, `accepted`, `expired`, `canceled`

#### `AssuranceLevel`
`limited`, `reasonable`

### 2.7 Key Relationships and Foreign Keys

```
organizations (1)
   |
   +--< users (N)               via users.organization_id
   +--< sites (N)               via sites.organization_id
   +--< reporting_periods (N)   via reporting_periods.organization_id
   +--< invitations (N)         via invitations.organization_id
   +--< audit_logs (N)          via audit_logs.organization_id
   +--< import_batches (N)      via import_batches.organization_id
   +--< cbam_installations (N)  via cbam_installations.organization_id
   +--< cbam_imports (N)        via cbam_imports.organization_id

reporting_periods (1)
   |
   +--< activities (N)          via activities.reporting_period_id
   +--< import_batches (N)      via import_batches.reporting_period_id

sites (1)
   |
   +--< activities (N)          via activities.site_id (optional)

activities (1)
   |
   +--< emissions (1)           via emissions.activity_id (UNIQUE, one-to-one)

import_batches (1)
   |
   +--< activities (N)          via activities.import_batch_id

emission_factors (self-referential)
   |
   +-- wtt_factor_id           -> emission_factors.id (WTT link)
   +-- previous_version_id     -> emission_factors.id (version chain)
```

---

## 3. Application Logic

### 3.1 Emission Calculation Pipeline

The calculation pipeline is a 3-stage architecture that converts user activity data into calculated CO2e emissions. It is implemented in `app/services/calculation/pipeline.py`.

```
              +-------------------+
              |  ActivityInput    |
              |  (from API/import)|
              +--------+----------+
                       |
            +----------v-----------+
            | Stage 1: NORMALIZE   |
            | Convert user units   |
            | to factor units      |
            | (via Pint library)   |
            +----------+-----------+
                       |
            +----------v-----------+
            | Stage 2: RESOLVE     |
            | Find emission factor |
            | exact -> region ->   |
            | global fallback      |
            +----------+-----------+
                       |
            +----------v-----------+
            | Stage 3: CALCULATE   |
            | Apply strategy:      |
            | Fuel / Electricity / |
            | Spend / Flight /     |
            | Transport / Waste /  |
            | Refrigerant /        |
            | LeasedAssets         |
            +----------+-----------+
                       |
            +----------v-----------+
            | + WTT Auto-Calc      |
            | Scope 3.3 emissions  |
            +----------+-----------+
                       |
              +--------v----------+
              |  CalculationResult |
              |  co2e_kg, formula, |
              |  confidence, etc.  |
              +-------------------+
```

**Pipeline usage (code):**

```python
pipeline = CalculationPipeline(session)
result = await pipeline.calculate(ActivityInput(
    activity_key="natural_gas_volume",
    quantity=Decimal("1000"),
    unit="m3",
    scope=1,
    category_code="1.1",
    region="Global",
    year=2024,
))
# result.co2e_kg = 1000 * 2.06318 = 2063.18 kg CO2e
```

**Special calculation paths:**

1. **Supplier-Specific** (`activity_key` starts with `supplier_specific`): User provides their own emission factor. Bypasses factor resolution entirely. Highest accuracy per GHG Protocol hierarchy.
2. **Market-Based Scope 2** (`scope=2`, `supplier_ef` provided, electricity keys): Uses supplier-provided emission factor for market-based Scope 2 reporting.
3. **Scope 1 Supplier EF** (`scope=1`, `supplier_ef` provided): Overrides standard DEFRA/IPCC factor with a supplier-provided value (e.g., Urea/AdBlue).

### 3.2 Factor Resolution Hierarchy

The `FactorResolver` (in `app/services/calculation/resolver.py`) finds the best emission factor using ranked fallback strategies. Only factors with `status='approved'` are eligible.

**Standard resolution (3-tier):**

| Priority | Strategy | Match Criteria | Confidence |
|----------|----------|----------------|------------|
| 1 | **EXACT** | activity_key + region + year | HIGH |
| 2 | **REGION** | activity_key + region (latest year) | HIGH |
| 3 | **GLOBAL** | activity_key + region="Global" (latest year) | MEDIUM |
| 4 | **ANY_REGION** | activity_key only (any region, latest year) | HIGH |
| -- | NOT_FOUND | No match | Error raised |

**GHG Protocol hierarchy for Category 3.1 (Purchased Goods):**

For Category 3.1, an extended hierarchy is available via `resolve_with_hierarchy()`:

| Tier | Strategy | Description | Accuracy |
|------|----------|-------------|----------|
| 1 | Supplier-Specific | EPD, LCA data (handled in pipeline) | Highest |
| 2 | EcoInvent | Process-specific LCA database (stub, future) | High |
| 3 | DEFRA Physical | Material-specific kg CO2e/kg factors | Medium |
| 4 | EEIO Spend | Input-output spend-based (kg CO2e/USD) | Lowest |

### 3.3 WTT (Well-to-Tank) Auto-Calculation

WTT emissions represent the upstream carbon cost of extracting, refining, and transporting fuels and generating electricity. CLIMATRIX automatically calculates WTT emissions for Scope 1 and Scope 2 activities and aggregates them into Scope 3, Category 3.3 (Fuel and Energy Related Activities).

**How it works:**

1. When a Scope 1 or 2 activity is calculated, the `WTTService` looks up a corresponding WTT factor using a pattern-based mapping.
2. The mapping connects activity keys (e.g., `natural_gas_volume`) plus their normalized units (e.g., `m3`) to WTT factor keys (e.g., `wtt_natural_gas_m3`).
3. The WTT emission is calculated as: `wtt_co2e_kg = quantity * wtt_factor.co2e_factor`
4. The result is stored on the `emissions.wtt_co2e_kg` column.
5. Aggregation: `pipeline.aggregate_wtt_for_period(period_id)` sums all WTT emissions grouped by source scope.

**Covered WTT mappings include:** Natural gas (m3, kWh, kg), diesel (liters, kg), petrol/gasoline, LPG, LNG, coal, fuel oil, electricity (all regions), district heat, steam, vehicle fuels by km, aviation fuel, and rail.

**Feature flag:** `enable_wtt_auto_calculation` (default: `true` in config).

### 3.4 Data Quality Scoring

CLIMATRIX uses the PCAF (Partnership for Carbon Accounting Financials) methodology for data quality assessment, scored 1 through 5:

| Score | Label | Criteria | Example |
|-------|-------|----------|---------|
| 1 | VERIFIED | Audited/verified data from primary sources | Audited energy bills, verified supplier data |
| 2 | PRIMARY | Non-audited data from primary sources | Unaudited utility bills, supplier invoices |
| 3 | ACTIVITY_AVERAGE | Physical activity data with average emission factors | Measured km driven with average fuel efficiency |
| 4 | SPEND_BASED | Economic activity-based modeling | Spend-based calculations, revenue proxies |
| 5 | ESTIMATED | Estimated data with high uncertainty | Industry averages, EEIO models, extrapolations |

- Default score for new activities is **5** (most conservative).
- Users can override with a justification (`data_quality_justification`) and supporting document URL.
- The score is stored on `activities.data_quality_score`.

### 3.5 Confidence Levels

Confidence levels are system-determined based on how the emission factor was resolved:

| Level | Meaning | Triggered By |
|-------|---------|-------------|
| **HIGH** | Exact or region-specific factor match | EXACT or REGION resolution strategy |
| **MEDIUM** | Global fallback factor used | GLOBAL resolution strategy |
| **LOW** | Proxy or estimated factor | EEIO spend-based fallback |

Confidence is stored on `emissions.confidence` and surfaced in the UI to guide users toward providing better data.

### 3.6 Import Processing Flow

CLIMATRIX supports bulk data import via Excel (.xlsx) and CSV files. The import flow has two paths based on file size.

```
[User uploads file]
        |
        v
[Parse file content]
  - Excel: openpyxl
  - CSV: csv.DictReader
        |
        v
[Normalize column headers]
  - Map aliases to standard names
  - Required: scope, category_code, activity_key, quantity, unit
  - Optional: description, activity_date, site_id
        |
        v
[AI Column Mapping (if enabled)]
  - Claude AI suggests column mappings for non-standard headers
        |
        v
[Validate each row]
  - Check required fields present
  - Validate scope (1-3)
  - Validate activity_key exists in factor database
  - Parse quantity as number
  - Validate date format
  - Suggest similar activity_keys on mismatch
        |
        v
[Preview returned to user]
  - total_rows, valid_rows, invalid_rows
  - Per-row errors and warnings
  - User reviews and confirms
        |
        v
[Process import]
  - Create ImportBatch record
  - For each valid row:
    1. Create Activity record
    2. Run CalculationPipeline
    3. Create Emission record
  - Track success/failure counts
        |
        v
[Result returned]
  - imported count, failed count
  - Per-row errors for failures
  - import_batch_id for filtering/review
```

**Async processing:** Large files (configurable threshold) are queued to Redis and processed by an Arq background worker. The frontend polls the `import_jobs` table for progress updates.

**Column aliases supported:**

| Standard Name | Accepted Aliases |
|--------------|------------------|
| scope | scope, scope_number, emission_scope |
| category_code | category_code, category, ghg_category |
| activity_key | activity_key, activity_type, activity, type |
| description | description, desc, notes, name |
| quantity | quantity, amount, value, qty |
| unit | unit, units, uom |
| activity_date | activity_date, date, activity_month, period |
| site_id | site_id, site, facility, location |

### 3.7 Calculation Strategies

The pipeline uses the Strategy pattern. Each GHG category maps to a specific calculator:

| Category | Calculator | Specialization |
|----------|-----------|----------------|
| 1.1 (Stationary Combustion) | FuelCalculator | quantity x factor with gas breakdown |
| 1.2 (Mobile Combustion) | FuelCalculator | Same as 1.1 |
| 1.3 (Fugitive Emissions) | RefrigerantCalculator | leaked_mass x GWP |
| 2 / 2.1 / 2.2 (Electricity/Heat) | ElectricityCalculator | Location-based and market-based |
| 3.1 (Purchased Goods) | SpendCalculator | Spend x EEIO factor or DEFRA physical |
| 3.2 (Capital Goods) | SpendCalculator | Same as 3.1 |
| 3.3 (Fuel & Energy) | FuelCalculator | WTT auto-aggregated from Scope 1/2 |
| 3.4 (Upstream Transport) | TransportCalculator | weight x distance x mode factor |
| 3.5 (Waste) | WasteCalculator | mass x waste_type x disposal_method factor |
| 3.6 (Business Travel) | FlightCalculator | Distance with cabin class, RF uplift, 9% routing |
| 3.7 (Employee Commuting) | FuelCalculator | Distance-based commute calculations |
| 3.8 (Upstream Leased) | LeasedAssetsCalculator | Area/energy-based |
| 3.9 (Downstream Transport) | TransportCalculator | Same as 3.4 |
| 3.12 (End-of-Life) | WasteCalculator | Same as 3.5 |
| 3.13 (Downstream Leased) | LeasedAssetsCalculator | Same as 3.8 |
| 3.14 (Franchises) | LeasedAssetsCalculator | Same as 3.8 |

**Base formula:** `co2e_kg = normalized_quantity x co2e_factor`

All calculators inherit from `BaseCalculator` and implement `_base_calculation()` which provides: gas-level breakdown (CO2, CH4, N2O), WTT calculation, unit conversion tracking, and human-readable formula generation.

### 3.8 Unit Normalization

The `UnitNormalizer` (Stage 1) uses the **Pint** library for physics-grade unit conversions. It converts user input units to the emission factor's expected unit.

**Custom Pint definitions:**

- `tonne = 1000 * kilogram`
- `therm = 105.5 * megajoule`
- `cubic_meter = meter^3` (aliases: m3, m3)
- `kilowatt_hour = kilowatt * hour` (alias: kWh)
- `passenger_km = kilometer` (alias: pkm)
- `tonne_km = tonne * kilometer` (alias: tkm)

**Unit alias mapping examples:** `m3` -> `cubic_meter`, `liters` -> `liter`, `kg` -> `kilogram`, `kwh` -> `kilowatt_hour`, `tonnes` -> `tonne`, `gallons` -> `gallon`, etc.

### 3.9 Currency Conversion

For spend-based categories (3.1, 3.2, and others), EEIO factors are denominated in USD. CLIMATRIX automatically converts non-USD inputs using annual average exchange rates:

| Currency | Rate to USD (2024) |
|----------|-------------------|
| USD | 1.00 |
| EUR | 1.08 |
| GBP | 1.27 |
| ILS | 0.27 |
| CAD | 0.74 |
| AUD | 0.66 |
| JPY | 0.0067 |
| CNY | 0.14 |
| INR | 0.012 |
| CHF | 1.13 |
| SEK | 0.095 |
| NOK | 0.092 |
| DKK | 0.145 |

Conversions are tracked via warnings on the `CalculationResult` for full transparency.

---

## 4. Admin Guide

### 4.1 CLI Commands

All CLI commands are run via the Typer framework. The entrypoint is `python -m app.cli db <command>`.

#### `seed` -- Seed Reference Data

Seeds emission factors, unit conversions, and fuel prices into the database.

```bash
# Check if seeding is needed
python -m app.cli db seed --check-only

# Seed reference data (skips if already seeded)
python -m app.cli db seed

# Force re-seed (clears and re-inserts all reference data)
python -m app.cli db seed --force
```

**What gets seeded:**
- Emission factors (DEFRA 2024, EPA, IEA, USEEIO)
- Unit conversions (volume, mass, energy, distance)
- Fuel prices (US, UK, IL, EU, Global)

#### `create-superuser` -- Create Super Admin

Creates a super admin user, optionally creating an organization if none exists.

```bash
python -m app.cli db create-superuser \
  --email admin@climatrix.io \
  --password "YourSecurePassword123!" \
  --name "Admin User" \
  --org-name "CLIMATRIX Admin"
```

**Behavior:**
- If the email already exists, the password and role are **updated** to super_admin.
- If no organization exists, one is created using `--org-name` (or prompted).
- If organizations exist, the user is assigned to the first one found.

**Options:**

| Flag | Short | Required | Description |
|------|-------|----------|-------------|
| `--email` | `-e` | Yes (prompted) | Super admin email |
| `--password` | `-p` | Yes (prompted, hidden) | Password |
| `--name` | `-n` | No | Full name (defaults to email prefix) |
| `--org-name` | -- | No | Organization name (prompted if needed) |

#### `create-user` -- Create Regular User

Creates a new user in an existing organization.

```bash
python -m app.cli db create-user user@example.com "password123" \
  --name "Jane Doe" \
  --role editor \
  --org-id "uuid-of-organization"
```

**Options:**

| Argument/Flag | Required | Default | Description |
|---------------|----------|---------|-------------|
| `EMAIL` | Yes | -- | User email (positional) |
| `PASSWORD` | Yes | -- | Password (positional) |
| `--name` | No | Email prefix | Full name |
| `--role` | No | editor | viewer, editor, admin |
| `--org-id` | No | First org | Target organization UUID |

#### `seed-fuel-prices` -- Seed Fuel Prices Only

Seeds fuel prices into an existing database (useful for adding price data after initial deployment).

```bash
python -m app.cli db seed-fuel-prices
python -m app.cli db seed-fuel-prices --force
```

#### `seed-scope3-reference` -- Seed Scope 3 Reference Data

Seeds all Scope 3-specific reference tables.

```bash
python -m app.cli db seed-scope3-reference
python -m app.cli db seed-scope3-reference --force
```

**What gets seeded:**
- Airports (IATA codes, coordinates for flight distance calculation)
- Transport distance matrix (sea/land/air distances between countries)
- Currency conversion rates (annual averages for spend-based calculations)
- Grid emission factors (country-specific electricity factors)
- Hotel emission factors (per room-night by country)
- Refrigerant GWP values (IPCC AR6)
- Waste disposal factors (by waste type and disposal method)

### 4.2 User Management

#### Roles and Permissions

| Capability | viewer | editor | admin | super_admin |
|-----------|:------:|:------:|:-----:|:-----------:|
| View dashboard & reports | Yes | Yes | Yes | Yes |
| Create/edit activities | -- | Yes | Yes | Yes |
| Import data | -- | Yes | Yes | Yes |
| Manage reporting periods | -- | -- | Yes | Yes |
| Manage users & invitations | -- | -- | Yes | Yes |
| Manage organization settings | -- | -- | Yes | Yes |
| Manage billing/subscription | -- | -- | Yes | Yes |
| Access admin panel (/api/admin/*) | -- | -- | -- | Yes |
| View all organizations | -- | -- | -- | Yes |
| View all users cross-tenant | -- | -- | -- | Yes |

#### Managing Users via API

Super admins can manage users across organizations via the admin API:

- `GET /api/admin/users` -- List all users with organization info
- `GET /api/admin/organizations` -- List all organizations with stats
- `GET /api/admin/activity-log` -- View all activities across tenants

Organization admins manage their own users via the organization API:

- `GET /api/organization/members` -- List organization members
- `POST /api/organization/invite` -- Send team invitation
- `PATCH /api/organization/members/{id}/role` -- Change member role
- `DELETE /api/organization/members/{id}` -- Deactivate member

### 4.3 Organization Setup

**Creating an organization:**

Organizations are typically created during user registration (onboarding wizard) or via the CLI when creating a super admin. The onboarding flow collects:

1. Organization name
2. Country code (ISO 3166-1 alpha-2)
3. Industry code
4. Base year for GHG inventory
5. Default region for factor resolution

**Configuring an organization:**

Via `PATCH /api/organization/settings`:
- Update name, country, industry code
- Set base year
- Set default region (affects factor resolution fallback)

### 4.4 Reporting Period Management

Reporting periods organize activity data and follow a verification workflow.

**Creating a period:**
- `POST /api/periods/` with `name`, `start_date`, `end_date`
- Example: `{"name": "FY 2024", "start_date": "2024-01-01", "end_date": "2024-12-31"}`

**Verification workflow transitions:**

```
DRAFT  -->  REVIEW  -->  SUBMITTED  -->  AUDIT  -->  VERIFIED  -->  LOCKED
  ^                                                                    |
  |  (revert to draft if issues found)                                 |
  +--------------------------------------------------------------------+
```

- **DRAFT:** Data entry allowed. Activities can be created, edited, deleted.
- **REVIEW:** Internal review. Organization admin reviews data completeness.
- **SUBMITTED:** Submitted to external auditor. `submitted_at` and `submitted_by_id` recorded.
- **AUDIT:** Auditor is reviewing the data.
- **VERIFIED:** Auditor has verified. `verified_at`, `verified_by`, and `verification_statement` recorded. `assurance_level` set (limited/reasonable).
- **LOCKED:** Period is finalized. No further edits possible. `is_locked = true`.

**Recalculation:**

After updating emission factors, recalculate all emissions for a period:
- `POST /api/admin/recalculate/{period_id}` -- Recalculates all activities in the period using the latest approved emission factors.

### 4.5 Subscription and Billing Management

CLIMATRIX uses Stripe for subscription billing.

**Plan hierarchy:**

| Plan | Stripe Price ID Config | Typical Features |
|------|----------------------|------------------|
| `free` | N/A | Basic access, limited activities |
| `starter` | `stripe_price_id_starter` | Small organizations |
| `professional` | `stripe_price_id_professional` | Full Scope 1/2/3 |
| `enterprise` | `stripe_price_id_enterprise` | Unlimited, CBAM, API access |

**Billing endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/billing/subscription` | GET | Get current subscription details |
| `/api/billing/plans` | GET | List available plans with limits |
| `/api/billing/checkout` | POST | Create Stripe Checkout session |
| `/api/billing/portal` | POST | Create Stripe Customer Portal session |
| `/api/billing/webhook` | POST | Stripe webhook handler |

**Stripe webhook events handled:**
- `checkout.session.completed` -- Subscription created
- `customer.subscription.updated` -- Plan change, renewal
- `customer.subscription.deleted` -- Cancellation
- `invoice.payment_succeeded` -- Payment confirmed
- `invoice.payment_failed` -- Payment failed

### 4.6 Data Import (Excel Templates)

**Excel template required columns:**

| Column | Required | Type | Example |
|--------|----------|------|---------|
| scope | Yes | Integer (1-3) | 1 |
| category_code | Yes | String | "1.1" |
| activity_key | Yes | String | "natural_gas_volume" |
| quantity | Yes | Number | 1500.5 |
| unit | Yes | String | "m3" |
| description | No | String | "Main office heating" |
| activity_date | No | Date (YYYY-MM-DD) | "2024-03-15" |
| site_id | No | UUID | "abc-def-..." |

**Import endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/import/template` | GET | Download blank Excel template |
| `/api/import/preview` | POST | Upload and preview file (validation) |
| `/api/import/process` | POST | Process validated import |
| `/api/import/upload` | POST | Upload for async processing (large files) |
| `/api/import/batches` | GET | List import batches |
| `/api/import/jobs/{id}` | GET | Check async job status |

### 4.7 Emission Factor Governance

Emission factors follow an approval workflow to ensure data integrity:

```
DRAFT  -->  PENDING_APPROVAL  -->  APPROVED  (used in calculations)
                  |
                  +--->  REJECTED  (with rejection_reason)

APPROVED  -->  ARCHIVED  (replaced by newer version)
```

- Only factors with `status = 'approved'` are used in calculations.
- Changes to approved factors create a new version (`version` incremented, `previous_version_id` set).
- The `change_reason` field documents why changes were made.
- `submitted_by_id`, `approved_by_id`, `rejected_by_id` track who performed each action.

**Factor management endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/emission-factors` | GET | List factors (filterable) |
| `/api/emission-factors/{id}` | GET | Get factor details |
| `/api/emission-factors` | POST | Create new factor (draft) |
| `/api/emission-factors/{id}` | PATCH | Update factor |
| `/api/emission-factors/{id}/submit` | POST | Submit for approval |
| `/api/emission-factors/{id}/approve` | POST | Approve (admin only) |
| `/api/emission-factors/{id}/reject` | POST | Reject with reason |

---

## 5. User Guide

### 5.1 Registration and Onboarding

**Registration flow:**

1. Navigate to the CLIMATRIX application URL.
2. Click "Sign Up" or "Get Started."
3. Choose authentication method:
   - **Email/Password:** Enter email, create password, verify email.
   - **Google SSO:** Click "Continue with Google" (requires `GOOGLE_CLIENT_ID` to be configured).
4. Complete the onboarding wizard:
   - **Step 1:** Organization name
   - **Step 2:** Country and industry
   - **Step 3:** Base year selection
   - **Step 4:** First reporting period setup
   - **Step 5:** (Optional) Invite team members

The first user in an organization is automatically assigned the `admin` role.

### 5.2 Entering Data via the Activity Wizard

The activity wizard guides users through creating emission activities step by step:

1. **Select Scope:** Choose Scope 1 (Direct), Scope 2 (Energy Indirect), or Scope 3 (Value Chain).
2. **Select Category:** Based on scope, choose the GHG Protocol category (e.g., 1.1 Stationary Combustion, 3.6 Business Travel).
3. **Select Activity Type:** Choose the specific activity key (e.g., "Natural Gas (volume)", "Diesel (liters)", "Electricity Israel").
4. **Enter Quantity and Unit:** Enter the numerical value and unit of measurement.
5. **Select Date and Site:** Choose the activity date and optionally assign to a site.
6. **Data Quality:** Optionally set the PCAF data quality score (1-5) with justification.
7. **Review and Submit:** Review the calculation preview (CO2e result, formula, confidence level) before saving.

The calculation runs in real-time as the user enters data, showing:
- Calculated CO2e emissions (kg and tonnes)
- Gas breakdown (CO2, CH4, N2O)
- WTT emissions (for Scope 1/2)
- Factor used (source, year, region)
- Confidence level and any warnings

### 5.3 Uploading Excel Templates

1. Navigate to the Import section.
2. Download the blank template via the "Download Template" button.
3. Fill in the template with your activity data:
   - One row per activity
   - Use the correct `activity_key` values (available in the reference data section)
   - Dates in YYYY-MM-DD format
4. Upload the file (.xlsx or .csv).
5. Review the preview:
   - Green rows: Valid, will be imported.
   - Red rows: Invalid, with error messages explaining the issue.
   - Yellow rows: Valid with warnings (e.g., scope/category mismatch).
6. Fix any errors in your file and re-upload, or proceed with valid rows only.
7. Click "Import" to process.
8. Review the import result: success count, failure count, and any row-level errors.

**AI-powered column mapping:** If your file uses non-standard column headers, the AI column mapper (powered by Claude) will suggest mappings. Review and confirm before proceeding.

### 5.4 Viewing the Dashboard

The dashboard provides an at-a-glance view of your organization's GHG inventory:

- **Total Emissions:** Overall CO2e in tonnes for the selected reporting period.
- **Scope Breakdown:** Pie/bar chart showing Scope 1, 2, and 3 proportions.
- **Category Breakdown:** Detailed view by GHG Protocol category.
- **Trends:** Time-series chart if multiple periods exist.
- **Data Quality:** Average PCAF score across activities.
- **Recent Activities:** Latest activity entries with status.

Charts are rendered using Recharts and update dynamically based on the selected reporting period.

### 5.5 Generating Reports

CLIMATRIX supports multiple report formats:

**Report Summary (JSON/API):**
- `GET /api/reports/summary?period_id={id}` -- Returns total CO2e, scope breakdowns, and category breakdowns.

**CSV Export:**
- `GET /api/reports/export/csv?period_id={id}` -- Downloads a CSV file with all activities and calculated emissions for the period.

**ISO 14064-1 GHG Inventory Report:**
- `GET /api/reports/ghg-inventory?period_id={id}` -- Generates a structured report compliant with ISO 14064-1, including:
  - Organization information and boundaries
  - Scope 1, 2, and 3 emissions by category
  - Data quality assessment
  - Methodology notes
  - Base year comparison (if base year is set)

**PDF Export:**
- Generated using ReportLab for printable GHG inventory reports.

**Audit Package:**
- Comprehensive export including all activities, emission factors used, calculation formulas, and data quality scores.

### 5.6 Using the CBAM Module

The CBAM (Carbon Border Adjustment Mechanism) module supports EU importers with compliance reporting.

**CBAM workflow:**

1. **Set up installations:** Register non-EU production facilities with operator details, sector, and emissions data.
2. **Record imports:** Enter individual import declarations with CN codes, quantities, and origin countries.
3. **Calculate embedded emissions:** Use actual installation data or EU default values.
4. **Deduct carbon prices:** Record any carbon prices paid in the origin country.
5. **Generate quarterly reports:** (Transitional phase 2024-2025) Aggregate data by sector and country.
6. **Annual declarations:** (Definitive phase 2026+) Calculate certificate requirements and financial liability.

**CBAM endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cbam/installations` | GET/POST | Manage non-EU installations |
| `/api/cbam/imports` | GET/POST | Record/list import declarations |
| `/api/cbam/quarterly-reports` | GET/POST | Generate quarterly reports |
| `/api/cbam/annual-declarations` | GET/POST | Generate annual declarations |
| `/api/cbam/products` | GET | List CBAM-covered CN codes |
| `/api/cbam/default-values` | GET | EU default emission values |

**Covered sectors:** Cement, Iron/Steel, Aluminium, Fertilisers, Electricity, Hydrogen.

### 5.7 Settings: Organization Info and Team Invitations

**Organization settings** (Admin role required):

- Update organization name, country, industry
- Set base year for GHG inventory comparisons
- Configure default region for emission factor resolution

**Team management** (Admin role required):

1. Navigate to Settings > Team.
2. Click "Invite Member."
3. Enter email address and select role (viewer, editor, admin).
4. An invitation email is sent with a secure token link.
5. The invitee clicks the link to accept and create their account.
6. Invitations expire after a configurable period.
7. Admins can view pending, accepted, and expired invitations.
8. Admins can cancel pending invitations or change member roles.

### 5.8 Decarbonization Pathways

The decarbonization module enables data-driven reduction planning:

- **Set targets:** Align with SBTi 1.5C (42% by 2030), Well-below 2C (25% by 2030), Net Zero, or custom targets.
- **Target types:** Absolute (total emissions reduction) or Intensity (per revenue/employee).
- **Reduction initiatives:** Plan specific actions categorized as: energy efficiency, renewable energy, fleet/transport, supply chain, process change, behavior change, waste reduction, or carbon removal.
- **Complexity levels:** Low (quick wins), Medium (moderate effort), High (major projects).
- **Scenarios:** Aggressive, Moderate, Conservative, or Custom reduction pathways.

---

## 6. Emission Factor Sources

### 6.1 DEFRA (UK Government)

**Full name:** Department for Environment, Food & Rural Affairs -- UK Government GHG Conversion Factors

**Version used:** DEFRA 2024 v1.1 (October 2024)

**Source URL:** https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024

**Coverage:**
- Scope 1: Stationary combustion (natural gas, diesel, LPG, LNG, coal, fuel oil), mobile combustion (car, van, HGV fuels), fugitive emissions (refrigerants)
- Scope 2: WTT factors for electricity and heat
- Scope 3: WTT factors for fuels, business travel (flights, rail, hotel), employee commuting, waste disposal, upstream transportation

**GWP basis:** AR5 (100-year) for fuel CH4/N2O components.

**Factor format:** Individual gas components (CO2, CH4, N2O) plus total CO2e. Uses "100% mineral" fuel variant (not biofuel blend) unless noted.

### 6.2 EEA (European Environment Agency)

**Coverage:** European-specific emission factors for electricity generation, transport, and industrial processes.

**Used for:** EU country-specific grid emission factors and transport emission intensities.

### 6.3 EPA eGRID (US Electricity)

**Full name:** Environmental Protection Agency -- Emissions & Generation Resource Integrated Database

**Coverage:** US electricity grid emission factors broken down by:
- National average
- Regional subgrids (eGRID subregions)
- State-level factors

**Used for:** Scope 2 calculations for US-based organizations, providing both location-based and market-based factors.

### 6.4 BEIS (UK Business Energy)

**Full name:** Department for Business, Energy & Industrial Strategy (now DESNZ)

**Coverage:** UK-specific energy prices and emission factors for:
- Electricity
- Natural gas
- Transport fuels

**Used for:** UK fuel price data for spend-to-quantity conversions.

### 6.5 IEA (International Energy Agency)

**Coverage:** Global coverage of electricity grid emission factors for 100+ countries.

**Used for:**
- Country-specific grid emission factors (Scope 2)
- Location-based vs. market-based factors
- T&D (Transmission & Distribution) loss factors for Scope 3.3

**Grid emission factor fields:**
- `location_factor`: Average grid mix (kg CO2e/kWh)
- `market_factor`: Residual mix for RE certificates (kg CO2e/kWh)
- `td_loss_factor`: Emissions from T&D losses (kg CO2e/kWh)
- `td_loss_percentage`: Percentage of electricity lost in transmission

### 6.6 IPCC AR6 GWP Values

**Full name:** Intergovernmental Panel on Climate Change, Sixth Assessment Report (2021)

**Used for:** Global Warming Potential values for refrigerants (Scope 1.3 Fugitive Emissions).

**Stored in:** `refrigerant_gwp` table with AR6, AR5, and AR4 values.

**Key refrigerant GWPs (AR6, 100-year):**

| Refrigerant | Type | GWP (AR6) |
|-------------|------|-----------|
| R-134a | HFC | 1,530 |
| R-410A | HFC blend | 2,088 |
| R-32 | HFC | 771 |
| R-404A | HFC blend | 4,728 |
| R-407C | HFC blend | 1,774 |
| R-22 | HCFC | 1,960 |
| CO2 (R-744) | Natural | 1 |
| NH3 (R-717) | Natural | 0 |

**Formula:** `CO2e = leaked_mass_kg x GWP`

### 6.7 USEEIO (US Environmentally-Extended Input-Output)

**Full name:** US Environmentally-Extended Input-Output Model v2.0

**Coverage:** Spend-based emission factors for all economic sectors (kg CO2e per USD).

**Used for:** Scope 3 spend-based calculations (Categories 3.1, 3.2, and others) when physical activity data is not available. This is the lowest tier in the GHG Protocol calculation hierarchy.

### 6.8 How Factors Are Structured in the Database

Every emission factor in the `emission_factors` table follows a consistent structure:

```
+-----------------+     +------------------+     +-------------------+
| activity_key    |---->| co2e_factor      |---->| Factor Value      |
| (lookup key)    |     | (per unit)       |     | (e.g., 2.06318)   |
+-----------------+     +------------------+     +-------------------+
        |                       |
        v                       v
+-----------------+     +------------------+
| activity_unit   |     | Gas Breakdown    |
| (expected unit) |     | co2_factor       |
| e.g., "m3"     |     | ch4_factor       |
+-----------------+     | n2o_factor       |
                        +------------------+
```

**Key fields for factor identification:**

- `activity_key`: The explicit lookup key that uniquely identifies the activity type. No fuzzy matching; exact string match only. Examples: `natural_gas_volume`, `diesel_liters`, `electricity_il`, `eeio_chemicals`.
- `region`: Geographic scope. "Global" for universally applicable factors, or ISO country codes (IL, UK, US) for region-specific factors.
- `year`: The reporting year of the factor data.
- `source`: The authoritative source identifier (e.g., `DEFRA_2024`, `EPA_2024`, `USEEIO_2.0`).

**Example factor record:**

```
activity_key:    natural_gas_volume
display_name:    Natural Gas (volume)
scope:           1
category_code:   1.1
co2_factor:      2.05916
ch4_factor:      0.00307
n2o_factor:      0.00095
co2e_factor:     2.06318
activity_unit:   m3
factor_unit:     kg CO2e/m3
source:          DEFRA_2024
region:          Global
year:            2024
status:          approved
```

---

## 7. Deployment Runbook

### 7.1 Railway Setup (Backend)

Railway hosts the FastAPI backend, PostgreSQL database, and Redis instance.

**Steps:**

1. **Create a Railway project** with three services:
   - **Web Service:** Python app from Git repository
   - **PostgreSQL:** Managed database add-on
   - **Redis:** Managed Redis add-on

2. **Configure the Web Service:**
   - **Root Directory:** `platform/backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/health`

3. **Connect the database:**
   - Railway automatically provides `DATABASE_URL` as an environment variable.
   - The application converts `postgresql://` to `postgresql+asyncpg://` automatically.

4. **Connect Redis:**
   - Railway provides `REDIS_URL` as an environment variable.

5. **Set environment variables** (see Section 7.3 for full list).

6. **Deploy and verify:**
   - Check `/health` endpoint returns `{"status": "healthy"}`.
   - Run database seed commands (see Section 7.4).

### 7.2 Vercel Setup (Frontend)

Vercel hosts the Next.js frontend with automatic deployments from Git.

**Steps:**

1. **Import the repository** into Vercel.

2. **Configure build settings:**
   - **Root Directory:** `platform/frontend`
   - **Framework Preset:** Next.js
   - **Build Command:** `next build` (default)
   - **Output Directory:** `.next` (default)
   - **Node.js Version:** 18.x or 20.x

3. **Set environment variables:**
   - `NEXT_PUBLIC_API_URL` = `https://your-backend.railway.app` (Railway backend URL)
   - `NEXT_PUBLIC_GOOGLE_CLIENT_ID` = Your Google OAuth Client ID
   - `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` = Your Stripe publishable key
   - `SENTRY_DSN` = Sentry DSN for frontend error tracking (optional)

4. **Configure domain:**
   - Add custom domain (e.g., `app.climatrix.io`)
   - Vercel handles SSL automatically

5. **Preview deploys:**
   - Every PR gets a preview deployment at `*.vercel.app`
   - Backend CORS is configured to allow `*.vercel.app` previews when `cors_allow_vercel_previews = true`

### 7.3 Complete Environment Variables Reference

#### Backend (Railway)

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| **Application** ||||
| `APP_NAME` | No | `CLIMATRIX` | Application name |
| `APP_VERSION` | No | `3.1.0` | Application version |
| `DEBUG` | No | `false` | Enable debug mode (shows /docs and /redoc) |
| `ENVIRONMENT` | Yes | `development` | `development`, `staging`, `production` |
| **Database** ||||
| `DATABASE_URL` | Yes | SQLite (dev) | PostgreSQL connection string (Railway provides this) |
| `DATABASE_ECHO` | No | `false` | Log SQL queries (debug only) |
| **Redis** ||||
| `REDIS_URL` | Yes | `redis://localhost:6379` | Redis connection string (Railway provides this) |
| **Authentication** ||||
| `SECRET_KEY` | **Yes** | CHANGE-THIS... | JWT signing key. Generate with `openssl rand -hex 32` |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |
| **CORS** ||||
| `CORS_ORIGINS_STR` | Yes (prod) | `*` | Allowed origins. Production: `https://app.climatrix.io,https://climatrix.io` |
| `CORS_ALLOW_VERCEL_PREVIEWS` | No | `true` | Allow `*.vercel.app` preview origins |
| **Google OAuth** ||||
| `GOOGLE_CLIENT_ID` | No | `""` | Google OAuth Client ID for SSO login |
| **Reference Data** ||||
| `DEFAULT_EMISSION_FACTOR_YEAR` | No | `2024` | Default factor year for lookups |
| `DEFAULT_REGION` | No | `Global` | Default region for factor resolution |
| **Feature Flags** ||||
| `ENABLE_WTT_AUTO_CALCULATION` | No | `true` | Enable automatic WTT calculation for Scope 3.3 |
| `ENABLE_MARKET_BASED_SCOPE2` | No | `true` | Enable market-based Scope 2 calculations |
| **AI Services** ||||
| `ANTHROPIC_API_KEY` | No | `""` | Anthropic API key for AI-powered features |
| `CLAUDE_MODEL` | No | `claude-sonnet-4-20250514` | Claude model for AI extraction |
| `AI_EXTRACTION_ENABLED` | No | `true` | Enable/disable AI features |
| **Monitoring** ||||
| `SENTRY_DSN` | No | `""` | Sentry DSN for error tracking |
| **Email** ||||
| `SMTP_HOST` | No | `""` | SMTP server (e.g., `smtp.sendgrid.net`) |
| `SMTP_PORT` | No | `587` | SMTP port |
| `SMTP_USER` | No | `""` | SMTP username |
| `SMTP_PASSWORD` | No | `""` | SMTP password |
| `SMTP_FROM_EMAIL` | No | `noreply@climatrix.io` | Sender email |
| `SMTP_FROM_NAME` | No | `CLIMATRIX` | Sender display name |
| `SMTP_USE_TLS` | No | `true` | Use TLS for SMTP |
| **Frontend URL** ||||
| `FRONTEND_URL` | Yes (prod) | `http://localhost:3000` | Frontend URL (for email links) |
| **Password Reset** ||||
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | No | `30` | Reset token TTL |
| **File Storage** ||||
| `STORAGE_BACKEND` | No | `local` | `local` or `s3` |
| `S3_BUCKET_NAME` | If s3 | `""` | S3/R2 bucket name |
| `S3_REGION` | If s3 | `auto` | S3 region (`auto` for Cloudflare R2) |
| `S3_ENDPOINT_URL` | If s3 | `""` | S3 endpoint (R2: `https://<account>.r2.cloudflarestorage.com`) |
| `S3_ACCESS_KEY_ID` | If s3 | `""` | S3 access key |
| `S3_SECRET_ACCESS_KEY` | If s3 | `""` | S3 secret key |
| **Stripe Billing** ||||
| `STRIPE_SECRET_KEY` | If billing | `""` | Stripe secret key |
| `STRIPE_PUBLISHABLE_KEY` | If billing | `""` | Stripe publishable key |
| `STRIPE_WEBHOOK_SECRET` | If billing | `""` | Stripe webhook signing secret |
| `STRIPE_PRICE_ID_STARTER` | If billing | `""` | Stripe Price ID for Starter plan |
| `STRIPE_PRICE_ID_PROFESSIONAL` | If billing | `""` | Stripe Price ID for Professional plan |
| `STRIPE_PRICE_ID_ENTERPRISE` | If billing | `""` | Stripe Price ID for Enterprise plan |

#### Frontend (Vercel)

| Variable | Required | Description |
|----------|:--------:|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API base URL |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | No | Google OAuth Client ID |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | No | Stripe publishable key |
| `SENTRY_DSN` | No | Sentry DSN for frontend |

### 7.4 Database Initialization

After deploying the backend and database, initialize with these commands. Run them via Railway's CLI or by exec-ing into the service container.

```bash
# Step 1: Run Alembic migrations (create tables)
alembic upgrade head

# Step 2: Seed core reference data (emission factors, unit conversions, fuel prices)
python -m app.cli db seed

# Step 3: Seed Scope 3 reference data (airports, grid factors, etc.)
python -m app.cli db seed-scope3-reference

# Step 4: (Optional) Seed fuel prices if not included in Step 2
python -m app.cli db seed-fuel-prices
```

**Verification:**

```bash
# Check seed status
python -m app.cli db seed --check-only
# Expected output: "Database is already seeded."
```

### 7.5 Creating the First Super Admin

```bash
python -m app.cli db create-superuser \
  --email admin@yourdomain.com \
  --password "StrongPassword123!" \
  --name "Platform Admin" \
  --org-name "Your Organization"
```

This creates:
1. An organization (if none exists) named "Your Organization"
2. A super admin user with the specified credentials

You can now log in via the frontend and configure the platform.

### 7.6 Updating Emission Factors

When new factor data is published (e.g., DEFRA 2025):

1. **Update the seed data files** in `app/data/emission_factors.py` with the new values.
2. **Force re-seed:**
   ```bash
   python -m app.cli db seed --force
   ```
   This clears existing factors and inserts the updated set.
3. **Recalculate affected periods:**
   ```bash
   # Via API (requires super_admin token):
   POST /api/admin/recalculate/{period_id}
   ```
   Or recalculate all periods programmatically.

**Important:** Re-seeding with `--force` replaces ALL emission factors. Custom or organization-specific factors will be lost. Back up custom factors before re-seeding.

For Scope 3 reference data updates:
```bash
python -m app.cli db seed-scope3-reference --force
```

### 7.7 Storage Configuration

CLIMATRIX supports two storage backends for uploaded files:

#### Local Storage (Development)

```env
STORAGE_BACKEND=local
```

Files are stored in the `platform/backend/uploads/` directory. Not suitable for production (ephemeral container filesystem).

#### S3-Compatible Storage (Production)

Supports AWS S3 and Cloudflare R2.

**AWS S3:**
```env
STORAGE_BACKEND=s3
S3_BUCKET_NAME=climatrix-uploads
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=AKIA...
S3_SECRET_ACCESS_KEY=secret...
```

**Cloudflare R2:**
```env
STORAGE_BACKEND=s3
S3_BUCKET_NAME=climatrix-uploads
S3_REGION=auto
S3_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=your-r2-access-key
S3_SECRET_ACCESS_KEY=your-r2-secret-key
```

R2 is S3-compatible and uses the same boto3 client with a custom endpoint URL.

---

## 8. Troubleshooting

### 8.1 Common Errors and Solutions

#### "No emission factor found for activity_key='...'"

**Cause:** The `activity_key` in the activity does not match any approved factor in the database.

**Solution:**
1. Check the correct `activity_key` values via `GET /api/reference/activity-keys`.
2. Ensure the database has been seeded: `python -m app.cli db seed --check-only`.
3. Verify the factor has `status = 'approved'` and `is_active = true`.

#### "Unit conversion error: Cannot convert from X to Y"

**Cause:** The Pint library cannot find a valid conversion path between the input unit and the factor's expected unit.

**Solution:**
1. Check the unit alias mapping -- the input unit may need to be in a recognized format (e.g., "m3" not "cubic_metres").
2. Verify the factor's `activity_unit` matches what is expected.
3. For custom units, add them to the Pint registry in `normalizer.py`.

#### "Database needs seeding" (Exit code 1)

**Cause:** The `emission_factors` table is empty.

**Solution:**
```bash
python -m app.cli db seed
python -m app.cli db seed-scope3-reference
```

#### 500 Internal Server Error with no detail

**Cause:** Unhandled exception in the backend.

**Solution:**
1. Check Railway logs for the full traceback.
2. If Sentry is configured, check Sentry for the error event.
3. Enable `DEBUG=true` temporarily to access `/docs` for API testing.

### 8.2 CORS Issues

**Symptom:** Browser console shows "Access to fetch at ... has been blocked by CORS policy."

**Common causes and fixes:**

1. **Missing origin in CORS config:**
   ```env
   # Add your frontend domain
   CORS_ORIGINS_STR=https://app.climatrix.io,https://climatrix.io
   ```

2. **Vercel preview deploys blocked:**
   ```env
   # Ensure preview deploys are allowed
   CORS_ALLOW_VERCEL_PREVIEWS=true
   ```
   This adds a regex pattern `https://.*\.vercel\.app` to allowed origins.

3. **Credentials with wildcard origin:**
   When `CORS_ORIGINS_STR=*`, `allow_credentials` is set to `false` (browser requirement). For authenticated APIs in production, use explicit origins:
   ```env
   CORS_ORIGINS_STR=https://app.climatrix.io
   ```
   This enables `allow_credentials=true` for cookie/token-based auth.

4. **CORS on error responses:**
   The global exception handler ensures CORS headers are set even on 500 errors. If you see CORS errors only on failures, check that the exception handler is not being bypassed.

### 8.3 Database Connection Issues

#### "Connection refused" or "could not connect to server"

**Causes:**
1. Database not running or not accessible.
2. Incorrect `DATABASE_URL`.
3. Railway internal networking issue.

**Solutions:**
1. Verify `DATABASE_URL` is set correctly in Railway environment variables.
2. Ensure the PostgreSQL service is running in Railway dashboard.
3. Check that the URL uses `postgresql://` (Railway format) -- the app converts it to `postgresql+asyncpg://` automatically.
4. For local development, use `sqlite+aiosqlite:///./climatrix.db`.

#### "relation 'xxx' does not exist"

**Cause:** Alembic migrations have not been run.

**Solution:**
```bash
alembic upgrade head
```

#### "asyncpg" connection errors

**Cause:** The `DATABASE_URL` starts with `postgres://` instead of `postgresql://`.

**Solution:** The application handles both formats automatically via `settings.async_database_url`. Ensure you are using `settings.async_database_url` and not `settings.database_url` directly for async connections.

### 8.4 Import Failures

#### "Unknown activity_key 'xxx'"

**Cause:** The `activity_key` in the import file does not match any known factor.

**Solution:**
1. Download the template to see valid activity keys.
2. Use the "Did you mean: ..." suggestions in the error message.
3. Check for typos or extra whitespace in cell values.

#### "Missing required column: scope"

**Cause:** The import file is missing one of the required columns, or the column header does not match any known alias.

**Solution:**
1. Ensure these columns are present: `scope`, `category_code`, `activity_key`, `quantity`, `unit`.
2. Column names are case-insensitive and support aliases (e.g., "Amount" works for "quantity").
3. If using non-standard headers, enable AI column mapping.

#### "Invalid value for quantity"

**Cause:** Non-numeric value in the quantity column.

**Solution:**
1. Ensure quantity cells are numeric (no currency symbols, commas as thousands separators may cause issues).
2. Remove any text or special characters from quantity cells.

#### Large file import hangs or times out

**Cause:** File is being processed synchronously instead of asynchronously.

**Solution:**
1. Use the `/api/import/upload` endpoint for async processing via Arq.
2. Ensure Redis is configured and running.
3. Ensure an Arq worker is running alongside the web service.
4. Check the import job status via `GET /api/import/jobs/{job_id}`.

### 8.5 OAuth Configuration

#### Google OAuth "redirect_uri_mismatch"

**Cause:** The redirect URI configured in Google Cloud Console does not match the application's callback URL.

**Solution:**
1. In Google Cloud Console > APIs & Services > Credentials:
   - Add `https://your-frontend-domain.com` to Authorized JavaScript origins.
   - Add `https://your-frontend-domain.com/auth/callback` to Authorized redirect URIs.
2. For Vercel previews, also add `https://*.vercel.app` patterns.

#### "Invalid Google token"

**Cause:** `GOOGLE_CLIENT_ID` is not set or does not match the frontend configuration.

**Solution:**
1. Set `GOOGLE_CLIENT_ID` in backend environment to match the frontend's `NEXT_PUBLIC_GOOGLE_CLIENT_ID`.
2. Both must use the same Google OAuth Client ID.

### 8.6 Stripe Webhook Debugging

#### Webhook events not being received

**Causes:**
1. Webhook endpoint URL is incorrect in Stripe Dashboard.
2. `STRIPE_WEBHOOK_SECRET` is not set or incorrect.

**Solutions:**
1. In Stripe Dashboard > Developers > Webhooks:
   - Set endpoint URL to `https://your-backend.railway.app/api/billing/webhook`
   - Subscribe to events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`, `invoice.payment_failed`
2. Copy the webhook signing secret (`whsec_...`) to `STRIPE_WEBHOOK_SECRET`.

#### "Webhook signature verification failed"

**Cause:** `STRIPE_WEBHOOK_SECRET` does not match the webhook's signing secret.

**Solution:**
1. Each webhook endpoint in Stripe has its own signing secret.
2. Ensure you copy the correct `whsec_...` value from the specific webhook endpoint.
3. When using Stripe CLI for local testing, use the CLI-provided signing secret.

#### Testing webhooks locally

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Listen to webhook events and forward to local backend
stripe listen --forward-to localhost:8000/api/billing/webhook

# Note the webhook signing secret printed by the CLI
# Set it as STRIPE_WEBHOOK_SECRET in your .env file

# Trigger a test event
stripe trigger checkout.session.completed
```

### 8.7 Sentry Error Tracking

**Setup:**
1. Create a Sentry project for the backend (Python/FastAPI).
2. Create a Sentry project for the frontend (Next.js).
3. Set `SENTRY_DSN` in both backend and frontend environments.

**Backend Sentry configuration:**
- Environment: Set via `ENVIRONMENT` variable
- Release: Automatically set to `climatrix@{app_version}`
- Traces sample rate: 10% (configurable)
- Profiles sample rate: 10%
- PII: Disabled (`send_default_pii=False`)

**Frontend Sentry configuration:**
- Uses `@sentry/nextjs` package
- Configure in `sentry.client.config.ts` and `sentry.server.config.ts`

**Monitoring checklist:**
- Check Sentry for unhandled exceptions after deployment
- Set up Sentry alerts for error spikes
- Review performance transactions for slow endpoints
- Use Sentry's release tracking to correlate errors with deploys

---

## API Route Reference

For quick reference, here is the complete API route map:

| Prefix | Router | Tag | Description |
|--------|--------|-----|-------------|
| `/api/auth` | auth | Authentication | Login, register, token refresh, Google OAuth |
| `/api/periods` | periods | Reporting Periods | CRUD periods, verification workflow |
| `/api` | activities | Activities | CRUD activities, calculation |
| `/api` | reports | Reports | Summaries, CSV/PDF export, GHG inventory |
| `/api/reference` | reference | Reference Data | Activity keys, emission factors, units |
| `/api` | organization | Organization | Org settings, members, invitations |
| `/api` | import_data | Import | File upload, preview, process, templates |
| `/api/admin` | admin | Admin | Super admin: cross-tenant views |
| `/api/cbam` | cbam | CBAM | CBAM compliance module |
| `/api` | emission_factors | Emission Factors | Factor CRUD, governance workflow |
| `/api` | billing | Billing | Stripe subscription management |
| `/api` | audit | Audit | Audit log queries |
| `/api` | decarbonization | Decarbonization | Reduction targets and pathways |
| `/` | -- | Health | Root health check |
| `/health` | -- | Health | Detailed health check |

---

*This manual covers CLIMATRIX v3.1.0. For the latest updates, check the platform's changelog and API documentation at `/docs` (debug mode only).*
