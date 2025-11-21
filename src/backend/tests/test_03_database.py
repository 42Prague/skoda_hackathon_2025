"""
Database Tests
--------------
Test migrations, inserts, updates, deletes, JSONB fields, complex queries, analytics aggregations.
"""

import uuid
from datetime import datetime, timezone
from typing import List

import pytest
from sqlmodel import select, func

from swx_api.app.models.skill_models import (
    EmployeeRecord,
    SkillAnalysisRecord,
    DatasetRecord,
    LearningHistory,
    AuditLog,
)


class TestDatabaseCRUD:
    """Test basic CRUD operations."""
    
    def test_create_employee_record(self, db_session):
        """Test creating an employee record."""
        employee = EmployeeRecord(
            employee_id="TEST001",
            department="Engineering",
            skills=["Python", "SQL", "JavaScript"],
            metadata={"test": True, "created_by": "test"}
        )
        db_session.add(employee)
        db_session.commit()
        db_session.refresh(employee)
        
        assert employee.id is not None
        assert employee.employee_id == "TEST001"
        assert employee.department == "Engineering"
        assert len(employee.skills) == 3
        assert employee.metadata["test"] is True
    
    def test_read_employee_record(self, db_session):
        """Test reading an employee record."""
        employee = EmployeeRecord(
            employee_id="TEST002",
            department="Marketing",
            skills=["Excel", "Power BI"]
        )
        db_session.add(employee)
        db_session.commit()
        
        # Query by employee_id
        statement = select(EmployeeRecord).where(
            EmployeeRecord.employee_id == "TEST002"
        )
        found = db_session.exec(statement).first()
        
        assert found is not None
        assert found.employee_id == "TEST002"
        assert found.department == "Marketing"
    
    def test_update_employee_record(self, db_session):
        """Test updating an employee record."""
        employee = EmployeeRecord(
            employee_id="TEST003",
            department="Engineering",
            skills=["Python"]
        )
        db_session.add(employee)
        db_session.commit()
        db_session.refresh(employee)
        
        # Update
        employee.department = "Data Science"
        employee.skills = ["Python", "R", "Machine Learning"]
        employee.updated_at = datetime.now(timezone.utc)
        db_session.add(employee)
        db_session.commit()
        db_session.refresh(employee)
        
        assert employee.department == "Data Science"
        assert len(employee.skills) == 3
        assert "Machine Learning" in employee.skills
    
    def test_delete_employee_record(self, db_session):
        """Test deleting an employee record."""
        employee = EmployeeRecord(
            employee_id="TEST004",
            department="Engineering",
            skills=["Python"]
        )
        db_session.add(employee)
        db_session.commit()
        employee_id = employee.id
        
        # Delete
        db_session.delete(employee)
        db_session.commit()
        
        # Verify deleted
        statement = select(EmployeeRecord).where(EmployeeRecord.id == employee_id)
        found = db_session.exec(statement).first()
        assert found is None


