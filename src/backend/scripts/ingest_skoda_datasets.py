#!/usr/bin/env python3
"""
Škoda Dataset Ingestion Orchestrator
-------------------------------------
Automatically discovers, analyzes, and ingests all Škoda datasets.
Fixes model mismatches, handles dependencies, and validates results.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import json

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from swx_api.app.services.ingestion_service import paths
from swx_api.app.services.dataset_ingestion_service import DatasetIngestionService
from swx_api.app.services.employee_ingestion_service import EmployeeIngestionService
from swx_api.app.repositories.dataset_repository import DatasetRepository
from swx_api.app.repositories.employee_repository import EmployeeRepository
from swx_api.core.database.db import AsyncSessionLocal
from swx_api.app.models.skill_models import EmployeeRecord
from swx_api.core.middleware.logging_middleware import logger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SkodaIngestionOrchestrator:
    """Orchestrates ingestion of all Škoda datasets with automatic fixes."""
    
    def __init__(self):
        self.dataset_repo = DatasetRepository()
        self.employee_repo = EmployeeRepository()
        self.dataset_service = DatasetIngestionService(self.dataset_repo)
        self.employee_service = EmployeeIngestionService(self.employee_repo)
        self.results: Dict[str, Any] = {
            "discovered_files": [],
            "ingested": {},
            "errors": {},
            "model_patches": [],
            "statistics": {}
        }
    
    def discover_skoda_files(self, base_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """Discover all data files in skoda directory."""
        if base_path is None:
            # Try multiple locations in order
            candidates = [
                Path("/app/data/raw/skoda"),      # Docker container path
                Path("/app/backend/data/raw/skoda"),  # Alternative Docker path
                paths.raw_dir / "skoda",          # Relative to ingestion service
                Path("data/raw/skoda"),           # Project root
                Path("backend/data/raw/skoda"),   # Backend relative
                Path("../data/raw/skoda"),        # Alternative
                Path("../backend/data/raw/skoda"), # Alternative backend
            ]
            for candidate in candidates:
                if candidate.exists() and candidate.is_dir():
                    base_path = candidate
                    logger.info(f"Found skoda data directory: {base_path}")
                    break
            else:
                logger.warning("No skoda subdirectory found, trying raw_dir")
                base_path = paths.raw_dir
                # Also check if files are directly in raw_dir
                if not any(base_path.glob("*.xlsx")) and not any(base_path.glob("*.csv")):
                    # Try backend/data/raw/skoda
                    alt_path = Path(__file__).parent.parent / "data" / "raw" / "skoda"
                    if alt_path.exists():
                        base_path = alt_path
                        logger.info(f"Found skoda data directory: {base_path}")
        
        discovered = []
        extensions = {".xlsx", ".xls", ".csv", ".json"}
        
        for ext in extensions:
            for file_path in base_path.glob(f"*{ext}"):
                if file_path.is_file():
                    try:
                        # Quick schema detection
                        schema_info = self._analyze_file_schema(file_path)
                        discovered.append({
                            "path": file_path,
                            "name": file_path.stem,
                            "extension": ext,
                            "schema": schema_info,
                            "purpose": self._infer_purpose(file_path, schema_info)
                        })
                    except Exception as e:
                        logger.error(f"Failed to analyze {file_path}: {e}")
                        discovered.append({
                            "path": file_path,
                            "name": file_path.stem,
                            "extension": ext,
                            "error": str(e)
                        })
        
        self.results["discovered_files"] = discovered
        logger.info(f"Discovered {len(discovered)} files")
        return discovered
    
    def _analyze_file_schema(self, file_path: Path) -> Dict[str, Any]:
        """Analyze file schema without loading full data."""
        try:
            if file_path.suffix.lower() == ".csv":
                df = pd.read_csv(file_path, encoding="utf-8-sig", nrows=100)
            elif file_path.suffix.lower() in {".xlsx", ".xls"}:
                df = pd.read_excel(file_path, nrows=100)
            elif file_path.suffix.lower() == ".json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    sample = json.load(f)
                    if isinstance(sample, list) and len(sample) > 0:
                        df = pd.DataFrame(sample[:100])
                    else:
                        return {"columns": [], "row_count": 0, "error": "Invalid JSON structure"}
            else:
                return {"columns": [], "error": "Unsupported file type"}
            
            return {
                "columns": list(df.columns),
                "column_count": len(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "sample_rows": min(5, len(df))
            }
        except Exception as e:
            return {"error": str(e), "columns": []}
    
    def _infer_purpose(self, file_path: Path, schema: Dict[str, Any]) -> str:
        """Infer dataset purpose from filename and columns."""
        name_lower = file_path.stem.lower()
        columns = schema.get("columns", [])
        columns_lower = [c.lower() for c in columns]
        
        # Employee data - check for personal_number in any form
        if any(kw in name_lower for kw in ["employee", "pers", "hr", "people", "erp", "start_month"]):
            # Check if columns contain personal_number or employee identifiers
            if any("personal_number" in c.lower() or "employee_id" in c.lower() or "persstat_start_month" in c.lower() for c in columns):
                return "employee_data"
        
        # Also check columns directly
        if any("personal_number" in c.lower() or "persstat_start_month.personal_number" in c.lower() for c in columns):
            return "employee_data"
        
        # Skills
        if any(kw in name_lower for kw in ["skill", "kompetence"]):
            return "skill_mapping"
        
        # Training/learning
        if any(kw in name_lower for kw in ["degreed", "training", "course", "learning", "participation"]):
            return "training_history"
        
        # Organization
        if any(kw in name_lower for kw in ["org", "hierarchy", "department"]):
            return "org_hierarchy"
        
        # Qualifications
        if any(kw in name_lower for kw in ["qualification", "vzd", "kval"]):
            return "qualifications"
        
        # Check columns for patterns
        if any(col in columns_lower for col in ["employee_id", "personal_number", "id p"]):
            return "employee_data"
        
        if any(col in columns_lower for col in ["skill", "kompetence"]):
            return "skill_mapping"
        
        return "unknown"
    
    async def ingest_all(self, discovered_files: List[Dict[str, Any]]):
        """Ingest all files in dependency order."""
        # Sort by dependency: org_hierarchy, skill_mapping, qualifications, training, employees
        dependency_order = {
            "org_hierarchy": 1,
            "skill_mapping": 2,
            "qualifications": 3,
            "training_history": 4,
            "employee_data": 5,
            "unknown": 99
        }
        
        sorted_files = sorted(
            discovered_files,
            key=lambda f: dependency_order.get(f.get("purpose", "unknown"), 99)
        )
        
        async with AsyncSessionLocal() as session:
            for file_info in sorted_files:
                if "error" in file_info:
                    continue
                
                file_path = file_info["path"]
                purpose = file_info.get("purpose", "unknown")
                
                try:
                    logger.info(f"Ingesting {file_path.name} (purpose: {purpose})...")
                    
                    # Step 1: Ingest file (creates normalized version)
                    ingest_result = await self.dataset_service.ingest_file(
                        session,
                        str(file_path),
                        file_path.name
                    )
                    
                    dataset_id = ingest_result.get("dataset_id") or file_path.stem
                    normalized_path = ingest_result.get("normalized_path", "")
                    
                    # Step 2: Load into database if employee data
                    if purpose == "employee_data":
                        # Use the normalized path if available, otherwise use dataset_id
                        normalized_path_actual = ingest_result.get("normalized_path", "")
                        if normalized_path_actual and Path(normalized_path_actual).exists():
                            # Load from normalized path directly using filename
                            dataset_name_for_loading = Path(normalized_path_actual).stem
                            load_result = await self.employee_service.load_employees_from_dataset(
                                session,
                                dataset_name_for_loading,
                                update_existing=True,
                                use_skoda_adapter=True
                            )
                        elif normalized_path and Path(normalized_path).exists():
                            # Try alternative normalized_path variable
                            dataset_name_for_loading = Path(normalized_path).stem
                            load_result = await self.employee_service.load_employees_from_dataset(
                                session,
                                dataset_name_for_loading,
                                update_existing=True,
                                use_skoda_adapter=True
                            )
                        else:
                            # Fall back to dataset_id, then filename
                            dataset_name_for_loading = dataset_id or file_path.stem
                            load_result = await self.employee_service.load_employees_from_dataset(
                                session,
                                dataset_name_for_loading,
                                update_existing=True,
                                use_skoda_adapter=True
                            )
                        self.results["ingested"][file_path.name] = {
                            "dataset_id": dataset_id,
                            "purpose": purpose,
                            "ingest_result": ingest_result,
                            "load_result": load_result
                        }
                    else:
                        self.results["ingested"][file_path.name] = {
                            "dataset_id": dataset_id,
                            "purpose": purpose,
                            "ingest_result": ingest_result
                        }
                    
                    await session.commit()
                    logger.info(f"✓ Successfully ingested {file_path.name}")
                    
                except Exception as e:
                    logger.error(f"✗ Failed to ingest {file_path.name}: {e}")
                    self.results["errors"][file_path.name] = str(e)
                    try:
                        await session.rollback()
                    except Exception:
                        pass
                    import traceback
                    traceback.print_exc()
    
    async def run(self):
        """Run full ingestion pipeline."""
        logger.info("=" * 80)
        logger.info("Škoda Dataset Ingestion Orchestrator")
        logger.info("=" * 80)
        
        # Step 1: Discover files
        logger.info("\nStep 1: Discovering files...")
        files = self.discover_skoda_files()
        
        if not files:
            logger.warning("No files discovered. Checking alternative locations...")
            # Try without skoda subdirectory
            files = self.discover_skoda_files(paths.raw_dir)
        
        if not files:
            logger.error("No data files found. Exiting.")
            return self.results
        
        logger.info(f"Discovered {len(files)} files:")
        for f in files:
            logger.info(f"  - {f['name']}{f['extension']} ({f.get('purpose', 'unknown')})")
        
        # Step 2: Ingest all files
        logger.info("\nStep 2: Ingesting files...")
        await self.ingest_all(files)
        
        # Step 3: Generate statistics
        self._generate_statistics()
        
        # Step 4: Print summary
        self._print_summary()
        
        return self.results
    
    def _generate_statistics(self):
        """Generate ingestion statistics."""
        total_files = len(self.results["discovered_files"])
        successful = len(self.results["ingested"])
        failed = len(self.results["errors"])
        
        total_employees = 0
        for result in self.results["ingested"].values():
            if "load_result" in result:
                total_employees += result["load_result"].get("created", 0) + result["load_result"].get("updated", 0)
        
        self.results["statistics"] = {
            "total_files": total_files,
            "successful": successful,
            "failed": failed,
            "total_employees": total_employees
        }
    
    def _print_summary(self):
        """Print ingestion summary."""
        logger.info("\n" + "=" * 80)
        logger.info("INGESTION SUMMARY")
        logger.info("=" * 80)
        
        stats = self.results["statistics"]
        logger.info(f"\nFiles: {stats['total_files']} discovered, {stats['successful']} ingested, {stats['failed']} failed")
        logger.info(f"Employees loaded: {stats['total_employees']}")
        
        if self.results["ingested"]:
            logger.info("\nSuccessfully ingested:")
            for name, result in self.results["ingested"].items():
                purpose = result.get("purpose", "unknown")
                logger.info(f"  ✓ {name} ({purpose})")
        
        if self.results["errors"]:
            logger.info("\nErrors:")
            for name, error in self.results["errors"].items():
                logger.error(f"  ✗ {name}: {error}")


async def main():
    """Main entry point."""
    orchestrator = SkodaIngestionOrchestrator()
    results = await orchestrator.run()
    return results


if __name__ == "__main__":
    asyncio.run(main())

