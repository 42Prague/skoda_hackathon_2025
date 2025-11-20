"""
Configuration module for Škoda AI Skill Coach.
Uses Pydantic BaseSettings for type-safe environment variable management.
All paths point to the persistent volume mount for Azure Container Apps compatibility.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    IMPORTANT: All data/model/state paths MUST reside under /app/persistent_data/
    for Azure Container Apps compatibility (ephemeral root filesystem).
    """

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Persistent volume root (Azure Files/Disk mount point)
    persistent_root: Path = Field(
        default="/app/persistent_data",
        env="PERSISTENT_ROOT"
    )

    # Data directories
    raw_xlsx_dir: Path = Field(
        default="/app/persistent_data/raw_xlsx",
        env="RAW_XLSX_DIR",
        description="Directory containing input Excel files (read-only)"
    )

    clean_parquet_dir: Path = Field(
        default="/app/persistent_data/clean_parquet",
        env="CLEAN_PARQUET_DIR",
        description="Directory for cleaned Parquet output"
    )

    models_dir: Path = Field(
        default="/app/persistent_data/models",
        env="MODELS_DIR",
        description="Directory containing local LLM and embedding models"
    )

    graph_state_path: Path = Field(
        default="/app/persistent_data/state/skill_graph.pkl",
        env="GRAPH_STATE_PATH",
        description="Path to serialized skill graph state"
    )

    # Skill_mapping.xlsx sheet names (USER: adjust these if your Excel has different sheet names)
    skill_mapping_sheet_name: str = Field(
        default="Mapping",
        env="SKILL_MAPPING_SHEET",
        description="Sheet name for course->skill mapping in Skill_mapping.xlsx"
    )

    skill_mapping_skills_sheet: str = Field(
        default="Skills",
        env="SKILL_MAPPING_SKILLS_SHEET",
        description="Sheet name for skills catalog in Skill_mapping.xlsx"
    )

    skill_mapping_elearning_sheet: str = Field(
        default="eLearnings",
        env="SKILL_MAPPING_ELEARNING_SHEET",
        description="Sheet name for eLearning courses in Skill_mapping.xlsx"
    )

    skill_mapping_courses_sheet: str = Field(
        default="Kurzy_kompetence",
        env="SKILL_MAPPING_COURSES_SHEET",
        description="Sheet name for course competencies in Skill_mapping.xlsx"
    )

    # Hosted LLM API configuration
    llm_api_url: str = Field(
        default="https://api.example.com/v1/chat/completions",
        env="LLM_API_URL",
        description="URL for hosted LLM API endpoint"
    )

    llm_api_key: str = Field(
        default="",
        env="LLM_API_KEY",
        description="API key for hosted LLM service"
    )

    llm_api_version: str = Field(
        default="2024-02-15-preview",
        env="LLM_API_VERSION",
        description="API version for hosted LLM service (e.g., Azure OpenAI API version)"
    )

    llm_model_name: str = Field(
        default="gpt-3.5-turbo",
        env="LLM_MODEL_NAME",
        description="Model name/deployment name for hosted LLM"
    )

    # LLM inference parameters
    llm_context_size: int = Field(default=4096, env="LLM_CONTEXT_SIZE")
    llm_max_tokens: int = Field(default=512, env="LLM_MAX_TOKENS")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")

    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        # Create directories
        for path in [self.raw_xlsx_dir, self.clean_parquet_dir, self.models_dir]:
            path.mkdir(parents=True, exist_ok=True)

        # Create parent directory for state file
        self.graph_state_path.parent.mkdir(parents=True, exist_ok=True)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = Settings()
# Ensure directories exist on import
settings.ensure_directories()
