"""
Skill Ontology Engine
----------------------
Extracts, normalizes, and clusters skills from datasets.
"""

import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import numpy as np

from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("skill_ontology")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import DBSCAN
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Clustering will use fallback method.")


# Common skill synonyms and variants
SKILL_SYNONYMS = {
    "react": ["reactjs", "react.js", "react-js"],
    "javascript": ["js", "ecmascript"],
    "python": ["py"],
    "machine learning": ["ml", "machine-learning"],
    "artificial intelligence": ["ai", "artificial-intelligence"],
    "data science": ["data-science", "datascience"],
    "project management": ["pm", "project-management"],
    "user experience": ["ux", "user-experience"],
    "user interface": ["ui", "user-interface"],
    "quality assurance": ["qa", "quality-assurance", "testing"],
    "devops": ["dev-ops", "devops"],
    "software engineering": ["software-engineering", "software development"],
}


def extract_skills_from_dataset(df: pd.DataFrame) -> List[str]:
    """
    Detect skills from column names and values.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        List of detected skills
    """
    skills: Set[str] = set()
    
    # Check column names for skill-related columns
    skill_keywords = [
        "skill", "competenc", "ability", "expertise", "proficiency",
        "knowledge", "capability", "qualification", "certification"
    ]
    
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in skill_keywords):
            # Extract unique values from this column
            unique_values = df[col].dropna().unique()
            for value in unique_values:
                if pd.notna(value):
                    value_str = str(value).strip()
                    if value_str and len(value_str) > 1:
                        skills.add(value_str)
    
    # Also check for comma-separated or list-like values
    for col in df.columns:
        if df[col].dtype == object:
            for value in df[col].dropna():
                value_str = str(value).strip()
                # Check for comma-separated skills
                if "," in value_str:
                    parts = [p.strip() for p in value_str.split(",")]
                    skills.update(parts)
                # Check for semicolon-separated skills
                elif ";" in value_str:
                    parts = [p.strip() for p in value_str.split(";")]
                    skills.update(parts)
    
    return sorted(list(skills))


def normalize_skill_name(skill: str) -> str:
    """
    Normalize skill name (fix capitalization, synonyms, variants).
    
    Args:
        skill: Raw skill name
        
    Returns:
        Normalized skill name
    """
    if not skill:
        return ""
    
    # Convert to lowercase for comparison
    skill_lower = skill.lower().strip()
    
    # Check synonyms
    for canonical, variants in SKILL_SYNONYMS.items():
        if skill_lower in variants or skill_lower == canonical:
            return canonical.title()
    
    # Normalize common patterns
    # Remove extra spaces
    skill = re.sub(r'\s+', ' ', skill.strip())
    
    # Fix capitalization (Title Case for multi-word, PascalCase for single word)
    if ' ' in skill or '-' in skill:
        # Multi-word: Title Case
        words = re.split(r'[\s\-]+', skill)
        normalized = ' '.join(word.capitalize() for word in words if word)
    else:
        # Single word: PascalCase
        normalized = skill.capitalize()
    
    return normalized


def cluster_similar_skills(skills: List[str], embeddings: Optional[np.ndarray] = None) -> List[List[str]]:
    """
    Group similar skills automatically using clustering.
    
    Args:
        skills: List of skill names
        embeddings: Optional pre-computed embeddings
        
    Returns:
        List of skill clusters (each cluster is a list of similar skills)
    """
    if not skills:
        return []
    
    if len(skills) == 1:
        return [[skills[0]]]
    
    # Create embeddings if not provided
    if embeddings is None:
        if not SKLEARN_AVAILABLE:
            # Fallback: simple clustering by string similarity
            return _cluster_by_string_similarity(skills)
        
        vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            max_features=1000
        )
        try:
            embeddings = vectorizer.fit_transform(skills).toarray()
        except Exception as e:
            logger.warning(f"Failed to create embeddings: {e}")
            # Fallback: simple clustering by string similarity
            return _cluster_by_string_similarity(skills)
    
    # Use DBSCAN for clustering
    if not SKLEARN_AVAILABLE:
        return _cluster_by_string_similarity(skills)
    
    try:
        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(embeddings)
        
        # Convert similarity to distance
        distance_matrix = 1 - similarity_matrix
        
        # Use DBSCAN with eps threshold
        clustering = DBSCAN(eps=0.3, min_samples=1, metric='precomputed')
        cluster_labels = clustering.fit_predict(distance_matrix)
        
        # Group skills by cluster
        clusters: Dict[int, List[str]] = {}
        for idx, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(skills[idx])
        
        return [clusters[label] for label in sorted(clusters.keys())]
        
    except Exception as e:
        logger.warning(f"Clustering failed: {e}")
        return _cluster_by_string_similarity(skills)


def _cluster_by_string_similarity(skills: List[str]) -> List[List[str]]:
    """Fallback clustering by string similarity."""
    clusters: List[List[str]] = []
    used = set()
    
    for skill in skills:
        if skill in used:
            continue
        
        cluster = [skill]
        used.add(skill)
        
        # Find similar skills
        skill_lower = skill.lower()
        for other in skills:
            if other in used or other == skill:
                continue
            
            other_lower = other.lower()
            # Simple similarity check
            if (skill_lower in other_lower or other_lower in skill_lower or
                _jaccard_similarity(skill_lower, other_lower) > 0.7):
                cluster.append(other)
                used.add(other)
        
        clusters.append(cluster)
    
    return clusters


def _jaccard_similarity(str1: str, str2: str) -> float:
    """Calculate Jaccard similarity between two strings."""
    set1 = set(str1.lower())
    set2 = set(str2.lower())
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def build_skill_ontology(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Build complete skill ontology from dataset.
    
    Args:
        df: DataFrame containing skill data
        
    Returns:
        Skill ontology dictionary with:
        - skills: List of all unique skills
        - clusters: List of skill clusters
        - normalized_mapping: Mapping from raw to normalized skill names
        - department_skill_map: Skills grouped by department (if department column exists)
    """
    # Extract raw skills
    raw_skills = extract_skills_from_dataset(df)
    
    # Normalize skills
    normalized_skills = [normalize_skill_name(skill) for skill in raw_skills]
    normalized_mapping = {
        raw: normalized for raw, normalized in zip(raw_skills, normalized_skills)
    }
    
    # Get unique normalized skills
    unique_skills = sorted(list(set(normalized_skills)))
    
    # Cluster similar skills
    clusters = cluster_similar_skills(unique_skills)
    
    # Build department-skill map if department column exists
    department_skill_map: Dict[str, List[str]] = {}
    if "department" in df.columns:
        for dept in df["department"].dropna().unique():
            dept_str = str(dept)
            dept_df = df[df["department"] == dept]
            dept_skills = extract_skills_from_dataset(dept_df)
            normalized_dept_skills = [normalize_skill_name(s) for s in dept_skills]
            department_skill_map[dept_str] = sorted(list(set(normalized_dept_skills)))
    
    return {
        "skills": unique_skills,
        "clusters": clusters,
        "normalized_mapping": normalized_mapping,
        "department_skill_map": department_skill_map,
    }


async def load_skill_ontology_from_file(ontology_path: Path) -> Dict[str, Any]:
    """Load skill ontology from JSON file asynchronously."""
    import json
    import aiofiles
    async with aiofiles.open(ontology_path, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)


async def save_skill_ontology(ontology: Dict[str, Any], ontology_path: Path) -> None:
    """Save skill ontology to JSON file asynchronously."""
    import json
    import aiofiles
    async with aiofiles.open(ontology_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(ontology, ensure_ascii=False, indent=2))

