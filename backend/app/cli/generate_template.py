"""
Generate Excel import template for CLIMATRIX bulk data upload.

This script creates a formatted Excel file with:
- Introduction sheet with instructions
- Organization info sheet
- Category-specific data entry sheets with dropdowns
- Reference sheet with valid values

Usage:
    python -m app.cli.generate_template
    python -m app.cli.generate_template --output /path/to/template.xlsx
"""

import typer
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.comments import Comment
from datetime import datetime

app = typer.Typer()

# =============================================================================
# REFERENCE DATA - Valid values for dropdowns
# =============================================================================

FUEL_TYPES_STATIONARY = [
    "Natural Gas",
    "Diesel",
    "Petrol",
    "LPG",
    "Coal",
    "Fuel Oil",
    "Kerosene",
    "Burning Oil",
]

UNITS_BY_FUEL = {
    "Natural Gas": ["m3", "kWh"],
    "Diesel": ["liters"],
    "Petrol": ["liters"],
    "LPG": ["liters", "kg"],
    "Coal": ["kg", "tonnes"],
    "Fuel Oil": ["liters"],
    "Kerosene": ["liters"],
    "Burning Oil": ["liters"],
}

VEHICLE_TYPES = [
    "Car",
    "Van",
    "LGV",
    "HGV",
    "Motorcycle",
    "Bus",
    "Taxi",
    "(Fuel Only)",
]

FUEL_TYPES_MOBILE = [
    "Petrol",
    "Diesel",
    "Hybrid",
    "Electric",
    "Plugin Hybrid",
]

MOBILE_UNITS = ["km", "liters"]

REFRIGERANT_TYPES = [
    "R-134a",
    "R-410A",
    "R-32",
    "R-404A",
    "R-407A",
    "R-407C",
    "R-407F",
    "R-417A",
    "R-422D",
    "R-507A",
    "R-508B",
    "HFC-23",
    "HFC-125",
    "HFC-143a",
    "HFC-152a",
    "HFC-227ea",
    "SF6",
    "NF3",
    "R-1234yf",
    "R-1234ze",
    "R-290 (Propane)",
    "R-600a (Isobutane)",
    "R-717 (Ammonia)",
    "R-744 (CO2)",
]

PROCESS_MATERIALS = [
    "Cement",
    "Clinker",
    "Quicklite (CaO)",
    "Dolomitic Lime",
    "Glass",
    "Iron & Steel (Integrated)",
    "Steel (EAF)",
    "Primary Aluminum",
    "Ammonia",
    "Nitric Acid",
    "Adipic Acid",
    "Hydrogen (SMR)",
    "Ethylene",
]

# Scope 2.1 - Electricity (separate from heat/cooling)
ELECTRICITY_TYPES = [
    "Grid Electricity (Location-based)",
    "Supplier Specific (Market-based)",
    "100% Renewable (Certified)",
]

# Scope 2.2 - Heat/Steam
HEAT_STEAM_TYPES = [
    "District Heating",
    "Steam",
]

# Scope 2.3 - Cooling
COOLING_TYPES = [
    "Chilled Water",
    "District Cooling",
]

# ALL countries from database (56 regions)
COUNTRIES = [
    "AE - UAE",
    "AR - Argentina",
    "AT - Austria",
    "AU - Australia",
    "BE - Belgium",
    "BR - Brazil",
    "CA - Canada",
    "CH - Switzerland",
    "CL - Chile",
    "CN - China",
    "CO - Colombia",
    "CZ - Czech Republic",
    "DE - Germany",
    "DK - Denmark",
    "EG - Egypt",
    "ES - Spain",
    "EU - European Union (Average)",
    "FI - Finland",
    "FR - France",
    "Global - World Average",
    "GR - Greece",
    "HK - Hong Kong",
    "HU - Hungary",
    "ID - Indonesia",
    "IE - Ireland",
    "IL - Israel",
    "IN - India",
    "IT - Italy",
    "JP - Japan",
    "KE - Kenya",
    "KR - South Korea",
    "MX - Mexico",
    "MY - Malaysia",
    "NG - Nigeria",
    "NL - Netherlands",
    "NO - Norway",
    "NZ - New Zealand",
    "PH - Philippines",
    "PL - Poland",
    "PT - Portugal",
    "RO - Romania",
    "RU - Russia",
    "SA - Saudi Arabia",
    "SE - Sweden",
    "SG - Singapore",
    "TH - Thailand",
    "TR - Turkey",
    "TW - Taiwan",
    "UK - United Kingdom",
    "US - United States (Average)",
    "US-CA - USA California",
    "US-MW - USA Midwest",
    "US-NY - USA New York",
    "US-TX - USA Texas (ERCOT)",
    "VN - Vietnam",
    "ZA - South Africa",
]

