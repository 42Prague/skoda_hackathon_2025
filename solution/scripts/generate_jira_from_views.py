#!/usr/bin/env python3
"""
Generate realistic JIRA JSON from PostgreSQL database team views.
Uses Faker for data generation and OpenAI for realistic task descriptions.

The script queries team views directly (e.g., team_1, team_2) which should exist in your database.

Usage:
    python generate_jira_from_views.py [num_projects] [stories_per_project] [output_prefix] [--runs N] --teams team1 team2 ...
    
Arguments:
    num_projects: Number of projects per JSON (default: 2)
    stories_per_project: Number of stories per project (default: 2)
    output_prefix: Prefix for output filenames (default: "jira_generated")
    --runs N: Number of times to run per team (default: 10)
    --teams: List of team view names to query
    
Examples:
    # Query team_1 and team_2 views, generate 10 JSON files per team
    python generate_jira_from_views.py --teams team_1 team_2 --runs 10
    
    # Custom projects, stories, and number of runs
    python generate_jira_from_views.py 3 4 jira_data --runs 5 --teams team_1 team_2
    
    # Using environment variables
    export TEAMS="team_1,team_2"
    export NUM_RUNS=10
    python generate_jira_from_views.py
"""
import os
import sys
import json
import random
import hashlib
import time
from typing import List, Dict, Any
from faker import Faker
from openai import OpenAI
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://skoda_user:skoda_password@localhost:5432/skoda_user"
)

