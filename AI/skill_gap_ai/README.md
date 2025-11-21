# Skill Gap Analysis AI System

A comprehensive AI-powered system for analyzing employee skill gaps, recommending personalized learning paths, and providing manager-level insights.

## Features

### 👤 Employee Level
- **Skill Gap Analysis**: Compare employee skills against position requirements
- **Readiness Scoring**: 0-100 score indicating preparedness for target position
- **Personalized Learning Paths**: Tailored course recommendations based on:
  - Current skills and knowledge
  - Target position requirements
  - Learning history
  - Career goals
- **Prioritized Course Recommendations**: Focus on required skills first, then optional skills

### 👔 Manager Level
- **Team Overview Dashboard**: High-level team performance metrics
- **Skill Coverage Matrix**: Visual representation of team skill distribution
- **Training Priorities**: Data-driven recommendations for team training
- **ROI Analysis**: Calculate training costs vs. productivity gains
- **Succession Planning**: Identify risks and prepare backup candidates
- **Quarterly Training Plans**: Optimize training schedule and budget
- **Team Analytics**: 
  - Skill redundancy analysis
  - Critical skill identification
  - High performers and employees needing support

### 🤖 AI Capabilities
- **Auto-Mapping**: Automatically map courses to skills using NLP
- **Duplicate Detection**: Identify similar/duplicate courses
- **Fuzzy Skill Matching**: Recognize similar skills with different names
- **Smart Recommendations**: Context-aware learning path generation
- **Batch Analysis**: Analyze entire teams efficiently

## Installation

```bash
# Create project directory
mkdir -p ~/Documents/Projects/skill_gap_ai
cd ~/Documents/Projects/skill_gap_ai

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install pandas numpy openpyxl
```

## Project Structure

```
skill_gap_ai/
├── data_models.py           # Core data structures (Employee, Course, Skill, Position)
├── skill_gap_analyzer.py    # Skill gap analysis engine
├── course_recommender.py    # Course recommendations and auto-mapping
├── manager_dashboard.py     # Manager-level analytics
├── main.py                  # Main orchestration and examples
└── README.md               # This file
```

## Usage

### Basic Usage

```python
from main import SkillGapAI

# Initialize the AI system
ai = SkillGapAI(data_folder="/path/to/excel/files")

# Load data
ai.load_data()

# Analyze individual employee
result = ai.analyze_employee(employee_id="0001689")
print(f"Readiness Score: {result['skill_gap_analysis']['readiness_score']}/100")

# Analyze team
team_result = ai.analyze_team()
print(f"Team Average Readiness: {team_result['team_overview']['avg_readiness_score']}")

# Generate manager report
report = ai.generate_manager_report(output_file="manager_report.json")
```

### Running the Demo

```bash
# Make sure your Excel files are in the data folder
# Then run:
python main.py
```

## Data Requirements

The system expects Excel files with the following columns:

### Employee Data
- `persstat_start_month.personal_number` - Employee ID
- `persstat_start_month.user_name` - Employee name
- `persstat_start_month.profession` - Current position
- `persstat_start_month.planned_position` - Target position
- `persstat_start_month.basic_branch_of_education_grou2` - Education background

### Course Data
- `ID Kurzu` - Course ID
- `Název D` or `Content Title` - Course title
- `Content Provider` - Course provider
- `Kompetence / Skill` - Skills/competencies (comma-separated)
- `Verified Learning Minutes` - Course duration
- `Content URL` - Course link

## Key Components

### 1. Skill Gap Analyzer
```python
from skill_gap_analyzer import SkillGapAnalyzer

analyzer = SkillGapAnalyzer()
gap = analyzer.analyze_employee(employee, target_position)

print(f"Gap: {gap.gap_percentage}%")
print(f"Missing Skills: {[s.name for s in gap.missing_required_skills]}")
```

### 2. Course Recommender
```python
from course_recommender import LearningPathRecommender

recommender = LearningPathRecommender()
recommendations = recommender.recommend_for_employee(employee, skill_gap, courses)

print(f"Recommended Courses: {len(recommendations['priority_courses'])}")
print(f"Total Hours: {recommendations['estimated_hours']}")
```

### 3. Manager Dashboard
```python
from manager_dashboard import ManagerDashboard

dashboard = ManagerDashboard()
overview = dashboard.generate_team_overview(team, skill_gaps)
roi = dashboard.analyze_training_roi(team, skill_gaps, recommendations)

print(f"Training ROI: {roi['months_to_breakeven']} months to break-even")
```

## Customization

### Adding New Positions

Edit `data_models.py` in the `create_position_requirements()` method:

```python
positions['your_role'] = Position(
    position_id='pos_004',
    title='Your Role Title',
    required_skills=[
        Skill('sk_015', 'Skill 1', 'Category', 3),
        Skill('sk_016', 'Skill 2', 'Category', 4),
    ],
    optional_skills=[
        Skill('sk_017', 'Optional Skill', 'Category', 2),
    ]
)
```

### Adjusting ROI Calculations

Edit `manager_dashboard.py` in the `analyze_training_roi()` method to customize:
- Cost per training hour
- Average salary assumptions
- Productivity gain calculations

## Output Examples

### Employee Report
```
📊 SKILL GAP ANALYSIS REPORT
======================================================================
👤 Employee: John Doe (ID: 0001689)
   Current Position: IT Specialist
   Target Position: Senior IT Specialist

📈 Readiness Score: 75/100
   Skill Gap: 25%

✅ Matched Skills (5):
   • Programming
   • Database Management
   • System Administration
   • Cloud Computing
   • Problem Solving

❗ Missing Required Skills (3):
   • Advanced Networking
   • Security Architecture
   • Team Leadership

📚 Recommended Courses (3):
   1. Advanced Networking Fundamentals
      Target Skill: Advanced Networking | 12.5 hours
   2. Cybersecurity Architecture
      Target Skill: Security Architecture | 16.0 hours
   3. Technical Leadership
      Target Skill: Team Leadership | 8.5 hours

⏱️  Total Estimated Learning Time: 37.0 hours
```

### Manager Report (JSON)
```json
{
  "generated_at": "2025-11-20T16:30:00",
  "team_overview": {
    "team_size": 50,
    "avg_readiness_score": 68.5,
    "ready_count": 15,
    "developing_count": 25,
    "needs_development_count": 10
  },
  "training_roi": {
    "total_training_hours_needed": 850.5,
    "estimated_training_cost": 42525.00,
    "months_to_breakeven": 8.2
  }
}
```

## Future Enhancements

- Machine learning for better skill similarity matching
- Integration with LMS (Learning Management Systems)
- Real-time dashboard with visualizations
- Automated email reports
- Skills prediction based on industry trends
- Integration with HR systems
- Mobile app for employee access

## License

Proprietary - Internal Use Only

## Support

For questions or issues, contact the HR Development team.
