"""
Test Configuration and Fixtures
--------------------------------
Comprehensive test infrastructure for ŠKODA AI Skill Coach backend.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

# Import app lazily to avoid MCP dependencies during test discovery
# from swx_api.core.main import app
from swx_api.core.database.db import get_db, SessionLocal
from swx_api.app.models.skill_models import (
    EmployeeRecord,
    SkillAnalysisRecord,
    DatasetRecord,
    LearningHistory,
    AuditLog,
)

# Test database URL (SQLite for speed)
TEST_DATABASE_URL = "sqlite:///./test_skoda_skill_coach.db"


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    # Create all tables
    SQLModel.metadata.create_all(engine)
    yield engine
    # Cleanup
    SQLModel.metadata.drop_all(engine)
    if os.path.exists("./test_skoda_skill_coach.db"):
        os.remove("./test_skoda_skill_coach.db")


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """Create a test client with database override."""
    # Import app here to avoid MCP dependencies during test discovery
    from swx_api.core.main import app
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session: Session) -> AsyncClient:
    """Create an async test client."""
    # Import app here to avoid MCP dependencies during test discovery
    from swx_api.core.main import app
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def temp_data_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test data."""
    temp_dir = Path(tempfile.mkdtemp())
    # Create subdirectories
    (temp_dir / "raw").mkdir()
    (temp_dir / "normalized").mkdir()
    (temp_dir / "processed").mkdir()
    (temp_dir / "analysis").mkdir()
    (temp_dir / "logs").mkdir()
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def mock_llm_response() -> Dict[str, Any]:
    """Mock LLM response for testing."""
    return {
        "current_skills": ["Python", "SQL", "JavaScript"],
        "missing_skills": ["Docker", "Kubernetes"],
        "gap_score": 75,
        "strengths": ["Strong in data analysis", "Good at problem-solving"],
        "recommended_roles": ["Data Engineer", "Backend Developer"],
        "development_path": [
            "Learn Docker basics",
            "Practice containerization",
            "Study Kubernetes fundamentals"
        ],
        "analysis_summary": "Employee has strong data skills but needs DevOps knowledge."
    }


@pytest.fixture(scope="function")
def mock_llm_client(mock_llm_response: Dict[str, Any]):
    """Mock LLM client for testing."""
    with patch("swx_api.app.services.llm_client.LLMClient") as mock_client:
        instance = mock_client.return_value
        instance.analyze_skills.return_value = mock_llm_response
        instance.call_llm.return_value = mock_llm_response
        yield instance


@pytest.fixture(scope="function")
def sample_employee_data() -> Dict[str, Any]:
    """Sample employee data for testing."""
    return {
        "employee_id": "EMP001",
        "department": "Engineering",
        "skills": ["Python", "SQL", "JavaScript", "React"],
        "metadata": {
            "years_experience": 5,
            "location": "Prague",
            "email": "emp001@example.com"
        }
    }


@pytest.fixture(scope="function")
def sample_employees(db_session: Session) -> list[EmployeeRecord]:
    """Create sample employee records in database."""
    employees = []
    departments = ["Engineering", "Marketing", "Sales", "HR", "Finance"]
    skills_pool = [
        "Python", "JavaScript", "React", "Node.js", "SQL", "Docker",
        "Kubernetes", "AWS", "Azure", "Java", "C++", "Go", "Rust",
        "TypeScript", "Vue.js", "Angular", "MongoDB", "PostgreSQL",
        "Redis", "Kafka", "GraphQL", "REST API", "Microservices",
        "CI/CD", "Git", "Linux", "Agile", "Scrum", "Project Management",
        "Data Analysis", "Machine Learning", "Deep Learning", "NLP",
        "Computer Vision", "Statistics", "Excel", "Power BI", "Tableau"
    ]
    
    for i in range(10):
        import random
        employee = EmployeeRecord(
            employee_id=f"EMP{i:03d}",
            department=random.choice(departments),
            skills=random.sample(skills_pool, k=random.randint(3, 8)),
            metadata={"test": True, "index": i}
        )
        db_session.add(employee)
        employees.append(employee)
    
    db_session.commit()
    for emp in employees:
        db_session.refresh(emp)
    
    return employees


@pytest.fixture(scope="function")
def sample_dataset_record(db_session: Session) -> DatasetRecord:
    """Create a sample dataset record."""
    dataset = DatasetRecord(
        dataset_id="test_dataset_001",
        metadata={
            "row_count": 100,
            "column_count": 5,
            "ingested_at": "2024-01-01T00:00:00Z"
        },
        summary={
            "dataset_name": "test_dataset",
            "data_quality_score": 95
        },
        dq_score=95
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)
    return dataset


