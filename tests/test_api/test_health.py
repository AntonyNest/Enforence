"""
Тести для health check endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app


@pytest.fixture
def client():
    """Тестовий HTTP клієнт."""
    app = create_app()
    return TestClient(app)


def test_health_check(client):
    """Перевірка health endpoint повертає 200."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_docs_available(client):
    """Перевірка доступності Swagger UI."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema(client):
    """Перевірка генерації OpenAPI схеми."""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert schema["info"]["title"] == "ENFORENCE API"
    assert "/health" in schema["paths"]
