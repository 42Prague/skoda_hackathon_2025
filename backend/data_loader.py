import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

class DataLoader:
    """Loads and preprocesses all data files on startup"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.employees = {}
        self.roles = {}
        self.employee_profiles = {}
        self.role_profiles = {}
        
        # Intermediate data structures
        self.course_attendance = defaultdict(list)  # personal_number -> list of course IDs
        self.skill_mapping = {}  # course_id -> list of skills
        self.employee_qualifications = defaultdict(list)  # personal_number -> list of qualifications
        self.required_qualifications = defaultdict(list)  # position_id -> list of required qualifications
        self.degreed_data = defaultdict(list)  # employee_id -> list of completed content
        
    def load_all(self):
        """Load all data files and build in-memory structures"""
        print("Loading data files...")
        
        # Try to load real data, fall back to mock data if files don't exist
        if self._check_data_files_exist():
            self._load_real_data()
        else:
            print("Data files not found, using mock data for development")
            self._load_mock_data()
            
        print(f"Loaded {len(self.employees)} employees and {len(self.roles)} roles")
        
    def _check_data_files_exist(self) -> bool:
        """Check if required data files exist"""
        required_files = [
            "ERP_SK1.Start_month - SE.xlsx",
            "ZHRPD_VZD_STA_007.xlsx",
        ]
        return all((self.data_dir / f).exists() for f in required_files)
    
    def _load_real_data(self):
        """Load real data from Excel files"""
        self._load_employees()
        self._load_courses()
        self._load_skills()
        self._load_qualifications()
        self._load_required_qualifications()
        self._load_degreed()
        self._build_employee_profiles()
        self._build_role_profiles()
    
    def _load_employees(self):
        """Load employee data from ERP_SK1.Start_month - SE.xlsx"""
        df = pd.read_excel(self.data_dir / "ERP_SK1.Start_month - SE.xlsx")
        
        # Handle prefixed column names (persstat_start_month.*)
        df.columns = [col.replace('persstat_start_month.', '') for col in df.columns]
        
        for _, row in df.iterrows():
            personal_number = str(row.get("personal_number", "")).strip()
            user_name = str(row.get("user_name", "")).strip()
            
            if not personal_number or personal_number == "nan":
                continue
            
            employee = {
                "personal_number": personal_number,
                "user_name": user_name,
                "profession": str(row.get("profession", "")).strip(),
                "planned_profession": str(row.get("planned_profession", "")).strip(),
                "planned_position_id": str(row.get("planned_position_id", "")),
                "planned_position": str(row.get("planned_position", "")),
            }
            
            self.employees[personal_number] = employee
            
            # Also collect unique roles from planned positions
            planned_pos_id = str(row.get("planned_position_id", "")).strip()
            planned_pos_name = str(row.get("planned_position", "")).strip()
            
            if planned_pos_id and planned_pos_id != "nan" and planned_pos_id not in self.roles:
                self.roles[planned_pos_id] = {
                    "role_id": planned_pos_id,
                    "name": planned_pos_name if planned_pos_name and planned_pos_name != "nan" else f"Position {planned_pos_id}",
                    "org_unit": "",
                    "description": f"Target position: {planned_pos_name}" if planned_pos_name else ""
                }
    
    def _load_courses(self):
        """Load course attendance from ZHRPD_VZD_STA_007.xlsx"""
        try:
            df = pd.read_excel(self.data_dir / "ZHRPD_VZD_STA_007.xlsx")
            
            for _, row in df.iterrows():
                participant_id = str(row.get("ID účastníka", "")).strip()
                course_id = str(row.get("IDOBJ", "")).strip()
                
                if participant_id and course_id and participant_id != "nan" and course_id != "nan":
                    self.course_attendance[participant_id].append({
                        "course_id": course_id,
                        "course_name": str(row.get("Označení typu akce", "")).strip(),
                        "start_date": row.get("Datum zahájení"),
                        "end_date": row.get("Datum ukončení")
                    })
            
            print(f"Loaded course attendance for {len(self.course_attendance)} participants")
        except Exception as e:
            print(f"Warning: Could not load course attendance: {e}")
    
    def _load_skills(self):
        """Load skill mapping from Skill_mapping.xlsx"""
        try:
            df = pd.read_excel(self.data_dir / "Skill_mapping.xlsx")
            
            for _, row in df.iterrows():
                course_id = str(row.get("ID Kurzu", "")).strip()
                skill = str(row.get("Kompetence / Skill", "")).strip()
                
                if course_id and skill and course_id != "nan" and skill != "nan":
                    if course_id not in self.skill_mapping:
                        self.skill_mapping[course_id] = []
                    self.skill_mapping[course_id].append({
                        "skill": skill,
                        "course_name": str(row.get("Název D", "")).strip(),
                        "category": str(row.get("Kategorie", "")).strip()
                    })
            
            print(f"Loaded skill mappings for {len(self.skill_mapping)} courses")
        except Exception as e:
            print(f"Warning: Could not load skill mapping: {e}")
    
    def _load_qualifications(self):
        """Load qualifications from ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx"""
        try:
            df = pd.read_excel(self.data_dir / "ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx")
            
            for _, row in df.iterrows():
                person_id = str(row.get("ID P", "")).strip()
                qual_id = str(row.get("ID Q", "")).strip()
                qual_name = str(row.get("Název Q", "")).strip()
                
                if person_id and qual_id and person_id != "nan" and qual_id != "nan":
                    end_date = row.get("Koncové datum")
                    # Check if qualification is active (end date is far future or NaT)
                    is_active = pd.isna(end_date) or (
                        isinstance(end_date, pd.Timestamp) and end_date.year > 2099
                    )
                    
                    self.employee_qualifications[person_id].append({
                        "id": qual_id,
                        "name": qual_name,
                        "active": is_active,
                        "start_date": row.get("Počát.datum"),
                        "end_date": end_date
                    })
            
            print(f"Loaded qualifications for {len(self.employee_qualifications)} people")
        except Exception as e:
            print(f"Warning: Could not load qualifications: {e}")
    
    def _load_required_qualifications(self):
        """Load required qualifications per role from ZPE_KOM_KVAL.xlsx"""
        try:
            df = pd.read_excel(self.data_dir / "ZPE_KOM_KVAL.xlsx")
            
            for _, row in df.iterrows():
                position_id = str(row.get("Číslo FM", "")).strip()
                qual_id = str(row.get("ID kvalifikace", "")).strip()
                qual_name = str(row.get("Kvalifikace", "")).strip()
                
                if position_id and qual_id and position_id != "nan" and qual_id != "nan":
                    self.required_qualifications[position_id].append({
                        "id": qual_id,
                        "name": qual_name
                    })
            
            print(f"Loaded required qualifications for {len(self.required_qualifications)} positions")
            
            # Build roles from unique position IDs
            for position_id in self.required_qualifications.keys():
                if position_id not in self.roles:
                    self.roles[position_id] = {
                        "role_id": position_id,
                        "name": f"Position {position_id}",
                        "org_unit": "",
                        "description": ""
                    }
        except Exception as e:
            print(f"Warning: Could not load required qualifications: {e}")
    
    def _load_degreed(self):
        """Load Degreed data"""
        try:
            df = pd.read_excel(self.data_dir / "Degreed.xlsx")
            
            for _, row in df.iterrows():
                employee_id = str(row.get("Employee ID", "")).strip()
                content_id = str(row.get("Content ID", "")).strip()
                
                if employee_id and employee_id != "nan":
                    self.degreed_data[employee_id].append({
                        "content_id": content_id,
                        "content_title": str(row.get("Content Title", "")).strip(),
                        "content_type": str(row.get("Content Type", "")).strip(),
                        "provider": str(row.get("Content Provider", "")).strip(),
                        "completed_date": row.get("Completed Date"),
                        "verified_minutes": row.get("Verified Learning Minutes", 0),
                        "estimated_minutes": row.get("Estimated Learning Minutes", 0)
                    })
            
            print(f"Loaded Degreed data for {len(self.degreed_data)} employees")
        except Exception as e:
            print(f"Warning: Could not load Degreed data: {e}")
    
    def _build_employee_profiles(self):
        """Build comprehensive employee profiles with skills and qualifications"""
        for pn, employee in self.employees.items():
            skills = []
            skill_counts = defaultdict(int)
            
            # Get skills from internal courses
            if pn in self.course_attendance:
                for course in self.course_attendance[pn]:
                    course_id = course["course_id"]
                    if course_id in self.skill_mapping:
                        for skill_data in self.skill_mapping[course_id]:
                            skill_name = skill_data["skill"]
                            skill_counts[skill_name] += 1
            
            # Convert skill counts to skill list
            for skill_name, count in skill_counts.items():
                # Determine level based on count
                if count >= 3:
                    level = "advanced"
                elif count >= 2:
                    level = "intermediate"
                else:
                    level = "beginner"
                
                skills.append({
                    "name": skill_name,
                    "source": "internal",
                    "count": count,
                    "level": level
                })
            
            # Get skills from Degreed (using user_name as Employee ID)
            user_name = employee.get("user_name", "")
            if user_name in self.degreed_data:
                degreed_skills = defaultdict(int)
                for content in self.degreed_data[user_name]:
                    content_title = content["content_title"]
                    # Simple skill extraction from title (could be improved with NLP)
                    if content_title:
                        degreed_skills[content_title] += 1
                
                for skill_name, count in degreed_skills.items():
                    skills.append({
                        "name": skill_name,
                        "source": "degreed",
                        "count": count,
                        "level": "beginner"  # Default for Degreed
                    })
            
            # Get qualifications
            qualifications = self.employee_qualifications.get(pn, [])
            
            self.employee_profiles[pn] = {
                "employee": employee,
                "skills": skills,
                "qualifications": qualifications
            }
    
    def _build_role_profiles(self):
        """Build role profiles with requirements and activities"""
        for role_id, role in self.roles.items():
            # Get required qualifications for this role
            req_quals = self.required_qualifications.get(role_id, [])
            
            # Extract unique skills from required qualifications (simple heuristic)
            required_skills = set()
            for qual in req_quals:
                qual_name = qual.get("name", "")
                # Simple skill extraction from qualification names
                # This could be improved with NLP or a lookup table
                if qual_name:
                    required_skills.add(qual_name)
            
            self.role_profiles[role_id] = {
                "role": role,
                "required_qualifications": req_quals,
                "required_skills": list(required_skills),
                "activities": []  # Could be populated from description files
            }
    
    def _load_mock_data(self):
        """Load mock data for development"""
        # Mock employees
        self.employees = {
            "00004241": {
                "personal_number": "00004241",
                "user_name": "DZCTSCQ",
                "profession": "Software Developer",
                "planned_profession": "Senior Software Developer",
                "planned_position_id": "POS001",
                "planned_position": "Senior Developer"
            },
            "00004242": {
                "personal_number": "00004242",
                "user_name": "ABCDEFG",
                "profession": "Junior Developer",
                "planned_profession": "Full Stack Developer",
                "planned_position_id": "POS002",
                "planned_position": "Full Stack Developer"
            },
            "00004243": {
                "personal_number": "00004243",
                "user_name": "HIJKLMN",
                "profession": "QA Engineer",
                "planned_profession": "QA Lead",
                "planned_position_id": "POS003",
                "planned_position": "QA Team Lead"
            }
        }
        
        # Mock roles
        self.roles = {
            "POS001": {
                "role_id": "POS001",
                "name": "Senior Developer",
                "org_unit": "SEA/1",
                "description": "Lead development of complex features"
            },
            "POS002": {
                "role_id": "POS002",
                "name": "Full Stack Developer",
                "org_unit": "SEA/2",
                "description": "Develop both frontend and backend"
            },
            "POS003": {
                "role_id": "POS003",
                "name": "QA Team Lead",
                "org_unit": "SEA/3",
                "description": "Lead quality assurance team"
            },
            "POS004": {
                "role_id": "POS004",
                "name": "DevOps Engineer",
                "org_unit": "SEA/4",
                "description": "Manage infrastructure and deployments"
            }
        }
        
        # Mock employee profiles
        self.employee_profiles = {
            "00004241": {
                "employee": self.employees["00004241"],
                "skills": [
                    {"name": "JavaScript", "source": "internal", "count": 3, "level": "advanced"},
                    {"name": "React", "source": "internal", "count": 2, "level": "intermediate"},
                    {"name": "Python", "source": "degreed", "count": 1, "level": "beginner"},
                    {"name": "SQL", "source": "internal", "count": 2, "level": "intermediate"}
                ],
                "qualifications": [
                    {"id": "Q001", "name": "Fire Safety Training", "active": True, "valid_until": "2026-12-31"},
                    {"id": "Q002", "name": "Information Security", "active": True, "valid_until": "2025-06-30"}
                ]
            },
            "00004242": {
                "employee": self.employees["00004242"],
                "skills": [
                    {"name": "HTML/CSS", "source": "internal", "count": 2, "level": "intermediate"},
                    {"name": "JavaScript", "source": "internal", "count": 1, "level": "beginner"},
                    {"name": "Git", "source": "degreed", "count": 1, "level": "beginner"}
                ],
                "qualifications": [
                    {"id": "Q001", "name": "Fire Safety Training", "active": True, "valid_until": "2026-12-31"}
                ]
            },
            "00004243": {
                "employee": self.employees["00004243"],
                "skills": [
                    {"name": "Test Automation", "source": "internal", "count": 3, "level": "advanced"},
                    {"name": "Selenium", "source": "internal", "count": 2, "level": "intermediate"},
                    {"name": "JIRA", "source": "degreed", "count": 1, "level": "intermediate"}
                ],
                "qualifications": [
                    {"id": "Q001", "name": "Fire Safety Training", "active": True, "valid_until": "2026-12-31"},
                    {"id": "Q003", "name": "ISTQB Foundation", "active": True, "valid_until": "9999-12-31"}
                ]
            }
        }
        
        # Mock role profiles
        self.role_profiles = {
            "POS001": {
                "role": self.roles["POS001"],
                "required_qualifications": [
                    {"id": "Q001", "name": "Fire Safety Training"},
                    {"id": "Q002", "name": "Information Security"},
                    {"id": "Q004", "name": "Advanced Architecture Training"}
                ],
                "required_skills": [
                    "JavaScript", "React", "Node.js", "TypeScript", "SQL", "Git"
                ],
                "activities": [
                    "Design and implement complex features",
                    "Code review and mentoring",
                    "Architecture decisions",
                    "Technical documentation"
                ]
            },
            "POS002": {
                "role": self.roles["POS002"],
                "required_qualifications": [
                    {"id": "Q001", "name": "Fire Safety Training"},
                    {"id": "Q002", "name": "Information Security"}
                ],
                "required_skills": [
                    "JavaScript", "React", "Node.js", "SQL", "REST APIs", "Git"
                ],
                "activities": [
                    "Develop frontend components",
                    "Implement backend APIs",
                    "Database design",
                    "Testing and debugging"
                ]
            },
            "POS003": {
                "role": self.roles["POS003"],
                "required_qualifications": [
                    {"id": "Q001", "name": "Fire Safety Training"},
                    {"id": "Q003", "name": "ISTQB Foundation"},
                    {"id": "Q005", "name": "Leadership Training"}
                ],
                "required_skills": [
                    "Test Automation", "Selenium", "JIRA", "Test Strategy", "Team Management"
                ],
                "activities": [
                    "Lead QA team",
                    "Define test strategy",
                    "Review test plans",
                    "Stakeholder communication"
                ]
            },
            "POS004": {
                "role": self.roles["POS004"],
                "required_qualifications": [
                    {"id": "Q001", "name": "Fire Safety Training"},
                    {"id": "Q002", "name": "Information Security"},
                    {"id": "Q006", "name": "Cloud Certification"}
                ],
                "required_skills": [
                    "Docker", "Kubernetes", "CI/CD", "AWS", "Linux", "Monitoring"
                ],
                "activities": [
                    "Manage cloud infrastructure",
                    "Set up CI/CD pipelines",
                    "Monitor system performance",
                    "Incident response"
                ]
            }
        }
    
    def get_employees(self) -> List[Dict[str, Any]]:
        """Get list of all employees"""
        return list(self.employees.values())
    
    def get_employee(self, personal_number: str) -> Dict[str, Any]:
        """Get employee by personal number"""
        return self.employees.get(personal_number)
    
    def get_roles(self) -> List[Dict[str, Any]]:
        """Get list of all roles"""
        return list(self.roles.values())
    
    def get_role(self, role_id: str) -> Dict[str, Any]:
        """Get role by ID"""
        return self.roles.get(role_id)
    
    def get_employee_profile(self, personal_number: str) -> Dict[str, Any]:
        """Get comprehensive employee profile"""
        return self.employee_profiles.get(personal_number)
    
    def get_role_profile(self, role_id: str) -> Dict[str, Any]:
        """Get comprehensive role profile"""
        return self.role_profiles.get(role_id)
    
    def compute_gaps(self, personal_number: str, role_id: str) -> Dict[str, Any]:
        """Compute skill and qualification gaps between employee and role"""
        employee_profile = self.get_employee_profile(personal_number)
        role_profile = self.get_role_profile(role_id)
        
        if not employee_profile or not role_profile:
            return None
        
        # Get employee's skills and qualifications
        employee_skills = {skill["name"] for skill in employee_profile.get("skills", [])}
        employee_qualifications = {
            qual["id"] for qual in employee_profile.get("qualifications", []) 
            if qual.get("active", False)
        }
        
        # Get role requirements
        required_skills = set(role_profile.get("required_skills", []))
        required_qualifications = {
            qual["id"] for qual in role_profile.get("required_qualifications", [])
        }
        
        # Compute gaps
        missing_skills = required_skills - employee_skills
        missing_qualifications = required_qualifications - employee_qualifications
        
        return {
            "role": role_profile["role"],
            "employee": employee_profile["employee"],
            "required_qualifications": role_profile.get("required_qualifications", []),
            "employee_qualifications": employee_profile.get("qualifications", []),
            "missing_qualifications": [
                qual for qual in role_profile.get("required_qualifications", [])
                if qual["id"] in missing_qualifications
            ],
            "required_skills": list(required_skills),
            "employee_skills": employee_profile.get("skills", []),
            "missing_skills": list(missing_skills),
            "activities": role_profile.get("activities", [])
        }

# Global instance
data_loader = None

def get_data_loader() -> DataLoader:
    """Get global data loader instance"""
    global data_loader
    if data_loader is None:
        data_loader = DataLoader()
        data_loader.load_all()
    return data_loader