@pytest.fixture(scope="function")
def csv_file_content() -> str:
    """Sample CSV file content."""
    return """employee_id,department,skills,email,years_experience
EMP001,Engineering,"Python,SQL,JavaScript",john.doe@example.com,5
EMP002,Marketing,"Excel,Power BI,Analytics",jane.smith@example.com,3
EMP003,Sales,"CRM,Salesforce,Communication",bob.jones@example.com,7
"""


@pytest.fixture(scope="function")
def excel_file_content() -> bytes:
    """Sample Excel file content (minimal binary)."""
    # This is a placeholder - in real tests, use openpyxl or xlsxwriter
    return b"PK\x03\x04"  # Minimal ZIP header (Excel is a ZIP file)


@pytest.fixture(scope="function")
def json_file_content() -> str:
    """Sample JSON file content."""
    return """[
    {
        "employee_id": "EMP001",
        "department": "Engineering",
        "skills": ["Python", "SQL", "JavaScript"],
        "email": "john.doe@example.com",
        "years_experience": 5
    },
    {
        "employee_id": "EMP002",
        "department": "Marketing",
        "skills": ["Excel", "Power BI", "Analytics"],
        "email": "jane.smith@example.com",
        "years_experience": 3
    }
]"""


@pytest.fixture(scope="function")
def txt_file_content() -> str:
    """Sample TXT file content."""
    return """Employee Skills Report

Employee ID: EMP001
Department: Engineering
Skills: Python, SQL, JavaScript
Email: john.doe@example.com
Years of Experience: 5

Employee ID: EMP002
Department: Marketing
Skills: Excel, Power BI, Analytics
Email: jane.smith@example.com
Years of Experience: 3
"""


@pytest.fixture(scope="function")
def malformed_csv_content() -> str:
    """Malformed CSV content for error testing."""
    return """employee_id,department,skills
EMP001,Engineering,"Python,SQL
EMP002,Marketing,Excel,Power BI
"""


@pytest.fixture(scope="function")
def large_dataset_content() -> str:
    """Large dataset for load testing."""
    header = "employee_id,department,skills,email,years_experience\n"
    rows = []
    for i in range(2000):
        rows.append(
            f"EMP{i:04d},Engineering,\"Python,SQL,JavaScript\",emp{i:04d}@example.com,{i % 10 + 1}\n"
        )
    return header + "".join(rows)


@pytest.fixture(scope="function")
def e2e_dataset_content() -> str:
    """E2E test dataset with 200 employees, 35 skills, PII, missing values."""
    import random
    
    departments = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations", "IT"]
    skills_pool = [
        "Python", "JavaScript", "React", "Node.js", "SQL", "Docker", "Kubernetes",
        "AWS", "Azure", "Java", "C++", "Go", "Rust", "TypeScript", "Vue.js",
        "Angular", "MongoDB", "PostgreSQL", "Redis", "Kafka", "GraphQL",
        "REST API", "Microservices", "CI/CD", "Git", "Linux", "Agile", "Scrum",
        "Project Management", "Data Analysis", "Machine Learning", "Deep Learning",
        "NLP", "Computer Vision", "Statistics"
    ]
    
    header = "employee_id,department,skills,email,years_experience,location\n"
    rows = []
    
    for i in range(200):
        emp_id = f"EMP{i:03d}"
        dept = random.choice(departments)
        # Inconsistent skill naming
        skill_variants = {
            "Python": ["python", "Python", "PYTHON", "Python3"],
            "JavaScript": ["javascript", "JS", "js", "JavaScript"],
            "React": ["react", "React", "ReactJS", "react.js"]
        }
        selected_skills = random.sample(skills_pool, k=random.randint(3, 10))
        # Add some inconsistent naming
        skills_list = []
        for skill in selected_skills:
            if skill in skill_variants:
                skills_list.append(random.choice(skill_variants[skill]))
            else:
                skills_list.append(skill)
        
        skills_str = ",".join(skills_list)
        email = f"emp{i:03d}@example.com" if random.random() > 0.1 else ""  # 10% missing emails
        years = random.randint(1, 15) if random.random() > 0.05 else ""  # 5% missing years
        location = random.choice(["Prague", "Brno", "Ostrava"]) if random.random() > 0.15 else ""  # 15% missing location
        
        rows.append(f"{emp_id},{dept},{skills_str},{email},{years},{location}\n")
    
    return header + "".join(rows)


@pytest.fixture(scope="function", autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="function")
def mock_tone_service():
    """Mock TONE service for testing."""
    with patch("swx_api.app.services.tone_service.get_tone_service") as mock:
        tone_service = MagicMock()
        tone_service.use_tone = False
        tone_service.build_tone_prompt.return_value = "test prompt"
        tone_service.parse_llm_response.return_value = {"test": "data"}
        tone_service.encode_to_tone.return_value = '{"test": "data"}'
        tone_service.decode_from_tone.return_value = {"test": "data"}
        mock.return_value = tone_service
        yield tone_service

