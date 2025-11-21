"""
Universal Data Ingestion Service
---------------------------------
Handles ingestion of CSV, Excel, JSON, TXT, DOCX files with:
- Auto schema detection
- Skill field detection
- PII masking
- Data normalization
- Quality reports
- Škoda dataset support
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import anyio
import pandas as pd
from docx import Document  # type: ignore[import-untyped]

from swx_api.core.middleware.logging_middleware import logger
from swx_api.app.services.skoda_data_adapter import SkodaDataAdapter
from swx_api.app.services.multilingual_normalization_service import MultilingualNormalizationService

# Supported file extensions
SUPPORTED_TABLE_EXTENSIONS = {".csv", ".xlsx", ".xls"}
SUPPORTED_TEXT_EXTENSIONS = {".txt", ".docx"}
SUPPORTED_JSON_EXTENSIONS = {".json"}
SUPPORTED_EXTENSIONS = SUPPORTED_TABLE_EXTENSIONS | SUPPORTED_TEXT_EXTENSIONS | SUPPORTED_JSON_EXTENSIONS


class IngestionPaths:
    """Manages data directory structure."""
    
    def __init__(self) -> None:
        services_dir = Path(__file__).resolve().parent
        backend_dir = services_dir.parents[2]
        repo_root = backend_dir.parent

        # Determine data directory with fallback logic
        self.data_dir = self._resolve_data_dir(repo_root)
        self.raw_dir = self.data_dir / "raw"
        self.normalized_dir = self.data_dir / "normalized"
        self.processed_dir = self.data_dir / "processed"
        self.analysis_dir = self.data_dir / "analysis"
        self.logs_dir = self.data_dir / "logs"

        # Create subdirectories (data_dir already created by _resolve_data_dir)
        for path in (
            self.raw_dir,
            self.normalized_dir,
            self.processed_dir,
            self.analysis_dir,
            self.logs_dir,
        ):
            try:
                path.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as e:
                logger.warning(f"Ingestion subdirectory not writable ({path}): {e}")
                # Continue - individual subdir failures shouldn't block initialization

        self.log_file = self.logs_dir / "ingest.log"
    
    def _resolve_data_dir(self, repo_root: Path) -> Path:
        """Resolve data directory with graceful fallbacks."""
        import os
        import tempfile
        
        candidate_dirs = []
        
        # Check environment override
        override_dir = os.getenv("SKODA_DATA_ROOT")
        if override_dir:
            candidate_dirs.append(Path(override_dir))
        
        # Add standard candidates
        candidate_dirs.extend([
            repo_root / "data",
            Path.cwd() / "data",
            Path(tempfile.gettempdir()) / "skoda_data",
        ])
        
        # Try each candidate
        for path in candidate_dirs:
            try:
                path.mkdir(parents=True, exist_ok=True)
                return path.resolve()
            except (PermissionError, OSError) as e:
                logger.debug(f"Data dir candidate not writable ({path}): {e}")
                continue
        
        # Last resort: use temp directory
        fallback = Path(tempfile.mkdtemp(prefix="skoda_ingestion_"))
        logger.warning(f"Using temporary ingestion data directory at {fallback}")
        return fallback


paths = IngestionPaths()

# Set up logger
ingestion_logger = logging.getLogger("ingestion")
ingestion_logger.setLevel(logging.INFO)
if not any(isinstance(handler, logging.FileHandler) and handler.baseFilename == str(paths.log_file)
           for handler in ingestion_logger.handlers):
    try:
        file_handler = logging.FileHandler(paths.log_file, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        ingestion_logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        logger.warning(f"Could not create ingestion log file ({paths.log_file}): {e}. Logging to console only.")


# PII Detection Patterns
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{3,4}\b")
NAME_REGEX = re.compile(r"\b(?:[A-ZÁČĎÉĚÍĹĽŇÓŘŠŤÚŮÝŽ][a-záčďéěíĺľňóřšťúůýž]+(?:\s+|$)){2,3}")


def timestamped_filename(original_name: str) -> str:
    """Generate timestamped filename."""
    suffix = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    original_path = Path(original_name)
    base = re.sub(r"\s+", "_", original_path.stem)
    return f"{base}_{suffix}{original_path.suffix.lower()}"


def mask_pii_text(text: str) -> str:
    """Mask PII in text."""
    masked = EMAIL_REGEX.sub("[REDACTED]", text)
    masked = PHONE_REGEX.sub("[REDACTED]", masked)
    masked = NAME_REGEX.sub("[REDACTED]", masked)
    return masked


def mask_pii_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Mask PII in dataframe."""
    masked_df = df.copy()
    for column in masked_df.columns:
        if masked_df[column].dtype == object:
            masked_df[column] = masked_df[column].astype(str).apply(mask_pii_text)
    return masked_df


