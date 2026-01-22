# CLIMATRIX API Documentation

Base URL: `https://api.climatrix.io` (production) or `http://localhost:8000` (development)

## Authentication

All API endpoints (except `/health` and `/auth/*`) require a Bearer token.

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "admin"
  },
  "organization": {
    "id": "uuid",
    "name": "Acme Corp"
  }
}
```

### Using Token
```http
Authorization: Bearer <access_token>
```

## Core Endpoints

### Health Check
```http
GET /health
```

### Organizations
```http
GET /api/organizations/current
PUT /api/organizations/current
```

### Sites
```http
GET /api/sites
POST /api/sites
GET /api/sites/{id}
PUT /api/sites/{id}
DELETE /api/sites/{id}
```

### Reporting Periods
```http
GET /api/reporting-periods
POST /api/reporting-periods
GET /api/reporting-periods/{id}
PUT /api/reporting-periods/{id}
DELETE /api/reporting-periods/{id}
```

### Activities
```http
GET /api/activities
POST /api/activities
GET /api/activities/{id}
PUT /api/activities/{id}
DELETE /api/activities/{id}
```

Query Parameters:
- `scope`: Filter by scope (1, 2, 3)
- `period_id`: Filter by reporting period
- `site_id`: Filter by site
- `category`: Filter by category

### Emissions
```http
GET /api/emissions
GET /api/emissions/summary
GET /api/emissions/by-scope
GET /api/emissions/by-category
```

### Import
```http
POST /api/import/upload
POST /api/import/preview
POST /api/import/confirm
GET /api/import/batches
GET /api/import/batches/{id}
GET /api/import/template
```

### Reports
```http
GET /api/reports/ghg-inventory
GET /api/reports/summary
POST /api/reports/export
```

## Data Models

### Activity
```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "site_id": "uuid",
  "period_id": "uuid",
  "scope": 1,
  "category": "1.1",
  "subcategory": "Stationary Combustion",
  "activity_key": "stationary_combustion_natural_gas",
  "description": "Office heating",
  "consumption": 1000,
  "unit": "m3",
  "emission_factor_id": "uuid",
  "co2e_kg": 2100.5,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Emission Factor
```json
{
  "id": "uuid",
  "activity_key": "stationary_combustion_natural_gas",
  "factor_type": "combustion",
  "co2_factor": 1.89,
  "ch4_factor": 0.034,
  "n2o_factor": 0.0001,
  "unit": "kg CO2e/m3",
  "source": "DEFRA 2024",
  "year": 2024
}
```

## Error Responses

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE"
}
```

Common HTTP Status Codes:
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Rate Limiting

- 100 requests per minute per user
- 1000 requests per hour per organization

## Interactive Documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`
