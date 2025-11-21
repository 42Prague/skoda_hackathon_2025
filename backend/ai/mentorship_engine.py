"""
Mentorship & Retraining Recommendation Engine
Recommends mentor-mentee pairings based on:
- Graph centrality (skill influence/connectivity)
- Skill similarity (semantic matching)
- Growth trajectories (emerging vs declining skills)
"""
import os
import psycopg2
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from collections import defaultdict


def get_db_connection():
    """Get PostgreSQL connection from environment"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please configure DATABASE_URL with your PostgreSQL connection string."
        )
    return psycopg2.connect(database_url)


class MentorshipEngine:
    """
    Recommends optimal mentor-mentee pairings for skill development
    """

    def __init__(self, embedding_analyzer=None, timeseries_analyzer=None):
        """
        Initialize with optional analyzers for enhanced recommendations

        Args:
            embedding_analyzer: EmbeddingAnalyzer for semantic similarity
            timeseries_analyzer: SkillEvolutionAnalyzer for growth trends
        """
        self.embedding_analyzer = embedding_analyzer
        self.timeseries_analyzer = timeseries_analyzer

    def calculate_skill_centrality(self, employee_id: str) -> float:
        """
        Calculate skill centrality score (0-1) based on:
        - Skill diversity (number of unique skills)
        - Skill rarity (having uncommon skills)
        - Skill proficiency levels

        Higher centrality = more influential/knowledgeable employee
        """
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Get employee's skills with proficiency
            cur.execute("""
                SELECT s.skill_name, se.proficiency_level
                FROM skill_events se
                JOIN skills s ON se.skill_id = s.skill_id
                WHERE se.employee_id = %s
                  AND se.proficiency_level IS NOT NULL
                ORDER BY se.proficiency_level DESC
            """, (employee_id,))

            skills = cur.fetchall()

            if not skills:
                return 0.0

            # Skill diversity score
            diversity_score = min(len(skills) / 20.0, 1.0)  # Normalize to 20 skills = max

            # Skill proficiency score (average proficiency)
            avg_proficiency = np.mean([prof for _, prof in skills]) / 5.0  # Normalize to 0-1

            # Skill rarity score (how many employees have each skill)
            rarity_scores = []
            for skill_name, _ in skills:
                cur.execute("""
                    SELECT COUNT(DISTINCT se.employee_id)
                    FROM skill_events se
                    JOIN skills s ON se.skill_id = s.skill_id
                    WHERE s.skill_name = %s
                """, (skill_name,))

                employee_count = cur.fetchone()[0]
                # Rare skills (fewer people) = higher rarity score
                rarity = 1.0 - min(employee_count / 100.0, 1.0)  # Normalize to 100 employees
                rarity_scores.append(rarity)

            avg_rarity = np.mean(rarity_scores) if rarity_scores else 0.0

            # Weighted combination
            centrality = (
                0.4 * diversity_score +
                0.4 * avg_proficiency +
                0.2 * avg_rarity
            )

            return round(centrality, 3)

        finally:
            cur.close()
            conn.close()

    def get_employee_skills(self, employee_id: str) -> List[Tuple[str, int]]:
        """
        Get employee's skills with proficiency levels

        Returns:
            List of (skill_name, proficiency_level) tuples
        """
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT s.skill_name, MAX(se.proficiency_level) as max_proficiency
                FROM skill_events se
                JOIN skills s ON se.skill_id = s.skill_id
                WHERE se.employee_id = %s
                  AND se.proficiency_level IS NOT NULL
                GROUP BY s.skill_name
                ORDER BY max_proficiency DESC
            """, (employee_id,))

            return cur.fetchall()

        finally:
            cur.close()
            conn.close()

    def calculate_skill_overlap(
        self,
        mentor_skills: List[Tuple[str, int]],
        mentee_skills: List[Tuple[str, int]]
    ) -> Dict[str, Any]:
        """
        Calculate skill overlap between mentor and mentee

        Returns:
            {
                'overlap_count': Number of shared skills,
                'mentor_advantage': Skills mentor has at higher proficiency,
                'overlap_ratio': Ratio of shared skills to mentee's total skills
            }
        """
        mentor_dict = {skill: prof for skill, prof in mentor_skills}
        mentee_dict = {skill: prof for skill, prof in mentee_skills}

        shared_skills = set(mentor_dict.keys()) & set(mentee_dict.keys())
        overlap_count = len(shared_skills)

        # Skills where mentor has higher proficiency (can teach)
        mentor_advantage = []
        for skill in shared_skills:
            if mentor_dict[skill] > mentee_dict[skill]:
                mentor_advantage.append({
                    'skill': skill,
                    'mentor_level': mentor_dict[skill],
                    'mentee_level': mentee_dict[skill],
                    'gap': mentor_dict[skill] - mentee_dict[skill]
                })

        overlap_ratio = overlap_count / len(mentee_dict) if mentee_dict else 0.0

        return {
            'overlap_count': overlap_count,
            'mentor_advantage': mentor_advantage,
            'overlap_ratio': round(overlap_ratio, 3)
        }

    def recommend_mentors(
        self,
        mentee_id: str,
        target_skill: Optional[str] = None,
        top_k: int = 5,
        min_centrality: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Recommend top mentors for a given mentee

        Args:
            mentee_id: Employee ID of the mentee
            target_skill: Optional specific skill to learn (filters mentors with this skill)
            top_k: Number of top mentors to return
            min_centrality: Minimum centrality score for mentor candidates

        Returns:
            List of mentor recommendations with scores and reasoning
        """
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Get mentee's skills
            mentee_skills = self.get_employee_skills(mentee_id)
            mentee_skill_names = {skill for skill, _ in mentee_skills}

            # Get all potential mentors (employees with higher skill counts or proficiency)
            if target_skill:
                # Filter to employees with target skill at high proficiency
                cur.execute("""
                    SELECT DISTINCT se.employee_id
                    FROM skill_events se
                    JOIN skills s ON se.skill_id = s.skill_id
                    WHERE s.skill_name = %s
                      AND se.proficiency_level >= 4
                      AND se.employee_id != %s
                """, (target_skill, mentee_id))
            else:
                # All employees except mentee
                cur.execute("""
                    SELECT DISTINCT employee_id
                    FROM skill_events
                    WHERE employee_id != %s
                """, (mentee_id,))

            mentor_candidates = [row[0] for row in cur.fetchall()]

            # Score each mentor candidate
            mentor_scores = []

            for mentor_id in mentor_candidates:
                # Calculate centrality
                centrality = self.calculate_skill_centrality(mentor_id)

                if centrality < min_centrality:
                    continue  # Skip low-centrality candidates

                # Get mentor's skills
                mentor_skills = self.get_employee_skills(mentor_id)
                mentor_skill_names = {skill for skill, _ in mentor_skills}

                # Calculate overlap
                overlap = self.calculate_skill_overlap(mentor_skills, mentee_skills)

                # Skills mentor has that mentee lacks (teaching potential)
                unique_mentor_skills = mentor_skill_names - mentee_skill_names
                teaching_potential = len(unique_mentor_skills)

                # Growth trajectory alignment (if timeseries analyzer available)
                growth_alignment = 0.5  # Default neutral score
                if self.timeseries_analyzer and target_skill:
                    try:
                        growth_info = self.timeseries_analyzer.calculate_growth_rate(target_skill)
                        # Prioritize mentors for growing skills
                        if growth_info['trend'] in ['explosive', 'growing']:
                            growth_alignment = 0.8
                        elif growth_info['trend'] == 'declining':
                            growth_alignment = 0.3
                    except:
                        pass

                # Combined mentorship score (0-1)
                score = (
                    0.35 * centrality +
                    0.25 * min(overlap['overlap_ratio'] * 2, 1.0) +  # Bonus for shared context
                    0.20 * min(teaching_potential / 10.0, 1.0) +  # Normalize to 10 new skills
                    0.10 * min(len(overlap['mentor_advantage']) / 5.0, 1.0) +  # Skills to improve
                    0.10 * growth_alignment
                )

                # Get mentor details
                cur.execute("""
                    SELECT first_name, last_name, department, position
                    FROM employees
                    WHERE employee_id = %s
                """, (mentor_id,))

                mentor_info = cur.fetchone()

                if mentor_info:
                    first_name, last_name, department, position = mentor_info

                    mentor_scores.append({
                        'mentor_id': mentor_id,
                        'mentor_name': f"{first_name} {last_name}",
                        'department': department,
                        'position': position,
                        'score': round(score, 3),
                        'centrality': centrality,
                        'shared_skills': overlap['overlap_count'],
                        'skills_to_improve': len(overlap['mentor_advantage']),
                        'new_skills_offered': teaching_potential,
                        'top_skills_to_learn': list(unique_mentor_skills)[:5],
                        'improvement_opportunities': overlap['mentor_advantage'][:3],
                        'reasoning': self._generate_reasoning(
                            centrality,
                            overlap,
                            teaching_potential,
                            target_skill
                        )
                    })

            # Sort by score and return top K
            mentor_scores.sort(key=lambda x: x['score'], reverse=True)
            return mentor_scores[:top_k]

        finally:
            cur.close()
            conn.close()

    def _generate_reasoning(
        self,
        centrality: float,
        overlap: Dict[str, Any],
        teaching_potential: int,
        target_skill: Optional[str]
    ) -> str:
        """Generate human-readable reasoning for mentor recommendation"""
        reasons = []

        if centrality > 0.7:
            reasons.append("highly experienced expert")
        elif centrality > 0.5:
            reasons.append("experienced professional")
        else:
            reasons.append("knowledgeable colleague")

        if len(overlap['mentor_advantage']) > 0:
            reasons.append(f"can help improve {len(overlap['mentor_advantage'])} shared skills")

        if teaching_potential > 5:
            reasons.append(f"can teach {teaching_potential} new skills")

        if target_skill and overlap['overlap_ratio'] > 0.3:
            reasons.append(f"shares domain context for {target_skill}")

        return "; ".join(reasons).capitalize()

    def recommend_retraining_paths(
        self,
        employee_id: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Recommend retraining paths for employee based on:
        - Declining skills they possess
        - Emerging skills they lack
        - Similar employees' skill transitions

        Returns:
            List of retraining recommendations with target skills and reasoning
        """
        if not self.timeseries_analyzer:
            return [{
                'error': 'Timeseries analyzer required for retraining recommendations'
            }]

        employee_skills = self.get_employee_skills(employee_id)
        employee_skill_names = {skill for skill, _ in employee_skills}

        recommendations = []

        # Identify declining skills employee possesses
        declining_skills = []
        for skill_name, proficiency in employee_skills:
            try:
                growth_info = self.timeseries_analyzer.calculate_growth_rate(skill_name)
                if growth_info['trend'] in ['declining', 'dying']:
                    declining_skills.append({
                        'skill': skill_name,
                        'proficiency': proficiency,
                        'growth_rate': growth_info['growth_rate']
                    })
            except:
                pass

        # Identify emerging skills employee lacks
        emerging_skills = []
        try:
            mutations = self.timeseries_analyzer.identify_mutations(threshold_growth=10.0)
            for mutation in mutations[:10]:
                if mutation['skill'] not in employee_skill_names:
                    emerging_skills.append(mutation)
        except:
            pass

        # Generate recommendations: transition from declining to emerging
        for declining in declining_skills[:top_k]:
            # Find best emerging skill match (semantic similarity if available)
            best_match = None
            best_similarity = 0.0

            if self.embedding_analyzer:
                try:
                    for emerging in emerging_skills:
                        similarity = self.embedding_analyzer.calculate_similarity(
                            declining['skill'],
                            emerging['skill']
                        )
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = emerging
                except:
                    pass

            # Fallback: pick highest growth emerging skill
            if not best_match and emerging_skills:
                best_match = emerging_skills[0]

            if best_match:
                recommendations.append({
                    'from_skill': declining['skill'],
                    'to_skill': best_match['skill'],
                    'urgency': 'high' if declining['growth_rate'] < -10 else 'medium',
                    'opportunity': best_match.get('growth_rate', 0),
                    'semantic_similarity': round(best_similarity, 3) if best_similarity > 0 else None,
                    'reasoning': f"Transition from declining skill ({declining['growth_rate']}%/yr) to high-growth skill (+{best_match.get('growth_rate', 0)}%/yr)"
                })

        return recommendations[:top_k]


def get_mentorship_recommendations(
    mentee_id: str,
    target_skill: Optional[str] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Get mentorship recommendations for an employee

    Args:
        mentee_id: Employee ID
        target_skill: Optional specific skill to learn
        top_k: Number of recommendations

    Returns:
        {
            'mentee_id': str,
            'target_skill': str,
            'recommendations': List[mentor recommendations],
            'retraining_paths': List[retraining recommendations]
        }
    """
    try:
        # Initialize engine (without analyzers for basic mode)
        engine = MentorshipEngine()

        # Get mentor recommendations
        mentors = engine.recommend_mentors(
            mentee_id=mentee_id,
            target_skill=target_skill,
            top_k=top_k
        )

        # Get retraining paths (will fail gracefully if no analyzer)
        retraining = engine.recommend_retraining_paths(mentee_id, top_k=3)

        return {
            'mentee_id': mentee_id,
            'target_skill': target_skill,
            'mentorship_recommendations': mentors,
            'retraining_paths': retraining
        }

    except Exception as e:
        return {
            'error': f'Mentorship recommendation failed: {str(e)}',
            'mentee_id': mentee_id
        }
