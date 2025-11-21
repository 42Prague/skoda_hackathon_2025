"""Configuration settings for the skills taxonomy system."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenRouter Configuration
    openrouter_api_key: str = Field(..., description="OpenRouter API key")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter base URL"
    )
    openrouter_model: str = Field(
        default="google/gemini-2.5-flash-exp:free",
        description="Model to use for extraction"
    )

    # Neo4j Configuration
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="skillspassword", description="Neo4j password")
    neo4j_database: str = Field(default="neo4j", description="Neo4j database name")

    # LLM Extraction Settings
    llm_batch_size: int = Field(default=50, description="Number of jobs per batch")
    llm_max_concurrent: int = Field(default=50, description="Max concurrent LLM requests")
    llm_timeout: int = Field(default=30, description="LLM request timeout in seconds")
    llm_max_retries: int = Field(default=3, description="Max retries for failed requests")

    # Skill Normalization Settings
    clustering_eps: float = Field(default=0.15, description="DBSCAN epsilon parameter")
    clustering_min_samples: int = Field(default=2, description="DBSCAN min_samples parameter")
    semantic_similarity_threshold: float = Field(
        default=0.85,
        description="Minimum similarity for semantic matching"
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-mpnet-base-v2",
        description="Sentence transformer model for embeddings"
    )

    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8002, description="API port")
    api_workers: int = Field(default=4, description="Number of API workers")

    # Data Settings
    data_dir: Path = Field(default=Path("./data"), description="Data directory")
    checkpoint_dir: Path = Field(
        default=Path("./data/checkpoints"),
        description="Checkpoint directory"
    )
    cache_dir: Path = Field(default=Path("./data/cache"), description="Cache directory")

    def __init__(self, **kwargs):
        """Initialize settings and create necessary directories."""
        super().__init__(**kwargs)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
