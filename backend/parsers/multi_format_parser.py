"""
Multi-Format CSV Parser for Skill DNA
Supports 5 different CSV formats from HR/LMS/Planning systems
Handles Czech and English field names with UTF-8 encoding
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import re


class MultiFormatParser:
    """
    Auto-detects and parses 5 different CSV formats into unified schema
    """

    # Format signatures for auto-detection
    FORMAT_SIGNATURES = {
        "format1_hr": ["VP", "TO", "ID obj.", "ITyp", "STyp", "Zaèátek", "Konec"],
        "format2_planning": ["Var.plánu", "Typ obj.", "ID objektu", "Subtyp", "Platí od", "Platí do"],
        "format3_lms": ["Employee ID", "Content Title", "Content Type", "Completed Date"],
        "format4_projects": ["ID P", "Počát.datum", "Koncové datum", "ID Q", "Název Q"],
        "format5_qualifications": ["ID kvalifikace", "Kvalifikace", "Číslo FM"],
        "format6_personnel_stats": ["personal_number", "profession", "field_of_study"]
    }

    # Czech to English field mappings
    CZECH_TO_ENGLISH = {
        # Format 1
        "Zaèátek": "start_date",
        "Začátek": "start_date",
        "Konec": "end_date",
        "ID obj.": "object_id",

        # Format 2
        "Var.plánu": "plan_variant",
        "Typ obj.": "object_type",
        "ID objektu": "object_id",
        "Platí od": "valid_from",
        "Platí do": "valid_to",
        "Jazyk": "language",
        "Øetìzec": "text",
        "Řetězec": "text",

        # Format 4
        "Počát.datum": "start_date",
        "Koncové datum": "end_date",
        "Název Q": "qualification_name",

        # Format 5
        "ID kvalifikace": "qualification_id",
        "Kvalifikace": "qualification",
        "Číslo FM": "fm_number",

        # Common
        "ID zaměstnance": "employee_id",
        "Oddělení": "department",
        "Pozice": "position"
    }

    def __init__(self):
        self.detected_format = None
        self.encoding_used = None

    def detect_format(self, df: pd.DataFrame) -> Optional[str]:
        """
        Auto-detect which of 6 formats the CSV matches
        Returns: format name or None
        """
        columns = set(df.columns)

        # Also create stripped version (remove table prefixes like "persstat_start_month.")
        stripped_columns = set()
        for col in columns:
            if '.' in col:
                stripped_columns.add(col.split('.')[-1])  # Take last part after dot
            stripped_columns.add(col)

        for format_name, signature in self.FORMAT_SIGNATURES.items():
            # Check if signature columns are present (at least 60% match)
            matches = sum(1 for col in signature if col in columns or col in stripped_columns)
            match_ratio = matches / len(signature)

            if match_ratio >= 0.6:
                self.detected_format = format_name
                return format_name

        return None

    def read_csv_with_encoding(self, file_path: str) -> pd.DataFrame:
        """
        Try multiple encodings to read Czech CSV files
        """
        encodings = ['utf-8', 'cp1250', 'iso-8859-2', 'windows-1250']

        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                self.encoding_used = encoding
                return df
            except (UnicodeDecodeError, UnicodeError):
                continue

        # Fallback: use utf-8 with error handling
        df = pd.read_csv(file_path, encoding='utf-8', errors='replace')
        self.encoding_used = 'utf-8 (with replacements)'
        return df

    def parse_format1_hr_system(self, df: pd.DataFrame) -> Dict:
        """
        Format 1: VP,TO,ID obj.,ITyp,STyp,S,Zaèátek,Konec,VarPole,ÈZá,H,Var.pole uivatel.dat
        Czech HR system with start/end dates
        """
        employees = []
        skills_by_employee = {}

        for idx, row in df.iterrows():
            employee_id = row.get('ID obj.', f"EMP_{idx}")
            skill_name = row.get('ITyp', 'Unknown Skill')
            start_date = row.get('Zaèátek') or row.get('Začátek')

            # Parse date
            parsed_date = self._parse_date(start_date)

            # Add to skills collection
            if employee_id not in skills_by_employee:
                skills_by_employee[employee_id] = {
                    'skills': [],
                    'hire_date': parsed_date,
                    'department': row.get('S', 'Unknown'),
                    'position': row.get('TO', 'Unknown')
                }

            skills_by_employee[employee_id]['skills'].append({
                'name': skill_name,
                'acquired_date': parsed_date
            })

        return {
            'format': 'format1_hr',
            'employees': skills_by_employee,
            'total_employees': len(skills_by_employee),
            'encoding': self.encoding_used
        }

    def parse_format2_planning(self, df: pd.DataFrame) -> Dict:
        """
        Format 2: Var.plánu,Typ obj.,ID objektu,Subtyp,Platí od,Platí do,Jazyk,Øetìzec
        Planning system with validity periods
        """
        employees = {}

        for idx, row in df.iterrows():
            employee_id = row.get('ID objektu', f"EMP_{idx}")
            skill_name = row.get('Øetìzec') or row.get('Řetězec', 'Unknown Skill')
            valid_from = row.get('Platí od')

            parsed_date = self._parse_date(valid_from)

            if employee_id not in employees:
                employees[employee_id] = {
                    'skills': [],
                    'hire_date': parsed_date,
                    'department': row.get('Typ obj.', 'Unknown'),
                    'position': row.get('Subtyp', 'Unknown')
                }

            employees[employee_id]['skills'].append({
                'name': skill_name,
                'acquired_date': parsed_date
            })

        return {
            'format': 'format2_planning',
            'employees': employees,
            'total_employees': len(employees),
            'encoding': self.encoding_used
        }

    def parse_format3_lms(self, df: pd.DataFrame) -> Dict:
        """
        Format 3: Completed Date,Employee ID,Content ID,Content Title,Content Type,...
        Learning Management System - EASIEST format to parse
        """
        employees = {}

        for idx, row in df.iterrows():
            employee_id = str(row.get('Employee ID', f"EMP_{idx}"))

            # Extract skills from both Content Title AND Content Type
            content_title = row.get('Content Title', '')
            content_type = row.get('Content Type', '')
            completed_date = row.get('Completed Date')

            parsed_date = self._parse_date(completed_date)

            if employee_id not in employees:
                employees[employee_id] = {
                    'skills': [],
                    'hire_date': parsed_date,  # Use earliest completion as proxy
                    'department': 'Unknown',
                    'position': 'Unknown'
                }

            # Add both content title and type as skills (if meaningful)
            if content_title and len(content_title) > 2:
                employees[employee_id]['skills'].append({
                    'name': content_title,
                    'acquired_date': parsed_date,
                    'category': content_type
                })

            if content_type and len(content_type) > 2 and content_type != content_title:
                employees[employee_id]['skills'].append({
                    'name': content_type,
                    'acquired_date': parsed_date,
                    'category': 'Category'
                })

        return {
            'format': 'format3_lms',
            'employees': employees,
            'total_employees': len(employees),
            'encoding': self.encoding_used
        }

    def parse_format4_projects(self, df: pd.DataFrame) -> Dict:
        """
        Format 4: ID P,Počát.datum,Koncové datum,ID Q,Název Q
        Project/task data with qualifications
        """
        employees = {}

        for idx, row in df.iterrows():
            # Use ID Q as employee ID (or ID P if more appropriate)
            employee_id = str(row.get('ID Q', row.get('ID P', f"EMP_{idx}")))
            skill_name = row.get('Název Q', 'Unknown Qualification')
            start_date = row.get('Počát.datum')

            parsed_date = self._parse_date(start_date)

            if employee_id not in employees:
                employees[employee_id] = {
                    'skills': [],
                    'hire_date': parsed_date,
                    'department': 'Unknown',
                    'position': 'Project Member'
                }

            employees[employee_id]['skills'].append({
                'name': skill_name,
                'acquired_date': parsed_date
            })

        return {
            'format': 'format4_projects',
            'employees': employees,
            'total_employees': len(employees),
            'encoding': self.encoding_used
        }

    def parse_format5_qualifications(self, df: pd.DataFrame) -> Dict:
        """
        Format 5: ID kvalifikace,Kvalifikace,Číslo FM
        Direct qualification/skill listing
        """
        employees = {}

        for idx, row in df.iterrows():
            employee_id = str(row.get('ID kvalifikace', f"EMP_{idx}"))
            skill_name = row.get('Kvalifikace', 'Unknown Skill')

            if employee_id not in employees:
                employees[employee_id] = {
                    'skills': [],
                    'hire_date': datetime.now(),
                    'department': 'Unknown',
                    'position': 'Unknown'
                }

            employees[employee_id]['skills'].append({
                'name': skill_name,
                'acquired_date': datetime.now()
            })

        return {
            'format': 'format5_qualifications',
            'employees': employees,
            'total_employees': len(employees),
            'encoding': self.encoding_used
        }

    def parse_format6_personnel_stats(self, df: pd.DataFrame) -> Dict:
        """
        Format 6: personal_number,profession,field_of_study_name,education_category_name,...
        Personnel statistics with professions and education data
        Handles table-prefixed columns (e.g., persstat_start_month.personal_number)
        """
        employees = {}

        # Helper function to get column value regardless of table prefix
        def get_col(row, col_name):
            # Try exact match first
            if col_name in row.index:
                return row.get(col_name)
            # Try with any prefix (e.g., persstat_start_month.col_name)
            for key in row.index:
                if key.endswith('.' + col_name):
                    return row.get(key)
            return None

        for idx, row in df.iterrows():
            employee_id = str(get_col(row, 'personal_number') or f"EMP_{idx}")

            # Extract skills from multiple columns
            skills_to_add = []

            # Profession
            profession = get_col(row, 'profession')
            if profession and len(str(profession)) > 2:
                skills_to_add.append(('profession', str(profession)))

            # Planned profession
            planned_profession = get_col(row, 'planned_profession')
            if planned_profession and len(str(planned_profession)) > 2:
                skills_to_add.append(('planned_profession', str(planned_profession)))

            # Field of study
            field_of_study = get_col(row, 'field_of_study_name')
            if field_of_study and len(str(field_of_study)) > 2:
                skills_to_add.append(('education', str(field_of_study)))

            # Education category
            education_category = get_col(row, 'education_category_name')
            if education_category and len(str(education_category)) > 2:
                skills_to_add.append(('education_category', str(education_category)))

            # Initialize employee if not exists
            if employee_id not in employees:
                employees[employee_id] = {
                    'skills': [],
                    'hire_date': datetime.now(),
                    'department': 'Unknown',
                    'position': profession or 'Unknown'
                }

            # Add all skills
            for skill_category, skill_name in skills_to_add:
                employees[employee_id]['skills'].append({
                    'name': skill_name,
                    'acquired_date': datetime.now(),
                    'category': skill_category
                })

        return {
            'format': 'format6_personnel_stats',
            'employees': employees,
            'total_employees': len(employees),
            'encoding': self.encoding_used
        }

    def parse(self, file_path: str) -> Dict:
        """
        Main parsing function - auto-detects format and parses accordingly.
        Added support for Excel (.xlsx/.xls) and basic PDF extraction.
        """
        ext = file_path.lower().split('.')[-1]
        if ext in ['xlsx', 'xls']:
            try:
                df = pd.read_excel(file_path)
                self.encoding_used = 'excel'
            except Exception as e:
                # Retry with explicit engine fallback
                try:
                    df = pd.read_excel(file_path, engine='openpyxl')
                    self.encoding_used = 'excel-openpyxl'
                except Exception as e2:
                    return {'success': False, 'error': f'Excel parse failed: {e2}'}
        elif ext == 'pdf':
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                lines = []
                for page in reader.pages[:3]:  # limit pages for speed
                    text = page.extract_text() or ''
                    lines.extend([l for l in text.split('\n') if l.count(',') >= 2])
                if not lines:
                    return {'success': False, 'error': 'No tabular comma-separated data detected in first pages of PDF'}
                # Build DataFrame by splitting commas; assume first line headers
                headers = [h.strip() for h in lines[0].split(',')]
                records = []
                for row in lines[1:]:
                    parts = [p.strip() for p in row.split(',')]
                    if len(parts) == len(headers):
                        records.append(parts)
                df = pd.DataFrame(records, columns=headers)
                self.encoding_used = 'pdf-extracted'
            except Exception as e:
                return {'success': False, 'error': f'PDF parse failed: {e}'}
        else:
            # CSV path
            df = self.read_csv_with_encoding(file_path)

        # Detect format
        format_detected = self.detect_format(df)

        if not format_detected:
            return {
                'success': False,
                'error': 'Unrecognized data format',
                'columns_found': list(df.columns),
                'suggestion': 'Ensure file matches one of 6 supported CSV formats or provide structured Excel/PDF with matching headers'
            }

        parsers = {
            'format1_hr': self.parse_format1_hr_system,
            'format2_planning': self.parse_format2_planning,
            'format3_lms': self.parse_format3_lms,
            'format4_projects': self.parse_format4_projects,
            'format5_qualifications': self.parse_format5_qualifications,
            'format6_personnel_stats': self.parse_format6_personnel_stats
        }

        result = parsers[format_detected](df)
        result['success'] = True
        return result

    def _parse_date(self, date_str) -> Optional[datetime]:
        """
        Parse multiple date formats (Czech and English)
        Supports: DD.MM.YYYY, MM/DD/YYYY, YYYY-MM-DD
        """
        if pd.isna(date_str) or not date_str:
            return None

        date_formats = [
            '%d.%m.%Y',      # Czech format: 25.12.2023
            '%m/%d/%Y',      # US format: 12/25/2023
            '%Y-%m-%d',      # ISO format: 2023-12-25
            '%d-%m-%Y',      # Alternative: 25-12-2023
            '%Y/%m/%d'       # Alternative: 2023/12/25
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except (ValueError, TypeError):
                continue

        # Fallback: return current date
        return datetime.now()


if __name__ == "__main__":
    # Test parser
    parser = MultiFormatParser()

    # Example usage
    print("[TEST] Multi-Format Parser initialized")
    print(f"[INFO] Supports {len(parser.FORMAT_SIGNATURES)} formats")
    print("[INFO] Czech and English field names supported")
