"""
Škoda Mapping Tables
--------------------
Mapping dictionaries for skills, job titles, qualifications, courses, and job requirements.
"""

SKILL_MAPPING = {
    "Python": {
        "canonical": "Python",
        "synonyms_cz": ["python", "py"],
        "synonyms_en": ["python", "py", "python3"],
    },
    "JavaScript": {
        "canonical": "JavaScript",
        "synonyms_cz": ["javascript", "js"],
        "synonyms_en": ["javascript", "js", "ecmascript"],
    },
    "Java": {
        "canonical": "Java",
        "synonyms_cz": ["java"],
        "synonyms_en": ["java", "jvm"],
    },
    "C++": {
        "canonical": "C++",
        "synonyms_cz": ["c++", "cpp"],
        "synonyms_en": ["c++", "cpp", "c plus plus"],
    },
    "SQL": {
        "canonical": "SQL",
        "synonyms_cz": ["sql", "databáze"],
        "synonyms_en": ["sql", "database"],
    },
    "Docker": {
        "canonical": "Docker",
        "synonyms_cz": ["docker"],
        "synonyms_en": ["docker", "containers"],
    },
    "Kubernetes": {
        "canonical": "Kubernetes",
        "synonyms_cz": ["kubernetes", "k8s"],
        "synonyms_en": ["kubernetes", "k8s"],
    },
    "Git": {
        "canonical": "Git",
        "synonyms_cz": ["git"],
        "synonyms_en": ["git", "version control"],
    },
    "Linux": {
        "canonical": "Linux",
        "synonyms_cz": ["linux", "unix"],
        "synonyms_en": ["linux", "unix"],
    },
    "Agile": {
        "canonical": "Agile",
        "synonyms_cz": ["agile", "scrum", "agilní"],
        "synonyms_en": ["agile", "scrum"],
    },
}

JOB_TITLE_MAPPING = {
    "Software Engineer": {
        "cz": "Softwarový inženýr",
        "en": "Software Engineer",
        "synonyms_cz": ["Programátor", "Vývojář", "Vývojář softwaru"],
        "synonyms_en": ["Developer", "Programmer", "Software Developer"]
    },
    "Data Engineer": {
        "cz": "Datový inženýr",
        "en": "Data Engineer",
        "synonyms_cz": ["Datový specialista"],
        "synonyms_en": ["Data Specialist"]
    },
    "Project Manager": {
        "cz": "Projektový manažer",
        "en": "Project Manager",
        "synonyms_cz": ["PM", "Manažer projektu"],
        "synonyms_en": ["PM", "Project Lead"]
    },
    "Data Scientist": {
        "cz": "Datový vědec",
        "en": "Data Scientist",
        "synonyms_cz": ["Datový analytik"],
        "synonyms_en": ["Data Analyst"]
    },
    "DevOps Engineer": {
        "cz": "DevOps inženýr",
        "en": "DevOps Engineer",
        "synonyms_cz": ["DevOps specialista"],
        "synonyms_en": ["DevOps Specialist"]
    },
}

QUALIFICATION_MAPPING = {
    "QUAL_PYTHON_CERT": {
        "name_cz": "Certifikace Python",
        "name_en": "Python Certification",
        "mandatory_for_roles": ["Software Engineer", "Data Engineer"]
    },
    "QUAL_JAVA_CERT": {
        "name_cz": "Certifikace Java",
        "name_en": "Java Certification",
        "mandatory_for_roles": ["Software Engineer"]
    },
    "QUAL_PMP": {
        "name_cz": "PMP certifikace",
        "name_en": "PMP Certification",
        "mandatory_for_roles": ["Project Manager"]
    },
    "QUAL_CLOUD_AWS": {
        "name_cz": "AWS certifikace",
        "name_en": "AWS Certification",
        "mandatory_for_roles": ["DevOps Engineer"]
    },
}

COURSE_CATALOG_MAPPING = {
    "COURSE_PYTHON_BASICS": {
        "name_cz": "Python základy",
        "name_en": "Python Basics",
        "provider": "Škoda Academy",
        "duration_hours": 40.0,
        "skills_covered": ["Python", "Programming"],
        "qualifications_granted": ["QUAL_PYTHON_CERT"],
        "skoda_academy": True
    },
    "COURSE_JAVA_ADVANCED": {
        "name_cz": "Java pokročilé",
        "name_en": "Java Advanced",
        "provider": "Škoda Academy",
        "duration_hours": 60.0,
        "skills_covered": ["Java", "Object-Oriented Programming"],
        "qualifications_granted": ["QUAL_JAVA_CERT"],
        "skoda_academy": True
    },
    "COURSE_DOCKER": {
        "name_cz": "Docker a kontejnery",
        "name_en": "Docker and Containers",
        "provider": "Škoda Academy",
        "duration_hours": 24.0,
        "skills_covered": ["Docker", "Containers", "DevOps"],
        "qualifications_granted": [],
        "skoda_academy": True
    },
}

JOB_REQUIREMENT_MAPPING = {
    "Software Engineer": {
        "mandatory_skills": ["Python", "Git"],
        "mandatory_qualifications": ["QUAL_PYTHON_CERT"],
        "preferred_skills": ["Docker", "Kubernetes", "Agile"]
    },
    "Data Engineer": {
        "mandatory_skills": ["Python", "SQL"],
        "mandatory_qualifications": ["QUAL_PYTHON_CERT"],
        "preferred_skills": ["Docker", "Data Processing"]
    },
    "Project Manager": {
        "mandatory_skills": ["Agile", "Project Management"],
        "mandatory_qualifications": ["QUAL_PMP"],
        "preferred_skills": ["Leadership", "Communication"]
    },
    "DevOps Engineer": {
        "mandatory_skills": ["Docker", "Kubernetes", "Linux"],
        "mandatory_qualifications": ["QUAL_CLOUD_AWS"],
        "preferred_skills": ["CI/CD", "Infrastructure as Code"]
    },
}

def get_skill_mapping() -> dict:
    """Get skill mapping dictionary."""
    return SKILL_MAPPING

def get_job_title_mapping() -> dict:
    """Get job title mapping dictionary."""
    return JOB_TITLE_MAPPING

def get_qualification_mapping() -> dict:
    """Get qualification mapping dictionary."""
    return QUALIFICATION_MAPPING

def get_course_catalog_mapping() -> dict:
    """Get course catalog mapping dictionary."""
    return COURSE_CATALOG_MAPPING

def get_job_requirement_mapping() -> dict:
    """Get job requirement mapping dictionary."""
    return JOB_REQUIREMENT_MAPPING

