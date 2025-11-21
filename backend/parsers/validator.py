"""
Data Validator and Transformer for Skill DNA
Validates uploaded data and transforms to 3 required CSV formats:
- employees.csv
- skill_matrix.csv
- skill_evolution.csv
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime


class DataValidator:
    """
    Validates and transforms parsed employee data into Skill DNA format
    """

    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []

    def validate_parsed_data(self, parsed_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate parsed data structure
        Returns: (is_valid, error_messages)
        """
        self.validation_errors = []
        self.validation_warnings = []

        # Check if parsing succeeded
        if not parsed_data.get('success', False):
            self.validation_errors.append(parsed_data.get('error', 'Unknown parsing error'))
            return False, self.validation_errors

        employees = parsed_data.get('employees', {})

        # Validation 1: At least one employee
        if len(employees) == 0:
            self.validation_errors.append("No employees found in uploaded file")
            return False, self.validation_errors

        # Validation 2: Each employee has at least one skill
        employees_without_skills = 0
        for emp_id, emp_data in employees.items():
            skills = emp_data.get('skills', [])
            if len(skills) == 0:
                employees_without_skills += 1

        if employees_without_skills > 0:
            self.validation_warnings.append(
                f"{employees_without_skills} employees have no skills assigned"
            )

        # Validation 3: Check for required fields
        sample_emp = list(employees.values())[0]
        required_fields = ['skills', 'hire_date', 'department', 'position']
        missing_fields = [f for f in required_fields if f not in sample_emp]

        if missing_fields:
            self.validation_warnings.append(
                f"Some fields are missing or defaulted: {', '.join(missing_fields)}"
            )

        # Success if no critical errors
        return len(self.validation_errors) == 0, self.validation_errors

    def transform_to_employees_csv(self, parsed_data: Dict) -> pd.DataFrame:
        """
        Transform to employees.csv format
        Columns: employee_id, department, hire_date, skills (list), position
        """
        employees = parsed_data.get('employees', {})
        records = []

        for emp_id, emp_data in employees.items():
            # Extract all skill names
            skills = emp_data.get('skills', [])
            skill_names = [s.get('name', '') for s in skills if s.get('name')]

            # Format hire_date
            hire_date = emp_data.get('hire_date')
            if isinstance(hire_date, datetime):
                hire_date_str = hire_date.strftime('%Y-%m-%d')
            else:
                hire_date_str = str(hire_date) if hire_date else ''

            records.append({
                'employee_id': emp_id,
                'department': emp_data.get('department', 'Unknown'),
                'hire_date': hire_date_str,
                'skills': ','.join(skill_names),  # Comma-separated list
                'position': emp_data.get('position', 'Unknown')
            })

        df = pd.DataFrame(records)
        return df

    def transform_to_skill_matrix(self, parsed_data: Dict) -> pd.DataFrame:
        """
        Transform to skill_matrix.csv format
        Binary matrix: rows = employees, columns = skills (0/1)
        """
        employees = parsed_data.get('employees', {})

        # Collect all unique skills
        all_skills = set()
        for emp_data in employees.values():
            skills = emp_data.get('skills', [])
            for skill_info in skills:
                skill_name = skill_info.get('name')
                if skill_name:
                    all_skills.add(skill_name)

        all_skills = sorted(list(all_skills))

        # Build binary matrix
        matrix_records = []

        for emp_id, emp_data in employees.items():
            # Get employee's skills
            emp_skills = set()
            for skill_info in emp_data.get('skills', []):
                skill_name = skill_info.get('name')
                if skill_name:
                    emp_skills.add(skill_name)

            # Create binary row
            row = {'employee_id': emp_id}
            for skill in all_skills:
                row[skill] = 1 if skill in emp_skills else 0

            matrix_records.append(row)

        df = pd.DataFrame(matrix_records)

        # Ensure employee_id is first column
        cols = ['employee_id'] + [c for c in df.columns if c != 'employee_id']
        df = df[cols]

        return df

    def get_validation_summary(self, parsed_data: Dict, employees_df: pd.DataFrame,
                              skill_matrix_df: pd.DataFrame,
                              skill_evolution_df: pd.DataFrame = None) -> Dict:
        """
        Generate comprehensive validation summary
        """
        employees = parsed_data.get('employees', {})

        # Count skills
        all_skills = set()
        skill_acquisitions = []

        for emp_data in employees.values():
            for skill_info in emp_data.get('skills', []):
                skill_name = skill_info.get('name')
                acquired_date = skill_info.get('acquired_date')

                if skill_name:
                    all_skills.add(skill_name)
                if acquired_date and isinstance(acquired_date, datetime):
                    skill_acquisitions.append(acquired_date)

        # Time range
        if skill_acquisitions:
            min_date = min(skill_acquisitions)
            max_date = max(skill_acquisitions)
            time_range = f"{min_date.year}-{max_date.year}"
        else:
            time_range = "Unknown"

        summary = {
            'format_detected': parsed_data.get('format', 'Unknown'),
            'encoding_used': parsed_data.get('encoding', 'Unknown'),
            'employees_processed': len(employees_df),
            'skills_extracted': len(all_skills),
            'time_range': time_range,
            'validation_errors': self.validation_errors,
            'validation_warnings': self.validation_warnings,
            'files_generated': {
                'employees_csv': f"{len(employees_df)} rows",
                'skill_matrix_csv': f"{len(skill_matrix_df)} rows × {len(skill_matrix_df.columns)-1} skills",
                'skill_evolution_csv': f"{len(skill_evolution_df)} rows" if skill_evolution_df is not None else "Pending"
            }
        }

        return summary

    def save_csvs(self, employees_df: pd.DataFrame,
                  skill_matrix_df: pd.DataFrame,
                  skill_evolution_df: pd.DataFrame = None,
                  output_dir: str = "data") -> Dict[str, str]:
        """
        Save all CSV files to output directory
        Returns: Dict with file paths
        """
        import os

        # Create output directory if not exists
        os.makedirs(output_dir, exist_ok=True)

        file_paths = {}

        # Save employees.csv
        employees_path = os.path.join(output_dir, "employees.csv")
        employees_df.to_csv(employees_path, index=False)
        file_paths['employees'] = employees_path

        # Save skill_matrix.csv
        matrix_path = os.path.join(output_dir, "skill_matrix.csv")
        skill_matrix_df.to_csv(matrix_path, index=False)
        file_paths['skill_matrix'] = matrix_path

        # Save skill_evolution.csv (if provided)
        if skill_evolution_df is not None:
            evolution_path = os.path.join(output_dir, "skill_evolution.csv")
            skill_evolution_df.to_csv(evolution_path, index=False)
            file_paths['skill_evolution'] = evolution_path

        return file_paths