INDUSTRIES = [
    "Manufacturing",
    "Retail & Wholesale",
    "Financial Services",
    "Technology & Software",
    "Healthcare",
    "Construction",
    "Transportation & Logistics",
    "Food & Beverage",
    "Professional Services",
    "Real Estate",
    "Energy & Utilities",
    "Agriculture",
    "Education",
    "Hospitality",
    "Other",
]

EMPLOYEE_RANGES = [
    "1-10",
    "11-50",
    "51-100",
    "101-250",
    "251-500",
    "501-1000",
    "1001-5000",
    "5000+",
]

# Calculation methods
CALCULATION_METHODS = [
    "Physical",  # liters, kWh, km, kg, etc.
    "Spend",     # Currency amount - will be converted using fuel prices
]

# Currencies supported
CURRENCIES = [
    "USD",
    "EUR",
    "GBP",
    "ILS",
    "AUD",
    "CAD",
    "CHF",
    "CNY",
    "JPY",
    "Other",
]

# =============================================================================
# STYLES
# =============================================================================

HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
TITLE_FONT = Font(bold=True, size=16, color="1F4E79")
SUBTITLE_FONT = Font(bold=True, size=12, color="1F4E79")
INSTRUCTION_FONT = Font(size=11)
EXAMPLE_FILL = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
DROPDOWN_FILL = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
THIN_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)


def create_introduction_sheet(ws):
    """Create the introduction/instructions sheet."""
    ws.title = "Introduction"

    # Set column widths
    ws.column_dimensions['A'].width = 100

    # Title
    ws['A1'] = "CLIMATRIX - GHG Emissions Data Import Template"
    ws['A1'].font = Font(bold=True, size=20, color="1F4E79")
    ws.row_dimensions[1].height = 30

    # Version info
    ws['A3'] = f"Template Version: 1.0 | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ws['A3'].font = Font(italic=True, size=10, color="666666")

    # Welcome
    ws['A5'] = "Welcome to CLIMATRIX Data Import"
    ws['A5'].font = TITLE_FONT

    instructions = [
        "",
        "This template allows you to bulk import your emissions data into CLIMATRIX.",
        "Please follow the instructions below carefully to ensure successful data import.",
        "",
        "HOW TO USE THIS TEMPLATE",
        "=" * 50,
        "",
        "Step 1: Fill Organization Info (Optional but Recommended)",
        "   - Go to the 'Organization Info' sheet",
        "   - Enter your organization details",
        "   - This helps us configure your account correctly",
        "",
        "Step 2: Choose the Right Sheet for Your Data",
        "   SCOPE 1 - DIRECT EMISSIONS:",
        "   - 1.1 Stationary: Fuel burned in boilers, generators, heaters",
        "   - 1.2 Mobile: Company vehicles and fleet fuel",
        "   - 1.3 Fugitive: Refrigerant leaks and top-ups",
        "   - 1.4 Process: Industrial process emissions (cement, steel, chemicals)",
        "",
        "   SCOPE 2 - INDIRECT ENERGY EMISSIONS:",
        "   - 2.1 Electricity: Purchased grid electricity (56 countries supported)",
        "   - 2.2 Heat/Steam: District heating, industrial steam",
        "   - 2.3 Cooling: Chilled water, district cooling",
        "",
        "Step 3: Choose Calculation Method",
        "   - PHYSICAL: Enter actual consumption (liters, kWh, km, kg)",
        "   - SPEND: Enter cost amount (USD, EUR, GBP, etc.) - we convert using fuel prices",
        "",
        "Step 4: Enter Your Data",
        "   - YELLOW columns: Select from dropdown list",
        "   - WHITE columns: Paste or type your data",
        "   - GREEN rows: Example data (delete before uploading)",
        "",
        "Step 5: Review Your Data",
        "   - Check that all required columns are filled",
        "   - Ensure quantities are positive numbers",
        "   - Verify units/currencies match your calculation method",
        "",
        "Step 6: Save and Upload",
        "   - Save this file as .xlsx (Excel format)",
        "   - Upload to CLIMATRIX via Import page",
        "",
        "",
        "COLUMN COLOR GUIDE",
        "=" * 50,
        "",
        "   YELLOW background = Dropdown selection (click cell, select from list)",
        "   WHITE background = Free entry (paste or type your data)",
        "   GREEN row = Example data (for reference, delete before upload)",
        "",
        "",
        "TIPS FOR SUCCESS",
        "=" * 50,
        "",
        "   1. Use copy-paste for quantity and description columns",
        "   2. Select dropdown values AFTER pasting your quantities",
        "   3. Leave optional columns empty if you don't have the data",
        "   4. Date format: YYYY-MM-DD or YYYY-MM (e.g., 2024-01-15 or 2024-01)",
        "   5. Use decimal point (.) not comma (,) for numbers: 1234.56",
        "   6. Delete the green example row before uploading",
        "",
        "",
        "NEED HELP?",
        "=" * 50,
        "",
        "   - Check the 'Reference' sheet for all valid values",
        "   - Contact support@climatrix.com for assistance",
        "",
    ]

    row = 6
    for line in instructions:
        ws[f'A{row}'] = line
        if line.startswith("Step") or line.startswith("HOW") or line.startswith("COLUMN") or line.startswith("TIPS") or line.startswith("NEED"):
            ws[f'A{row}'].font = SUBTITLE_FONT
        elif line.startswith("   "):
            ws[f'A{row}'].font = INSTRUCTION_FONT
        row += 1


