"""
Tests for FastAPI endpoints.
Run: pytest tests/test_api.py -v
Requires backend running: uvicorn app.main:app --port 8000
"""
import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv
load_dotenv()

from app.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["app"] == "ResearchNu"


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_sources_endpoint():
    r = client.get("/api/sources")
    assert r.status_code == 200
    data = r.json()
    assert "sources" in data
    assert len(data["sources"]) > 0


def test_query_endpoint_basic():
    r = client.post("/query", json={
        "query": "machine learning scoliosis",
        "user_type": "researcher",
        "privacy_mode": False,
    })
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data
    assert "detailed_answer" in data
    assert "novelty_score" in data
    assert "citations" in data
    assert isinstance(data["citations"], list)
    assert isinstance(data["novelty_score"], float)


def test_query_endpoint_founder():
    r = client.post("/query", json={
        "query": "AI drug discovery startup",
        "user_type": "founder",
    })
    assert r.status_code == 200
    assert r.json()["novelty_score"] >= 0


def test_query_with_focus_areas():
    r = client.post("/query", json={
        "query": "CRISPR gene therapy",
        "user_type": "researcher",
        "focus_areas": ["clinical trials", "safety"],
    })
    assert r.status_code == 200


def test_invalid_request():
    r = client.post("/query", json={})
    assert r.status_code == 422  # missing required field