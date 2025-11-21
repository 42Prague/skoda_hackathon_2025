"""
Backend Data Engine for ŠKODA AI Skill Coach
- Cleans raw data from PostgreSQL tables
- Normalizes Czech/English variations
- Merges skills, qualifications, tests, learning history, professions, positions
- Produces JSON structures optimized for frontend visualizations using MUI X Charts
- Applies ŠKODA business logic for skill matching, readiness, learning recommendations
"""
import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import pandas as pd
from sqlalchemy import create_engine
from collections import defaultdict

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://skoda_user:skoda_password@postgres:5432/skoda_user"
)

# Create SQLAlchemy engine
_engine = None

def get_db_engine():
    """Get SQLAlchemy engine for pandas queries"""
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL)
    return _engine


# ============================================================================
# NORMALIZATION FUNCTIONS
# ============================================================================

# Czech to English skill name mappings
CZECH_ENGLISH_SKILL_MAP = {
    # Add common mappings here
    'programování': 'programming',
    'vývoj': 'development',
    'testování': 'testing',
    'analýza': 'analysis',
    'design': 'design',
    'řízení': 'management',
    'komunikace': 'communication',
    'týmová práce': 'teamwork',
    'vedení': 'leadership',
    'plánování': 'planning',
    'řešení problémů': 'problem solving',
}

# Expertise level normalization
EXPERTISE_MAP = {
    'expert': 5,
    'advanced': 4,
    'intermediate': 3,
    'basic': 2,
    'beginner': 1,
    'začátečník': 1,
    'základní': 2,
    'střední': 3,
    'pokročilý': 4,
    'expertní': 5,
    'expert': 5,
    'senior': 5,
    'junior': 2,
}