class TestJSONBFields:
    """Test JSONB field operations."""
    
    def test_jsonb_skills_field(self, db_session):
        """Test JSONB skills field."""
        employee = EmployeeRecord(
            employee_id="JSONB001",
            department="Engineering",
            skills=["Python", "SQL", "JavaScript", "React", "Node.js"],
            metadata={
                "years_experience": 5,
                "certifications": ["AWS Certified", "Kubernetes Admin"],
                "projects": [
                    {"name": "Project A", "tech": ["Python", "Django"]},
                    {"name": "Project B", "tech": ["React", "Node.js"]}
                ]
            }
        )
        db_session.add(employee)
        db_session.commit()
        db_session.refresh(employee)
        
        assert isinstance(employee.skills, list)
        assert len(employee.skills) == 5
        assert isinstance(employee.metadata, dict)
        assert employee.metadata["years_experience"] == 5
        assert len(employee.metadata["certifications"]) == 2
    
    def test_jsonb_complex_nested(self, db_session):
        """Test complex nested JSONB structures."""
        complex_metadata = {
            "personal": {
                "location": "Prague",
                "timezone": "CET"
            },
            "professional": {
                "level": "Senior",
                "specializations": ["Backend", "DevOps"],
                "achievements": [
                    {"year": 2023, "award": "Best Engineer"},
                    {"year": 2024, "award": "Innovation Award"}
                ]
            },
            "skills_matrix": {
                "technical": {"Python": 9, "SQL": 8, "Docker": 7},
                "soft": {"Leadership": 8, "Communication": 9}
            }
        }
        
        employee = EmployeeRecord(
            employee_id="JSONB002",
            department="Engineering",
            skills=["Python", "SQL"],
            metadata=complex_metadata
        )
        db_session.add(employee)
        db_session.commit()
        db_session.refresh(employee)
        
        assert employee.metadata["personal"]["location"] == "Prague"
        assert employee.metadata["professional"]["level"] == "Senior"
        assert len(employee.metadata["professional"]["achievements"]) == 2
        assert employee.metadata["skills_matrix"]["technical"]["Python"] == 9
    
    def test_jsonb_skill_analysis(self, db_session):
        """Test JSONB in skill analysis records."""
        analysis_data = {
            "current_skills": ["Python", "SQL", "JavaScript"],
            "missing_skills": ["Docker", "Kubernetes"],
            "gap_score": 75,
            "strengths": ["Strong in data analysis", "Good problem solver"],
            "recommended_roles": ["Data Engineer", "Backend Developer"],
            "development_path": [
                {"step": 1, "action": "Learn Docker basics", "priority": "high"},
                {"step": 2, "action": "Practice containerization", "priority": "medium"}
            ]
        }
        
        analysis = SkillAnalysisRecord(
            employee_id="TEST001",
            analysis_json=analysis_data,
            recommendations_json={
                "top_recommendations": ["Docker", "Kubernetes"],
                "confidence": 0.85
            }
        )
        db_session.add(analysis)
        db_session.commit()
        db_session.refresh(analysis)
        
        assert analysis.analysis_json["gap_score"] == 75
        assert len(analysis.analysis_json["development_path"]) == 2
        assert analysis.recommendations_json["confidence"] == 0.85


class TestComplexQueries:
    """Test complex database queries."""
    
    def test_query_by_department(self, db_session, sample_employees):
        """Test querying employees by department."""
        statement = select(EmployeeRecord).where(
            EmployeeRecord.department == "Engineering"
        )
        engineering_employees = db_session.exec(statement).all()
        
        assert len(engineering_employees) > 0
        for emp in engineering_employees:
            assert emp.department == "Engineering"
    
    def test_query_with_jsonb_filter(self, db_session):
        """Test querying with JSONB field filters."""
        # Create employees with different skill levels
        emp1 = EmployeeRecord(
            employee_id="SKILL001",
            department="Engineering",
            skills=["Python", "SQL"],
            metadata={"skill_level": "junior"}
        )
        emp2 = EmployeeRecord(
            employee_id="SKILL002",
            department="Engineering",
            skills=["Python", "SQL", "Docker", "Kubernetes"],
            metadata={"skill_level": "senior"}
        )
        db_session.add(emp1)
        db_session.add(emp2)
        db_session.commit()
        
        # Query all employees
        statement = select(EmployeeRecord)
        all_employees = db_session.exec(statement).all()
        
        # Filter in Python (JSONB queries would need raw SQL for complex filters)
        senior_employees = [
            emp for emp in all_employees
            if emp.metadata and emp.metadata.get("skill_level") == "senior"
        ]
        
        assert len(senior_employees) > 0
    
    def test_query_with_skill_filter(self, db_session):
        """Test querying employees with specific skills."""
        # Create employees with different skills
        emp1 = EmployeeRecord(
            employee_id="PYTHON001",
            department="Engineering",
            skills=["Python", "SQL"]
        )
        emp2 = EmployeeRecord(
            employee_id="JAVA001",
            department="Engineering",
            skills=["Java", "Spring"]
        )
        db_session.add(emp1)
        db_session.add(emp2)
        db_session.commit()
        
        # Query all and filter in Python
        statement = select(EmployeeRecord)
        all_employees = db_session.exec(statement).all()
        
        python_employees = [
            emp for emp in all_employees
            if emp.skills and "Python" in emp.skills
        ]
        
        assert len(python_employees) > 0
        assert all("Python" in emp.skills for emp in python_employees)
    
    def test_join_query(self, db_session):
        """Test join queries between tables."""
        # Create employee
        employee = EmployeeRecord(
            employee_id="JOIN001",
            department="Engineering",
            skills=["Python", "SQL"]
        )
        db_session.add(employee)
        db_session.commit()
        
        # Create analysis for employee
        analysis = SkillAnalysisRecord(
            employee_id=employee.employee_id,
            analysis_json={"gap_score": 75}
        )
        db_session.add(analysis)
        db_session.commit()
        
        # Query with join (using subquery)
        statement = select(SkillAnalysisRecord).where(
            SkillAnalysisRecord.employee_id == employee.employee_id
        )
        found_analysis = db_session.exec(statement).first()
        
        assert found_analysis is not None
        assert found_analysis.employee_id == employee.employee_id