# OpenAI configuration (matching chatbot.py pattern)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_BASE_URL = os.getenv("OPENAI_API_BASE_URL")
OPEN_WEBUI_API_KEY = os.getenv("OPEN_WEBUI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Faker
fake = Faker()
Faker.seed(42)  # For reproducibility

# Initialize OpenAI client (matching chatbot.py pattern)
openai_client = None

def get_openai_client():
    """Initialize OpenAI client with support for Open WebUI proxy (matching chatbot.py pattern)"""
    global openai_client
    if openai_client is None:
        # If routing through Open WebUI, use Open WebUI API token
        # Otherwise, use OpenAI API key directly
        if OPENAI_API_BASE_URL and "open-webui" in OPENAI_API_BASE_URL:
            # Use Open WebUI API token for authentication
            api_key = OPEN_WEBUI_API_KEY or OPENAI_API_KEY
        else:
            # Use OpenAI API key directly
            api_key = OPENAI_API_KEY
        
        if not api_key:
            print("⚠️  Warning: API key not set. Will use Faker-generated descriptions only.")
            return None
        
        # Configure OpenAI client
        client_kwargs = {
            "api_key": api_key,
            "timeout": 180,  # 3 minutes timeout for LLM calls
            "max_retries": 2  # Retry up to 2 times on failure
        }
        
        # If OPENAI_API_BASE_URL is set, route through Open WebUI
        if OPENAI_API_BASE_URL:
            client_kwargs["base_url"] = OPENAI_API_BASE_URL
        
        openai_client = OpenAI(**client_kwargs)
    
    return openai_client

# Initialize client on module load
openai_client = get_openai_client()


def check_team_views_exist(engine, team_names: List[str]) -> Dict[str, bool]:
    """Check if team views exist in PostgreSQL"""
    print(f"Checking for team views: {', '.join(team_names)}...")
    
    with engine.connect() as conn:
        # Check if views exist
        placeholders = ', '.join([f"'{name}'" for name in team_names])
        result = conn.execute(text(f"""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public' 
            AND table_name IN ({placeholders})
        """))
        existing_views = {row[0] for row in result}
        
        view_status = {}
        for team_name in team_names:
            exists = team_name in existing_views
            view_status[team_name] = exists
            if exists:
                print(f"  ✓ Found view: {team_name}")
            else:
                print(f"  ✗ View not found: {team_name}")
        
        return view_status


def get_users_from_team_view(engine, team_view_name: str) -> List[Dict[str, Any]]:
    """Fetch users from a specific team view
    
    Args:
        engine: Database engine
        team_view_name: Name of the team view (e.g., 'team_1', 'team_2')
    """
    print(f"Fetching users from {team_view_name}...")
    
    with engine.connect() as conn:
        # Query the team view directly with actual columns
        # Note: Using f-string for table name is safe here as team_view_name is validated
        query = text(f"""
            SELECT 
                personal_number,
                user_name,
                profession,
                planned_profession,
                planned_position,
                education_branch_name,
                education_category_name,
                field_of_study_name,
                coordinator_group_id
            FROM {team_view_name}
            WHERE personal_number IS NOT NULL
            ORDER BY personal_number
        """)
        
        result = conn.execute(query)
        
        users = []
        for row in result:
            # Generate email from user_name or personal_number
            display_name = row.user_name or f"User {row.personal_number}"
            email = generate_email_from_name(display_name, row.personal_number)
            
            users.append({
                'user_id': row.personal_number,
                'display_name': display_name,
                'email_address': email,
                'profession': row.profession or '',
                'planned_profession': row.planned_profession or '',
                'planned_position': row.planned_position or '',
                'education_branch': row.education_branch_name or '',
                'education_category': row.education_category_name or '',
                'field_of_study': row.field_of_study_name or '',
                'coordinator_group_id': row.coordinator_group_id or ''
            })
    
        print(f"  ✓ Found {len(users)} users in {team_view_name}")
        return users


def get_users_from_team_views(engine, team_names: List[str]) -> List[Dict[str, Any]]:
    """Fetch users from multiple team views and combine them
    
    Args:
        engine: Database engine
        team_names: List of team view names (e.g., ['team_1', 'team_2'])
    """
    all_users = []
    user_ids_seen = set()  # To avoid duplicates
    
    for team_name in team_names:
        users = get_users_from_team_view(engine, team_name)
        for user in users:
            # Only add if we haven't seen this user_id before
            if user['user_id'] not in user_ids_seen:
                all_users.append(user)
                user_ids_seen.add(user['user_id'])
    
    print(f"✓ Total unique users: {len(all_users)}")
    return all_users


def generate_email_from_name(name: str, personal_number: str) -> str:
    """Generate email address from name or personal number"""
    if name and name != f"User {personal_number}":
        # Try to create email from name
        email_name = name.lower().replace(' ', '.').replace('_', '.')
        # Remove special characters
        email_name = ''.join(c for c in email_name if c.isalnum() or c == '.')
        if email_name:
            return f"{email_name}@skoda-auto.cz"
    
    # Fallback to personal number
    return f"{personal_number.lower().replace('-', '.')}@skoda-auto.cz"


def get_users_from_view2(engine, team_names: List[str] = None) -> List[Dict[str, Any]]:
    """Fetch users from view2 with additional information (deprecated - use get_users_from_team_views instead)
    
    This function is kept for backward compatibility but is not used when team views are specified.
    """
    return []


def generate_account_id(user_id: str) -> str:
    """Generate a JIRA-style account ID from user_id"""
    # Create a hash-based account ID similar to JIRA format
    hash_obj = hashlib.md5(user_id.encode())
    hash_hex = hash_obj.hexdigest()[:24]
    # Format: 5b10a2844c20165700ede21g (24 chars)
    return hash_hex


def generate_project_id(project_index: int) -> str:
    """Generate a project ID"""
    return str(10000 + project_index)


def generate_story_id(project_id: str, story_index: int) -> str:
    """Generate a story ID"""
    base_id = int(project_id)
    return str(base_id + story_index + 1)


def generate_subtask_id(story_id: str, subtask_index: int) -> str:
    """Generate a subtask ID"""
    base_id = int(story_id)
    return str(base_id + subtask_index + 1)


def generate_project_key(project_name: str) -> str:
    """Generate a project key from project name"""
    # Take first 4 uppercase letters/numbers
    key = ''.join(c.upper() for c in project_name if c.isalnum())[:4]
    if len(key) < 4:
        key = key.ljust(4, 'X')
    return key


def generate_story_key(project_key: str, story_index: int) -> str:
    """Generate a story key"""
    return f"{project_key}-{story_index + 1}"


def generate_subtask_key(project_key: str, subtask_index: int) -> str:
    """Generate a subtask key"""
    return f"{project_key}-{subtask_index + 2}"  # Start from 2 to avoid conflict with story


def create_atlassian_doc(text_content: str) -> Dict[str, Any]:
    """Create Atlassian Document Format structure"""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text_content
                    }
                ]
            }
        ]
    }


