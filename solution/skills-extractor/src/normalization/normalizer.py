"""Skill normalization with embeddings and clustering."""

import logging
from typing import List, Dict, Set, Tuple
from collections import defaultdict, Counter
import numpy as np

from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.console import Console

from config.settings import settings
from src.models import ExtractedSkill, NormalizedSkill, SkillCategory

logger = logging.getLogger(__name__)
console = Console()


class SkillNormalizer:
    """Normalizes extracted skills using embeddings and clustering."""

    def __init__(self):
        """Initialize the skill normalizer."""
        self.embedding_model_name = settings.embedding_model
        self.eps = settings.clustering_eps
        self.min_samples = settings.clustering_min_samples

        # Lazy load the embedding model
        self._embedding_model: SentenceTransformer | None = None

    @property
    def embedding_model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._embedding_model is None:
            console.print(f"[cyan]Loading embedding model: {self.embedding_model_name}[/cyan]")
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
            console.print("[green]✓ Embedding model loaded[/green]")
        return self._embedding_model

    def _collect_unique_skills(
        self, all_extracted_skills: List[List[ExtractedSkill]]
    ) -> List[Tuple[str, SkillCategory]]:
        """Collect all unique skills from extraction results."""
        unique_skills: Dict[str, SkillCategory] = {}

        for job_skills in all_extracted_skills:
            for skill in job_skills:
                # Use lowercase for deduplication but preserve original case
                skill_lower = skill.name.lower()
                if skill_lower not in unique_skills:
                    unique_skills[skill.name] = skill.category

        console.print(f"[cyan]Found {len(unique_skills)} unique skills[/cyan]")
        return list(unique_skills.items())

    def _generate_embeddings(
        self, skill_names: List[str]
    ) -> np.ndarray:
        """Generate embeddings for skill names."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Generating embeddings...", total=1)

            # Batch encode all skills
            embeddings = self.embedding_model.encode(
                skill_names,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True,
            )

            progress.update(task, completed=1)

        console.print(f"[green]✓ Generated embeddings: shape {embeddings.shape}[/green]")
        return embeddings

    def _cluster_skills(
        self, embeddings: np.ndarray
    ) -> np.ndarray:
        """Cluster skills using DBSCAN."""
        console.print(f"[cyan]Clustering with DBSCAN (eps={self.eps}, min_samples={self.min_samples})...[/cyan]")

        clustering = DBSCAN(
            eps=self.eps,
            min_samples=self.min_samples,
            metric="cosine",
        )

        labels = clustering.fit_predict(embeddings)

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)

        console.print(f"[green]✓ Found {n_clusters} clusters ({n_noise} noise points)[/green]")

        return labels

    def _select_canonical_names(
        self,
        skill_names: List[str],
        labels: np.ndarray,
        skill_counts: Counter,
    ) -> Dict[int, str]:
        """Select canonical name for each cluster (most common or shortest)."""
        cluster_names: Dict[int, List[str]] = defaultdict(list)

        for skill_name, label in zip(skill_names, labels):
            if label != -1:  # Skip noise points
                cluster_names[label].append(skill_name)

        canonical_names: Dict[int, str] = {}

        for cluster_id, names in cluster_names.items():
            # Prefer the most common name in the cluster
            name_counts = [(name, skill_counts.get(name, 1)) for name in names]
            name_counts.sort(key=lambda x: (-x[1], len(x[0])))  # Most common, then shortest
            canonical_names[cluster_id] = name_counts[0][0]

        return canonical_names

    def _build_normalized_skills(
        self,
        skill_names: List[str],
        categories: List[SkillCategory],
        embeddings: np.ndarray,
        labels: np.ndarray,
        canonical_names: Dict[int, str],
    ) -> List[NormalizedSkill]:
        """Build normalized skill objects with aliases."""
        # Group skills by cluster
        cluster_skills: Dict[int, List[Tuple[str, SkillCategory, np.ndarray]]] = defaultdict(list)

        for skill_name, category, embedding, label in zip(
            skill_names, categories, embeddings, labels
        ):
            if label != -1:
                cluster_skills[label].append((skill_name, category, embedding))

        normalized_skills: List[NormalizedSkill] = []

        # Create normalized skills for each cluster
        for cluster_id, skills in cluster_skills.items():
            canonical_name = canonical_names[cluster_id]

            # Find the canonical skill's data
            canonical_category = None
            canonical_embedding = None

            for skill_name, category, embedding in skills:
                if skill_name == canonical_name:
                    canonical_category = category
                    canonical_embedding = embedding
                    break

            # If canonical not found, use first skill
            if canonical_category is None:
                canonical_category = skills[0][1]
                canonical_embedding = skills[0][2]

            # Build alias list (exclude canonical name)
            aliases = [s[0] for s in skills if s[0] != canonical_name]

            normalized_skill = NormalizedSkill(
                canonical_name=canonical_name,
                original_name=canonical_name,
                category=canonical_category,
                aliases=aliases,
                embedding=canonical_embedding.tolist(),
                cluster_id=cluster_id,
            )

            normalized_skills.append(normalized_skill)

        # Handle noise points (each gets its own normalized skill)
        for skill_name, category, embedding, label in zip(
            skill_names, categories, embeddings, labels
        ):
            if label == -1:
                normalized_skill = NormalizedSkill(
                    canonical_name=skill_name,
                    original_name=skill_name,
                    category=category,
                    aliases=[],
                    embedding=embedding.tolist(),
                    cluster_id=None,
                )
                normalized_skills.append(normalized_skill)

        console.print(f"[green]✓ Created {len(normalized_skills)} normalized skills[/green]")
        return normalized_skills

    def normalize_skills(
        self,
        all_extracted_skills: List[List[ExtractedSkill]],
        skill_counts: Counter | None = None,
    ) -> List[NormalizedSkill]:
        """Normalize extracted skills using embeddings and clustering.

        Args:
            all_extracted_skills: List of skill lists from each job
            skill_counts: Counter of skill frequencies (optional)

        Returns:
            List of normalized skills with canonical names and aliases
        """
        console.print("\n[bold cyan]Starting Skill Normalization[/bold cyan]")

        # Collect unique skills
        unique_skills = self._collect_unique_skills(all_extracted_skills)
        skill_names = [s[0] for s in unique_skills]
        categories = [s[1] for s in unique_skills]

        # Count skill frequencies if not provided
        if skill_counts is None:
            skill_counts = Counter()
            for job_skills in all_extracted_skills:
                for skill in job_skills:
                    skill_counts[skill.name] += 1

        # Generate embeddings
        embeddings = self._generate_embeddings(skill_names)

        # Cluster skills
        labels = self._cluster_skills(embeddings)

        # Select canonical names
        canonical_names = self._select_canonical_names(skill_names, labels, skill_counts)

        # Build normalized skills
        normalized_skills = self._build_normalized_skills(
            skill_names, categories, embeddings, labels, canonical_names
        )

        # Print summary
        console.print("\n[bold green]Normalization Summary:[/bold green]")
        console.print(f"  • Total unique skills: {len(unique_skills)}")
        console.print(f"  • Normalized to: {len(normalized_skills)} canonical skills")
        console.print(f"  • Clusters formed: {len(canonical_names)}")
        console.print(f"  • Skills with aliases: {sum(1 for s in normalized_skills if s.aliases)}")

        return normalized_skills

    def find_similar_skills(
        self,
        query_skill: str,
        normalized_skills: List[NormalizedSkill],
        top_k: int = 5,
        threshold: float = 0.85,
    ) -> List[Tuple[NormalizedSkill, float]]:
        """Find similar skills to a query using cosine similarity.

        Args:
            query_skill: Skill name to find similar skills for
            normalized_skills: List of normalized skills to search
            top_k: Number of top results to return
            threshold: Minimum similarity threshold

        Returns:
            List of (skill, similarity_score) tuples
        """
        # Generate embedding for query
        query_embedding = self.embedding_model.encode(
            [query_skill], convert_to_numpy=True
        )[0]

        # Calculate similarities
        similarities = []
        for skill in normalized_skills:
            if skill.embedding:
                skill_embedding = np.array(skill.embedding)
                similarity = cosine_similarity(
                    query_embedding.reshape(1, -1),
                    skill_embedding.reshape(1, -1)
                )[0][0]

                if similarity >= threshold:
                    similarities.append((skill, float(similarity)))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]


# Global normalizer instance
skill_normalizer = SkillNormalizer()