def create_org_info_sheet(ws):
    """Create the organization information sheet."""
    ws.title = "Organization Info"

    # Set column widths
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 40
    ws.column_dimensions['C'].width = 50

    # Title
    ws['A1'] = "Organization Information"
    ws['A1'].font = TITLE_FONT
    ws.merge_cells('A1:C1')

    ws['A2'] = "(Optional but recommended - helps configure your account)"
    ws['A2'].font = Font(italic=True, size=10, color="666666")
    ws.merge_cells('A2:C2')

    # Headers
    headers = [
        ("Field", "Value", "Notes"),
    ]

    fields = [
        ("Organization Name", "", "Your company or organization name"),
        ("Industry Sector", "", "Select from dropdown"),
        ("Primary Country", "", "Main country of operations"),
        ("Number of Sites", "", "How many facilities/locations"),
        ("Number of Employees", "", "Select range from dropdown"),
        ("Reporting Period Start", "", "e.g., 2024-01-01"),
        ("Reporting Period End", "", "e.g., 2024-12-31"),
        ("Contact Email", "", "For import notifications"),
    ]

    # Write headers
    for col, header in enumerate(headers[0], 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER

    # Write fields
    dropdown_fields = ["Industry Sector", "Primary Country", "Number of Employees"]
    for row_num, (field, value, notes) in enumerate(fields, 5):
        ws.cell(row=row_num, column=1, value=field).border = THIN_BORDER
        cell_b = ws.cell(row=row_num, column=2, value=value)
        cell_b.border = THIN_BORDER
        if field in dropdown_fields:
            cell_b.fill = DROPDOWN_FILL
        ws.cell(row=row_num, column=3, value=notes).font = Font(italic=True, color="666666")

    # Add dropdowns
    # Industry dropdown
    dv_industry = DataValidation(type="list", formula1='"' + ','.join(INDUSTRIES) + '"', allow_blank=True)
    dv_industry.error = "Please select from the list"
    dv_industry.errorTitle = "Invalid Industry"
    ws.add_data_validation(dv_industry)
    dv_industry.add(ws['B6'])

    # Country dropdown
    country_short = [c.split(' - ')[0] for c in COUNTRIES]
    dv_country = DataValidation(type="list", formula1='"' + ','.join(country_short) + '"', allow_blank=True)
    ws.add_data_validation(dv_country)
    dv_country.add(ws['B7'])

    # Employee range dropdown
    dv_emp = DataValidation(type="list", formula1='"' + ','.join(EMPLOYEE_RANGES) + '"', allow_blank=True)
    ws.add_data_validation(dv_emp)
    dv_emp.add(ws['B9'])


def create_scope_1_1_sheet(ws):
    """Create Scope 1.1 Stationary Combustion sheet."""
    ws.title = "1.1 Stationary"

    # Column widths
    ws.column_dimensions['A'].width = 18
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 35
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 10
    ws.column_dimensions['G'].width = 15

    # Title
    ws['A1'] = "Scope 1.1 - Stationary Combustion"
    ws['A1'].font = TITLE_FONT
    ws.merge_cells('A1:G1')

    ws['A2'] = "Fuel burned in boilers, furnaces, generators, heaters. Use Physical (liters, kWh) OR Spend (currency)."
    ws['A2'].font = Font(italic=True, size=10, color="666666")
    ws.merge_cells('A2:G2')

    # Headers
    headers = ["Fuel Type", "Method", "Description", "Quantity/Amount", "Unit/Currency", "Date", "Site (Optional)"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER
        cell.alignment = Alignment(horizontal='center')

    # Add column type indicators
    indicators = ["[Dropdown]", "[Dropdown]", "[Paste/Type]", "[Paste/Type]", "[Dropdown]", "[Paste/Type]", "[Paste/Type]"]
    for col, ind in enumerate(indicators, 1):
        cell = ws.cell(row=5, column=col, value=ind)
        cell.font = Font(italic=True, size=9, color="666666")
        cell.alignment = Alignment(horizontal='center')

    # Example rows (green) - Physical AND Spend examples
    examples = [
        ["Natural Gas", "Physical", "Office heating - Q1 2024", "15000", "kWh", "2024-01", "HQ Building"],
        ["Diesel", "Physical", "Backup generator", "500", "liters", "2024-02", "Factory"],
        ["Natural Gas", "Spend", "Monthly gas bill", "2500", "USD", "2024-03", "Warehouse"],
    ]
    for row_offset, example in enumerate(examples):
        for col, ex in enumerate(example, 1):
            cell = ws.cell(row=6+row_offset, column=col, value=ex)
            cell.fill = EXAMPLE_FILL
            cell.border = THIN_BORDER

    # Data entry rows with formatting
    for row in range(9, 109):  # 100 data rows
        for col in range(1, 8):
            cell = ws.cell(row=row, column=col)
            cell.border = THIN_BORDER
            if col in [1, 2, 5]:  # Dropdown columns
                cell.fill = DROPDOWN_FILL

    # Add dropdowns
    # Fuel type dropdown
    dv_fuel = DataValidation(type="list", formula1='"' + ','.join(FUEL_TYPES_STATIONARY) + '"', allow_blank=True)
    dv_fuel.error = "Please select a valid fuel type"
    dv_fuel.errorTitle = "Invalid Fuel Type"
    ws.add_data_validation(dv_fuel)
    dv_fuel.add('A6:A108')

    # Method dropdown (Physical vs Spend)
    dv_method = DataValidation(type="list", formula1='"' + ','.join(CALCULATION_METHODS) + '"', allow_blank=True)
    dv_method.error = "Select Physical or Spend"
    ws.add_data_validation(dv_method)
    dv_method.add('B6:B108')

    # Unit/Currency dropdown (combined)
    all_units = list(set(u for units in UNITS_BY_FUEL.values() for u in units)) + CURRENCIES
    dv_unit = DataValidation(type="list", formula1='"' + ','.join(all_units) + '"', allow_blank=True)
    dv_unit.error = "Please select a valid unit or currency"
    ws.add_data_validation(dv_unit)
    dv_unit.add('E6:E108')


def create_scope_1_2_sheet(ws):
    """Create Scope 1.2 Mobile Combustion sheet."""
    ws.title = "1.2 Mobile"

    # Column widths
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 35
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 12
    ws.column_dimensions['G'].width = 12

    # Title
    ws['A1'] = "Scope 1.2 - Mobile Combustion"
    ws['A1'].font = TITLE_FONT
    ws.merge_cells('A1:G1')

    ws['A2'] = "Company vehicles. Use Physical (km/liters) OR Spend (fuel cost). Select '(Fuel Only)' for fuel purchases without vehicle info."
    ws['A2'].font = Font(italic=True, size=10, color="666666")
    ws.merge_cells('A2:G2')

    # Headers
    headers = ["Vehicle Type", "Fuel Type", "Method", "Description", "Quantity/Amount", "Unit/Currency", "Date"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER
        cell.alignment = Alignment(horizontal='center')

    # Add column type indicators
    indicators = ["[Dropdown]", "[Dropdown]", "[Dropdown]", "[Paste/Type]", "[Paste/Type]", "[Dropdown]", "[Paste/Type]"]
    for col, ind in enumerate(indicators, 1):
        cell = ws.cell(row=5, column=col, value=ind)
        cell.font = Font(italic=True, size=9, color="666666")
        cell.alignment = Alignment(horizontal='center')

    # Example rows (green) - Physical AND Spend
    examples = [
        ["Car", "Diesel", "Physical", "Sales team vehicle ABC-123", "25000", "km", "2024-01"],
        ["HGV", "Diesel", "Physical", "Delivery truck fleet", "85000", "km", "2024-01"],
        ["(Fuel Only)", "Diesel", "Physical", "Fleet fuel purchase", "5500", "liters", "2024-01"],
        ["(Fuel Only)", "Petrol", "Spend", "Monthly fuel cards", "8500", "USD", "2024-02"],
    ]
    for row_offset, example in enumerate(examples):
        for col, val in enumerate(example, 1):
            cell = ws.cell(row=6+row_offset, column=col, value=val)
            cell.fill = EXAMPLE_FILL
            cell.border = THIN_BORDER

    # Data entry rows
    for row in range(10, 110):
        for col in range(1, 8):
            cell = ws.cell(row=row, column=col)
            cell.border = THIN_BORDER
            if col in [1, 2, 3, 6]:  # Dropdown columns
                cell.fill = DROPDOWN_FILL

    # Add dropdowns
    dv_vehicle = DataValidation(type="list", formula1='"' + ','.join(VEHICLE_TYPES) + '"', allow_blank=True)
    ws.add_data_validation(dv_vehicle)
    dv_vehicle.add('A6:A109')

    dv_fuel = DataValidation(type="list", formula1='"' + ','.join(FUEL_TYPES_MOBILE) + '"', allow_blank=True)
    ws.add_data_validation(dv_fuel)
    dv_fuel.add('B6:B109')

    dv_method = DataValidation(type="list", formula1='"' + ','.join(CALCULATION_METHODS) + '"', allow_blank=True)
    ws.add_data_validation(dv_method)
    dv_method.add('C6:C109')

    # Unit/Currency dropdown
    mobile_units_currency = MOBILE_UNITS + CURRENCIES
    dv_unit = DataValidation(type="list", formula1='"' + ','.join(mobile_units_currency) + '"', allow_blank=True)
    ws.add_data_validation(dv_unit)
    dv_unit.add('F6:F109')


def create_scope_1_3_sheet(ws):
    """Create Scope 1.3 Fugitive Emissions sheet."""
    ws.title = "1.3 Fugitive"

    # Column widths
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 40
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 12

    # Title
    ws['A1'] = "Scope 1.3 - Fugitive Emissions"
    ws['A1'].font = TITLE_FONT
    ws.merge_cells('A1:F1')

    ws['A2'] = "Refrigerant leaks, top-ups, equipment disposal. Use Physical (kg) OR Spend (purchase cost)."
    ws['A2'].font = Font(italic=True, size=10, color="666666")
    ws.merge_cells('A2:F2')

    # Headers
    headers = ["Refrigerant Type", "Method", "Description", "Quantity/Amount", "Unit/Currency", "Date"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER
        cell.alignment = Alignment(horizontal='center')

    # Indicators
    indicators = ["[Dropdown]", "[Dropdown]", "[Paste/Type]", "[Paste/Type]", "[Dropdown]", "[Paste/Type]"]
    for col, ind in enumerate(indicators, 1):
        cell = ws.cell(row=5, column=col, value=ind)
        cell.font = Font(italic=True, size=9, color="666666")
        cell.alignment = Alignment(horizontal='center')

    # Example rows - Physical AND Spend
    examples = [
        ["R-410A", "Physical", "AC system refill - Building A", "3.5", "kg", "2024-03"],
        ["R-134a", "Spend", "Refrigerant purchase invoice", "450", "USD", "2024-04"],
    ]
    for row_offset, example in enumerate(examples):
        for col, ex in enumerate(example, 1):
            cell = ws.cell(row=6+row_offset, column=col, value=ex)
            cell.fill = EXAMPLE_FILL
            cell.border = THIN_BORDER

    # Data entry rows
    for row in range(8, 58):  # 50 rows
        for col in range(1, 7):
            cell = ws.cell(row=row, column=col)
            cell.border = THIN_BORDER
            if col in [1, 2, 5]:
                cell.fill = DROPDOWN_FILL

    # Dropdowns
    dv_ref = DataValidation(type="list", formula1='"' + ','.join(REFRIGERANT_TYPES) + '"', allow_blank=True)
    ws.add_data_validation(dv_ref)
    dv_ref.add('A6:A57')

    dv_method = DataValidation(type="list", formula1='"' + ','.join(CALCULATION_METHODS) + '"', allow_blank=True)
    ws.add_data_validation(dv_method)
    dv_method.add('B6:B57')

    dv_unit = DataValidation(type="list", formula1='"kg,' + ','.join(CURRENCIES) + '"', allow_blank=True)
    ws.add_data_validation(dv_unit)
    dv_unit.add('E6:E57')


def create_scope_1_4_sheet(ws):
    """Create Scope 1.4 Process Emissions sheet."""
    ws.title = "1.4 Process"

    # Column widths
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 40
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 12

    # Title
    ws['A1'] = "Scope 1.4 - Process Emissions"
    ws['A1'].font = TITLE_FONT
    ws.merge_cells('A1:F1')

    ws['A2'] = "Industrial process emissions. Use Physical (tonnes produced) OR Spend (material purchase cost)."
    ws['A2'].font = Font(italic=True, size=10, color="666666")
    ws.merge_cells('A2:F2')

    # Headers
    headers = ["Material Type", "Method", "Description", "Quantity/Amount", "Unit/Currency", "Date"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER
        cell.alignment = Alignment(horizontal='center')

    # Indicators
    indicators = ["[Dropdown]", "[Dropdown]", "[Paste/Type]", "[Paste/Type]", "[Dropdown]", "[Paste/Type]"]
    for col, ind in enumerate(indicators, 1):
        cell = ws.cell(row=5, column=col, value=ind)
        cell.font = Font(italic=True, size=9, color="666666")
        cell.alignment = Alignment(horizontal='center')

    # Examples - Physical AND Spend
    examples = [
        ["Cement", "Physical", "Portland cement production - Plant A", "25000", "tonnes", "2024-Q1"],
        ["Iron & Steel (Integrated)", "Spend", "Steel raw material purchase", "1500000", "USD", "2024-Q1"],
    ]
    for row_offset, example in enumerate(examples):
        for col, ex in enumerate(example, 1):
            cell = ws.cell(row=6+row_offset, column=col, value=ex)
            cell.fill = EXAMPLE_FILL
            cell.border = THIN_BORDER

    # Data rows
    for row in range(8, 38):  # 30 rows
        for col in range(1, 7):
            cell = ws.cell(row=row, column=col)
            cell.border = THIN_BORDER
            if col in [1, 2, 5]:
                cell.fill = DROPDOWN_FILL

    # Dropdowns
    dv_mat = DataValidation(type="list", formula1='"' + ','.join(PROCESS_MATERIALS) + '"', allow_blank=True)
    ws.add_data_validation(dv_mat)
    dv_mat.add('A6:A37')

    dv_method = DataValidation(type="list", formula1='"' + ','.join(CALCULATION_METHODS) + '"', allow_blank=True)
    ws.add_data_validation(dv_method)
    dv_method.add('B6:B37')

    dv_unit = DataValidation(type="list", formula1='"tonnes,' + ','.join(CURRENCIES) + '"', allow_blank=True)
    ws.add_data_validation(dv_unit)
    dv_unit.add('E6:E37')


def create_scope_2_1_sheet(ws):
    """Create Scope 2.1 Purchased Electricity sheet."""
    ws.title = "2.1 Electricity"

    # Column widths
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 35
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 12
    ws.column_dimensions['G'].width = 12

    # Title
    ws['A1'] = "Scope 2.1 - Purchased Electricity"
    ws['A1'].font = TITLE_FONT
    ws.merge_cells('A1:G1')

    ws['A2'] = "Grid electricity. Use Physical (kWh) OR Spend (electricity bill amount). Select country for correct grid factor."
    ws['A2'].font = Font(italic=True, size=10, color="666666")
    ws.merge_cells('A2:G2')

    # Headers
    headers = ["Electricity Type", "Method", "Country/Region", "Description", "Quantity/Amount", "Unit/Currency", "Date"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER
        cell.alignment = Alignment(horizontal='center')

    # Indicators
    indicators = ["[Dropdown]", "[Dropdown]", "[Dropdown: 56]", "[Paste/Type]", "[Paste/Type]", "[Dropdown]", "[Paste/Type]"]
    for col, ind in enumerate(indicators, 1):
        cell = ws.cell(row=5, column=col, value=ind)
        cell.font = Font(italic=True, size=9, color="666666")
        cell.alignment = Alignment(horizontal='center')

    # Examples - Physical AND Spend
    examples = [
        ["Grid Electricity (Location-based)", "Physical", "IL", "Main office - Tel Aviv", "45000", "kWh", "2024-01"],
        ["Grid Electricity (Location-based)", "Physical", "US", "US subsidiary", "28000", "kWh", "2024-01"],
        ["Grid Electricity (Location-based)", "Spend", "DE", "Germany office - bill", "3500", "EUR", "2024-02"],
        ["Supplier Specific (Market-based)", "Physical", "UK", "UK - green tariff", "22000", "kWh", "2024-01"],
        ["100% Renewable (Certified)", "Physical", "Global", "Data center - RECs", "180000", "kWh", "2024-Q1"],
    ]
    for row_offset, example in enumerate(examples):
        for col, val in enumerate(example, 1):
            cell = ws.cell(row=6+row_offset, column=col, value=val)
            cell.fill = EXAMPLE_FILL
            cell.border = THIN_BORDER

    # Data rows
    for row in range(11, 111):  # 100 rows
        for col in range(1, 8):
            cell = ws.cell(row=row, column=col)
            cell.border = THIN_BORDER
            if col in [1, 2, 3, 6]:
                cell.fill = DROPDOWN_FILL

    # Dropdowns
    dv_type = DataValidation(type="list", formula1='"' + ','.join(ELECTRICITY_TYPES) + '"', allow_blank=True)
    ws.add_data_validation(dv_type)
    dv_type.add('A6:A110')

    dv_method = DataValidation(type="list", formula1='"' + ','.join(CALCULATION_METHODS) + '"', allow_blank=True)
    ws.add_data_validation(dv_method)
    dv_method.add('B6:B110')

    country_codes = [c.split(' - ')[0] for c in COUNTRIES]
    dv_country = DataValidation(type="list", formula1='"' + ','.join(country_codes) + '"', allow_blank=True)
    ws.add_data_validation(dv_country)
    dv_country.add('C6:C110')

    dv_unit = DataValidation(type="list", formula1='"kWh,' + ','.join(CURRENCIES) + '"', allow_blank=True)
    ws.add_data_validation(dv_unit)
    dv_unit.add('F6:F110')


def create_scope_2_2_sheet(ws):
    """Create Scope 2.2 Purchased Heat/Steam sheet."""
    ws.title = "2.2 Heat-Steam"

    # Column widths
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 35
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 12

    # Title
    ws['A1'] = "Scope 2.2 - Purchased Heat & Steam"
    ws['A1'].font = TITLE_FONT
    ws.merge_cells('A1:F1')

    ws['A2'] = "District heating and industrial steam. Use Physical (kWh) OR Spend (bill amount)."
    ws['A2'].font = Font(italic=True, size=10, color="666666")
    ws.merge_cells('A2:F2')

    # Headers
    headers = ["Energy Type", "Method", "Description", "Quantity/Amount", "Unit/Currency", "Date"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER
        cell.alignment = Alignment(horizontal='center')

    # Indicators
    indicators = ["[Dropdown]", "[Dropdown]", "[Paste/Type]", "[Paste/Type]", "[Dropdown]", "[Paste/Type]"]
    for col, ind in enumerate(indicators, 1):
        cell = ws.cell(row=5, column=col, value=ind)
        cell.font = Font(italic=True, size=9, color="666666")
        cell.alignment = Alignment(horizontal='center')

    # Examples - Physical AND Spend
    examples = [
        ["District Heating", "Physical", "Office heating - Winter 2024", "35000", "kWh", "2024-Q1"],
        ["Steam", "Physical", "Manufacturing process steam", "18000", "kWh", "2024-01"],
        ["District Heating", "Spend", "Monthly heating bill", "1200", "EUR", "2024-02"],
    ]
    for row_offset, example in enumerate(examples):
        for col, val in enumerate(example, 1):
            cell = ws.cell(row=6+row_offset, column=col, value=val)
            cell.fill = EXAMPLE_FILL
            cell.border = THIN_BORDER

    # Data rows
    for row in range(9, 59):  # 50 rows
        for col in range(1, 7):
            cell = ws.cell(row=row, column=col)
            cell.border = THIN_BORDER
            if col in [1, 2, 5]:
                cell.fill = DROPDOWN_FILL

    # Dropdowns
    dv_energy = DataValidation(type="list", formula1='"' + ','.join(HEAT_STEAM_TYPES) + '"', allow_blank=True)
    ws.add_data_validation(dv_energy)
    dv_energy.add('A6:A58')

    dv_method = DataValidation(type="list", formula1='"' + ','.join(CALCULATION_METHODS) + '"', allow_blank=True)
    ws.add_data_validation(dv_method)
    dv_method.add('B6:B58')

    dv_unit = DataValidation(type="list", formula1='"kWh,' + ','.join(CURRENCIES) + '"', allow_blank=True)
    ws.add_data_validation(dv_unit)
    dv_unit.add('E6:E58')


def create_scope_2_3_sheet(ws):
    """Create Scope 2.3 Purchased Cooling sheet."""
    ws.title = "2.3 Cooling"

    # Column widths
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 35
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 12

    # Title
    ws['A1'] = "Scope 2.3 - Purchased Cooling"
    ws['A1'].font = TITLE_FONT
    ws.merge_cells('A1:F1')

    ws['A2'] = "Chilled water and district cooling. Use Physical (kWh) OR Spend (bill amount)."
    ws['A2'].font = Font(italic=True, size=10, color="666666")
    ws.merge_cells('A2:F2')

    # Headers
    headers = ["Cooling Type", "Method", "Description", "Quantity/Amount", "Unit/Currency", "Date"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER
        cell.alignment = Alignment(horizontal='center')

    # Indicators
    indicators = ["[Dropdown]", "[Dropdown]", "[Paste/Type]", "[Paste/Type]", "[Dropdown]", "[Paste/Type]"]
    for col, ind in enumerate(indicators, 1):
        cell = ws.cell(row=5, column=col, value=ind)
        cell.font = Font(italic=True, size=9, color="666666")
        cell.alignment = Alignment(horizontal='center')

    # Examples - Physical AND Spend
    examples = [
        ["Chilled Water", "Physical", "Data center cooling", "42000", "kWh", "2024-02"],
        ["District Cooling", "Physical", "Office cooling - Summer", "28000", "kWh", "2024-Q3"],
        ["District Cooling", "Spend", "Monthly cooling bill", "850", "USD", "2024-07"],
    ]
    for row_offset, example in enumerate(examples):
        for col, val in enumerate(example, 1):
            cell = ws.cell(row=6+row_offset, column=col, value=val)
            cell.fill = EXAMPLE_FILL
            cell.border = THIN_BORDER

    # Data rows
    for row in range(9, 59):  # 50 rows
        for col in range(1, 7):
            cell = ws.cell(row=row, column=col)
            cell.border = THIN_BORDER
            if col in [1, 2, 5]:
                cell.fill = DROPDOWN_FILL

    # Dropdowns
    dv_cooling = DataValidation(type="list", formula1='"' + ','.join(COOLING_TYPES) + '"', allow_blank=True)
    ws.add_data_validation(dv_cooling)
    dv_cooling.add('A6:A58')

    dv_method = DataValidation(type="list", formula1='"' + ','.join(CALCULATION_METHODS) + '"', allow_blank=True)
    ws.add_data_validation(dv_method)
    dv_method.add('B6:B58')

    dv_unit = DataValidation(type="list", formula1='"kWh,' + ','.join(CURRENCIES) + '"', allow_blank=True)
    ws.add_data_validation(dv_unit)
    dv_unit.add('E6:E58')


def create_reference_sheet(ws):
    """Create reference sheet with all valid values."""
    ws.title = "Reference"

    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 30
    ws.column_dimensions['D'].width = 30
    ws.column_dimensions['E'].width = 25

    # Title
    ws['A1'] = "Reference - Valid Values for All Fields"
    ws['A1'].font = TITLE_FONT
    ws.merge_cells('A1:E1')

    ws['A2'] = "This sheet shows all valid values accepted by the system. Use these exact values in your data."
    ws['A2'].font = Font(italic=True, size=10, color="666666")
    ws.merge_cells('A2:E2')

    # Headers - 10 columns now
    ws.column_dimensions['F'].width = 30
    ws.column_dimensions['G'].width = 25
    ws.column_dimensions['H'].width = 20
    ws.column_dimensions['I'].width = 15
    ws.column_dimensions['J'].width = 15

    headers = [
        "Fuels (1.1)",
        "Vehicles (1.2)",
        "Refrigerants (1.3)",
        "Materials (1.4)",
        "Countries (2.1)",
        "Electricity Types (2.1)",
        "Heat/Steam (2.2)",
        "Cooling (2.3)",
        "Calc Method",
        "Currencies"
    ]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER

    # Values - all lists
    lists = [
        FUEL_TYPES_STATIONARY,
        VEHICLE_TYPES + FUEL_TYPES_MOBILE,
        REFRIGERANT_TYPES,
        PROCESS_MATERIALS,
        COUNTRIES,
        ELECTRICITY_TYPES,
        HEAT_STEAM_TYPES,
        COOLING_TYPES,
        CALCULATION_METHODS,
        CURRENCIES
    ]

    max_len = max(len(lst) for lst in lists)

    for row in range(5, 5 + max_len):
        for col, lst in enumerate(lists, 1):
            idx = row - 5
            if idx < len(lst):
                ws.cell(row=row, column=col, value=lst[idx]).border = THIN_BORDER


@app.command()
def generate(
    output: str = typer.Option(
        "climatrix_import_template.xlsx",
        "--output", "-o",
        help="Output file path"
    )
):
    """Generate the CLIMATRIX data import Excel template."""

    typer.echo("Generating CLIMATRIX import template...")

    wb = Workbook()

    # Remove default sheet
    wb.remove(wb.active)

    # Create all sheets
    create_introduction_sheet(wb.create_sheet())
    typer.echo("  + Introduction sheet")

    create_org_info_sheet(wb.create_sheet())
    typer.echo("  + Organization Info sheet")

    create_scope_1_1_sheet(wb.create_sheet())
    typer.echo("  + Scope 1.1 Stationary sheet")

    create_scope_1_2_sheet(wb.create_sheet())
    typer.echo("  + Scope 1.2 Mobile sheet")

    create_scope_1_3_sheet(wb.create_sheet())
    typer.echo("  + Scope 1.3 Fugitive sheet")

    create_scope_1_4_sheet(wb.create_sheet())
    typer.echo("  + Scope 1.4 Process sheet")

    create_scope_2_1_sheet(wb.create_sheet())
    typer.echo("  + Scope 2.1 Electricity sheet")

    create_scope_2_2_sheet(wb.create_sheet())
    typer.echo("  + Scope 2.2 Heat/Steam sheet")

    create_scope_2_3_sheet(wb.create_sheet())
    typer.echo("  + Scope 2.3 Cooling sheet")

    create_reference_sheet(wb.create_sheet())
    typer.echo("  + Reference sheet")

    # Save
    output_path = Path(output)
    wb.save(output_path)

    typer.echo(f"\n Template saved to: {output_path.absolute()}")
    typer.echo(f" File size: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    app()