def read_table(path: Path) -> pd.DataFrame:
    """Read table file (CSV, Excel)."""
    if path.suffix.lower() == ".csv":
        try:
            return pd.read_csv(path, encoding="utf-8-sig")
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="latin-1")
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported table extension: {path.suffix}")


def read_text(path: Path) -> str:
    """Read text file (TXT, DOCX) - sync version."""
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".docx":
        document = Document(path)
        paragraphs = [para.text for para in document.paragraphs]
        return "\n".join(paragraphs)
    raise ValueError(f"Unsupported text extension: {path.suffix}")


async def read_text_async(path: Path) -> str:
    """Read text file asynchronously (TXT only - DOCX requires sync library)."""
    import aiofiles
    if path.suffix.lower() == ".txt":
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            return await f.read()
    if path.suffix.lower() == ".docx":
        return read_text(path)
    raise ValueError(f"Unsupported text extension: {path.suffix}")


def read_json(path: Path) -> Any:
    """Read JSON file (sync - for backward compatibility)."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


async def read_json_async(path: Path) -> Any:
    """Read JSON file asynchronously."""
    import aiofiles
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)


def detect_skill_fields(df: pd.DataFrame) -> List[str]:
    """Auto-detect skill-related columns."""
    skill_keywords = [
        "skill", "competenc", "ability", "expertise", "proficiency",
        "knowledge", "capability", "qualification", "certification"
    ]
    skill_columns = []
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in skill_keywords):
            skill_columns.append(str(col))
    return skill_columns


def detect_skoda_schema(df: pd.DataFrame) -> bool:
    """Detect if dataset is Škoda format."""
    skoda_indicators = [
        "personal_number",
        "persstat_start_month_abc",
        "pers_organization_branch",
        "pers_profession_id",
        "pers_job_family_id",
        "s1_org_hierarchy",
        "s2_org_hierarchy",
        "s3_org_hierarchy",
        "s4_org_hierarchy",
    ]
    
    found_indicators = sum(1 for col in df.columns if str(col).lower() in [ind.lower() for ind in skoda_indicators])
    return found_indicators >= 3


def profile_dataframe(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], float]:
    """Profile dataframe columns."""
    profiles: List[Dict[str, Any]] = []
    numeric_columns = 0
    total_columns = len(df.columns)

    for column in df.columns:
        series = df[column]
        dtype = str(series.dtype)
        null_ratio = float(series.isnull().sum() / max(len(series), 1))
        is_numeric = pd.api.types.is_numeric_dtype(series)
        if is_numeric:
            numeric_columns += 1
        profiles.append({
            "name": str(column),
            "dtype": dtype,
            "null_ratio": round(null_ratio, 4),
            "is_numeric": is_numeric,
        })

    numeric_ratio = numeric_columns / total_columns if total_columns else 0.0
    return profiles, numeric_ratio


def compute_data_quality_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute data quality metrics."""
    total_rows = len(df)
    total_cols = len(df.columns)
    
    missing_values = {}
    for col in df.columns:
        missing_count = df[col].isnull().sum()
        missing_values[str(col)] = {
            "count": int(missing_count),
            "percentage": round(float(missing_count / total_rows * 100) if total_rows > 0 else 0, 2)
        }
    
    outliers = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            series = df[col].dropna()
            if len(series) > 0:
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outlier_count = int(((series < lower_bound) | (series > upper_bound)).sum())
                if outlier_count > 0:
                    outliers[str(col)] = {
                        "count": outlier_count,
                        "percentage": round(float(outlier_count / len(series) * 100), 2)
                    }
    
    correlation_matrix = {}
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    if len(numeric_cols) > 1:
        corr_df = df[numeric_cols].corr()
        correlation_matrix = corr_df.to_dict()
    
    skill_frequency = {}
    skill_columns = detect_skill_fields(df)
    for col in skill_columns:
        if df[col].dtype == object:
            value_counts = df[col].value_counts().head(20)
            skill_frequency[str(col)] = {
                str(k): int(v) for k, v in value_counts.items()
            }
    
    return {
        "total_rows": total_rows,
        "total_columns": total_cols,
        "missing_values": missing_values,
        "outliers": outliers,
        "correlation_matrix": correlation_matrix,
        "skill_frequency": skill_frequency
    }


