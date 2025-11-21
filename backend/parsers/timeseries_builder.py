"""
Time-Series Aggregation Engine for Skill DNA
Builds skill_evolution.csv from completion dates
Aggregates by year (2013-2025) and calculates skill popularity trends
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
from collections import defaultdict


class TimeSeriesBuilder:
    """
    Aggregates employee skill data into yearly time-series format
    Generates skill_evolution.csv from raw completion dates
    """

    # Skill category classification (auto-detect based on keywords)
    CATEGORY_KEYWORDS = {
        "Legacy Engineering": [
            "CAD", "CATIA", "AutoCAD", "Mechanical", "CNC", "SolidWorks",
            "Mechanický", "Konstrukce", "Výkres"
        ],
        "Software/Cloud": [
            "Python", "JavaScript", "Java", "React", "AWS", "Azure", "Docker",
            "Kubernetes", "Git", "SQL", "MongoDB", "Node.js", "TypeScript",
            "Programování", "Software", "Cloud"
        ],
        "E-Mobility": [
            "Battery", "Electric", "Charging", "EV", "Powertrain", "ADAS",
            "Baterie", "Elektrický", "Nabíjení", "Elektromobilita"
        ],
        "AI/Emerging": [
            "Machine Learning", "ML", "AI", "TensorFlow", "PyTorch", "LLM",
            "Deep Learning", "Neural", "Strojové učení", "Umělá inteligence"
        ]
    }

    def __init__(self, start_year: int = 2013, end_year: int = 2025):
        """
        Initialize time-series builder
        Args:
            start_year: Start of time range
            end_year: End of time range
        """
        self.start_year = start_year
        self.end_year = end_year
        self.years = list(range(start_year, end_year + 1))

    def classify_skill_category(self, skill_name: str) -> str:
        """
        Auto-detect skill category based on keywords
        """
        skill_lower = skill_name.lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in skill_lower:
                    return category

        # Default to Software if unknown
        return "Software/Cloud"

    def aggregate_by_year(self, employees_data: Dict) -> pd.DataFrame:
        """
        Aggregate employee skills by year
        Input: employees_data from multi_format_parser
        Output: DataFrame with columns [year, skill, category, popularity]
        """
        # Track skills per year
        skills_by_year = defaultdict(lambda: defaultdict(int))

        # Count employees with each skill per year
        for employee_id, emp_data in employees_data.items():
            skills = emp_data.get('skills', [])

            for skill_info in skills:
                skill_name = skill_info.get('name')
                acquired_date = skill_info.get('acquired_date')

                if not skill_name or not acquired_date:
                    continue

                # Extract year
                if isinstance(acquired_date, datetime):
                    year = acquired_date.year
                else:
                    continue

                # Only count years within range
                if self.start_year <= year <= self.end_year:
                    skills_by_year[year][skill_name] += 1

        # Build evolution DataFrame
        evolution_records = []

        for year in self.years:
            year_skills = skills_by_year.get(year, {})

            # Calculate total employees for this year (for popularity %)
            total_employees_year = len(employees_data)

            for skill_name, count in year_skills.items():
                # Calculate popularity percentage
                popularity = (count / total_employees_year) * 100 if total_employees_year > 0 else 0

                # Classify category
                category = self.classify_skill_category(skill_name)

                evolution_records.append({
                    'year': year,
                    'skill': skill_name,
                    'category': category,
                    'popularity': round(popularity, 2),
                    'employee_count': count
                })

        df = pd.DataFrame(evolution_records)

        # Sort by year and skill
        df = df.sort_values(['year', 'skill'])

        return df

    def fill_missing_years(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fill missing years for each skill with 0 popularity
        Ensures continuous time-series for visualization
        """
        all_skills = df['skill'].unique()
        filled_records = []

        for skill in all_skills:
            skill_data = df[df['skill'] == skill]
            category = skill_data['category'].iloc[0] if len(skill_data) > 0 else "Software/Cloud"

            for year in self.years:
                existing = skill_data[skill_data['year'] == year]

                if len(existing) > 0:
                    # Use existing data
                    filled_records.append(existing.iloc[0].to_dict())
                else:
                    # Fill with 0
                    filled_records.append({
                        'year': year,
                        'skill': skill,
                        'category': category,
                        'popularity': 0.0,
                        'employee_count': 0
                    })

        filled_df = pd.DataFrame(filled_records)
        filled_df = filled_df.sort_values(['year', 'skill'])

        return filled_df

    def interpolate_trends(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Smooth time-series with linear interpolation for better visualization
        """
        interpolated_records = []

        for skill in df['skill'].unique():
            skill_data = df[df['skill'] == skill].sort_values('year')

            # Interpolate popularity
            skill_data['popularity'] = skill_data['popularity'].interpolate(method='linear')

            interpolated_records.append(skill_data)

        return pd.concat(interpolated_records, ignore_index=True)

    def calculate_growth_trends(self, df: pd.DataFrame) -> Dict:
        """
        Calculate growth metrics for each skill
        Returns: Dict with skill growth classifications
        """
        trends = {}

        for skill in df['skill'].unique():
            skill_data = df[df['skill'] == skill].sort_values('year')

            if len(skill_data) < 2:
                continue

            # Calculate linear regression for trend
            years_numeric = skill_data['year'].values
            popularity = skill_data['popularity'].values

            # Simple linear fit
            coeffs = np.polyfit(years_numeric, popularity, 1)
            slope = coeffs[0]  # Growth rate per year

            # Classify trend
            if slope > 5:
                trend_class = "Explosive Emerging"
            elif slope > 1:
                trend_class = "Rapidly Growing"
            elif slope > -1:
                trend_class = "Stable Dominant"
            elif slope > -5:
                trend_class = "Slowly Declining"
            else:
                trend_class = "Dying/Legacy"

            trends[skill] = {
                'growth_rate': round(slope, 2),
                'trend_class': trend_class,
                'latest_popularity': round(popularity[-1], 2),
                'earliest_popularity': round(popularity[0], 2)
            }

        return trends

    def build_evolution_csv(self, employees_data: Dict,
                           output_path: str = "data/skill_evolution.csv",
                           fill_gaps: bool = True,
                           interpolate: bool = False) -> pd.DataFrame:
        """
        Main function: Build complete skill_evolution.csv
        """
        # Aggregate by year
        df = self.aggregate_by_year(employees_data)

        # Fill missing years
        if fill_gaps:
            df = self.fill_missing_years(df)

        # Interpolate trends (optional)
        if interpolate:
            df = self.interpolate_trends(df)

        # Calculate growth trends
        trends = self.calculate_growth_trends(df)

        # Save to CSV
        df.to_csv(output_path, index=False)

        print(f"[OK] Generated skill_evolution.csv")
        print(f"[INFO] Time range: {self.start_year}-{self.end_year}")
        print(f"[INFO] Unique skills: {df['skill'].nunique()}")
        print(f"[INFO] Total records: {len(df)}")

        return df, trends

    def generate_category_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate category-level aggregation for high-level insights
        """
        category_summary = df.groupby(['year', 'category']).agg({
            'popularity': 'mean',
            'employee_count': 'sum',
            'skill': 'count'
        }).reset_index()

        category_summary.columns = ['year', 'category', 'avg_popularity', 'total_employees', 'skill_count']

        return category_summary


if __name__ == "__main__":
    # Test time-series builder
    builder = TimeSeriesBuilder(start_year=2013, end_year=2025)

    print("[TEST] Time-Series Builder initialized")
    print(f"[INFO] Year range: {builder.start_year}-{builder.end_year}")
    print(f"[INFO] Categories: {len(builder.CATEGORY_KEYWORDS)}")

    # Test category classification
    test_skills = ["Python", "CAD", "Battery Systems", "Machine Learning"]
    for skill in test_skills:
        category = builder.classify_skill_category(skill)
        print(f"[TEST] '{skill}' → Category: '{category}'")
