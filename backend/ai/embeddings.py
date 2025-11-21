"""
LLM-based skill embeddings and semantic analysis
Uses Azure OpenAI GPT-4o for skill vectorization and insights
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

class SkillEmbeddingAnalyzer:
    """
    Generate semantic embeddings for skills using Azure GPT-4o
    Enables semantic similarity analysis beyond co-occurrence
    """

    def __init__(self, azure_endpoint: str = None, api_key: str = None):
        """
        Initialize Azure OpenAI client
        Falls back to environment variables if not provided
        """
        self.endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")

        if not self.endpoint or not self.api_key:
            print("[WARN]  Azure OpenAI credentials not found - using mock embeddings for demo")
            self.client = None
        else:
            self.client = AzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version="2024-02-15-preview"
            )

        self.embeddings_cache = {}

    def get_skill_embedding(self, skill: str) -> np.ndarray:
        """
        Get embedding vector for a skill
        Uses Azure OpenAI embeddings API
        """
        # Check cache
        if skill in self.embeddings_cache:
            return self.embeddings_cache[skill]

        if not self.client:
            # Mock embedding for demo (random but consistent)
            np.random.seed(hash(skill) % (2**32))
            embedding = np.random.randn(1536)  # GPT embedding dimension
            embedding = embedding / np.linalg.norm(embedding)  # Normalize
            self.embeddings_cache[skill] = embedding
            return embedding

        try:
            # Real Azure OpenAI embedding
            response = self.client.embeddings.create(
                input=skill,
                model="text-embedding-ada-002"  # Or deployment name in Azure
            )
            embedding = np.array(response.data[0].embedding)
            self.embeddings_cache[skill] = embedding
            return embedding

        except Exception as e:
            print(f"[WARN]  Embedding failed for '{skill}': {e}")
            # Fallback to mock
            np.random.seed(hash(skill) % (2**32))
            embedding = np.random.randn(1536)
            embedding = embedding / np.linalg.norm(embedding)
            self.embeddings_cache[skill] = embedding
            return embedding

    def get_skill_embeddings_batch(self, skills: List[str]) -> Dict[str, np.ndarray]:
        """
        Get embeddings for multiple skills efficiently
        """
        embeddings = {}
        for skill in skills:
            embeddings[skill] = self.get_skill_embedding(skill)
        return embeddings

    def find_similar_skills(self, target_skill: str, all_skills: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find semantically similar skills using cosine similarity
        """
        target_embedding = self.get_skill_embedding(target_skill)
        all_embeddings = self.get_skill_embeddings_batch(all_skills)

        similarities = []
        for skill, embedding in all_embeddings.items():
            if skill == target_skill:
                continue

            similarity = cosine_similarity(
                target_embedding.reshape(1, -1),
                embedding.reshape(1, -1)
            )[0][0]

            similarities.append({
                "skill": skill,
                "similarity": float(similarity)
            })

        # Sort by similarity
        similarities = sorted(similarities, key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]

    def cluster_skills_semantically(self, skills: List[str], n_clusters: int = 4) -> Dict[int, List[str]]:
        """
        Cluster skills based on semantic embeddings
        Alternative to co-occurrence-based clustering
        """
        from sklearn.cluster import KMeans

        # Get embeddings
        embeddings = self.get_skill_embeddings_batch(skills)
        embedding_matrix = np.array([embeddings[s] for s in skills])

        # K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(embedding_matrix)

        # Group skills by cluster
        clusters = {}
        for i, skill in enumerate(skills):
            cluster_id = int(labels[i])
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(skill)

        return clusters

    def generate_skill_insights(self, skill: str, context: str = "Škoda Auto automotive company") -> str:
        """
        Generate AI insights about a skill using Azure GPT-4o
        """
        if not self.client:
            # Mock insight for demo
            return f"**{skill}** is a key competency in modern automotive engineering. Organizations should invest in training programs to build expertise in this area."

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Or deployment name in Azure
                messages=[
                    {"role": "system", "content": f"You are a strategic HR analyst at {context}."},
                    {"role": "user", "content": f"Analyze the skill '{skill}' in 2-3 sentences. Cover: (1) Current relevance, (2) Future outlook, (3) One training recommendation."}
                ],
                max_tokens=150,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"[WARN]  GPT-4o insight failed for '{skill}': {e}")
            return f"**{skill}** is a valuable competency. Consider developing this skill through targeted training programs."

    def analyze_skill_gap(self, required_skills: List[str], employee_skills: List[str]) -> Dict[str, Any]:
        """
        Analyze gap between required skills and employee's current skills
        Using semantic similarity (more intelligent than exact matching)
        """
        # Get embeddings
        required_embeddings = self.get_skill_embeddings_batch(required_skills)
        employee_embeddings = self.get_skill_embeddings_batch(employee_skills)

        # Find coverage for each required skill
        coverage = []
        for req_skill in required_skills:
            req_emb = required_embeddings[req_skill]

            # Find closest employee skill
            best_match = None
            best_similarity = 0.0

            for emp_skill in employee_skills:
                emp_emb = employee_embeddings[emp_skill]
                similarity = cosine_similarity(
                    req_emb.reshape(1, -1),
                    emp_emb.reshape(1, -1)
                )[0][0]

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = emp_skill

            coverage.append({
                "required_skill": req_skill,
                "closest_match": best_match,
                "similarity": round(float(best_similarity), 3),
                "status": "covered" if best_similarity > 0.8 else "partial" if best_similarity > 0.5 else "missing"
            })

        # Calculate overall gap score
        avg_similarity = np.mean([c['similarity'] for c in coverage])
        gap_score = round(1.0 - avg_similarity, 2)

        # Identify priority training needs
        training_priorities = [c for c in coverage if c['status'] in ['missing', 'partial']]
        training_priorities = sorted(training_priorities, key=lambda x: x['similarity'])

        return {
            "gap_score": gap_score,  # 0 = perfect match, 1 = no overlap
            "coverage_details": coverage,
            "training_priorities": training_priorities[:5],  # Top 5 gaps
            "summary": {
                "covered": len([c for c in coverage if c['status'] == 'covered']),
                "partial": len([c for c in coverage if c['status'] == 'partial']),
                "missing": len([c for c in coverage if c['status'] == 'missing'])
            }
        }


