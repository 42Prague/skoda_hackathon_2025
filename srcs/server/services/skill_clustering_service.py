import os
import ast
import math
from typing import List, Dict, Any

import pandas as pd

from data_scripts.employee_skill_model import generate_employee_skill_positions

# Simple in-memory cache
_CLUST_CACHE: Dict[str, Any] = {}

DEFAULT_OUTPUT = "employee_skill_positions.csv"


class SkillClusteringService:
    """Wrapper around data_scripts.employee_skill_model for API consumption."""

    def __init__(
        self,
        degreed_path: str = "../data/Degreed.xlsx",
        sap_courses_path: str = "../data/ZHRPD_VZD_STA_007.xlsx",
        sap_quals_path: str = "../data/ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx",
        skill_map_path: str = "../data/skill_mapping_with_predicted_skills.csv",
        output_path: str = DEFAULT_OUTPUT,
        n_clusters: int = 10,
    ):
        self.degreed_path = degreed_path
        self.sap_courses_path = sap_courses_path
        self.sap_quals_path = sap_quals_path
        self.skill_map_path = skill_map_path
        self.output_path = output_path
        self.n_clusters = n_clusters

    # --------------------------- PUBLIC API ---------------------------
    def get_clustering_data(self, force_recompute: bool = False) -> List[Dict[str, Any]]:
        cache_key = f"data:{int(force_recompute)}"
        if not force_recompute and cache_key in _CLUST_CACHE:
            return _CLUST_CACHE[cache_key]

        if (not force_recompute) and os.path.exists(self.output_path):
            data = self._load_from_csv(self.output_path)
            _CLUST_CACHE[cache_key] = data
            return data

        data = self._compute_pipeline()
        _CLUST_CACHE[cache_key] = data
        return data

    # --------------------------- PIPELINE -----------------------------
    def _compute_pipeline(self) -> List[Dict[str, Any]]:
        self._ensure_skill_mapping_exists()
        self._validate_source_files()
        generate_employee_skill_positions(
            degreed_path=self.degreed_path,
            sap_courses_path=self.sap_courses_path,
            sap_quals_path=self.sap_quals_path,
            skill_map_path=self.skill_map_path,
            output_path=self.output_path,
            n_clusters=self.n_clusters,
        )
        return self._load_from_csv(self.output_path)

    # --------------------------- HELPERS -----------------------------
    def _ensure_skill_mapping_exists(self):
        if os.path.exists(self.skill_map_path):
            return
        try:
            from services.skill_mapping_service import skill_mapping_service

            skill_mapping_service.ensure_predicted_mapping(force=False)
        except Exception as exc:
            raise FileNotFoundError(
                f"Skill mapping predictions not found at {self.skill_map_path} and could not be generated automatically."
            ) from exc

    def _validate_source_files(self):
        missing = [
            path
            for path in [
                self.degreed_path,
                self.sap_courses_path,
                self.sap_quals_path,
                self.skill_map_path,
            ]
            if not os.path.exists(path)
        ]
        if missing:
            raise FileNotFoundError(
                "Missing required data files for clustering: " + ", ".join(missing)
            )

    @staticmethod
    def _parse_list_cell(cell):
        if isinstance(cell, list):
            return cell
        if cell is None:
            return []
        if isinstance(cell, float):
            if math.isnan(cell):
                return []
        try:
            parsed = ast.literal_eval(str(cell))
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

    def _load_from_csv(self, path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(path):
            return []
        try:
            df = pd.read_csv(path)
        except Exception as exc:
            print(f"[SkillClusteringService] Failed to read {path}: {exc}")
            return []

        results = []
        for _, r in df.iterrows():
            parsed_top = self._parse_list_cell(r.get("top_skills_tfidf"))
            results.append(
                {
                    "employee_id": str(r.get("employee_id")),
                    "skill": str(r.get("skill", "")),
                    "skill_sentence": str(r.get("skill_sentence", r.get("skill", ""))),
                    "x": float(r.get("x", 0.0)),
                    "y": float(r.get("y", 0.0)),
                    "cluster_kmeans": int(r.get("cluster_kmeans", 0)),
                    "top_skills_tfidf": parsed_top,
                    "top_skills": parsed_top,
                }
            )
        return results


# Module-level instance
skill_clustering_service = SkillClusteringService()
