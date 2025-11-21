"""
Auto-Data-Repair Suggestions (AI-Powered)
------------------------------------------
Identifies anomalies, proposes fixes, normalizes broken skill names,
detects impossible values, and generates JSON patch plans.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from swx_api.app.services.llm_client import LLMClient, LLMConfig
from swx_api.app.services.data_quality_service import AdvancedDQService
from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("data_repair")


class DataRepairService:
    """Service for identifying and proposing data repairs."""
    
    def __init__(self):
        self.llm_config = LLMConfig.from_env()
        self.llm_client = LLMClient(self.llm_config)
        self.dq_service = AdvancedDQService()
    
    async def analyze_and_propose_repairs(
        self,
        df: pd.DataFrame,
        dataset_id: str,
        dataset_name: str
    ) -> Dict[str, Any]:
        """
        Analyze data and propose repair suggestions.
        
        Args:
            df: DataFrame to analyze
            dataset_id: Dataset identifier
            dataset_name: Dataset name
            
        Returns:
            Dictionary with:
            - anomalies: List of detected anomalies
            - proposed_fixes: List of proposed fixes
            - normalization_suggestions: Skill name normalization suggestions
            - impossible_values: Detected impossible values
            - patch_plan: JSON patch plan for repairs
        """
        try:
            # Run advanced DQ analysis (async)
            dq_metrics = await self.dq_service.compute_advanced_dq_metrics(df, dataset_id, dataset_name)
            
            # Identify anomalies
            anomalies = self._identify_anomalies(df, dq_metrics)
            
            # Propose fixes
            proposed_fixes = self._propose_fixes(anomalies, df)
            
            # Normalize skill names
            normalization_suggestions = self._normalize_skill_names(df, dq_metrics)
            
            # Detect impossible values
            impossible_values = self._detect_impossible_values(df)
            
            # Generate patch plan
            patch_plan = self._generate_patch_plan(
                proposed_fixes,
                normalization_suggestions,
                impossible_values
            )
            
            return {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "anomalies": anomalies,
                "proposed_fixes": proposed_fixes,
                "normalization_suggestions": normalization_suggestions,
                "impossible_values": impossible_values,
                "patch_plan": patch_plan,
                "repair_priority": self._calculate_repair_priority(anomalies, impossible_values),
                "analyzed_at": json.dumps({"$date": None}),
            }
            
        except Exception as e:
            logger.error(f"Error analyzing data repairs: {e}", exc_info=True)
            return {
                "dataset_id": dataset_id,
                "error": str(e),
                "anomalies": [],
                "proposed_fixes": [],
                "patch_plan": []
            }
    
    def _identify_anomalies(
        self,
        df: pd.DataFrame,
        dq_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify anomalies in the data."""
        anomalies = []
        
        # From DQ metrics
        ai_anomalies = dq_metrics.get("anomaly_detection", {}).get("anomalies", [])
        anomalies.extend(ai_anomalies)
        
        # Outlier-based anomalies
        outliers = dq_metrics.get("outlier_detection", {}).get("outliers_by_column", {})
        for col, outlier_info in outliers.items():
            if outlier_info.get("outlier_percentage", 0) > 10:
                anomalies.append({
                    "type": "outlier",
                    "column": col,
                    "description": f"High percentage of outliers: {outlier_info['outlier_percentage']}%",
                    "severity": "high" if outlier_info["outlier_percentage"] > 20 else "medium",
                    "recommendation": "Review and validate outlier values"
                })
        
        # Duplicate-based anomalies
        duplicates = dq_metrics.get("duplicate_detection", {})
        if duplicates.get("exact_duplicate_percentage", 0) > 5:
            anomalies.append({
                "type": "duplicate",
                "column": "all",
                "description": f"High duplicate rate: {duplicates['exact_duplicate_percentage']}%",
                "severity": "medium",
                "recommendation": "Remove or merge duplicate rows"
            })
        
        return anomalies
    
    def _propose_fixes(
        self,
        anomalies: List[Dict[str, Any]],
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Propose fixes for identified anomalies."""
        fixes = []
        
        for anomaly in anomalies:
            fix = {
                "anomaly_id": f"anomaly_{len(fixes)}",
                "anomaly_type": anomaly.get("type"),
                "column": anomaly.get("column"),
                "description": anomaly.get("description"),
                "proposed_action": self._determine_fix_action(anomaly, df),
                "estimated_impact": "low" if anomaly.get("severity") == "low" else "medium",
                "confidence": 0.8
            }
            fixes.append(fix)
        
        return fixes
    
    def _determine_fix_action(
        self,
        anomaly: Dict[str, Any],
        df: pd.DataFrame
    ) -> str:
        """Determine appropriate fix action for an anomaly."""
        anomaly_type = anomaly.get("type")
        column = anomaly.get("column")
        
        if anomaly_type == "outlier":
            return f"Review and validate values in column '{column}', consider removing or correcting outliers"
        elif anomaly_type == "duplicate":
            return "Remove duplicate rows or merge them based on business rules"
        elif anomaly_type == "missing":
            return f"Fill missing values in column '{column}' using appropriate method (mean, median, mode, or business logic)"
        elif anomaly_type == "inconsistent":
            return f"Normalize inconsistent values in column '{column}' to standard format"
        else:
            return "Review and correct based on business rules"
    
    def _normalize_skill_names(
        self,
        df: pd.DataFrame,
        dq_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate skill name normalization suggestions."""
        inconsistent_naming = dq_metrics.get("inconsistent_naming", {})
        
        if not inconsistent_naming.get("available"):
            return []
        
        inconsistencies = inconsistent_naming.get("inconsistencies", [])
        
        suggestions = []
        for inconsistency in inconsistencies:
            variations = inconsistency.get("variations", [])
            recommended = inconsistency.get("recommended_normalized", variations[0] if variations else "")
            
            suggestions.append({
                "variations": variations,
                "recommended_normalized": recommended,
                "confidence": inconsistency.get("confidence", 0.7),
                "action": f"Normalize all variations to '{recommended}'"
            })
        
        return suggestions
    
    def _detect_impossible_values(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect impossible or invalid values."""
        impossible = []
        
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                series = df[col].dropna()
                
                # Check for negative values where they shouldn't exist
                if "age" in col.lower() or "years" in col.lower():
                    negative = series[series < 0]
                    if len(negative) > 0:
                        impossible.append({
                            "column": col,
                            "value_type": "negative_age",
                            "invalid_values": negative.tolist()[:10],
                            "count": len(negative),
                            "description": f"Negative values in {col} column",
                            "recommendation": "Remove or correct negative values"
                        })
                
                # Check for values exceeding reasonable limits
                if "level" in col.lower() or "score" in col.lower():
                    # Assume max level/score is 10
                    exceeded = series[series > 10]
                    if len(exceeded) > 0:
                        impossible.append({
                            "column": col,
                            "value_type": "exceeds_max",
                            "invalid_values": exceeded.tolist()[:10],
                            "count": len(exceeded),
                            "description": f"Values exceeding maximum (10) in {col}",
                            "recommendation": "Cap values at maximum or correct data entry errors"
                        })
        
        return impossible
    
    def _generate_patch_plan(
        self,
        proposed_fixes: List[Dict[str, Any]],
        normalization_suggestions: List[Dict[str, Any]],
        impossible_values: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate JSON patch plan for repairs."""
        patch_plan = []
        
        # Add normalization patches
        for norm in normalization_suggestions:
            variations = norm.get("variations", [])
            recommended = norm.get("recommended_normalized", "")
            
            for variation in variations:
                patch_plan.append({
                    "op": "replace",
                    "path": f"/skills/{variation}",
                    "value": recommended,
                    "description": f"Normalize '{variation}' to '{recommended}'"
                })
        
        # Add impossible value fixes
        for impossible in impossible_values:
            column = impossible.get("column")
            invalid_values = impossible.get("invalid_values", [])
            
            for value in invalid_values[:5]:  # Limit to first 5
                patch_plan.append({
                    "op": "remove" if impossible.get("value_type") == "negative_age" else "replace",
                    "path": f"/{column}/{value}",
                    "value": None if impossible.get("value_type") == "negative_age" else 0,
                    "description": impossible.get("recommendation", "Fix impossible value")
                })
        
        return patch_plan
    
    def _calculate_repair_priority(
        self,
        anomalies: List[Dict[str, Any]],
        impossible_values: List[Dict[str, Any]]
    ) -> str:
        """Calculate overall repair priority."""
        high_severity_count = sum(
            1 for a in anomalies if a.get("severity") == "high"
        )
        
        if high_severity_count > 5 or len(impossible_values) > 10:
            return "high"
        elif high_severity_count > 0 or len(impossible_values) > 0:
            return "medium"
        else:
            return "low"

