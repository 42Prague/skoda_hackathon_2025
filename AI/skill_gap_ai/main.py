"""
Main AI Orchestration - Skill Gap Analysis System
Entry point for employee and manager interfaces
"""
import os
import pandas as pd
import json
from typing import List, Dict, Optional
from data_models import (Employee, Position, Course, Skill, DataLoader)
from skill_gap_analyzer import SkillGapAnalyzer, TeamAnalyzer
from course_recommender import (CourseSkillMapper, DuplicateCourseDetector, 
                                LearningPathRecommender)
from manager_dashboard import ManagerDashboard


class SkillGapAI:
    """Main AI system for skill gap analysis and recommendations"""
    
    def __init__(self, data_folder: str):
        """
        Initialize the AI system
        
        Args:
            data_folder: Path to folder containing Excel data files
        """
        self.data_folder = data_folder
        self.employees = []
        self.courses = []
        self.skills = []
        self.positions = {}
        
        # Initialize components
        self.gap_analyzer = SkillGapAnalyzer()
        self.team_analyzer = TeamAnalyzer()
        self.course_mapper = CourseSkillMapper()
        self.duplicate_detector = DuplicateCourseDetector()
        self.recommender = LearningPathRecommender()
        self.manager_dashboard = ManagerDashboard()
        
        print("🤖 Skill Gap AI System Initialized")
    
    def load_data(self):
        """Load all data from Excel files"""
        print("\n📊 Loading data from Excel files...")
        
        # Load all Excel files from folder
        excel_files = [f for f in os.listdir(self.data_folder) if f.endswith('.xlsx')]
        
        if not excel_files:
            raise ValueError(f"No Excel files found in {self.data_folder}")
        
        # Read all files into one dataframe
        dfs = []
        for file in excel_files:
            file_path = os.path.join(self.data_folder, file)
            print(f"  - Reading {file}")
            df = pd.read_excel(file_path)
            dfs.append(df)
        
        combined_df = pd.concat(dfs, ignore_index=True)
        print(f"  ✓ Loaded {len(combined_df)} rows from {len(excel_files)} files")
        
        # Extract data
        print("\n🔧 Processing data...")
        self.employees = DataLoader.load_employees_from_excel(combined_df)
        print(f"  ✓ Found {len(self.employees)} employees")
        
        self.courses = DataLoader.load_courses_from_excel(combined_df)
        print(f"  ✓ Found {len(self.courses)} courses")
        
        self.skills = DataLoader.extract_skills_from_data(combined_df)
        print(f"  ✓ Extracted {len(self.skills)} unique skills")
        
        self.positions = DataLoader.create_position_requirements()
        print(f"  ✓ Created {len(self.positions)} position profiles")
        
        # Auto-map courses to skills
        print("\n🔗 Auto-mapping courses to skills...")
        self.course_mapper.map_courses_to_skills(self.courses, self.skills)
        print("  ✓ Course-to-skill mapping complete")
        
        # Detect duplicate courses
        print("\n🔍 Detecting duplicate courses...")
        duplicates = self.duplicate_detector.find_duplicates(self.courses)
        if duplicates:
            print(f"  ⚠️  Found {len(duplicates)} groups of duplicate courses")
            for i, group in enumerate(duplicates[:3], 1):
                print(f"     Group {i}: {', '.join([c.title[:30] for c in group])}")
        else:
            print("  ✓ No significant duplicates found")
        
        print("\n✅ Data loading complete!\n")
    
    def analyze_employee(self, employee_id: str, target_position_name: Optional[str] = None) -> Dict:
        """
        Analyze skill gaps for a specific employee
        
        Args:
            employee_id: Employee ID to analyze
            target_position_name: Target position (if None, uses employee's planned position)
            
        Returns:
            Dictionary with analysis and recommendations
        """
        # Find employee
        employee = next((e for e in self.employees if e.employee_id == employee_id), None)
        if not employee:
            return {'error': f'Employee {employee_id} not found'}
        
        # Determine target position
        if target_position_name:
            position = next((p for p in self.positions.values() if p.title.lower() == target_position_name.lower()), None)
        elif employee.planned_position:
            position = next((p for p in self.positions.values() if p.title.lower() in employee.planned_position.lower()), None)
        else:
            # Default to current position analysis
            position = next((p for p in self.positions.values() if p.title.lower() in employee.current_position.lower()), None)
        
        if not position:
            # Use first available position as fallback
            position = list(self.positions.values())[0]
        
        # Perform skill gap analysis
        skill_gap = self.gap_analyzer.analyze_employee(employee, position)
        
        # Get course recommendations
        recommendations = self.recommender.recommend_for_employee(
            employee, skill_gap, self.courses
        )
        
        return {
            'employee_info': {
                'id': employee.employee_id,
                'name': employee.name,
                'current_position': employee.current_position,
                'target_position': position.title,
                'current_skills': list(employee.get_skill_names()),
                'education': employee.education_background
            },
            'skill_gap_analysis': {
                'readiness_score': skill_gap.readiness_score,
                'gap_percentage': skill_gap.gap_percentage,
                'matched_skills': [s.name for s in skill_gap.matched_skills],
                'missing_required_skills': [s.name for s in skill_gap.missing_required_skills],
                'missing_optional_skills': [s.name for s in skill_gap.missing_optional_skills]
            },
            'recommendations': {
                'priority_courses': [
                    {
                        'course_title': c['course'].title,
                        'skill_target': c['skill'].name,
                        'hours': c['hours'],
                        'provider': c['course'].provider
                    } for c in recommendations['priority_courses']
                ],
                'learning_sequence': recommendations['learning_sequence'],
                'estimated_total_hours': recommendations['estimated_hours']
            }
        }
    
    def analyze_team(self, team_ids: Optional[List[str]] = None, 
                    department: Optional[str] = None) -> Dict:
        """
        Analyze entire team or department
        
        Args:
            team_ids: List of employee IDs (if None, analyzes all employees)
            department: Filter by department name
            
        Returns:
            Dictionary with team-level analytics
        """
        # Select team members
        if team_ids:
            team = [e for e in self.employees if e.employee_id in team_ids]
        elif department:
            team = [e for e in self.employees if department.lower() in e.department.lower()]
        else:
            team = self.employees[:50]  # Limit to first 50 for demo
        
        if not team:
            return {'error': 'No employees found for specified criteria'}
        
        print(f"\n📈 Analyzing team of {len(team)} employees...")
        
        # Analyze each employee
        skill_gaps = []
        for employee in team:
            # Use first position as default for team analysis
            position = list(self.positions.values())[0]
            gap = self.gap_analyzer.analyze_employee(employee, position)
            skill_gaps.append(gap)
        
        # Get recommendations for each employee
        all_recommendations = {}
        for gap in skill_gaps:
            rec = self.recommender.recommend_for_employee(gap.employee, gap, self.courses)
            all_recommendations[gap.employee.employee_id] = rec
        
        # Generate manager dashboard
        team_overview = self.manager_dashboard.generate_team_overview(team, skill_gaps)
        team_coverage = self.team_analyzer.analyze_team_coverage(
            team, list(self.positions.values())
        )
        training_priorities = self.manager_dashboard.generate_training_priorities(team, skill_gaps)
        training_roi = self.manager_dashboard.analyze_training_roi(team, skill_gaps, all_recommendations)
        
        return {
            'team_info': {
                'team_size': len(team),
                'analyzed_at': pd.Timestamp.now().isoformat()
            },
            'team_overview': team_overview,
            'skill_coverage': team_coverage,
            'training_priorities': training_priorities[:10],
            'training_roi': training_roi,
            'individual_recommendations_count': len(all_recommendations)
        }
    
    def generate_manager_report(self, output_file: Optional[str] = None) -> Dict:
        """
        Generate comprehensive manager report
        
        Args:
            output_file: Optional path to save JSON report
            
        Returns:
            Complete manager report
        """
        print("\n📋 Generating comprehensive manager report...")
        
        # Analyze full team
        team = self.employees[:100]  # Analyze up to 100 employees
        
        # Get skill gaps for all
        skill_gaps = []
        for employee in team:
            position = list(self.positions.values())[0]
            gap = self.gap_analyzer.analyze_employee(employee, position)
            skill_gaps.append(gap)
        
        # Get recommendations
        all_recommendations = {}
        for gap in skill_gaps:
            rec = self.recommender.recommend_for_employee(gap.employee, gap, self.courses)
            all_recommendations[gap.employee.employee_id] = rec
        
        # Generate full report
        report = self.manager_dashboard.export_report(team, skill_gaps, all_recommendations)
        
        # Add additional sections
        report['succession_risks'] = self.manager_dashboard.identify_succession_risks(
            team, list(self.positions.values())
        )
        report['quarterly_plan'] = self.manager_dashboard.generate_quarterly_plan(
            team, all_recommendations
        )
        
        # Save if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"  ✓ Report saved to {output_file}")
        
        return report
    
    def print_employee_report(self, employee_id: str):
        """Print formatted employee report"""
        result = self.analyze_employee(employee_id)
        
        if 'error' in result:
            print(f"❌ {result['error']}")
            return
        
        print("\n" + "="*70)
        print(f"📊 SKILL GAP ANALYSIS REPORT")
        print("="*70)
        
        emp = result['employee_info']
        print(f"\n👤 Employee: {emp['name']} (ID: {emp['id']})")
        print(f"   Current Position: {emp['current_position']}")
        print(f"   Target Position: {emp['target_position']}")
        
        gap = result['skill_gap_analysis']
        print(f"\n📈 Readiness Score: {gap['readiness_score']}/100")
        print(f"   Skill Gap: {gap['gap_percentage']}%")
        
        print(f"\n✅ Matched Skills ({len(gap['matched_skills'])}):")
        for skill in gap['matched_skills'][:5]:
            print(f"   • {skill}")
        
        if gap['missing_required_skills']:
            print(f"\n❗ Missing Required Skills ({len(gap['missing_required_skills'])}):")
            for skill in gap['missing_required_skills']:
                print(f"   • {skill}")
        
        rec = result['recommendations']
        if rec['priority_courses']:
            print(f"\n📚 Recommended Courses ({len(rec['priority_courses'])}):")
            for i, course in enumerate(rec['priority_courses'][:5], 1):
                print(f"   {i}. {course['course_title']}")
                print(f"      Target Skill: {course['skill_target']} | {course['hours']:.1f} hours")
        
        print(f"\n⏱️  Total Estimated Learning Time: {rec['estimated_total_hours']} hours")
        print("="*70 + "\n")


