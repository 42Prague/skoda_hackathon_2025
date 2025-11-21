"""
Complete Skill Gap Analysis System
- Individual employee skill gap analysis
- Position requirement matching
- Personalized learning path recommendations
- Manager dashboard with team analytics
"""
from ai_training import SkillMatchingAI
from data_models import DataLoader, Employee, Position, Course, Skill, SkillGap
from skill_gap_analyzer import SkillGapAnalyzer
from course_recommender import LearningPathRecommender, DuplicateCourseDetector
import pandas as pd
from typing import Dict, List, Optional
import os


class SkillGapSystem:
    """Complete skill gap analysis system"""
    
    def __init__(self, data_folder='data'):
        self.data_folder = data_folder
        self.employees = []
        self.courses = []
        self.positions = {}
        self.skills_dict = {}
        
        # AI components
        self.skill_ai = SkillMatchingAI()
        self.gap_analyzer = SkillGapAnalyzer()
        self.recommender = LearningPathRecommender()
        self.duplicate_detector = DuplicateCourseDetector()
        
        # Load AI model
        try:
            self.skill_ai.load_model('models')
            print("✓ AI model loaded")
        except:
            print("⚠️ AI model not loaded - auto-mapping disabled")
        
        # Load data
        self._load_all_data()
    
    def _load_all_data(self):
        """Load employees, courses, and positions from data folder"""
        print("\n📊 Loading data...")
        
        excel_files = [f for f in os.listdir(self.data_folder) if f.endswith('.xlsx')]
        
        all_dfs = []
        for file in excel_files:
            try:
                df = pd.read_excel(os.path.join(self.data_folder, file))
                all_dfs.append(df)
            except:
                pass
        
        if not all_dfs:
            print("⚠️ No data files found")
            return
        
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # Load employees
        self.employees = DataLoader.load_employees_from_excel(combined_df)
        print(f"  ✓ Loaded {len(self.employees)} employees")
        
        # Load courses
        self.courses = DataLoader.load_courses_from_excel(combined_df)
        
        # Auto-map courses to skills using AI
        if self.skill_ai.trained:
            for course in self.courses:
                course_text = f"{course.title} {course.description}"
                predicted_skills = self.skill_ai.predict_skills_for_course(course_text, top_k=3)
                
                for skill_name, confidence in predicted_skills:
                    if confidence > 0.3:  # Only add if confident enough
                        skill = Skill(
                            skill_id=f"skill_{skill_name.lower().replace(' ', '_')}",
                            name=skill_name,
                            category="Auto-detected"
                        )
                        if skill not in course.skills_taught:
                            course.skills_taught.append(skill)
                            self.skills_dict[skill.skill_id] = skill
        
        print(f"  ✓ Loaded {len(self.courses)} courses")
        print(f"  ✓ Detected {len(self.skills_dict)} unique skills")
        
        # Create position requirements
        self.positions = self._create_positions()
        print(f"  ✓ Created {len(self.positions)} position profiles")
    
    def _create_positions(self) -> Dict[str, Position]:
        """Create position requirements based on common roles"""
        positions = {}
        
        # Extract unique professions from employee data
        professions = set(emp.current_position for emp in self.employees if emp.current_position)
        
        # Create positions with auto-detected skills
        for i, profession in enumerate(professions):
            # Get skills commonly associated with this profession
            required_skills = self._get_skills_for_position(profession)
            
            positions[profession.lower().replace(' ', '_')] = Position(
                position_id=f'pos_{i:03d}',
                title=profession,
                required_skills=required_skills[:5],  # Top 5 as required
                optional_skills=required_skills[5:10],  # Next 5 as optional
                description=f"Position: {profession}"
            )
        
        return positions
    
    def _get_skills_for_position(self, position_name: str) -> List[Skill]:
        """Auto-detect skills needed for a position using AI"""
        if not self.skill_ai.trained:
            return []
        
        # Use AI to predict what skills this position needs
        predictions = self.skill_ai.predict_skills_for_course(position_name, top_k=10)
        
        skills = []
        for skill_name, confidence in predictions:
            skill = Skill(
                skill_id=f"skill_{skill_name.lower().replace(' ', '_')}",
                name=skill_name,
                category="Position Requirement",
                level_required=3 if confidence > 0.7 else 2
            )
            skills.append(skill)
            self.skills_dict[skill.skill_id] = skill
        
        return skills
    
    def analyze_employee(self, employee_id: str, target_position: Optional[str] = None) -> Dict:
        """
        Analyze individual employee skill gaps
        
        Args:
            employee_id: Employee ID to analyze
            target_position: Target position name (uses planned_position if not provided)
            
        Returns:
            Complete analysis with gaps, readiness, and recommendations
        """
        # Find employee
        employee = next((e for e in self.employees if e.employee_id == employee_id), None)
        if not employee:
            return {"error": "Employee not found"}
        
        # Determine target position
        if not target_position:
            target_position = employee.planned_position or employee.current_position
        
        # Find position profile
        position_key = target_position.lower().replace(' ', '_')
        position = self.positions.get(position_key)
        
        if not position:
            # Create position on the fly
            required_skills = self._get_skills_for_position(target_position)
            position = Position(
                position_id=f'pos_custom',
                title=target_position,
                required_skills=required_skills[:5],
                optional_skills=required_skills[5:10]
            )
        
        # Analyze skill gap
        skill_gap = self.gap_analyzer.analyze_employee(employee, position)
        
        # Get personalized course recommendations
        recommended_courses = self.recommender.recommend_learning_path(
            employee,
            skill_gap,
            self.courses,
            max_courses=10
        )
        
        # Calculate detailed metrics
        analysis = {
            "employee": {
                "id": employee.employee_id,
                "name": employee.name,
                "current_position": employee.current_position,
                "target_position": target_position,
                "current_skills": [s.name for s in employee.current_skills],
                "completed_courses": len(employee.completed_courses),
                "total_learning_hours": employee.get_total_learning_hours()
            },
            "skill_gap_analysis": {
                "readiness_score": skill_gap.readiness_score,
                "gap_percentage": skill_gap.gap_percentage,
                "status": self._get_readiness_status(skill_gap.readiness_score),
                "matched_skills": [s.name for s in skill_gap.matched_skills],
                "missing_required_skills": [s.name for s in skill_gap.missing_required_skills],
                "missing_optional_skills": [s.name for s in skill_gap.missing_optional_skills]
            },
            "position_requirements": {
                "title": position.title,
                "required_skills": [s.name for s in position.required_skills],
                "optional_skills": [s.name for s in position.optional_skills],
                "total_skills_needed": len(position.required_skills) + len(position.optional_skills)
            },
            "recommended_learning_path": [
                {
                    "course_id": course.course_id,
                    "title": course.title,
                    "provider": course.provider,
                    "duration_hours": course.duration_minutes / 60,
                    "skills_taught": [s.name for s in course.skills_taught],
                    "priority": "HIGH" if any(s in skill_gap.missing_required_skills for s in course.skills_taught) else "MEDIUM",
                    "reason": self._get_recommendation_reason(course, skill_gap)
                }
                for course in recommended_courses[:10]
            ],
            "development_plan": {
                "estimated_hours_needed": sum(c.duration_minutes for c in recommended_courses[:10]) / 60,
                "estimated_completion_weeks": len(recommended_courses[:10]) * 2,  # Assume 2 weeks per course
                "priority_skills": [s.name for s in skill_gap.missing_required_skills],
                "next_steps": self._generate_next_steps(skill_gap, recommended_courses)
            }
        }
        
        return analysis
    
    def get_manager_dashboard(self, manager_id: Optional[str] = None) -> Dict:
        """
        Generate manager dashboard with team analytics
        
        Args:
            manager_id: Manager ID (if provided, filters to their team)
            
        Returns:
            Team overview, skill gaps, training priorities
        """
        # For now, analyze all employees (can filter by manager later)
        employees_to_analyze = self.employees
        
        all_analyses = []
        skill_gaps_summary = {}
        
        print(f"\n📊 Analyzing {len(employees_to_analyze)} employees...")
        
        for i, employee in enumerate(employees_to_analyze):
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(employees_to_analyze)}")
            
            analysis = self.analyze_employee(employee.employee_id)
            if "error" not in analysis:
                all_analyses.append(analysis)
                
                # Aggregate skill gaps
                for skill in analysis['skill_gap_analysis']['missing_required_skills']:
                    skill_gaps_summary[skill] = skill_gaps_summary.get(skill, 0) + 1
        
        # Calculate team statistics
        readiness_scores = [a['skill_gap_analysis']['readiness_score'] for a in all_analyses]
        
        dashboard = {
            "team_overview": {
                "total_employees": len(all_analyses),
                "average_readiness_score": sum(readiness_scores) / len(readiness_scores) if readiness_scores else 0,
                "ready_for_promotion": len([s for s in readiness_scores if s >= 80]),
                "needs_development": len([s for s in readiness_scores if s < 60]),
                "in_progress": len([s for s in readiness_scores if 60 <= s < 80])
            },
            "top_skill_gaps": [
                {
                    "skill": skill,
                    "employees_missing": count,
                    "percentage_of_team": (count / len(all_analyses)) * 100,
                    "priority": "HIGH" if count > len(all_analyses) * 0.5 else "MEDIUM"
                }
                for skill, count in sorted(skill_gaps_summary.items(), key=lambda x: x[1], reverse=True)[:10]
            ],
            "employee_details": [
                {
                    "employee_id": a['employee']['id'],
                    "name": a['employee']['name'],
                    "current_position": a['employee']['current_position'],
                    "target_position": a['employee']['target_position'],
                    "readiness_score": a['skill_gap_analysis']['readiness_score'],
                    "status": a['skill_gap_analysis']['status'],
                    "missing_skills_count": len(a['skill_gap_analysis']['missing_required_skills']),
                    "recommended_courses": len(a['recommended_learning_path'])
                }
                for a in all_analyses
            ],
            "training_recommendations": self._generate_team_training_plan(all_analyses, skill_gaps_summary),
            "statistics": {
                "total_courses_available": len(self.courses),
                "total_skills_tracked": len(self.skills_dict),
                "positions_defined": len(self.positions),
                "average_courses_per_employee": sum(a['employee']['completed_courses'] for a in all_analyses) / len(all_analyses) if all_analyses else 0
            }
        }
        
        return dashboard
    
    def _get_readiness_status(self, score: float) -> str:
        """Get readiness status from score"""
        if score >= 80:
            return "READY"
        elif score >= 60:
            return "IN_PROGRESS"
        else:
            return "NEEDS_DEVELOPMENT"
    
    def _get_recommendation_reason(self, course: Course, skill_gap: SkillGap) -> str:
        """Generate reason for course recommendation"""
        missing_skills = set(s.name for s in skill_gap.missing_required_skills + skill_gap.missing_optional_skills)
        course_skills = set(s.name for s in course.skills_taught)
        
        matched = missing_skills & course_skills
        
        if matched:
            return f"Teaches: {', '.join(list(matched)[:3])}"
        else:
            return "Related to target position"
    
    def _generate_next_steps(self, skill_gap: SkillGap, courses: List[Course]) -> List[str]:
        """Generate actionable next steps"""
        steps = []
        
        if skill_gap.missing_required_skills:
            steps.append(f"Complete {len(courses[:3])} priority courses to address critical skill gaps")
            steps.append(f"Focus on: {', '.join([s.name for s in skill_gap.missing_required_skills[:3]])}")
        
        if skill_gap.readiness_score < 60:
            steps.append("Schedule meeting with manager to discuss development plan")
        elif skill_gap.readiness_score >= 80:
            steps.append("Ready for promotion - discuss timing with manager")
        else:
            steps.append("Continue current development path - on track for promotion")
        
        return steps
    
    def _generate_team_training_plan(self, analyses: List[Dict], skill_gaps: Dict[str, int]) -> Dict:
        """Generate team-wide training recommendations"""
        total_employees = len(analyses)
        
        # Find most critical skills
        critical_skills = [
            skill for skill, count in skill_gaps.items()
            if count > total_employees * 0.3  # Affecting >30% of team
        ]
        
        return {
            "priority_skills": critical_skills[:5],
            "recommended_group_trainings": [
                {
                    "skill": skill,
                    "employees_affected": skill_gaps[skill],
                    "urgency": "HIGH" if skill_gaps[skill] > total_employees * 0.5 else "MEDIUM",
                    "suggested_action": f"Schedule group training for {skill}"
                }
                for skill in critical_skills[:5]
            ],
            "budget_estimate": {
                "total_courses_needed": sum(len(a['recommended_learning_path']) for a in analyses),
                "estimated_cost_per_course": 500,  # Example
                "total_estimated_cost": sum(len(a['recommended_learning_path']) for a in analyses) * 500
            }
        }


# Global instance
skill_gap_system = None


def get_system():
    """Get or create skill gap system instance"""
    global skill_gap_system
    if skill_gap_system is None:
        skill_gap_system = SkillGapSystem()
    return skill_gap_system
