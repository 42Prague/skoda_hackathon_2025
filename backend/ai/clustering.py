"""
Clustering algorithms for Skill DNA - Organizational Genome Analysis
Implements multiple clustering techniques to identify skill clusters and employee segments
"""
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
from umap import UMAP
import networkx as nx
from typing import Dict, List, Tuple, Any


def convert_numpy_types(obj):
    """
    Recursively convert numpy types to Python native types for JSON serialization
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {convert_numpy_types(key): convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

class SkillClusterAnalyzer:
    """
    Advanced clustering for skill DNA analysis
    Implements multiple algorithms to identify skill clusters and patterns
    """

    def __init__(self, skill_matrix_df: pd.DataFrame):
        """
        Initialize with skill matrix (employees x skills binary matrix)
        """
        self.skill_matrix = skill_matrix_df
        self.employee_ids = skill_matrix_df['employee_id'].values
        self.skill_columns = [col for col in skill_matrix_df.columns if col != 'employee_id']
        self.X = skill_matrix_df[self.skill_columns].values
        self.X_scaled = StandardScaler().fit_transform(self.X)

        # Results storage
        self.clusters = None
        self.embeddings_2d = None
        self.cluster_labels = {}

    def dbscan_clustering(self, eps: float = 0.5, min_samples: int = 5) -> np.ndarray:
        """
        DBSCAN clustering - identifies dense skill clusters
        Good for finding outliers (employees with unique skill combinations)
        """
        dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean')
        labels = dbscan.fit_predict(self.X_scaled)

        self.cluster_labels['dbscan'] = labels
        return labels

    def hierarchical_clustering(self, n_clusters: int = 4) -> np.ndarray:
        """
        Agglomerative hierarchical clustering
        Creates skill "species" - distinct groups with common characteristics
        """
        hierarchical = AgglomerativeClustering(
            n_clusters=n_clusters,
            linkage='ward'
        )
        labels = hierarchical.fit_predict(self.X_scaled)

        self.cluster_labels['hierarchical'] = labels
        return labels

    def umap_reduction(self, n_neighbors: int = 15, min_dist: float = 0.1) -> np.ndarray:
        """
        UMAP dimensionality reduction for 2D visualization
        Projects high-dimensional skill space into 2D "genome map"
        """
        reducer = UMAP(
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            n_components=2,
            random_state=42
        )
        embeddings = reducer.fit_transform(self.X_scaled)

        self.embeddings_2d = embeddings
        return embeddings

    def evaluate_clustering(self, labels: np.ndarray) -> Dict[str, float]:
        """
        Evaluate clustering quality using multiple metrics
        """
        # Filter out noise points (label = -1 in DBSCAN)
        mask = labels >= 0
        if mask.sum() < 2:
            return {"silhouette": 0, "davies_bouldin": 0, "n_clusters": 0}

        X_filtered = self.X_scaled[mask]
        labels_filtered = labels[mask]

        n_clusters = len(set(labels_filtered))
        if n_clusters < 2:
            return {"silhouette": 0, "davies_bouldin": 0, "n_clusters": n_clusters}

        silhouette = silhouette_score(X_filtered, labels_filtered)
        davies_bouldin = davies_bouldin_score(X_filtered, labels_filtered)

        return {
            "silhouette": float(round(silhouette, 3)),
            "davies_bouldin": float(round(davies_bouldin, 3)),
            "n_clusters": n_clusters,
            "n_noise": int((labels == -1).sum())
        }

    def get_cluster_characteristics(self, labels: np.ndarray) -> Dict[int, Dict[str, Any]]:
        """
        Analyze each cluster's defining skills and characteristics
        Returns "Cluster DNA" - what makes each cluster unique
        """
        cluster_chars = {}

        for cluster_id in set(labels):
            cluster_id = int(cluster_id)  # Ensure Python int
            if cluster_id == -1:  # Skip noise
                continue

            # Get employees in this cluster
            cluster_mask = labels == cluster_id
            cluster_skills = self.X[cluster_mask]

            # Calculate skill prevalence in cluster
            skill_prevalence = cluster_skills.mean(axis=0)

            # Top defining skills (>50% prevalence)
            top_skill_indices = np.where(skill_prevalence > 0.5)[0]
            top_skills = [self.skill_columns[i] for i in top_skill_indices]
            top_prevalence = [skill_prevalence[i] for i in top_skill_indices]

            # Sort by prevalence
            sorted_pairs = sorted(zip(top_skills, top_prevalence), key=lambda x: x[1], reverse=True)

            cluster_chars[cluster_id] = {
                "size": int(cluster_mask.sum()),
                "defining_skills": [s for s, _ in sorted_pairs[:5]],  # Top 5
                "skill_prevalence": {s: float(p) for s, p in sorted_pairs[:10]},  # Top 10 with %
                "avg_skills_per_employee": float(cluster_skills.sum(axis=1).mean())
            }

        return cluster_chars

    def build_skill_network(self, labels: np.ndarray, threshold: float = 0.3) -> nx.Graph:
        """
        Build skill co-occurrence network
        Edges = skills that frequently appear together in same employees
        """
        G = nx.Graph()

        # Add nodes (skills)
        for skill in self.skill_columns:
            G.add_node(skill)

        # Calculate co-occurrence matrix
        skill_matrix = self.X.T  # Skills x Employees
        cooccurrence = np.dot(skill_matrix, skill_matrix.T)

        # Normalize by geometric mean
        diagonal = np.sqrt(np.diag(cooccurrence))
        cooccurrence_norm = cooccurrence / np.outer(diagonal, diagonal)

        # Add edges above threshold
        for i, skill_i in enumerate(self.skill_columns):
            for j, skill_j in enumerate(self.skill_columns):
                if i < j and cooccurrence_norm[i, j] > threshold:
                    G.add_edge(
                        skill_i,
                        skill_j,
                        weight=float(cooccurrence_norm[i, j])
                    )

        return G

    def get_network_insights(self, G: nx.Graph) -> Dict[str, Any]:
        """
        Extract insights from skill network
        PageRank = "hub skills", Communities = skill families
        """
        # PageRank - identify hub skills
        pagerank = nx.pagerank(G, weight='weight')
        top_hubs = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]

        # Betweenness centrality - bridge skills connecting different domains
        betweenness = nx.betweenness_centrality(G, weight='weight')
        top_bridges = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]

        # Community detection (Louvain)
        communities = nx.community.greedy_modularity_communities(G, weight='weight')

        return {
            "hub_skills": [{"skill": s, "score": round(score, 3)} for s, score in top_hubs],
            "bridge_skills": [{"skill": s, "score": round(score, 3)} for s, score in top_bridges],
            "skill_families": [list(c) for c in communities],
            "network_density": round(nx.density(G), 3),
            "avg_clustering_coefficient": round(nx.average_clustering(G, weight='weight'), 3)
        }

    def generate_genome_visualization_data(self, method: str = 'hierarchical') -> Dict[str, Any]:
        """
        Generate complete data structure for frontend D3.js force-directed graph
        Replaces the mock MOCK_GENOME_DATA in constants.ts
        """
        # Get clustering labels
        if method == 'hierarchical':
            labels = self.hierarchical_clustering(n_clusters=4)
        elif method == 'dbscan':
            labels = self.dbscan_clustering()
        else:
            labels = self.hierarchical_clustering(n_clusters=4)

        # Get 2D embeddings
        embeddings = self.umap_reduction()

        # Build skill network
        G = self.build_skill_network(labels)

        # Create nodes (skills with metadata)
        nodes = []
        for i, skill in enumerate(self.skill_columns):
            # Calculate skill growth (mock for now - will be replaced by time-series analysis)
            skill_count = self.X[:, i].sum()
            growth = np.random.uniform(-0.3, 0.8)  # Placeholder

            # Find cluster assignment (most common cluster for this skill)
            skill_employees = self.X[:, i] == 1
            skill_clusters = labels[skill_employees]
            if len(skill_clusters) > 0:
                cluster = int(np.bincount(skill_clusters[skill_clusters >= 0]).argmax())
            else:
                cluster = 0

            nodes.append({
                "id": skill,
                "label": skill,
                "value": float(skill_count),  # Size in visualization
                "group": int(cluster) + 1,  # 1-indexed for frontend
                "growth": float(growth)
            })

        # Create links (skill co-occurrences from network)
        links = []
        for edge in G.edges(data=True):
            links.append({
                "source": edge[0],
                "target": edge[1],
                "value": float(edge[2]['weight'])
            })

        result = {
            "nodes": nodes,
            "links": links,
            "metadata": {
                "total_employees": len(self.employee_ids),
                "total_skills": len(self.skill_columns),
                "clustering_method": method,
                "cluster_metrics": self.evaluate_clustering(labels)
            }
        }

        # Convert all numpy types to Python types for JSON serialization
        return convert_numpy_types(result)


def analyze_skill_genome(skill_matrix_path: str) -> Dict[str, Any]:
    """
    Main analysis pipeline - takes skill matrix CSV and returns complete genome analysis
    """
    # Load data
    skill_matrix = pd.read_csv(skill_matrix_path)

    # Initialize analyzer
    analyzer = SkillClusterAnalyzer(skill_matrix)

    # Run all analyses
    results = {
        "genome_visualization": analyzer.generate_genome_visualization_data(method='hierarchical'),
        "clustering_evaluation": {},
        "cluster_characteristics": {},
        "network_insights": {}
    }

    # DBSCAN analysis
    dbscan_labels = analyzer.dbscan_clustering()
    results["clustering_evaluation"]["dbscan"] = analyzer.evaluate_clustering(dbscan_labels)
    results["cluster_characteristics"]["dbscan"] = analyzer.get_cluster_characteristics(dbscan_labels)

    # Hierarchical analysis
    hierarchical_labels = analyzer.hierarchical_clustering(n_clusters=4)
    results["clustering_evaluation"]["hierarchical"] = analyzer.evaluate_clustering(hierarchical_labels)
    results["cluster_characteristics"]["hierarchical"] = analyzer.get_cluster_characteristics(hierarchical_labels)

    # Network analysis
    G = analyzer.build_skill_network(hierarchical_labels)
    results["network_insights"] = analyzer.get_network_insights(G)

    return results


if __name__ == "__main__":
    # Test with synthetic data
    import sys
    sys.path.append('..')

    from data.synthetic_data import save_synthetic_data

    # Generate synthetic data
    print("🧬 Generating synthetic Škoda employee data...")
    save_synthetic_data()

    # Run clustering analysis
    print("\n🔬 Running skill genome analysis...")
    results = analyze_skill_genome("data/skill_matrix.csv")

    print("\n[OK] Analysis Complete!")
    print(f"📊 Clusters identified: {results['clustering_evaluation']['hierarchical']['n_clusters']}")
    print(f"📈 Silhouette score: {results['clustering_evaluation']['hierarchical']['silhouette']}")
    print(f"🕸️  Network density: {results['network_insights']['network_density']}")
    print(f"\n🎯 Top hub skills:")
    for hub in results['network_insights']['hub_skills'][:5]:
        print(f"   - {hub['skill']}: {hub['score']}")
