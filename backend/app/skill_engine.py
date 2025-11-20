"""
Skill Engine for Semantic Search over Skills and Content.

IMPORTANT: This module does NOT download models at runtime.
All models must be pre-placed in MODELS_DIR by the user.

USER ACTIONS REQUIRED:
1. Download a compatible embedding model (GGUF format or compatible with llama-cpp-python)
2. Place it in /app/persistent_data/models/
3. Set EMBEDDING_MODEL_FILENAME in config.py

For simplicity, this implementation uses a basic approach.
For production, consider using a proper embedding model via llama-cpp-python
or implement a custom TF-IDF based solution.
"""

import logging
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd
from config import settings

logger = logging.getLogger(__name__)


class SkillEngine:
    """
    Engine for semantic search over skills and content.
    
    This is a simplified implementation that uses basic text similarity.
    For production with actual models, integrate llama-cpp-python embeddings.
    """
    
    def __init__(self):
        """Initialize the skill engine."""
        self.skills_data: Optional[pd.DataFrame] = None
        self.content_data: Optional[pd.DataFrame] = None
        self.embeddings: Optional[np.ndarray] = None
        self.embedding_model = None
        
        logger.info("Initialized SkillEngine")
    
    def check_model_availability(self):
        """
        Check if required embedding model files exist.
        
        Raises RuntimeError if models are not found.
        """
        model_path = settings.embedding_model_path
        
        if not model_path.exists():
            error_msg = (
                f"Embedding model not found at {model_path}\n\n"
                f"USER ACTION REQUIRED:\n"
                f"1. Download a compatible embedding model (GGUF format)\n"
                f"2. Place it in {settings.models_dir}/\n"
                f"3. Update EMBEDDING_MODEL_FILENAME in config.py\n\n"
                f"Example models (MIT/BSD licensed):\n"
                f"- Use llama-cpp-python compatible GGUF models\n"
                f"- Or implement TF-IDF based similarity (no model needed)\n"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info(f"Embedding model found at {model_path}")
    
    def load_embedding_model(self):
        """
        Load embedding model from MODELS_DIR.
        
        USER: Implement actual model loading here based on your chosen model.
        This is a placeholder that checks for model existence.
        """
        self.check_model_availability()
        
        # Placeholder: In production, load the actual model
        # Example with llama-cpp-python:
        # from llama_cpp import Llama
        # self.embedding_model = Llama(
        #     model_path=str(settings.embedding_model_path),
        #     embedding=True
        # )
        
        logger.info("Embedding model loaded (placeholder)")
    
    def load_skills_data(self):
        """Load skills dictionary from Parquet."""
        skills_path = settings.clean_parquet_dir / "skill_dictionary.parquet"
        
        if not skills_path.exists():
            logger.warning(f"Skills dictionary not found at {skills_path}")
            return
        
        self.skills_data = pd.read_parquet(skills_path)
        logger.info(f"Loaded {len(self.skills_data)} skills")
    
    def load_content_data(self):
        """Load content catalog (Degreed or course data) from Parquet."""
        # Try Degreed content first
        degreed_path = settings.clean_parquet_dir / "degreed_content.parquet"
        if degreed_path.exists():
            self.content_data = pd.read_parquet(degreed_path)
            logger.info(f"Loaded {len(self.content_data)} Degreed content items")
            return
        
        # Fallback to course data
        course_path = settings.clean_parquet_dir / "course_participation.parquet"
        if course_path.exists():
            self.content_data = pd.read_parquet(course_path)
            logger.info(f"Loaded {len(self.content_data)} course items")
            return
        
        logger.warning("No content data found")
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for texts.
        
        USER: Implement actual embedding logic here.
        This is a placeholder using simple hash-based vectors.
        """
        if self.embedding_model is None:
            # Fallback: Use simple bag-of-words style representation
            # This is NOT semantic but allows the system to run without models
            logger.warning("Using fallback text representation (no semantic understanding)")
            
            # Simple character-based hash for demonstration
            # In production, use actual embeddings
            vectors = []
            for text in texts:
                if pd.isna(text):
                    text = ""
                # Create a simple vector based on text characteristics
                vector = np.array([
                    len(text),
                    text.lower().count('a'),
                    text.lower().count('e'),
                    text.lower().count('i'),
                    text.lower().count('o'),
                    text.lower().count('u'),
                    len(text.split()),
                    hash(text.lower()) % 100
                ], dtype=np.float32)
                vectors.append(vector)
            
            return np.array(vectors)
        
        # Actual model inference would go here
        # Example with llama-cpp-python:
        # embeddings = []
        # for text in texts:
        #     embedding = self.embedding_model.embed(text)
        #     embeddings.append(embedding)
        # return np.array(embeddings)
        
        raise NotImplementedError("Actual embedding model inference not implemented")
    
    def build_skill_index(self):
        """Build vector index for skills."""
        if self.skills_data is None:
            logger.warning("No skills data loaded, cannot build index")
            return
        
        # Combine name and description for richer embeddings
        texts = []
        for _, row in self.skills_data.iterrows():
            name = row.get('name', '')
            description = row.get('description', '')
            text = f"{name} {description}".strip()
            texts.append(text)
        
        self.embeddings = self.embed_texts(texts)
        logger.info(f"Built skill index with {len(self.embeddings)} vectors")
    
    def search_similar_skills(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for skills similar to the query.
        
        Returns list of dicts with: skill_id, name, description, similarity_score
        """
        if self.skills_data is None or self.embeddings is None:
            logger.warning("Skills index not built, cannot search")
            return []
        
        # Embed query
        query_vector = self.embed_texts([query])[0]
        
        # Compute cosine similarity
        # Simple dot product for demonstration (assumes normalized vectors)
        similarities = []
        for i, skill_vector in enumerate(self.embeddings):
            # Cosine similarity
            dot_product = np.dot(query_vector, skill_vector)
            norm_product = np.linalg.norm(query_vector) * np.linalg.norm(skill_vector)
            if norm_product > 0:
                similarity = dot_product / norm_product
            else:
                similarity = 0.0
            similarities.append((i, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top k
        results = []
        for idx, score in similarities[:top_k]:
            row = self.skills_data.iloc[idx]
            results.append({
                'skill_id': row.get('skillid'),
                'name': row.get('name'),
                'description': row.get('description'),
                'similarity_score': float(score)
            })
        
        return results
    
    def save_index(self, path: Optional[Path] = None):
        """Save the embeddings index to disk."""
        if path is None:
            path = settings.graph_state_path.parent / "skill_index.pkl"
        
        if self.embeddings is None:
            logger.warning("No index to save")
            return
        
        with open(path, 'wb') as f:
            pickle.dump({
                'embeddings': self.embeddings,
                'skills_data': self.skills_data
            }, f)
        
        logger.info(f"Saved skill index to {path}")
    
    @classmethod
    def load_index(cls, path: Optional[Path] = None) -> 'SkillEngine':
        """Load a pre-built index from disk."""
        if path is None:
            path = settings.graph_state_path.parent / "skill_index.pkl"
        
        instance = cls()
        
        if not path.exists():
            logger.warning(f"Index file not found at {path}")
            return instance
        
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        instance.embeddings = data.get('embeddings')
        instance.skills_data = data.get('skills_data')
        
        logger.info(f"Loaded skill index from {path}")
        return instance


def build_skill_index() -> SkillEngine:
    """
    Build skill index from cleaned data.
    
    This is the main entry point for index construction.
    """
    logger.info("Building skill index...")
    
    engine = SkillEngine()
    
    # Note: We skip model loading if not needed for basic operation
    # engine.load_embedding_model()  # Uncomment when model is available
    
    engine.load_skills_data()
    engine.load_content_data()
    engine.build_skill_index()
    engine.save_index()
    
    return engine


if __name__ == "__main__":
    # Build and save index
    engine = build_skill_index()
    print("Skill index built successfully!")
    
    # Test search
    if engine.skills_data is not None:
        results = engine.search_similar_skills("python programming", top_k=3)
        print(f"\nTest search results for 'python programming':")
        for result in results:
            print(f"  - {result['name']}: {result['similarity_score']:.3f}")
