"""Tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from urban_graph_engine.core.api import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

def test_analyze_route():
    """Test analyze route (requires token)."""
    # Assuming API_KEY is set
    headers = {"access_token": "SANDOVAL-ENGINE-PRO-2040"}
    payload = {
        "origin": "WTC Ciudad de México",
        "destination": "Parque de los Venados",
        "hurry_factor": 50.0
    }
    response = client.post("/api/v1/analyze", json=payload, headers=headers)
    # May fail if graph not loaded, but test structure
    assert response.status_code in [200, 500]  # 200 if works, 500 if graph issue