def generate_task_description_with_openai(task_type: str, context: str = "") -> str:
    """Generate realistic, detailed task description using OpenAI for skill extraction
    
    Generates comprehensive descriptions that include:
    - Technical requirements and implementation details
    - Specific technologies, frameworks, and tools
    - Skills and competencies needed (including domain expertise from user's background)
    - Business context and objectives
    - Acceptance criteria and deliverables
    """
    client = get_openai_client()
    if not client:
        return generate_fallback_description(task_type)
    
    try:
        prompt = f"""Generate a detailed, realistic {task_type} description for a software development project.
The description should be comprehensive (3-5 sentences, 100-200 words) and include:

1. **Technical Requirements**: Specific technologies, frameworks, libraries, or tools to be used
2. **Implementation Details**: How the feature should be built, architectural considerations
3. **Skills Required**: Programming languages, methodologies, AND domain expertise relevant to the user's background (HR, career management, pedagogy, economics, psychology, etc.)
4. **Business Context**: Why this is needed, what problem it solves, user impact - align with the user's profession and role
5. **Acceptance Criteria**: What needs to be delivered, testing requirements, documentation needs

IMPORTANT: The user's background context is provided below. Use this to make the task relevant to their profession and education:
- If they work in HR/Career Management: focus on HR systems, employee development platforms, career path tools, learning management systems
- If they have education in Pedagogy/Teaching: consider educational technology, learning platforms, training systems
- If they have Economics/Management background: focus on business systems, analytics, reporting, process optimization
- If they have Psychology background: consider user experience, behavioral analytics, assessment tools
- If they are Coordinators: focus on workflow systems, coordination tools, project management features

Make it realistic and specific. Include actual technology names (e.g., React, Python, PostgreSQL, Docker, Kubernetes, REST APIs, GraphQL, microservices, etc.) AND domain-specific tools (e.g., HRIS systems, LMS platforms, analytics tools, etc.).

Context: {context}

Example format for HR/Career Management role:
"As an HR specialist working on career management systems, I need to [action related to employee development] so that [benefit for employees/organization]. This requires implementing [specific feature] using [technologies like React for frontend, Python/FastAPI for backend, PostgreSQL for data]. The solution should integrate with existing HRIS systems and support [domain-specific requirements like skill assessments, career path recommendations]. Key skills needed include [programming languages], [frameworks], [methodologies], AND domain expertise in [HR practices, career development, talent management]. Deliverables include [specific outputs] with [testing/documentation requirements]."

Generate a detailed, professional description that reflects the user's professional background:"""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a senior technical project manager with expertise in software development AND domain knowledge in HR, career management, education, and business systems. Generate detailed, realistic task descriptions that include technical specifications, required skills (both technical AND domain-specific), and implementation details suitable for skill extraction. Always consider the user's profession and education background when generating tasks."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,  # Increased from 50 to allow detailed descriptions
            temperature=0.8
        )
        
        description = response.choices[0].message.content.strip()
        # Remove quotes if present
        description = description.strip('"\'')
        return description
    
    except Exception as e:
        print(f"⚠️  OpenAI error: {e}, using fallback")
        return generate_fallback_description(task_type)


