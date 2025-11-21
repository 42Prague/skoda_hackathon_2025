"""
Course Recommendation System with Auto-mapping and Duplicate Detection
Uses NLP/embeddings to map courses to skills and recommend learning paths
"""
import numpy as np
from typing import List, Dict, Set, Tuple
from collections import defaultdict
import re
from data_models import Employee, Course, Skill, SkillGap


class CourseSkillMapper:
    """Automatically maps courses to skills using text similarity"""
    
    def __init__(self):
        self.course_skill_map = defaultdict(list)
        self.skill_keywords = {}
    
    def map_courses_to_skills(self, courses: List[Course], skills: List[Skill]) -> Dict[str, List[Skill]]:
        """
        Automatically map courses to skills based on title, description, and competencies
        
        Returns:
            Dictionary mapping course_id to list of relevant skills
        """
        # Build keyword sets for each skill
        for skill in skills:
            keywords = self._extract_keywords(skill.name)
            self.skill_keywords[skill.skill_id] = (skill, keywords)
        
        # Map each course
        for course in courses:
            # Combine all course text
            course_text = f"{course.title} {course.description} {' '.join(course.competencies)}"
            course_keywords = self._extract_keywords(course_text)
            
            # Find matching skills
            matched_skills = []
            for skill_id, (skill, skill_keywords) in self.skill_keywords.items():
                # Calculate keyword overlap
                overlap = len(course_keywords & skill_keywords)
                if overlap > 0:
                    matched_skills.append((skill, overlap))
            
            # Sort by overlap and take top matches
            matched_skills.sort(key=lambda x: x[1], reverse=True)
            
            # Store top 5 matches
            self.course_skill_map[course.course_id] = [skill for skill, _ in matched_skills[:5]]
            
            # Update course's skills_taught
            course.skills_taught = [skill for skill, _ in matched_skills[:5]]
        
        return dict(self.course_skill_map)
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract meaningful keywords from text"""
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Split into words
        words = text.split()
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                     'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                     'can', 'could', 'may', 'might', 'must', 'shall'}
        
        keywords = {w for w in words if len(w) > 2 and w not in stop_words}
        
        return keywords
    
    def get_courses_for_skill(self, skill: Skill, courses: List[Course]) -> List[Course]:
        """Get all courses that teach a specific skill"""
        matching_courses = []
        
        for course in courses:
            if skill in course.skills_taught:
                matching_courses.append(course)
        
        # Sort by duration (shorter courses first for quick wins)
        matching_courses.sort(key=lambda c: c.duration_minutes)
        
        return matching_courses


class DuplicateCourseDetector:
    """Detects duplicate or very similar courses"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
    
    def find_duplicates(self, courses: List[Course]) -> List[List[Course]]:
        """
        Find groups of duplicate or highly similar courses
        
        Returns:
            List of course groups (each group contains similar courses)
        """
        duplicate_groups = []
        processed = set()
        
        for i, course1 in enumerate(courses):
            if course1.course_id in processed:
                continue
            
            similar_group = [course1]
            
            for j, course2 in enumerate(courses[i+1:], i+1):
                if course2.course_id in processed:
                    continue
                
                similarity = self._calculate_similarity(course1, course2)
                if similarity >= self.similarity_threshold:
                    similar_group.append(course2)
                    processed.add(course2.course_id)
            
            if len(similar_group) > 1:
                duplicate_groups.append(similar_group)
                processed.add(course1.course_id)
        
        return duplicate_groups
    
    def _calculate_similarity(self, course1: Course, course2: Course) -> float:
        """Calculate similarity score between two courses"""
        # Title similarity
        title_sim = self._jaccard_similarity(course1.title, course2.title)
        
        # Skill similarity
        skills1 = {s.name for s in course1.skills_taught}
        skills2 = {s.name for s in course2.skills_taught}
        skill_sim = len(skills1 & skills2) / max(len(skills1 | skills2), 1)
        
        # Provider check (same provider + similar title = likely duplicate)
        provider_match = 1.0 if course1.provider == course2.provider else 0.5
        
        # Combined score
        similarity = (title_sim * 0.5 + skill_sim * 0.3 + provider_match * 0.2)
        
        return similarity
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two texts"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0


