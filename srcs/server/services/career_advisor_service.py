import math
from typing import Dict, Any, List, Tuple
from services.skill_clustering_service import skill_clustering_service
from services.skill_mapping_service import skill_mapping_service

# Domain target skill sets (simplified examples)
DOMAIN_SKILLS = {
    "DATA_AI": [
        "data", "analytics", "python", "ai", "ml", "model", "cloud", "sql"
    ],
    "ESG": [
        "sustainability", "esg", "environment", "compliance", "reporting", "governance"
    ]
}

class CareerAdvisorService:
    def __init__(self):
        pass

    def _tokenize(self, sentence: str) -> List[str]:
        return [t.strip().lower() for t in sentence.split() if t.strip()]

    def _aggregate_cluster_skills(self, rows: List[Dict[str, Any]], cluster_id: int) -> Dict[str, int]:
        freq = {}
        for r in rows:
            if r.get("cluster_kmeans") != cluster_id:
                continue
            for tok in self._tokenize(r.get("skill_sentence", "")):
                freq[tok] = freq.get(tok, 0) + 1
        return freq

    def _nearest_neighbors(self, rows: List[Dict[str, Any]], employee_id: str, k: int = 5, radius: float = None) -> List[Tuple[Dict[str, Any], float]]:
        me = next((r for r in rows if str(r.get("employee_id")) == str(employee_id)), None)
        if not me:
            return []
        result = []
        for r in rows:
            if r is me:
                continue
            dx = r.get("x", 0.0) - me.get("x", 0.0)
            dy = r.get("y", 0.0) - me.get("y", 0.0)
            dist = math.sqrt(dx*dx + dy*dy)
            if radius is not None and dist > radius:
                continue
            result.append((r, dist))
        result.sort(key=lambda x: x[1])
        return result[:k]

    def _compute_skill_gaps(self, employee_tokens: List[str], target_skills: List[str]) -> Dict[str, List[str]]:
        have = set(employee_tokens)
        target_set = set(target_skills)
        missing = [s for s in target_skills if s not in have]
        present = [s for s in target_skills if s in have]
        return {"present": present, "missing": missing}

    def _recommend_courses(self, mapping_path: str, missing_skills: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        import os, ast, pandas as pd
        if not os.path.exists(mapping_path) or not missing_skills:
            return []
        df = pd.read_csv(mapping_path)
        recs = []
        for _, row in df.iterrows():
            skills = row.get("predicted_skills")
            if isinstance(skills, str):
                try:
                    skills = ast.literal_eval(skills)
                except Exception:
                    skills = []
            if not isinstance(skills, list):
                continue
            overlap = [s for s in skills if s in missing_skills]
            if overlap:
                recs.append({
                    "course_id": row.get("ID Kurzu"),
                    "title": row.get("Název D"),
                    "overlap_skills": overlap,
                    "total_predicted": len(skills)
                })
        recs.sort(key=lambda r: (-len(r["overlap_skills"]), r.get("title") or ""))
        return recs[:limit]

    def generate_report(self, employee_id: str) -> Dict[str, Any]:
        rows = skill_clustering_service.get_clustering_data(force_recompute=False)
        if not rows:
            return {"error": "Clustering data unavailable."}

        employee_row = next((r for r in rows if str(r.get("employee_id")) == str(employee_id)), None)
        if not employee_row:
            return {"error": f"Employee {employee_id} not found in clustering data."}

        # Cluster context
        cluster_id = employee_row.get("cluster_kmeans")
        cluster_skill_freq = self._aggregate_cluster_skills(rows, cluster_id)
        top_cluster_skills = sorted(cluster_skill_freq.items(), key=lambda x: x[1], reverse=True)[:15]

        # Employee tokens & top skills
        employee_tokens = self._tokenize(employee_row.get("skill_sentence", ""))
        employee_top_skills = [s for s, _ in employee_row.get("top_skills", [])]

        # Mentor selection (nearest neighbors)
        mentors = []
        for cand, dist in self._nearest_neighbors(rows, employee_id, k=7):
            overlap = len(set(employee_tokens) & set(self._tokenize(cand.get("skill_sentence", ""))))
            mentors.append({
                "employee_id": cand.get("employee_id"),
                "distance": round(dist, 4),
                "overlap_skill_count": overlap,
                "cluster": cand.get("cluster_kmeans")
            })
        mentors = mentors[:5]

        # Domain skill gap + course recommendations
        skill_mapping_service.ensure_predicted_mapping(force=False)
        mapping_path = skill_mapping_service.predicted_output_path

        domain_results = {}
        for domain_key, target_skills in DOMAIN_SKILLS.items():
            gaps = self._compute_skill_gaps(employee_tokens, target_skills)
            course_recs = self._recommend_courses(mapping_path, gaps["missing"], limit=5)
            domain_results[domain_key] = {
                "target_skills": target_skills,
                "present": gaps["present"],
                "missing": gaps["missing"],
                "course_recommendations": course_recs
            }

        # Narrative synthesis (simple template)
        narrative_parts = []
        narrative_parts.append(
            f"Employee {employee_id} is in cluster {cluster_id}, characterized by top skills: " + ", ".join(s for s,_ in top_cluster_skills[:8]) + "."
        )
        if employee_top_skills:
            narrative_parts.append("Their strongest inferred skills include: " + ", ".join(employee_top_skills[:8]) + ".")
        # Domain pivot snippet
        for domain_key, info in domain_results.items():
            if info["missing"]:
                narrative_parts.append(
                    f"To strengthen a pivot toward {domain_key.replace('_',' & ')} focus on: " + ", ".join(info["missing"][:5]) + "."
                )
        if mentors:
            narrative_parts.append(
                "Potential mentors nearby: " + ", ".join(str(m["employee_id"]) for m in mentors) + "."
            )

        narrative = " \n".join(narrative_parts)

        return {
            "employee_id": employee_id,
            "cluster_id": cluster_id,
            "cluster_top_skills": top_cluster_skills,
            "employee_top_skills": employee_top_skills,
            "domains": domain_results,
            "mentors": mentors,
            "narrative": narrative
        }

career_advisor_service = CareerAdvisorService()