def generate_fallback_description(task_type: str) -> str:
    """Generate detailed fallback description using Faker when OpenAI is unavailable"""
    tech_verbs = [
        "Implement", "Develop", "Create", "Design", "Build", "Optimize",
        "Refactor", "Add", "Update", "Enhance", "Fix", "Integrate", "Deploy"
    ]
    
    tech_nouns = [
        "authentication system", "database queries", "API endpoints",
        "user interface", "dashboard", "payment module", "notification service",
        "data pipeline", "caching layer", "search functionality", "analytics",
        "reporting system", "mobile app", "web application", "microservices"
    ]
    
    technologies = [
        "using React and TypeScript", "with Python and FastAPI", "leveraging PostgreSQL",
        "with Docker containers", "using Kubernetes orchestration", "with REST APIs",
        "implementing GraphQL endpoints", "using Node.js and Express", "with MongoDB",
        "leveraging Redis caching", "using AWS services", "with Azure cloud platform"
    ]
    
    skills = [
        "requiring expertise in JavaScript", "needing Python programming skills",
        "requiring database design knowledge", "needing API development experience",
        "requiring DevOps practices", "needing cloud architecture skills",
        "requiring frontend framework expertise", "needing backend development skills"
    ]
    
    verb = random.choice(tech_verbs)
    noun = random.choice(tech_nouns)
    tech = random.choice(technologies)
    skill = random.choice(skills)
    
    return f"{verb} {noun} {tech}. This task {skill} and involves creating comprehensive test coverage, writing technical documentation, and ensuring proper error handling and logging mechanisms are in place."


def generate_realistic_project_name() -> str:
    """Generate realistic project name"""
    project_types = [
        "Platform", "System", "Application", "Service", "Portal",
        "Dashboard", "Analytics", "Integration", "Migration", "Modernization"
    ]
    
    adjectives = [
        "Enterprise", "Cloud", "Digital", "Smart", "Advanced",
        "Next-Gen", "Unified", "Integrated", "Scalable", "Modern"
    ]
    
    if random.random() > 0.5:
        return f"{random.choice(adjectives)} {random.choice(project_types)}"
    else:
        return f"{random.choice(project_types)} {random.choice(['Platform', 'System', 'Solution'])}"


def generate_story_points() -> int:
    """Generate story points (Fibonacci-like sequence)"""
    points = [1, 2, 3, 5, 8, 13, 21]
    # Weight towards smaller points
    weights = [0.15, 0.20, 0.25, 0.20, 0.15, 0.04, 0.01]
    return random.choices(points, weights=weights)[0]