class LearningPathRecommender:
    """Recommends personalized learning paths for employees"""
    
    def __init__(self):
        self.mapper = CourseSkillMapper()
        self.duplicate_detector = DuplicateCourseDetector()
    
    def recommend_for_employee(self, employee: Employee, skill_gap: SkillGap, 
                               all_courses: List[Course], max_courses: int = 10) -> Dict:
        """
        Recommend personalized learning path for an employee
        
        Returns:
            Dictionary with recommended courses and learning path
        """
        recommendations = {
            'employee': employee,
            'target_position': skill_gap.target_position,
            'readiness_score': skill_gap.readiness_score,
            'priority_courses': [],
            'optional_courses': [],
            'estimated_hours': 0,
            'learning_sequence': []
        }
        
        # Get courses for missing required skills (priority)
        priority_courses = []
        for skill in skill_gap.missing_required_skills:
            courses = self.mapper.get_courses_for_skill(skill, all_courses)
            for course in courses[:2]:  # Top 2 courses per skill
                if course not in priority_courses:
                    priority_courses.append({
                        'course': course,
                        'skill': skill,
                        'priority': 'required',
                        'hours': course.duration_minutes / 60
                    })
        
        # Get courses for missing optional skills
        optional_courses = []
        for skill in skill_gap.missing_optional_skills[:5]:  # Limit optional skills
            courses = self.mapper.get_courses_for_skill(skill, all_courses)
            for course in courses[:1]:  # Top 1 course per optional skill
                if course not in optional_courses:
                    optional_courses.append({
                        'course': course,
                        'skill': skill,
                        'priority': 'optional',
                        'hours': course.duration_minutes / 60
                    })
        
        # Sort priority courses by duration (quick wins first)
        priority_courses.sort(key=lambda x: x['hours'])
        
        # Build learning sequence
        learning_sequence = self._build_learning_sequence(
            priority_courses[:max_courses],
            employee
        )
        
        total_hours = sum(item['hours'] for item in priority_courses + optional_courses)
        
        recommendations['priority_courses'] = priority_courses[:max_courses]
        recommendations['optional_courses'] = optional_courses[:max_courses//2]
        recommendations['estimated_hours'] = round(total_hours, 1)
        recommendations['learning_sequence'] = learning_sequence
        
        return recommendations
    
    def _build_learning_sequence(self, courses: List[Dict], employee: Employee) -> List[Dict]:
        """
        Build an optimal learning sequence considering prerequisites and difficulty
        """
        # Simple sequencing: start with shorter courses (quick wins)
        # Then move to longer, more complex courses
        
        sequence = []
        cumulative_hours = 0
        
        for i, course_info in enumerate(courses, 1):
            cumulative_hours += course_info['hours']
            sequence.append({
                'step': i,
                'course': course_info['course'].title,
                'skill_target': course_info['skill'].name,
                'hours': course_info['hours'],
                'cumulative_hours': round(cumulative_hours, 1),
                'priority': course_info['priority']
            })
        
        return sequence
    
    def recommend_for_team(self, team: List[Employee], skill_gaps: List[SkillGap],
                          all_courses: List[Course]) -> Dict:
        """
        Recommend team-wide training strategy
        
        Returns:
            Dictionary with team training recommendations
        """
        # Count how many people need each skill
        skill_demand = defaultdict(int)
        employee_gaps = {}
        
        for gap in skill_gaps:
            employee_gaps[gap.employee.employee_id] = gap
            for skill in gap.missing_required_skills:
                skill_demand[skill.name] += 1
        
        # Find high-demand skills (many people need them)
        high_demand_skills = sorted(skill_demand.items(), key=lambda x: x[1], reverse=True)
        
        # Recommend group training for high-demand skills
        group_training = []
        for skill_name, demand_count in high_demand_skills[:5]:
            if demand_count >= 3:  # If 3+ people need it
                # Find a course for this skill
                for course in all_courses:
                    if any(s.name == skill_name for s in course.skills_taught):
                        group_training.append({
                            'skill': skill_name,
                            'course': course.title,
                            'employees_needing': demand_count,
                            'hours_per_person': course.duration_minutes / 60
                        })
                        break
        
        return {
            'team_size': len(team),
            'group_training_opportunities': group_training,
            'individual_plans_needed': len([g for g in skill_gaps if g.gap_percentage > 0])
        }