def normalize_skill_name(skill_name: str) -> str:
    """
    Normalize skill name to lowercase, unify Czech/English names.
    Remove duplicates aggressively (same skill code).
    """
    if not skill_name or pd.isna(skill_name):
        return ""
    
    # Convert to lowercase and strip
    normalized = str(skill_name).lower().strip()
    
    # Remove special characters and extra spaces
    normalized = re.sub(r'[^\w\s-]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Check Czech to English mapping
    for czech, english in CZECH_ENGLISH_SKILL_MAP.items():
        if czech in normalized:
            normalized = normalized.replace(czech, english)
    
    return normalized


def normalize_expertise_level(expertise: str) -> int:
    """
    Convert expertise to numeric scale (Beginner=1, Intermediate=3, Expert=5).
    """
    if not expertise or pd.isna(expertise):
        return 1
    
    expertise_lower = str(expertise).lower().strip()
    
    # Direct mapping
    if expertise_lower in EXPERTISE_MAP:
        return EXPERTISE_MAP[expertise_lower]
    
    # Try to extract number if it's already numeric
    try:
        num = int(float(expertise))
        if 1 <= num <= 5:
            return num
    except (ValueError, TypeError):
        pass
    
    # Default to intermediate if unknown
    return 3


def normalize_date(date_value) -> Optional[str]:
    """Convert date to YYYY-MM-DD format string"""
    if pd.isna(date_value) or date_value is None:
        return None
    
    if isinstance(date_value, str):
        try:
            # Try parsing common date formats
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d.%m.%Y', '%d/%m/%Y']:
                try:
                    dt = datetime.strptime(date_value, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        except:
            return None
    
    if isinstance(date_value, (date, datetime)):
        return date_value.strftime('%Y-%m-%d')
    
    return None


# ============================================================================
# DATA AGGREGATION FUNCTIONS
# ============================================================================

def get_employee_skills(employee_id: str) -> List[Dict]:
    """
    Get all skills for an employee, normalized and deduplicated.
    """
    engine = get_db_engine()
    
    query = """
        SELECT 
            skill_name,
            skill_theme,
            expertise_level,
            validity_end_date,
            skill_category
        FROM skill_mapping
        WHERE personal_number = %s
    """
    
    df = pd.read_sql_query(query, engine, params=(employee_id,))
    
    if df.empty:
        return []
    
    # Normalize and deduplicate
    skills_map = {}
    for _, row in df.iterrows():
        skill_name = normalize_skill_name(row['skill_name'])
        if not skill_name:
            continue
        
        # Use skill name as key for deduplication
        if skill_name not in skills_map:
            skills_map[skill_name] = {
                'name': skill_name,
                'expertiseLevel': normalize_expertise_level(row['expertise_level']),
                'validUntil': normalize_date(row['validity_end_date']),
                'theme': normalize_skill_name(row['skill_theme']) if pd.notna(row['skill_theme']) else None,
                'category': normalize_skill_name(row['skill_category']) if pd.notna(row['skill_category']) else None,
            }
        else:
            # Keep highest expertise level if duplicate
            existing_level = skills_map[skill_name]['expertiseLevel']
            new_level = normalize_expertise_level(row['expertise_level'])
            if new_level > existing_level:
                skills_map[skill_name]['expertiseLevel'] = new_level
    
    return list(skills_map.values())


def get_qualification_timeline(employee_id: str) -> List[Dict]:
    """
    Get qualification timeline for an employee.
    """
    engine = get_db_engine()
    
    query = """
        SELECT 
            qualification_name,
            completion_date,
            start_date,
            status
        FROM doklad_kvalifikace_komplet
        WHERE personal_number = %s
        ORDER BY completion_date DESC NULLS LAST, start_date DESC
    """
    
    df = pd.read_sql_query(query, engine, params=(employee_id,))
    
    if df.empty:
        return []
    
    timeline = []
    for _, row in df.iterrows():
        # Use completion date if available, otherwise start date
        date_value = row['completion_date'] if pd.notna(row['completion_date']) else row['start_date']
        date_str = normalize_date(date_value)
        
        if date_str:
            timeline.append({
                'name': str(row['qualification_name']),
                'date': date_str,
                'status': str(row['status']) if pd.notna(row['status']) else 'Unknown'
            })
    
    return timeline


def get_skills_expiring_soon(employee_id: str, days_ahead: int = 90) -> List[Dict]:
    """
    Get skills expiring within the next N days.
    """
    skills = get_employee_skills(employee_id)
    today = date.today()
    cutoff_date = today + timedelta(days=days_ahead)
    
    expiring = []
    for skill in skills:
        if skill['validUntil']:
            try:
                valid_until = datetime.strptime(skill['validUntil'], '%Y-%m-%d').date()
                if today <= valid_until <= cutoff_date:
                    expiring.append(skill)
            except (ValueError, TypeError):
                continue
    
    return expiring


def get_learning_recommendations(employee_id: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Get AI learning recommendations and skill gaps.
    Returns: (recommendations, skill_gaps)
    """
    engine = get_db_engine()
    
    # Get employee's current skills
    current_skills = get_employee_skills(employee_id)
    current_skill_names = {s['name'] for s in current_skills}
    
    # Get employee's planned profession
    emp_query = """
        SELECT planned_profession, current_profession
        FROM employees
        WHERE personal_number = %s
    """
    emp_df = pd.read_sql_query(emp_query, engine, params=(employee_id,))
    planned_profession = emp_df.iloc[0]['planned_profession'] if not emp_df.empty else None
    
    # Get available learning content from Degreed catalog
    catalog_query = """
        SELECT 
            c.content_id,
            c.category,
            c.difficulty_level,
            c.description
        FROM degreed_catalog c
        ORDER BY c.category
    """
    catalog_df = pd.read_sql_query(catalog_query, engine)
    
    # Also get learning content from degreed_data (actual available content)
    # Get content that other employees have completed (as examples of available content)
    available_content_query = """
        SELECT DISTINCT
            d.content_id,
            d.content_title,
            d.estimated_time_minutes,
            d.content_type,
            c.category,
            c.difficulty_level,
            c.description
        FROM degreed_data d
        LEFT JOIN degreed_catalog c ON d.content_id = c.content_id
        WHERE d.content_id NOT IN (
            SELECT content_id FROM degreed_data WHERE personal_number = %s
        )
        ORDER BY d.content_title
        LIMIT 100
    """
    available_df = pd.read_sql_query(available_content_query, engine, params=(employee_id,))
    
    # Get employee's completed learning
    completed_query = """
        SELECT content_id, content_title
        FROM degreed_data
        WHERE personal_number = %s
    """
    completed_df = pd.read_sql_query(completed_query, engine, params=(employee_id,))
    completed_content_ids = set(completed_df['content_id'].dropna().tolist())
    
    # Generate recommendations based on skill gaps
    recommendations = []
    skill_gaps = []
    seen_skills = set()
    
    # First, process catalog content
    for _, row in catalog_df.iterrows():
        content_id = row['content_id']
        if content_id in completed_content_ids:
            continue
        
        category = normalize_skill_name(row['category']) if pd.notna(row['category']) else None
        if category and category not in current_skill_names and category not in seen_skills:
            seen_skills.add(category)
            # Calculate gap size based on planned profession
            gap_size = 5 if planned_profession else 3
            skill_gaps.append({
                'skill': category,
                'gapSize': gap_size
            })
            
            # Create recommendation
            title = str(row['description']) if pd.notna(row['description']) else category
            recommendations.append({
                'title': title,
                'skill': category,
                'estimatedMinutes': 120,  # Default estimate
                'url': f'/learning/{content_id}',
                'contentId': content_id
            })
    
    # Also add recommendations from available content
    for _, row in available_df.iterrows():
        if len(recommendations) >= 10:
            break
            
        content_id = row['content_id']
        if pd.isna(content_id) or content_id in completed_content_ids:
            continue
        
        category = normalize_skill_name(row['category']) if pd.notna(row['category']) else None
        if category and category not in current_skill_names and category not in seen_skills:
            seen_skills.add(category)
            gap_size = 5 if planned_profession else 3
            skill_gaps.append({
                'skill': category,
                'gapSize': gap_size
            })
            
            title = str(row['content_title']) if pd.notna(row['content_title']) else category
            estimated_minutes = int(row['estimated_time_minutes']) if pd.notna(row['estimated_time_minutes']) else 120
            
            recommendations.append({
                'title': title,
                'skill': category,
                'estimatedMinutes': estimated_minutes,
                'url': f'/learning/{content_id}',
                'contentId': content_id
            })
    
    return recommendations[:10], skill_gaps  # Limit to top 10


def calculate_career_readiness_score(employee_id: str) -> int:
    """
    Calculate career readiness score (0-100) based on:
    - Skills match with planned profession
    - Qualifications completed
    - Learning progress
    """
    engine = get_db_engine()
    
    # Get employee info
    emp_query = """
        SELECT planned_profession, current_profession
        FROM employees
        WHERE personal_number = %s
    """
    emp_df = pd.read_sql_query(emp_query, engine, params=(employee_id,))
    
    if emp_df.empty:
        return 0
    
    planned_profession = emp_df.iloc[0]['planned_profession']
    if not planned_profession or pd.isna(planned_profession):
        return 50  # Default if no planned profession
    
    # Get skills
    skills = get_employee_skills(employee_id)
    skill_score = min(len(skills) * 5, 40)  # Max 40 points for skills
    
    # Get completed qualifications
    qual_query = """
        SELECT COUNT(*) as completed_count
        FROM doklad_kvalifikace_komplet
        WHERE personal_number = %s AND status = 'Completed'
    """
    qual_df = pd.read_sql_query(qual_query, engine, params=(employee_id,))
    qual_count = qual_df.iloc[0]['completed_count'] if not qual_df.empty else 0
    qual_score = min(qual_count * 10, 30)  # Max 30 points for qualifications
    
    # Get learning activity
    learning_query = """
        SELECT COUNT(*) as learning_count
        FROM degreed_data
        WHERE personal_number = %s
    """
    learning_df = pd.read_sql_query(learning_query, engine, params=(employee_id,))
    learning_count = learning_df.iloc[0]['learning_count'] if not learning_df.empty else 0
    learning_score = min(learning_count * 2, 30)  # Max 30 points for learning
    
    total_score = skill_score + qual_score + learning_score
    return min(total_score, 100)


def get_team_skills_heatmap(team_member_ids: List[str]) -> Tuple[List[str], List[str], List[List[int]]]:
    """
    Get team skills heatmap data.
    Returns: (skills, members, heatmap_matrix)
    """
    if not team_member_ids:
        return [], [], []
    
    engine = get_db_engine()
    
    # Get all unique skills across team
    skills_query = """
        SELECT DISTINCT skill_name
        FROM skill_mapping
        WHERE personal_number = ANY(%s)
    """
    skills_df = pd.read_sql_query(skills_query, engine, params=(team_member_ids,))
    all_skills = [normalize_skill_name(s) for s in skills_df['skill_name'].dropna().tolist()]
    unique_skills = sorted(list(set([s for s in all_skills if s])))
    
    # Get member names
    members_query = """
        SELECT personal_number, name
        FROM employees
        WHERE personal_number = ANY(%s)
    """
    members_df = pd.read_sql_query(members_query, engine, params=(team_member_ids,))
    member_map = dict(zip(members_df['personal_number'], members_df['name']))
    members = [member_map.get(mid, mid) for mid in team_member_ids if mid in member_map]
    
    # Build heatmap matrix
    heatmap_matrix = []
    for member_id in team_member_ids:
        member_skills = get_employee_skills(member_id)
        skill_levels = {s['name']: s['expertiseLevel'] for s in member_skills}
        
        row = []
        for skill in unique_skills:
            level = skill_levels.get(skill, 0)
            row.append(level)
        heatmap_matrix.append(row)
    
    return unique_skills, members, heatmap_matrix


def calculate_position_readiness(employee_id: str, target_role: str) -> Tuple[int, List[str]]:
    """
    Calculate position readiness score and blocking skills.
    Returns: (readiness_score, blocking_skills)
    """
    engine = get_db_engine()
    
    # Get employee skills
    employee_skills = get_employee_skills(employee_id)
    employee_skill_names = {s['name'] for s in employee_skills}
    employee_skill_levels = {s['name']: s['expertiseLevel'] for s in employee_skills}
    
    # Get employee's planned profession to infer required skills
    emp_query = """
        SELECT planned_profession, current_profession
        FROM employees
        WHERE personal_number = %s
    """
    emp_df = pd.read_sql_query(emp_query, engine, params=(employee_id,))
    planned_profession = emp_df.iloc[0]['planned_profession'] if not emp_df.empty and pd.notna(emp_df.iloc[0]['planned_profession']) else None
    
    # Get required skills for target role
    # Strategy: Look for employees with similar roles and extract their skills
    # In production, this would query a dedicated roles/skills mapping table
    target_role_normalized = normalize_skill_name(target_role)
    
    # Try to find employees with this role to infer required skills
    role_skills_query = """
        SELECT DISTINCT skill_name
        FROM skill_mapping sm
        JOIN employees e ON sm.personal_number = e.personal_number
        WHERE LOWER(e.current_profession) LIKE %s
           OR LOWER(e.planned_profession) LIKE %s
        LIMIT 20
    """
    role_pattern = f'%{target_role_normalized}%'
    role_skills_df = pd.read_sql_query(role_skills_query, engine, params=(role_pattern, role_pattern))
    required_skills = [normalize_skill_name(s) for s in role_skills_df['skill_name'].dropna().tolist()]
    required_skills = list(set([s for s in required_skills if s]))
    
    # If no skills found, use role name as required skill
    if not required_skills:
        required_skills = [target_role_normalized] if target_role_normalized else []
    
    # Calculate readiness
    blocking_skills = []
    matched_skills = 0
    total_required_level = 0
    
    for req_skill in required_skills:
        if req_skill not in employee_skill_names:
            blocking_skills.append(req_skill)
        else:
            level = employee_skill_levels.get(req_skill, 0)
            total_required_level += level
            if level < 3:  # Need at least intermediate level
                blocking_skills.append(req_skill)
            else:
                matched_skills += 1
    
    if not required_skills:
        readiness_score = 50
    else:
        # Calculate score based on matched skills and average skill level
        match_ratio = matched_skills / len(required_skills)
        avg_level = total_required_level / len(required_skills) if required_skills else 0
        level_score = min(avg_level / 5.0, 1.0)  # Normalize to 0-1
        
        readiness_score = int((match_ratio * 0.7 + level_score * 0.3) * 100)
    
    return readiness_score, blocking_skills


def get_company_skill_trends() -> Dict:
    """
    Get company-wide skill trends.
    """
    engine = get_db_engine()
    
    # Get yearly skill counts
    yearly_query = """
        SELECT 
            EXTRACT(YEAR FROM created_at) as year,
            COUNT(*) as count
        FROM skill_mapping
        WHERE created_at IS NOT NULL
        GROUP BY EXTRACT(YEAR FROM created_at)
        ORDER BY year
    """
    yearly_df = pd.read_sql_query(yearly_query, engine)
    
    yearly_counts = []
    for _, row in yearly_df.iterrows():
        year = int(row['year']) if pd.notna(row['year']) else None
        count = int(row['count']) if pd.notna(row['count']) else 0
        if year:
            yearly_counts.append({
                'year': year,
                'count': count
            })
    
    # Get emerging skills (skills added in last year)
    emerging_query = """
        SELECT DISTINCT skill_name
        FROM skill_mapping
        WHERE created_at >= CURRENT_DATE - INTERVAL '1 year'
        ORDER BY skill_name
        LIMIT 10
    """
    emerging_df = pd.read_sql_query(emerging_query, engine)
    emerging_skills = [normalize_skill_name(s) for s in emerging_df['skill_name'].dropna().tolist()]
    emerging_skills = [s for s in emerging_skills if s]
    
    # Get obsolete skills (skills not updated in last 3 years)
    obsolete_query = """
        SELECT DISTINCT skill_name
        FROM skill_mapping
        WHERE created_at < CURRENT_DATE - INTERVAL '3 years'
          AND skill_name NOT IN (
              SELECT DISTINCT skill_name
              FROM skill_mapping
              WHERE created_at >= CURRENT_DATE - INTERVAL '1 year'
          )
        ORDER BY skill_name
        LIMIT 10
    """
    obsolete_df = pd.read_sql_query(obsolete_query, engine)
    obsolete_skills = [normalize_skill_name(s) for s in obsolete_df['skill_name'].dropna().tolist()]
    obsolete_skills = [s for s in obsolete_skills if s]
    
    return {
        'yearlySkillCounts': yearly_counts,
        'emergingSkills': emerging_skills,
        'obsoleteSkills': obsolete_skills
    }

