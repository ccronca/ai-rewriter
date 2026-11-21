"""Tests for the FastAPI app: import and endpoint behavior."""

import importlib

from fastapi.testclient import TestClient

import src.main


def test_imports_without_any_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ENMAAS_KEY", raising=False)
    importlib.reload(src.main)


def test_rewrite_returns_result(monkeypatch):
    monkeypatch.setattr(src.main, "complete", lambda prompt: "cleaned")
    client = TestClient(src.main.app)
    response = client.post("/rewrite", json={"text": "hi", "mode": "default"})
    assert response.status_code == 200
    assert response.json() == {"result": "cleaned"}


def test_rewrite_invalid_mode_422(monkeypatch):
    monkeypatch.setattr(src.main, "complete", lambda prompt: "cleaned")
    client = TestClient(src.main.app)
    response = client.post("/rewrite", json={"text": "hi", "mode": "bogus"})
    assert response.status_code == 422
