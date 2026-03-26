"""Test projects endpoints."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_get_projects_empty(client: TestClient):
    """Test getting projects when database is empty."""
    response = client.get("/api/v1/projects")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.integration
def test_create_project(client: TestClient):
    """Test creating a new project."""
    project_data = {
        "name": "Test Project",
        "slug": "test-project",
        "description": "A test project"
    }
    
    response = client.post("/api/v1/projects", json=project_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == project_data["name"]
    assert data["slug"] == project_data["slug"]
    assert data["description"] == project_data["description"]
    assert "id" in data


@pytest.mark.integration
def test_get_project_by_id(client: TestClient):
    """Test getting a specific project by ID."""
    # Create a project first
    project_data = {
        "name": "Test Project",
        "slug": "test-project",
        "description": "A test project"
    }
    create_response = client.post("/api/v1/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    # Get the project
    response = client.get(f"/api/v1/projects/{project_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == project_data["name"]


@pytest.mark.integration
def test_get_nonexistent_project(client: TestClient):
    """Test getting a project that doesn't exist."""
    response = client.get("/api/v1/projects/99999")
    
    assert response.status_code == 404
