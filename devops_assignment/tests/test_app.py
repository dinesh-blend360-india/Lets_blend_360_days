"""Basic automated tests for the FastAPI service."""

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_home_returns_service_message(client):
    response = client.get("/")
    payload = response.json()

    assert response.status_code == 200
    assert payload["service"] == "DevOps Python Service"
    assert payload["status"] == "success"


def test_health_endpoint_returns_healthy(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_info_endpoint_returns_application_details(client):
    response = client.get("/api/info")
    payload = response.json()

    assert response.status_code == 200
    assert payload["application"] == "devops-python-service"
    assert payload["framework"] == "FastAPI"
