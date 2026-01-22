"""
File Analyzer Service

Analyzes uploaded files to detect:
- File type (CSV, Excel single-sheet, Excel multi-sheet)
- Header row position (may not be row 1)
- Data start row
- Sheet structure for Excel files
- Column data types and patterns
"""

import pandas as pd
import io
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class FileType(str, Enum):
    CSV = "csv"
    EXCEL_SINGLE = "excel_single"
    EXCEL_MULTI = "excel_multi"
    UNKNOWN = "unknown"


@dataclass
class SheetAnalysis:
    """Analysis result for a single sheet"""
    sheet_name: str
    header_row: int  # 0-indexed
    data_start_row: int  # 0-indexed
    data_end_row: int
    total_rows: int
    columns: List[str]
    column_types: Dict[str, str]
    sample_data: List[Dict[str, Any]]
    is_empty: bool = False
    is_metadata_only: bool = False  # Sheets like "Intro", "Totals"
    detected_scope: Optional[int] = None
    detected_category: Optional[str] = None


@dataclass
class FileAnalysis:
    """Complete file analysis result"""
    file_type: FileType
    file_name: str
    sheets: List[SheetAnalysis]
    total_sheets: int
    data_sheets: int  # Sheets with actual data
    estimated_total_rows: int
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class FileAnalyzer:
    """
    Intelligent file analyzer that detects structure of any uploaded file.
    Handles complex Excel templates with headers not in row 1.
    """

    # Keywords that indicate a header row
    HEADER_KEYWORDS = [
        'date', 'month', 'year', 'period', 'description', 'quantity', 'amount',
        'unit', 'type', 'category', 'scope', 'site', 'location', 'country',
        'fuel', 'electricity', 'gas', 'diesel', 'consumption', 'emission',
        'co2', 'kg', 'kwh', 'liters', 'tonnes', 'km', 'flights', 'waste',
        # Hebrew keywords
        'תאריך', 'חודש', 'שנה', 'תיאור', 'כמות', 'יחידה', 'סוג', 'קטגוריה',
        'אתר', 'מיקום', 'מדינה', 'דלק', 'חשמל', 'גז', 'סולר', 'צריכה',
    ]

    # Sheet names that typically don't contain data
    METADATA_SHEET_NAMES = [
        'intro', 'introduction', 'instructions', 'help', 'readme',
        'totals', 'summary', 'overview', 'contents', 'index',
        'template', 'example', 'sample', 'notes', 'definitions',
    ]

    # Patterns to detect scope from sheet names
    SCOPE_PATTERNS = {
        1: ['scope 1', 'scope1', '1-', '1 -', 'mobile', 'combustion', 'fugitive', 'refrigerant'],
        2: ['scope 2', 'scope2', '2-', '2 -', 'electricity', 'heat', 'steam', 'cooling'],
        3: ['scope 3', 'scope3', '3-', '3 -', 'cat.', 'cat ', 'category', 'upstream', 'downstream',
            'waste', 'travel', 'commut', 'freight', 'transport', 'purchased', 'capital'],
    }

    # Category patterns
    CATEGORY_PATTERNS = {
        '1.1': ['stationary', 'combustion', 'fuel', 'boiler', 'heating'],
        '1.2': ['mobile', 'vehicle', 'fleet', 'car', 'truck', 'van'],
        '1.3': ['fugitive', 'refrigerant', 'leak', 'r-', 'r134', 'r410', 'ac', 'hvac'],
        '2': ['electricity', 'power', 'grid', 'kwh'],
        '3.1': ['purchased good', 'goods & service', 'procurement', 'supplier'],
        '3.2': ['capital good', 'capital equipment', 'asset'],
        '3.3': ['fuel and energy', 'wtt', 'well-to-tank', 't&d'],
        '3.4': ['upstream transport', 'upstream dist', 'inbound'],
        '3.5': ['waste', 'disposal', 'landfill', 'recycl'],
        '3.6': ['business travel', 'flight', 'hotel', 'air travel'],
        '3.7': ['commut', 'employee travel', 'staff travel', 'telework'],
        '3.9': ['downstream transport', 'downstream dist', 'outbound', 'delivery'],
        '3.12': ['end of life', 'end-of-life', 'eol', 'product disposal'],
    }

    def analyze(self, file_content: bytes, filename: str) -> FileAnalysis:
        """
        Analyze a file and return its structure.

        Args:
            file_content: Raw file bytes
            filename: Original filename (used to detect type)

        Returns:
            FileAnalysis with complete structure information
        """
        file_type = self._detect_file_type(filename)

        if file_type == FileType.CSV:
            return self._analyze_csv(file_content, filename)
        elif file_type in [FileType.EXCEL_SINGLE, FileType.EXCEL_MULTI]:
            return self._analyze_excel(file_content, filename)
        else:
            return FileAnalysis(
                file_type=FileType.UNKNOWN,
                file_name=filename,
                sheets=[],
                total_sheets=0,
                data_sheets=0,
                estimated_total_rows=0,
                errors=[f"Unknown file type: {filename}"]
            )

    def _detect_file_type(self, filename: str) -> FileType:
        """Detect file type from filename extension"""
        lower_name = filename.lower()
        if lower_name.endswith('.csv'):
            return FileType.CSV
        elif lower_name.endswith(('.xlsx', '.xls', '.xlsm')):
            return FileType.EXCEL_MULTI  # Will be refined after reading
        return FileType.UNKNOWN

    def _analyze_csv(self, file_content: bytes, filename: str) -> FileAnalysis:
        """Analyze a CSV file"""
        try:
            # Try different encodings
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    content = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                content = file_content.decode('utf-8', errors='replace')

            # Read CSV with pandas
            df = pd.read_csv(io.StringIO(content), header=None, nrows=100)

            # Detect header row
            header_row = self._find_header_row(df)

            # Re-read with correct header
            df_full = pd.read_csv(io.StringIO(content), header=header_row)

            sheet_analysis = SheetAnalysis(
                sheet_name="Sheet1",
                header_row=header_row,
                data_start_row=header_row + 1,
                data_end_row=len(df_full) + header_row,
                total_rows=len(df_full),
                columns=list(df_full.columns),
                column_types=self._detect_column_types(df_full),
                sample_data=df_full.head(5).to_dict('records'),
                is_empty=len(df_full) == 0,
            )

            return FileAnalysis(
                file_type=FileType.CSV,
                file_name=filename,
                sheets=[sheet_analysis],
                total_sheets=1,
                data_sheets=1 if not sheet_analysis.is_empty else 0,
                estimated_total_rows=len(df_full),
            )

        except Exception as e:
            return FileAnalysis(
                file_type=FileType.CSV,
                file_name=filename,
                sheets=[],
                total_sheets=0,
                data_sheets=0,
                estimated_total_rows=0,
                errors=[f"Failed to parse CSV: {str(e)}"]
            )

    def _analyze_excel(self, file_content: bytes, filename: str) -> FileAnalysis:
        """Analyze an Excel file with multiple sheets"""
        try:
            xl = pd.ExcelFile(io.BytesIO(file_content))
            sheet_names = xl.sheet_names

            sheets = []
            total_data_rows = 0
            warnings = []

            for sheet_name in sheet_names:
                try:
                    sheet_analysis = self._analyze_sheet(xl, sheet_name)
                    sheets.append(sheet_analysis)

                    if not sheet_analysis.is_empty and not sheet_analysis.is_metadata_only:
                        total_data_rows += sheet_analysis.total_rows
                except Exception as e:
                    warnings.append(f"Failed to analyze sheet '{sheet_name}': {str(e)}")

            # Determine if single or multi sheet
            data_sheets = [s for s in sheets if not s.is_empty and not s.is_metadata_only]
            file_type = FileType.EXCEL_SINGLE if len(data_sheets) <= 1 else FileType.EXCEL_MULTI

            return FileAnalysis(
                file_type=file_type,
                file_name=filename,
                sheets=sheets,
                total_sheets=len(sheet_names),
                data_sheets=len(data_sheets),
                estimated_total_rows=total_data_rows,
                warnings=warnings,
            )

        except Exception as e:
            return FileAnalysis(
                file_type=FileType.EXCEL_MULTI,
                file_name=filename,
                sheets=[],
                total_sheets=0,
                data_sheets=0,
                estimated_total_rows=0,
                errors=[f"Failed to parse Excel: {str(e)}"]
            )

    def _analyze_sheet(self, xl: pd.ExcelFile, sheet_name: str) -> SheetAnalysis:
        """Analyze a single Excel sheet"""
        # Read without header first to detect structure
        df_raw = pd.read_excel(xl, sheet_name=sheet_name, header=None, nrows=50)

        # Check if metadata sheet
        is_metadata = self._is_metadata_sheet(sheet_name, df_raw)

        if df_raw.empty or is_metadata:
            return SheetAnalysis(
                sheet_name=sheet_name,
                header_row=0,
                data_start_row=0,
                data_end_row=0,
                total_rows=0,
                columns=[],
                column_types={},
                sample_data=[],
                is_empty=df_raw.empty,
                is_metadata_only=is_metadata,
            )

        # Find header row
        header_row = self._find_header_row(df_raw)

        # Read full sheet with correct header
        df = pd.read_excel(xl, sheet_name=sheet_name, header=header_row)

        # Clean empty rows
        df = df.dropna(how='all')

        # Remove rows that are all empty strings
        df = df[~df.apply(lambda row: all(str(v).strip() == '' for v in row), axis=1)]

        # Detect scope and category from sheet name
        detected_scope = self._detect_scope_from_name(sheet_name)
        detected_category = self._detect_category_from_name(sheet_name)

        return SheetAnalysis(
            sheet_name=sheet_name,
            header_row=header_row,
            data_start_row=header_row + 1,
            data_end_row=header_row + 1 + len(df),
            total_rows=len(df),
            columns=[str(c) for c in df.columns if not str(c).startswith('Unnamed')],
            column_types=self._detect_column_types(df),
            sample_data=df.head(5).to_dict('records'),
            is_empty=len(df) == 0,
            is_metadata_only=False,
            detected_scope=detected_scope,
            detected_category=detected_category,
        )

    def _find_header_row(self, df: pd.DataFrame) -> int:
        """
        Find the header row in a dataframe.
        Headers often have keyword-like content and precede numeric data.
        """
        best_row = 0
        best_score = 0

        for idx in range(min(15, len(df))):  # Check first 15 rows
            row = df.iloc[idx]
            score = 0

            # Count non-null values
            non_null_count = row.notna().sum()
            if non_null_count < 2:
                continue

            # Check for header keywords
            row_text = ' '.join(str(v).lower() for v in row if pd.notna(v))
            for keyword in self.HEADER_KEYWORDS:
                if keyword in row_text:
                    score += 10

            # Headers typically have string values
            string_count = sum(1 for v in row if pd.notna(v) and isinstance(v, str) and len(str(v)) > 1)
            score += string_count * 2

            # Check if next row has numeric data (indicates this is header)
            if idx + 1 < len(df):
                next_row = df.iloc[idx + 1]
                numeric_count = sum(1 for v in next_row if pd.notna(v) and self._is_numeric(v))
                score += numeric_count * 3

            # Penalize rows with mostly numbers (likely data, not header)
            numeric_in_row = sum(1 for v in row if pd.notna(v) and self._is_numeric(v))
            score -= numeric_in_row * 2

            if score > best_score:
                best_score = score
                best_row = idx

        return best_row

    def _is_numeric(self, value) -> bool:
        """Check if a value is numeric"""
        if isinstance(value, (int, float)):
            return True
        try:
            float(str(value).replace(',', ''))
            return True
        except (ValueError, TypeError):
            return False

    def _is_metadata_sheet(self, sheet_name: str, df: pd.DataFrame) -> bool:
        """Check if a sheet is a metadata/instruction sheet"""
        name_lower = sheet_name.lower()

        # Check name patterns
        for pattern in self.METADATA_SHEET_NAMES:
            if pattern in name_lower:
                return True

        # Check content - metadata sheets have few columns and little numeric data
        if df.empty:
            return True

        # Count numeric cells in first 10 rows
        numeric_count = 0
        for _, row in df.head(10).iterrows():
            for v in row:
                if pd.notna(v) and self._is_numeric(v):
                    numeric_count += 1

        # If very few numbers, likely metadata
        return numeric_count < 3

    def _detect_scope_from_name(self, sheet_name: str) -> Optional[int]:
        """Detect scope number from sheet name"""
        name_lower = sheet_name.lower()

        for scope, patterns in self.SCOPE_PATTERNS.items():
            for pattern in patterns:
                if pattern in name_lower:
                    return scope
        return None

    def _detect_category_from_name(self, sheet_name: str) -> Optional[str]:
        """Detect GHG category from sheet name"""
        name_lower = sheet_name.lower()

        # Check for explicit category number (e.g., "Cat. 4", "Cat.5")
        import re
        cat_match = re.search(r'cat\.?\s*(\d+)', name_lower)
        if cat_match:
            cat_num = int(cat_match.group(1))
            return f"3.{cat_num}"

        # Check patterns
        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if pattern in name_lower:
                    return category
        return None

    def _detect_column_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """Detect the data type of each column"""
        types = {}
        for col in df.columns:
            if str(col).startswith('Unnamed'):
                continue

            sample = df[col].dropna().head(10)
            if sample.empty:
                types[str(col)] = 'empty'
            elif all(self._is_numeric(v) for v in sample):
                types[str(col)] = 'numeric'
            elif all(isinstance(v, str) and self._looks_like_date(v) for v in sample):
                types[str(col)] = 'date'
            else:
                types[str(col)] = 'text'
        return types

    def _looks_like_date(self, value: str) -> bool:
        """Check if a string looks like a date"""
        import re
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # 2024-01-15
            r'\d{2}/\d{2}/\d{4}',  # 15/01/2024
            r'\d{2}-\d{2}-\d{4}',  # 15-01-2024
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',  # Month names
        ]
        value_lower = str(value).lower()
        return any(re.search(p, value_lower) for p in date_patterns)