class DataTransformer:
    """
    Complete transformation pipeline: Parse → Validate → Transform → Save
    """

    def __init__(self):
        self.validator = DataValidator()

    def process_uploaded_file(self, parsed_data: Dict,
                              output_dir: str = "data",
                              generate_timeseries: bool = True) -> Dict:
        """
        Complete processing pipeline
        Returns: Summary with validation results and file paths
        """
        # Step 1: Validate
        is_valid, errors = self.validator.validate_parsed_data(parsed_data)

        if not is_valid:
            return {
                'success': False,
                'validation_errors': errors,
                'message': 'Data validation failed'
            }

        # Step 2: Transform to employees.csv
        employees_df = self.validator.transform_to_employees_csv(parsed_data)

        # Step 3: Transform to skill_matrix.csv
        skill_matrix_df = self.validator.transform_to_skill_matrix(parsed_data)

        # Step 4: Build skill_evolution.csv (optional)
        skill_evolution_df = None
        trends = None

        if generate_timeseries:
            from parsers.timeseries_builder import TimeSeriesBuilder

            builder = TimeSeriesBuilder(start_year=2013, end_year=2025)
            employees_data = parsed_data.get('employees', {})
            skill_evolution_df, trends = builder.build_evolution_csv(
                employees_data,
                output_path=f"{output_dir}/skill_evolution.csv"
            )

        # Step 5: Save CSVs
        file_paths = self.validator.save_csvs(
            employees_df,
            skill_matrix_df,
            skill_evolution_df,
            output_dir
        )

        # Step 6: Generate summary
        summary = self.validator.get_validation_summary(
            parsed_data,
            employees_df,
            skill_matrix_df,
            skill_evolution_df
        )

        summary['success'] = True
        summary['file_paths'] = file_paths
        summary['skill_trends'] = trends

        return summary


if __name__ == "__main__":
    # Test validator
    validator = DataValidator()

    print("[TEST] Data Validator initialized")
    print("[INFO] Validates and transforms to 3 CSV formats")

    # Test validation summary
    mock_data = {
        'success': True,
        'format': 'format3_lms',
        'encoding': 'utf-8',
        'employees': {
            'EMP001': {
                'skills': [{'name': 'Python', 'acquired_date': datetime(2020, 1, 1)}],
                'hire_date': datetime(2019, 6, 1),
                'department': 'Engineering',
                'position': 'Developer'
            }
        }
    }

    is_valid, errors = validator.validate_parsed_data(mock_data)
    print(f"[TEST] Validation result: {is_valid}")
    if errors:
        print(f"[TEST] Errors: {errors}")
