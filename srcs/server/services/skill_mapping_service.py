import os
from typing import Dict, Any

# from data_scripts.skill_model import generate_skill_mapping_predictions

DEFAULT_DEGREE_PATH = "../data/degree_content_catalog.xlsx"
DEFAULT_SKILL_MAP_SOURCE = "../data/skill_mapping.xlsx"
DEFAULT_SKILL_MAP_PREDICTED = "skill_mapping_with_predicted_skills.csv"


class SkillMappingService:
    """Thin wrapper that triggers data_scripts.skill_model pipeline."""

    def __init__(
        self,
        degree_catalog_path: str = DEFAULT_DEGREE_PATH,
        skill_mapping_source_path: str = DEFAULT_SKILL_MAP_SOURCE,
        predicted_output_path: str = DEFAULT_SKILL_MAP_PREDICTED,
        model_name: str = "all-MiniLM-L6-v2",
        top_n: int = 5,
    ):
        self.degree_catalog_path = degree_catalog_path
        self.skill_mapping_source_path = skill_mapping_source_path
        self.predicted_output_path = predicted_output_path
        self.model_name = model_name
        self.top_n = top_n

    # ---------------- PUBLIC API ----------------
    def ensure_predicted_mapping(self, force: bool = False) -> str:
        """Guarantee the predicted skill mapping CSV exists. Returns path."""
        if (not force) and os.path.exists(self.predicted_output_path):
            return self.predicted_output_path
        self._generate_predicted_skills()
        return self.predicted_output_path

    def get_status(self) -> Dict[str, Any]:
        return {
            "degree_catalog_path": self.degree_catalog_path,
            "skill_mapping_source_path": self.skill_mapping_source_path,
            "predicted_output_path": self.predicted_output_path,
            "predicted_exists": os.path.exists(self.predicted_output_path),
        }

    # --------------- INTERNAL STEPS ---------------
    def _generate_predicted_skills(self):
        out_dir = os.path.dirname(self.predicted_output_path)
        if out_dir and out_dir not in ("", "."):
            os.makedirs(out_dir, exist_ok=True)
        # generate_skill_mapping_predictions(
        #     degree_catalog_path=self.degree_catalog_path,
        #     skill_mapping_source_path=self.skill_mapping_source_path,
        #     output_path=self.predicted_output_path,
        #     model_name=self.model_name,
        #     top_n=self.top_n,
        # )


skill_mapping_service = SkillMappingService()