def generate_jira_json(users: List[Dict], 
                       num_projects: int = 2, stories_per_project: int = 2) -> Dict[str, Any]:
    """Generate JIRA JSON structure"""
    
    if not users:
        raise ValueError("No users found in views. Please ensure data is loaded in PostgreSQL.")
    
    # Select a primary user (first user or random)
    primary_user = users[0]
    user_id = primary_user['user_id']
    
    print(f"Generating JIRA JSON for user: {primary_user['display_name']} ({user_id})")
    
    projects = []
    
    for project_idx in range(num_projects):
        project_name = generate_realistic_project_name()
        project_key = generate_project_key(project_name)
        project_id = generate_project_id(project_idx)
        
        print(f"  Creating project: {project_name} ({project_key})")
        
        # Generate project description
        project_description = f"{project_name} for enterprise software development and delivery."
        
        stories = []
        
        for story_idx in range(stories_per_project):
            story_id = generate_story_id(project_id, story_idx)
            story_key = generate_story_key(project_key, story_idx)
            
            # Generate story description with rich context for skill extraction
            # Include all available user information for better context
            profession = primary_user.get('profession', '') or primary_user.get('planned_profession', '')
            position = primary_user.get('planned_position', '')
            education_branch = primary_user.get('education_branch', '')
            education_category = primary_user.get('education_category', '')
            field_of_study = primary_user.get('field_of_study', '')
            
            user_context = f"""User Background:
- Current/Planned Profession: {profession}
- Position: {position}
- Education Branch: {education_branch}
- Education Category: {education_category}
- Field of Study: {field_of_study}

Based on this background, generate a task that is relevant to their role. For example:
- HR Specialists/Career Management roles: HR systems, employee development platforms, career path tools, skill assessments, learning management systems
- Coordinators: workflow systems, coordination tools, project management, process automation
- Education/Pedagogy background: educational technology, learning platforms, training systems, curriculum management
- Economics/Management background: business analytics, reporting systems, process optimization, financial tools
- Psychology background: user experience design, behavioral analytics, assessment tools, data analysis"""
            
            project_context = f"Project: {project_name} ({project_key}), Project Description: {project_description}"
            context = f"{project_context}. {user_context}. Generate a detailed user story that includes: (1) Specific technical requirements and technologies (React, Python, PostgreSQL, APIs, etc.), (2) Domain-specific skills relevant to the user's profession and education, (3) Implementation details, (4) Business context aligned with their role, (5) Acceptance criteria. The description should be comprehensive (100-200 words) to enable skill extraction including both technical and domain expertise."
            story_description_text = generate_task_description_with_openai("user story", context)
            story_points = generate_story_points()
            
            # Select assignees (1-3 random users)
            num_assignees = random.randint(1, min(3, len(users)))
            assignees = random.sample(users, num_assignees)
            
            story_assignees = [
                {
                    "account_id": generate_account_id(assignee['user_id']),
                    "display_name": assignee['display_name'],
                    "email_address": assignee['email_address']
                }
                for assignee in assignees
            ]
            
            # Generate subtasks (1-3 per story)
            num_subtasks = random.randint(1, 3)
            subtasks = []
            
            for subtask_idx in range(num_subtasks):
                subtask_id = generate_subtask_id(story_id, subtask_idx)
                subtask_key = generate_subtask_key(project_key, subtask_idx + story_idx * 3)
                
                # Generate subtask description with detailed technical context
                # Include user context for domain-relevant subtasks
                profession = primary_user.get('profession', '') or primary_user.get('planned_profession', '')
                education_branch = primary_user.get('education_branch', '')
                field_of_study = primary_user.get('field_of_study', '')
                
                subtask_context = f"""Parent Story: {story_description_text}

User Background for context: Profession: {profession}, Education: {education_branch} - {field_of_study}

This subtask should be a specific, actionable technical task that contributes to the parent story. Include:
1. Specific implementation details and step-by-step approach
2. Technologies, frameworks, and tools to be used (be specific: React components, Python functions, database queries, API endpoints, etc.)
3. Technical skills required (programming languages, frameworks, databases, etc.)
4. Domain-specific knowledge needed (relevant to HR, career management, education, etc. based on user background)
5. Deliverables and acceptance criteria

Make it detailed (100-150 words) to enable comprehensive skill extraction."""
                subtask_description_text = generate_task_description_with_openai("subtask", subtask_context)
                subtask_points = generate_story_points()
                
                # Select 1-2 assignees for subtask
                num_subtask_assignees = random.randint(1, min(2, len(users)))
                subtask_assignees_list = random.sample(users, num_subtask_assignees)
                
                subtask_assignees = [
                    {
                        "account_id": generate_account_id(assignee['user_id']),
                        "display_name": assignee['display_name'],
                        "email_address": assignee['email_address']
                    }
                    for assignee in subtask_assignees_list
                ]
                
                subtasks.append({
                    "subtask_id": subtask_id,
                    "subtask_key": subtask_key,
                    "subtask_p_id": project_id,
                    "subtask_p_key": project_key,
                    "subtask_description": create_atlassian_doc(subtask_description_text),
                    "subtask_description_text": subtask_description_text,
                    "subtask_points": subtask_points,
                    "subtask_assignees": subtask_assignees
                })
            
            stories.append({
                "story_id": story_id,
                "story_key": story_key,
                "story_p_id": project_id,
                "story_p_key": project_key,
                "story_description": create_atlassian_doc(story_description_text),
                "story_description_text": story_description_text,
                "story_points": story_points,
                "story_assignees": story_assignees,
                "subtasks": subtasks
            })
        
        projects.append({
            "project_id": project_id,
            "project_key": project_key,
            "project_name": project_name,
            "project_description": project_description,
            "stories": stories
        })
    
    return {
        "user_id": generate_account_id(user_id),
        "projects": projects
    }


