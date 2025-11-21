"""
Advanced Data Quality Metrics Service
--------------------------------------
Upgraded DQ engine with correlation matrix, outlier detection,
anomaly detection (LLM-powered), duplicate detection, and
inconsistent skill naming detection (AI-assisted).
"""

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
try:
    from scipy.stats import zscore
except ImportError:
    # Fallback if scipy is not available
    def zscore(series):
        mean = series.mean()
        std = series.std()
        if std == 0:
            return pd.Series([0] * len(series), index=series.index)
        return (series - mean) / std

from swx_api.app.services.ingestion_service import paths, compute_data_quality_metrics
from swx_api.app.services.llm_client import LLMClient, LLMConfig
from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("advanced_dq")


class AdvancedDQService:
    """Advanced data quality service with AI-powered analysis."""
    
    def __init__(self):
        self.llm_config = LLMConfig.from_env()
        self.llm_client = LLMClient(self.llm_config)
        self.processed_dir = paths.processed_dir
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    async def compute_advanced_dq_metrics(
        self,
        df: pd.DataFrame,
        dataset_id: str,
        dataset_name: str
    ) -> Dict[str, Any]:
        """
        Compute advanced data quality metrics.
        
        Args:
            df: DataFrame to analyze
            dataset_id: Dataset identifier
            dataset_name: Dataset name
            
        Returns:
            Dictionary with advanced DQ metrics
        """
        try:
            # Base metrics
            base_metrics = compute_data_quality_metrics(df)
            
            # Advanced metrics
            correlation_matrix = self._compute_correlation_matrix(df)
            outlier_detection = self._detect_outliers_advanced(df)
            anomaly_detection = await self._detect_anomalies_ai(df)
            duplicate_detection = self._detect_duplicates(df)
            inconsistent_naming = await self._detect_inconsistent_naming(df)
            
            # Combine all metrics
            advanced_metrics = {
                **base_metrics,
                "correlation_matrix": correlation_matrix,
                "outlier_detection": outlier_detection,
                "anomaly_detection": anomaly_detection,
                "duplicate_detection": duplicate_detection,
                "inconsistent_naming": inconsistent_naming,
                "dq_score": self._calculate_overall_dq_score(
                    base_metrics,
                    outlier_detection,
                    duplicate_detection,
                    inconsistent_naming
                )
            }
            
            # Save report (async)
            await self._save_dq_report(advanced_metrics, dataset_id, dataset_name)
            
            return advanced_metrics
            
        except Exception as e:
            logger.error(f"Error computing advanced DQ metrics: {e}", exc_info=True)
            # Fallback to base metrics
            return compute_data_quality_metrics(df)
    
    def _compute_correlation_matrix(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute correlation matrix for numeric columns."""
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        
        if len(numeric_cols) < 2:
            return {
                "available": False,
                "reason": "Insufficient numeric columns for correlation analysis"
            }
        
        try:
            corr_df = df[numeric_cols].corr()
            
            # Find strong correlations (|r| > 0.7)
            strong_correlations = []
            for i, col1 in enumerate(corr_df.columns):
                for col2 in corr_df.columns[i+1:]:
                    corr_value = corr_df.loc[col1, col2]
                    if abs(corr_value) > 0.7:
                        strong_correlations.append({
                            "column1": col1,
                            "column2": col2,
                            "correlation": round(float(corr_value), 3),
                            "strength": "strong" if abs(corr_value) > 0.9 else "moderate"
                        })
            
            return {
                "available": True,
                "matrix": corr_df.to_dict(),
                "strong_correlations": strong_correlations,
                "numeric_columns": numeric_cols
            }
        except Exception as e:
            logger.warning(f"Error computing correlation matrix: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    def _detect_outliers_advanced(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Advanced outlier detection using multiple methods."""
        outliers = {}
        
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                series = df[col].dropna()
                if len(series) < 3:
                    continue
                
                # Method 1: IQR (already in base)
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                if IQR > 0:
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    iqr_outliers = ((series < lower_bound) | (series > upper_bound)).sum()
                else:
                    iqr_outliers = 0
                
                # Method 2: Z-score (|z| > 3)
                z_scores = zscore(series)
                z_outliers = (abs(z_scores) > 3).sum()
                
                # Method 3: Modified Z-score (MAD)
                median = series.median()
                mad = (series - median).abs().median()
                if mad > 0:
                    modified_z = 0.6745 * (series - median) / mad
                    mad_outliers = (abs(modified_z) > 3.5).sum()
                else:
                    mad_outliers = 0
                
                if iqr_outliers > 0 or z_outliers > 0 or mad_outliers > 0:
                    outliers[str(col)] = {
                        "iqr_outliers": int(iqr_outliers),
                        "z_score_outliers": int(z_outliers),
                        "mad_outliers": int(mad_outliers),
                        "total_unique_outliers": int(len(set(
                            series[(series < lower_bound) | (series > upper_bound)].index.tolist() +
                            series[abs(z_scores) > 3].index.tolist()
                        ))),
                        "outlier_percentage": round(
                            max(iqr_outliers, z_outliers, mad_outliers) / len(series) * 100, 2
                        )
                    }
        
        return {
            "outliers_by_column": outliers,
            "total_columns_with_outliers": len(outliers),
            "detection_methods": ["IQR", "Z-score", "MAD"]
        }
    
    async def _detect_anomalies_ai(self, df: pd.DataFrame) -> Dict[str, Any]:
        """AI-powered anomaly detection with async support."""
        try:
            # Sample data for AI analysis (limit to avoid token limits)
            sample_size = min(100, len(df))
            sample_df = df.head(sample_size)
            
            # Prepare summary for AI
            summary = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "sample_data_types": {col: str(df[col].dtype) for col in df.columns},
                "missing_value_summary": {
                    col: int(df[col].isnull().sum()) for col in df.columns
                }
            }
            
            prompt = f"""Analyze this dataset for anomalies and data quality issues.

Dataset Summary:
{json.dumps(summary, indent=2)}

Sample Data (first {sample_size} rows):
{sample_df.head(10).to_string()}

Identify:
1. Anomalous patterns
2. Data inconsistencies
3. Unusual value distributions
4. Potential data quality issues

Provide JSON response:
{{
  "anomalies": [
    {{
      "type": "anomaly type",
      "column": "column name",
      "description": "description",
      "severity": "high|medium|low",
      "recommendation": "how to fix"
    }}
  ],
  "data_quality_issues": ["issue 1", "issue 2"],
  "overall_assessment": "brief assessment"
}}

Response (JSON only):"""
            
            schema = {
                "anomalies": list,
                "data_quality_issues": list,
                "overall_assessment": str
            }
            
            # Use async LLM client
            async with LLMClient(self.llm_config) as llm:
                result = await llm.call_llm(
                    prompt=prompt,
                    schema=schema,
                    system_message="You are an expert data quality analyst. Always respond with valid JSON only.",
                    temperature=0.5,
                    max_tokens=2000
                )
            
            return result
        except Exception as e:
            logger.warning(f"AI anomaly detection failed: {e}")
        
        # Fallback
        return {
            "anomalies": [],
            "data_quality_issues": ["AI analysis unavailable"],
            "overall_assessment": "Manual review recommended"
        }
    
    def _detect_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect duplicate rows and near-duplicates."""
        # Exact duplicates
        exact_duplicates = df.duplicated().sum()
        exact_duplicate_rows = df[df.duplicated(keep=False)]
        
        # Near-duplicates (based on key columns)
        # Try to identify key columns (non-null, high uniqueness)
        key_columns = []
        for col in df.columns:
            null_ratio = df[col].isnull().sum() / len(df)
            unique_ratio = df[col].nunique() / len(df)
            if null_ratio < 0.5 and unique_ratio > 0.1:
                key_columns.append(col)
        
        near_duplicates = 0
        if key_columns:
            near_duplicates = df.duplicated(subset=key_columns).sum()
        
        return {
            "exact_duplicates": int(exact_duplicates),
            "exact_duplicate_percentage": round(exact_duplicates / len(df) * 100, 2) if len(df) > 0 else 0,
            "near_duplicates": int(near_duplicates),
            "near_duplicate_percentage": round(near_duplicates / len(df) * 100, 2) if len(df) > 0 else 0,
            "key_columns_used": key_columns[:5],
            "duplicate_rows_sample": exact_duplicate_rows.head(5).to_dict("records") if len(exact_duplicate_rows) > 0 else []
        }
    
    async def _detect_inconsistent_naming(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect inconsistent skill naming using async AI."""
        try:
            # Find skill-related columns
            skill_keywords = ["skill", "competenc", "ability", "expertise"]
            skill_columns = [
                col for col in df.columns
                if any(kw in str(col).lower() for kw in skill_keywords)
            ]
            
            if not skill_columns:
                return {
                    "available": False,
                    "reason": "No skill-related columns found"
                }
            
            # Collect all skill values
            all_skills = []
            for col in skill_columns:
                values = df[col].dropna().astype(str).tolist()
                all_skills.extend(values)
            
            # Get unique skills (sample if too many)
            unique_skills = list(set(all_skills))[:100]  # Limit to 100 for AI
            
            if not unique_skills:
                return {
                    "available": False,
                    "reason": "No skill values found"
                }
            
            prompt = f"""Analyze these skill names for inconsistencies and normalization opportunities.

Skills to analyze ({len(unique_skills)} unique):
{', '.join(unique_skills[:50])}

Identify:
1. Duplicate skills with different names (e.g., "Python" vs "python" vs "Python Programming")
2. Inconsistent naming patterns
3. Skills that should be normalized/merged
4. Naming conventions to recommend

Provide JSON response:
{{
  "inconsistencies": [
    {{
      "type": "case_variation|synonym|abbreviation",
      "variations": ["skill1", "skill2"],
      "recommended_normalized": "normalized name",
      "confidence": 0.9
    }}
  ],
  "naming_patterns": ["pattern 1", "pattern 2"],
  "recommendations": ["recommendation 1", "recommendation 2"]
}}

Response (JSON only):"""
            
            schema = {
                "inconsistencies": list,
                "naming_patterns": list,
                "recommendations": list
            }
            
            # Use async LLM client
            async with LLMClient(self.llm_config) as llm:
                result = await llm.call_llm(
                    prompt=prompt,
                    schema=schema,
                    system_message="You are an expert in data normalization and skill taxonomy. Always respond with valid JSON only.",
                    temperature=0.3,
                    max_tokens=2000
                )
            
            return {
                "available": True,
                **result
            }
        except Exception as e:
            logger.warning(f"AI naming detection failed: {e}")
        
        # Fallback: simple case-insensitive detection
        skill_counter = Counter([s.lower() for s in all_skills])
        unique_skills = list(set(all_skills))
        case_variations = {
            skill: [s for s in unique_skills if s.lower() == skill]
            for skill in skill_counter.keys()
            if len([s for s in unique_skills if s.lower() == skill]) > 1
        }
        
        return {
            "available": True,
            "inconsistencies": [
                {
                    "type": "case_variation",
                    "variations": variations,
                    "recommended_normalized": variations[0],
                    "confidence": 0.7
                }
                for variations in case_variations.values()[:10]
            ],
            "naming_patterns": ["Case variations detected"],
            "recommendations": ["Normalize skill names to consistent case"]
        }
    
    def _calculate_overall_dq_score(
        self,
        base_metrics: Dict[str, Any],
        outlier_detection: Dict[str, Any],
        duplicate_detection: Dict[str, Any],
        inconsistent_naming: Dict[str, Any]
    ) -> int:
        """Calculate overall data quality score (0-100)."""
        score = 100
        
        # Deduct for missing values
        missing_values = base_metrics.get("missing_values", {})
        if missing_values:
            avg_missing = sum(v.get("percentage", 0) for v in missing_values.values()) / len(missing_values)
            score -= min(30, avg_missing * 0.3)
        
        # Deduct for outliers
        outliers = outlier_detection.get("outliers_by_column", {})
        if outliers:
            total_outlier_pct = sum(
                v.get("outlier_percentage", 0) for v in outliers.values()
            ) / len(outliers)
            score -= min(20, total_outlier_pct * 0.2)
        
        # Deduct for duplicates
        duplicate_pct = duplicate_detection.get("exact_duplicate_percentage", 0)
        score -= min(25, duplicate_pct * 0.25)
        
        # Deduct for inconsistent naming
        if inconsistent_naming.get("available") and inconsistent_naming.get("inconsistencies"):
            inconsistency_count = len(inconsistent_naming["inconsistencies"])
            score -= min(15, inconsistency_count * 1.5)
        
        return max(0, int(round(score)))
    
    async def _save_dq_report(
        self,
        metrics: Dict[str, Any],
        dataset_id: str,
        dataset_name: str
    ) -> Path:
        """Save advanced DQ report to file (async)."""
        import aiofiles
        
        dq_dir = self.processed_dir / "dq"
        dq_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = dq_dir / f"{dataset_name}_advanced_dq_report.json"
        
        async with aiofiles.open(report_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(metrics, ensure_ascii=False, indent=2))
        
        logger.info(f"Saved advanced DQ report to {report_path}")
        return report_path