def infer_dataset_name(uploaded_path: Path) -> str:
    """Infer dataset name from file path."""
    return uploaded_path.stem


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    """Save JSON file (sync - for backward compatibility)."""
    with path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)


async def save_json_async(path: Path, payload: Dict[str, Any]) -> None:
    """Save JSON file asynchronously."""
    import aiofiles
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(payload, ensure_ascii=False, indent=2))


def _dataframe_from_records(records: List[Dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(records)


async def _to_thread(func, /, *args, **kwargs):
    return await anyio.to_thread.run_sync(func, *args, **kwargs)


def ingest_file(file_path: Path, original_filename: str) -> Dict[str, Any]:
    """
    Ingest a file and return normalized response (sync/async compatible).
    
    Can be called from sync or async contexts. In sync contexts, automatically
    runs the async implementation.
    
    Returns SWX normalized ingestion response:
    {
        success: true,
        data: {
            dataset_id,
            filename,
            stored_path,
            normalized_path,
            metadata,
            dq_report_path,
            summary_path
        }
    }
    """
    try:
        import asyncio
        loop = asyncio.get_running_loop()
        # We're in an async context, need to return coroutine
        raise RuntimeError("Cannot call sync wrapper from async context - use await ingest_file_async()")
    except RuntimeError as e:
        if "Cannot call sync wrapper" in str(e):
            raise
        # No event loop running, run in sync mode
        import asyncio
        return asyncio.run(_ingest_file_async(file_path, original_filename))


async def ingest_file_async(file_path: Path, original_filename: str) -> Dict[str, Any]:
    """
    Async version of ingest_file - use this in async contexts.
    """
    return await _ingest_file_async(file_path, original_filename)


async def _ingest_file_async(file_path: Path, original_filename: str) -> Dict[str, Any]:
    """
    Async implementation of file ingestion.
    """
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {file_path.suffix}")

    ingestion_logger.info("Ingesting file=%s saved_at=%s", original_filename, file_path)

    dataset_id = str(uuid.uuid4())
    dataset_name = infer_dataset_name(file_path)
    
    response: Dict[str, Any] = {
        "dataset_id": dataset_id,
        "filename": original_filename,
        "stored_path": str(file_path),
        "normalized_path": "",
        "metadata": {},
        "dq_report_path": None,
        "summary_path": "",
        "is_skoda_format": False,
    }

    # Process based on file type
    if file_path.suffix.lower() in SUPPORTED_TABLE_EXTENSIONS:
        df = await _to_thread(read_table, file_path)
        row_count = int(len(df))
        
        # Detect Škoda schema
        is_skoda = await _to_thread(detect_skoda_schema, df)
        response["is_skoda_format"] = is_skoda
        
        # Profile dataframe
        column_profiles, numeric_ratio = await _to_thread(profile_dataframe, df)
        
        # Mask PII
        masked_df = await _to_thread(mask_pii_dataframe, df)
        
        # Detect skill fields
        skill_fields = await _to_thread(detect_skill_fields, masked_df)
        
        # Save normalized data
        normalized_path = paths.normalized_dir / f"{dataset_name}.csv"
        def _save_csv():
            masked_df.to_csv(normalized_path, index=False, encoding="utf-8-sig")
        await _to_thread(_save_csv)
        response["normalized_path"] = str(normalized_path)
        
        # Compute data quality metrics
        dq_metrics = await _to_thread(compute_data_quality_metrics, masked_df)
        
        # Generate metadata
        metadata = {
            "row_count": row_count,
            "column_count": len(df.columns),
            "columns": column_profiles,
            "numeric_ratio": numeric_ratio,
            "skill_fields": skill_fields,
            "is_skoda_format": is_skoda,
            "ingested_at": datetime.utcnow().isoformat(),
        }
        response["metadata"] = metadata
        
        # Generate DQ report
        dq_report = {
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "generated_at": datetime.utcnow().isoformat(),
            "is_skoda_format": is_skoda,
            **dq_metrics
        }
        dq_report_path = paths.processed_dir / f"{dataset_name}_dq_report.json"
        await save_json_async(dq_report_path, dq_report)
        response["dq_report_path"] = str(dq_report_path)
        
        # Generate summary
        summary = {
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "row_count": row_count,
            "column_count": len(df.columns),
            "skill_fields": skill_fields,
            "is_skoda_format": is_skoda,
            "data_quality_score": 100 - int(sum(
                v["percentage"] for v in dq_metrics.get("missing_values", {}).values()
            ) / max(len(dq_metrics.get("missing_values", {})), 1)),
            "generated_at": datetime.utcnow().isoformat(),
        }
        summary_path = paths.processed_dir / f"{dataset_name}_summary.json"
        await save_json_async(summary_path, summary)
        response["summary_path"] = str(summary_path)
        
    elif file_path.suffix.lower() in SUPPORTED_JSON_EXTENSIONS:
        data = await read_json_async(file_path)
        
        # Convert JSON to DataFrame if it's a list of objects
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            df = await _to_thread(_dataframe_from_records, data)
            row_count = int(len(df))
            
            # Detect Škoda schema
            is_skoda = await _to_thread(detect_skoda_schema, df)
            response["is_skoda_format"] = is_skoda
            
            # Mask PII
            masked_df = await _to_thread(mask_pii_dataframe, df)
            
            # Detect skill fields
            skill_fields = await _to_thread(detect_skill_fields, masked_df)
            
            # Save normalized data
            normalized_path = paths.normalized_dir / f"{dataset_name}.csv"
            await _to_thread(masked_df.to_csv, normalized_path, index=False, encoding="utf-8-sig")
            response["normalized_path"] = str(normalized_path)
            
            # Compute data quality metrics
            dq_metrics = await _to_thread(compute_data_quality_metrics, masked_df)
            
            # Generate metadata
            column_profiles, numeric_ratio = await _to_thread(profile_dataframe, masked_df)
            metadata = {
                "row_count": row_count,
                "column_count": len(df.columns),
                "columns": column_profiles,
                "numeric_ratio": numeric_ratio,
                "skill_fields": skill_fields,
                "is_skoda_format": is_skoda,
                "ingested_at": datetime.utcnow().isoformat(),
            }
            response["metadata"] = metadata
            
            # Generate DQ report
            dq_report = {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "generated_at": datetime.utcnow().isoformat(),
                "is_skoda_format": is_skoda,
                **dq_metrics
            }
            dq_report_path = paths.processed_dir / f"{dataset_name}_dq_report.json"
            await save_json_async(dq_report_path, dq_report)
            response["dq_report_path"] = str(dq_report_path)
            
            # Generate summary
            summary = {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "row_count": row_count,
                "column_count": len(df.columns),
                "skill_fields": skill_fields,
                "is_skoda_format": is_skoda,
                "data_quality_score": 100 - int(sum(
                    v["percentage"] for v in dq_metrics.get("missing_values", {}).values()
                ) / max(len(dq_metrics.get("missing_values", {})), 1)),
                "generated_at": datetime.utcnow().isoformat(),
            }
            summary_path = paths.processed_dir / f"{dataset_name}_summary.json"
            await save_json_async(summary_path, summary)
            response["summary_path"] = str(summary_path)
        else:
            # Plain JSON - save as normalized text
            masked_text = mask_pii_text(json.dumps(data, indent=2))
            normalized_path = paths.normalized_dir / f"{dataset_name}.txt"
            import aiofiles
            async with aiofiles.open(normalized_path, "w", encoding="utf-8") as f:
                await f.write(masked_text)
            response["normalized_path"] = str(normalized_path)
            
            metadata = {
                "file_type": "json",
                "is_skoda_format": False,
                "ingested_at": datetime.utcnow().isoformat(),
            }
            response["metadata"] = metadata
            
    else:  # Text files
        raw_text = await read_text_async(file_path)
        masked_text = mask_pii_text(raw_text)
        
        normalized_path = paths.normalized_dir / f"{dataset_name}.txt"
        import aiofiles
        async with aiofiles.open(normalized_path, "w", encoding="utf-8") as f:
            await f.write(masked_text)
        response["normalized_path"] = str(normalized_path)
        
        metadata = {
            "file_type": "text",
            "text_length": len(masked_text),
            "is_skoda_format": False,
            "ingested_at": datetime.utcnow().isoformat(),
        }
        response["metadata"] = metadata

    ingestion_logger.info("Ingestion completed: dataset_id=%s is_skoda=%s", dataset_id, response.get("is_skoda_format"))
    return response


def list_datasets() -> List[Dict[str, Any]]:
    """List all ingested datasets (sync/async compatible)."""
    try:
        import asyncio
        loop = asyncio.get_running_loop()
        raise RuntimeError("Cannot call sync wrapper from async context - use await list_datasets_async()")
    except RuntimeError as e:
        if "Cannot call sync wrapper" in str(e):
            raise
        # No event loop running, run in sync mode
        import asyncio
        return asyncio.run(_list_datasets_async())


async def list_datasets_async() -> List[Dict[str, Any]]:
    """Async version of list_datasets - use this in async contexts."""
    return await _list_datasets_async()


async def _list_datasets_async() -> List[Dict[str, Any]]:
    """List all ingested datasets asynchronously."""
    datasets = []
    
    # Scan normalized directory
    for file_path in paths.normalized_dir.glob("*"):
        if file_path.is_file():
            dataset_name = file_path.stem
            summary_path = paths.processed_dir / f"{dataset_name}_summary.json"
            
            dataset_info = {
                "dataset_id": dataset_name,
                "filename": file_path.name,
                "normalized_path": str(file_path),
                "summary_path": str(summary_path) if summary_path.exists() else None,
            }
            
            if summary_path.exists():
                try:
                    summary = await read_json_async(summary_path)
                    dataset_info.update(summary)
                except Exception as e:
                    ingestion_logger.warning(f"Could not load summary for {dataset_name}: {e}")
            
            datasets.append(dataset_info)
    
    return datasets


def load_employees_from_dataset(
    dataset_path: Path,
    employee_id_column: str = "employee_id",
    department_column: str = "department",
    skills_column: Optional[str] = None,
    use_skoda_adapter: bool = False,
    supplemental_config: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Load employee records from an ingested dataset.
    
    Args:
        dataset_path: Path to normalized dataset CSV
        employee_id_column: Column name for employee ID
        department_column: Column name for department
        skills_column: Optional column name for skills
        use_skoda_adapter: Whether to use Škoda data adapter
    """
    if not dataset_path.exists():
        raise ValueError(f"Dataset not found: {dataset_path}")
    
    df = pd.read_csv(dataset_path, encoding="utf-8-sig")
    
    supplemental_config = supplemental_config or {}
    
    if use_skoda_adapter or detect_skoda_schema(df):
        adapter = SkodaDataAdapter()
        
        if supplemental_config.get("skill_mapping"):
            adapter.set_skill_mapping(supplemental_config["skill_mapping"])
        if supplemental_config.get("object_mapping"):
            adapter.set_object_mapping(supplemental_config["object_mapping"])
        if supplemental_config.get("org_hierarchy_lookup"):
            adapter.set_org_hierarchy_lookup(supplemental_config["org_hierarchy_lookup"])
        if supplemental_config.get("degreed_records"):
            adapter.set_degreed_records(supplemental_config["degreed_records"])
        if supplemental_config.get("external_qualifications"):
            adapter.set_external_qualifications(supplemental_config["external_qualifications"])
        employees = []
        
        for _, row in df.iterrows():
            try:
                employee_data = adapter.map_to_employee_record(row)
                employees.append(employee_data)
            except Exception as e:
                ingestion_logger.warning(f"Failed to map row: {e}")
                continue
        
        return employees
    
    # Legacy non-Škoda processing
    if not skills_column:
        skill_columns = detect_skill_fields(df)
        if skill_columns:
            skills_column = skill_columns[0]
    elif skills_column not in df.columns:
        skill_columns = detect_skill_fields(df)
        if skill_columns:
            skills_column = skill_columns[0]
        else:
            skills_column = None
    
    employees = []
    normalization_service = MultilingualNormalizationService()
    
    for _, row in df.iterrows():
        employee_id = str(row.get(employee_id_column, "")).strip()
        if not employee_id:
            continue
        
        department = str(row.get(department_column, "Unknown")).strip()
        
        skills: List[str] = []
        if skills_column and skills_column in df.columns:
            skill_value = row.get(skills_column)
            if pd.notna(skill_value):
                skill_str = str(skill_value).strip()
                if "," in skill_str:
                    skills = [s.strip() for s in skill_str.split(",") if s.strip()]
                elif ";" in skill_str:
                    skills = [s.strip() for s in skill_str.split(";") if s.strip()]
                elif isinstance(skill_value, list):
                    skills = [str(s).strip() for s in skill_value if s]
                else:
                    skills = [skill_str] if skill_str else []
        
        normalized_skills = [normalization_service.normalize_skill_name(skill) for skill in skills if skill]
        
        metadata: Dict[str, Any] = {}
        for col in df.columns:
            if col not in [employee_id_column, department_column, skills_column]:
                value = row.get(col)
                if pd.notna(value):
                    if pd.api.types.is_integer_dtype(df[col]):
                        metadata[str(col)] = int(value)
                    elif pd.api.types.is_float_dtype(df[col]):
                        metadata[str(col)] = float(value)
                    else:
                        metadata[str(col)] = str(value)
        
        employees.append({
            "employee_id": employee_id,
            "department": department,
            "skills": normalized_skills,
            "metadata": metadata,
        })
    
    return employees