def main():
    """Main entry point - Example usage"""
    print("="*70)
    print("🎯 SKILL GAP ANALYSIS AI SYSTEM")
    print("="*70)
    
    # Initialize AI
    data_folder = os.path.join(os.path.dirname(__file__), "data")  # Use data folder in current directory
    ai = SkillGapAI(data_folder)
    
    # Load data
    try:
        ai.load_data()
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Example 1: Analyze individual employee
    if ai.employees:
        print("\n" + "="*70)
        print("EXAMPLE 1: Individual Employee Analysis")
        print("="*70)
        sample_employee = ai.employees[0]
        ai.print_employee_report(sample_employee.employee_id)
    
    # Example 2: Team analysis
    print("\n" + "="*70)
    print("EXAMPLE 2: Team Analysis")
    print("="*70)
    team_result = ai.analyze_team()
    print(f"\n📊 Team Overview:")
    print(f"   Team Size: {team_result['team_info']['team_size']}")
    print(f"   Average Readiness: {team_result['team_overview']['avg_readiness_score']}/100")
    print(f"   Employees Ready: {team_result['team_overview']['ready_count']}")
    print(f"   Needs Development: {team_result['team_overview']['needs_development_count']}")
    
    if team_result['training_priorities']:
        print(f"\n🎯 Top Training Priorities:")
        for priority in team_result['training_priorities'][:5]:
            print(f"   • {priority['skill']} - {priority['priority_level']}")
            print(f"     {priority['employees_missing']} employees need this ({priority['percentage_of_team']:.1f}%)")
    
    # Example 3: Generate manager report
    print("\n" + "="*70)
    print("EXAMPLE 3: Manager Report")
    print("="*70)
    report_file = os.path.join(os.path.dirname(__file__), "manager_report.json")
    manager_report = ai.generate_manager_report(report_file)
    
    print(f"\n💼 Manager Dashboard Summary:")
    print(f"   Total Training Hours Needed: {manager_report['training_roi']['total_training_hours_needed']}")
    print(f"   Estimated Training Cost: ${manager_report['training_roi']['estimated_training_cost']:,.2f}")
    print(f"   Expected ROI: {manager_report['training_roi']['months_to_breakeven']} months to break-even")
    
    print("\n✅ AI Analysis Complete!")
    print("="*70)


if __name__ == "__main__":
    main()