def analyze_skill_semantics(skills: List[str], azure_config: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Main semantic analysis pipeline
    """
    # Initialize analyzer
    if azure_config:
        analyzer = SkillEmbeddingAnalyzer(
            azure_endpoint=azure_config.get('endpoint'),
            api_key=azure_config.get('api_key')
        )
    else:
        analyzer = SkillEmbeddingAnalyzer()

    # Run analyses
    results = {
        "semantic_clusters": analyzer.cluster_skills_semantically(skills, n_clusters=4),
        "skill_relationships": {},
        "insights": {}
    }

    # Analyze relationships for key skills
    key_skills = skills[:10]  # Analyze top 10 for demo
    for skill in key_skills:
        results["skill_relationships"][skill] = analyzer.find_similar_skills(skill, skills, top_k=5)

    # Generate insights for top 3 skills
    for skill in skills[:3]:
        results["insights"][skill] = analyzer.generate_skill_insights(skill)

    return results


if __name__ == "__main__":
    # Test with synthetic data
    import sys
    sys.path.append('..')

    from data.synthetic_data import SKILL_CATEGORIES

    # Flatten all skills
    all_skills = [skill for skills_list in SKILL_CATEGORIES.values() for skill in skills_list]

    print("🧠 Running semantic skill analysis...")
    results = analyze_skill_semantics(all_skills)

    print("\n[OK] Analysis Complete!")
    print(f"\n🎯 Semantic Clusters:")
    for cluster_id, skills in results['semantic_clusters'].items():
        print(f"   Cluster {cluster_id}: {', '.join(skills[:5])}...")

    print(f"\n🔗 Similar Skills Example (Python):")
    if 'Python' in results['skill_relationships']:
        for similar in results['skill_relationships']['Python'][:3]:
            print(f"   - {similar['skill']}: {similar['similarity']:.3f}")

    print(f"\n💡 AI Insights:")
    for skill, insight in list(results['insights'].items())[:2]:
        print(f"\n   {skill}:")
        print(f"   {insight}")
