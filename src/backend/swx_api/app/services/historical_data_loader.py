"""
Historical Data Loader
----------------------
Loads and processes 12 years of historical employee data.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from swx_api.app.models.skoda_models import HistoricalEmployeeSnapshot
from swx_api.app.services.skoda_data_adapter import SkodaDataAdapter
from swx_api.core.middleware.logging_middleware import logger


class HistoricalDataLoader:
    """Service for loading historical employee data."""
    
    def __init__(self):
        self.adapter = SkodaDataAdapter()
    
    def extract_year_from_filename(self, file_path: Path) -> int:
        """Extract year from filename."""
        year_match = re.search(r'(\d{4})', file_path.stem)
        if year_match:
            return int(year_match.group(1))
        return datetime.now().year
    
    async def load_historical_data(
        self,
        base_path: Path,
        years: List[int]
    ) -> List[Dict[str, Any]]:
        """Load 12 years of historical snapshots."""
        snapshots = []
        
        for year in years:
            patterns = [
                f"*{year}*.csv",
                f"*{year}*.xlsx",
                f"skoda_employees_{year}.csv",
                f"employees_{year}.csv",
            ]
            
            file_found = False
            for pattern in patterns:
                files = list(base_path.glob(pattern))
                if files:
                    file_path = files[0]
                    try:
                        df = self.adapter.parse_skoda_csv(file_path)
                        df["snapshot_year"] = year
                        df["snapshot_date"] = datetime(year, 1, 1)
                        
                        for _, row in df.iterrows():
                            try:
                                employee_data = self.adapter.map_to_employee_record(row)
                                snapshot = {
                                    "employee_id": employee_data["employee_id"],
                                    "snapshot_date": datetime(year, 1, 1),
                                    "department": employee_data["department"],
                                    "job_family_id": employee_data.get("pers_job_family_id"),
                                    "org_hierarchy": {
                                        "s1": employee_data.get("s1_org_hierarchy", ""),
                                        "s2": employee_data.get("s2_org_hierarchy", ""),
                                        "s3": employee_data.get("s3_org_hierarchy", ""),
                                        "s4": employee_data.get("s4_org_hierarchy", ""),
                                    },
                                    "skills": employee_data.get("skills", []),
                                    "qualifications": [q.get("qualification_id") for q in employee_data.get("qualifications", [])],
                                    "pers_profession_id": employee_data.get("pers_profession_id"),
                                    "pers_organization_branch": employee_data.get("pers_organization_branch"),
                                }
                                snapshots.append(snapshot)
                            except Exception as e:
                                logger.warning(f"Failed to create snapshot for row in {file_path}: {e}")
                                continue
                        
                        file_found = True
                        break
                    except Exception as e:
                        logger.warning(f"Failed to load historical file {file_path}: {e}")
                        continue
            
            if not file_found:
                logger.warning(f"No historical file found for year {year}")
        
        return snapshots
    
    async def save_historical_snapshots(
        self,
        session: AsyncSession,
        snapshots: List[Dict[str, Any]]
    ) -> int:
        """Save historical snapshots to database."""
        saved_count = 0
        
        for snapshot_data in snapshots:
            try:
                snapshot = HistoricalEmployeeSnapshot(**snapshot_data)
                session.add(snapshot)
                saved_count += 1
            except Exception as e:
                logger.warning(f"Failed to save snapshot: {e}")
                continue
        
        await session.commit()
        return saved_count
    
    async def merge_historical_datasets(
        self,
        files: List[Path]
    ) -> pd.DataFrame:
        """Merge multiple historical dataset files."""
        return self.adapter.merge_historical_datasets(files)

