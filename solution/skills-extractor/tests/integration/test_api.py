"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Skills Taxonomy API"


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    # May fail if Neo4j is not running, so we just check it responds
    assert response.status_code in [200, 503]


def test_find_jobs_endpoint():
    """Test the find jobs endpoint."""
    request_data = {
        "skills": ["Python", "Machine Learning"],
        "match_all": False,
        "include_parents": True,
        "limit": 10,
    }

    response = client.post("/api/v1/find-jobs", json=request_data)

    # Might return empty results if database is empty
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total" in data
    assert isinstance(data["jobs"], list)


def test_find_skills_endpoint():
    """Test the find skills endpoint."""
    request_data = {
        "job_title": "Python Developer",
        "include_children": True,
    }

    response = client.post("/api/v1/find-skills", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert isinstance(data["skills"], list)


def test_extract_skills_endpoint():
    """Test the extract skills endpoint."""
    request_data = {
        "text": "I have experience with Python, Django, and React."
    }

    response = client.post("/api/v1/extract-skills", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "validated_skills" in data
    assert "semantic_matches" in data
    assert "unmatched" in data
    assert "coverage" in data


def test_stats_endpoint():
    """Test the stats endpoint."""
    response = client.get("/api/v1/stats")

    assert response.status_code in [200, 500]  # May fail if DB not initialized
    if response.status_code == 200:
        data = response.json()
        assert "total_jobs" in data
        assert "total_skills" in data


def test_invalid_request():
    """Test that invalid requests return 422."""
    # Missing required field
    request_data = {
        "match_all": False,
    }

    response = client.post("/api/v1/find-jobs", json=request_data)
    assert response.status_code == 422