def main():
    """Main function"""
    print("=" * 60)
    print("Generating JIRA JSON from Database Views")
    print("=" * 60)
    
    # Parse command line arguments
    num_projects = int(os.getenv("NUM_PROJECTS", "2"))
    stories_per_project = int(os.getenv("STORIES_PER_PROJECT", "2"))
    output_prefix = os.getenv("OUTPUT_PREFIX", "jira_generated")
    num_runs = int(os.getenv("NUM_RUNS", "10"))  # Number of times to run per team
    team_names = None
    
    # Parse command line arguments
    # Usage: python script.py [num_projects] [stories_per_project] [output_prefix] [--runs N] [--teams team1 team2 ...]
    args = sys.argv[1:]  # Skip script name
    
    # Check for --runs flag
    runs_per_team = num_runs
    if '--runs' in args:
        runs_idx = args.index('--runs')
        try:
            runs_per_team = int(args[runs_idx + 1])
            args = args[:runs_idx] + args[runs_idx + 2:]  # Remove --runs and value
        except (ValueError, IndexError):
            print("⚠️  Invalid --runs value, using default: 10")
    
    # Check for --teams flag
    if '--teams' in args:
        teams_idx = args.index('--teams')
        team_names = args[teams_idx + 1:]
        # Remove --teams and team values from args for other parsing
        args = [arg for arg in args[:teams_idx] if arg != '--teams']
    
    # Parse other arguments
    if len(args) > 0:
        try:
            num_projects = int(args[0])
        except (ValueError, IndexError):
            pass
    if len(args) > 1:
        try:
            stories_per_project = int(args[1])
        except (ValueError, IndexError):
            pass
    if len(args) > 2:
        output_prefix = args[2]
    
    # Also check environment variable for teams
    if not team_names:
        teams_env = os.getenv("TEAMS")
        if teams_env:
            team_names = [t.strip() for t in teams_env.split(',')]
    
    if not team_names:
        print("⚠️  No team views specified. Please use --teams team_1 team_2 or set TEAMS environment variable.")
        print("   Example: python generate_jira_from_views.py --teams team_1 team_2 --runs 10")
        sys.exit(1)
    
    print(f"Team views to query: {', '.join(team_names)}")
    print(f"Number of runs per team: {runs_per_team}")
    
    try:
        # Connect to database
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ Connected to PostgreSQL")
        
        # Check if team views exist
        view_status = check_team_views_exist(engine, team_names)
        
        # Check if all required views exist
        missing_views = [name for name, exists in view_status.items() if not exists]
        if missing_views:
            print(f"\n✗ Error: The following team views do not exist: {', '.join(missing_views)}")
            print("   Please create these views in your PostgreSQL database first.")
            sys.exit(1)
        
        # Process each team separately
        for team_name in team_names:
            print(f"\n{'=' * 60}")
            print(f"Processing team: {team_name}")
            print(f"{'=' * 60}")
            
            # Fetch users from this team view
            users = get_users_from_team_views(engine, [team_name])
            
            if not users:
                print(f"⚠️  No users found in team view: {team_name}")
                continue
            
            # Generate multiple JSON files for this team
            generated_files = []
            for run_num in range(1, runs_per_team + 1):
                print(f"\n--- Run {run_num}/{runs_per_team} for {team_name} ---")
                
                # Generate unique filename for each run
                timestamp = int(time.time() * 1000)  # milliseconds
                output_file = f"{output_prefix}_{team_name}_run{run_num:02d}_{timestamp}.json"
                
                # Generate JIRA JSON (each run will be different due to randomization)
                print(f"Generating JIRA JSON ({num_projects} projects, {stories_per_project} stories each)...")
                jira_data = generate_jira_json(users, num_projects, stories_per_project)
                
                # Save to file
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(jira_data, f, indent=2, ensure_ascii=False)
                
                generated_files.append(output_file)
                
                print(f"✓ Generated: {output_file}")
                print(f"  Projects: {len(jira_data['projects'])}")
                total_stories = sum(len(p['stories']) for p in jira_data['projects'])
                print(f"  Stories: {total_stories}")
                total_subtasks = sum(
                    len(story['subtasks']) 
                    for project in jira_data['projects'] 
                    for story in project['stories']
                )
                print(f"  Subtasks: {total_subtasks}")
                
                # Small delay to ensure different timestamps
                time.sleep(0.1)
            
            print(f"\n✓ Completed {runs_per_team} runs for {team_name}")
            print(f"  Generated files:")
            for f in generated_files:
                print(f"    - {f}")
        
        print(f"\n{'=' * 60}")
        print("All teams processed successfully!")
        print(f"{'=' * 60}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