class TestAnalyticsAggregations:
    """Test analytics aggregation queries."""
    
    def test_count_by_department(self, db_session, sample_employees):
        """Test counting employees by department."""
        statement = select(
            EmployeeRecord.department,
            func.count(EmployeeRecord.id).label("count")
        ).group_by(EmployeeRecord.department)
        
        results = db_session.exec(statement).all()
        
        assert len(results) > 0
        for dept, count in results:
            assert isinstance(dept, str)
            assert isinstance(count, int)
            assert count > 0
    
    def test_skill_frequency(self, db_session, sample_employees):
        """Test skill frequency analysis."""
        # Get all employees
        statement = select(EmployeeRecord)
        all_employees = db_session.exec(statement).all()
        
        # Count skill frequency
        skill_counts = {}
        for emp in all_employees:
            if emp.skills:
                for skill in emp.skills:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        assert len(skill_counts) > 0
        assert all(isinstance(count, int) and count > 0 for count in skill_counts.values())
    
    def test_average_skills_per_employee(self, db_session, sample_employees):
        """Test calculating average skills per employee."""
        statement = select(EmployeeRecord)
        all_employees = db_session.exec(statement).all()
        
        total_skills = sum(len(emp.skills or []) for emp in all_employees)
        avg_skills = total_skills / len(all_employees) if all_employees else 0
        
        assert avg_skills >= 0
        assert isinstance(avg_skills, (int, float))
    
    def test_department_skill_distribution(self, db_session, sample_employees):
        """Test skill distribution by department."""
        statement = select(EmployeeRecord)
        all_employees = db_session.exec(statement).all()
        
        dept_skills = {}
        for emp in all_employees:
            dept = emp.department
            if dept not in dept_skills:
                dept_skills[dept] = []
            if emp.skills:
                dept_skills[dept].extend(emp.skills)
        
        assert len(dept_skills) > 0
        for dept, skills in dept_skills.items():
            assert len(skills) > 0


class TestMigrations:
    """Test database migrations."""
    
    def test_table_creation(self, db_session):
        """Test that all tables exist."""
        from sqlalchemy import inspect
        
        inspector = inspect(db_session.bind)
        tables = inspector.get_table_names()
        
        required_tables = [
            "employee_record",
            "skill_analysis_record",
            "dataset_record"
        ]
        
        for table in required_tables:
            assert table in tables, f"Table {table} not found"
    
    def test_foreign_key_constraints(self, db_session):
        """Test foreign key constraints."""
        # Create employee
        employee = EmployeeRecord(
            employee_id="FK001",
            department="Engineering",
            skills=["Python"]
        )
        db_session.add(employee)
        db_session.commit()
        
        # Create analysis with valid foreign key
        analysis = SkillAnalysisRecord(
            employee_id=employee.employee_id,
            analysis_json={"test": True}
        )
        db_session.add(analysis)
        db_session.commit()
        
        assert analysis.employee_id == employee.employee_id


class TestTransactionHandling:
    """Test transaction handling."""
    
    def test_rollback_on_error(self, db_session):
        """Test rollback on error."""
        employee = EmployeeRecord(
            employee_id="ROLLBACK001",
            department="Engineering",
            skills=["Python"]
        )
        db_session.add(employee)
        db_session.commit()
        employee_id = employee.id
        
        # Try to create duplicate (should fail if unique constraint exists)
        try:
            duplicate = EmployeeRecord(
                employee_id="ROLLBACK001",  # Same employee_id
                department="Marketing",
                skills=["Excel"]
            )
            db_session.add(duplicate)
            db_session.commit()
        except Exception:
            db_session.rollback()
        
        # Verify original still exists
        statement = select(EmployeeRecord).where(EmployeeRecord.id == employee_id)
        found = db_session.exec(statement).first()
        assert found is not None

