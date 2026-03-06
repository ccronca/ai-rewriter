"""Tests for the rewrite API endpoint."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.providers import ProviderError


@pytest.fixture
def client():
    """Create a test client with security disabled."""
    import src.main as main_module

    main_module.ENABLE_SECURITY = False
    return TestClient(main_module.app)


@pytest.fixture
def secure_client():
    """Create a test client with security enabled."""
    import src.main as main_module

    main_module.ENABLE_SECURITY = True
    return TestClient(main_module.app)


class TestRewriteEndpoint:
    """Rewrite endpoint behavior."""

    @patch("src.main.generate", return_value="Rewritten text")
    def test_successful_rewrite(self, mock_gen, client):
        resp = client.post(
            "/rewrite", json={"text": "hello world", "mode": "default"}
        )
        assert resp.status_code == 200
        assert resp.json() == {"result": "Rewritten text"}

    @patch("src.main.generate", side_effect=ProviderError("quota exceeded", 429))
    def test_provider_error_propagates(self, mock_gen, client):
        resp = client.post(
            "/rewrite", json={"text": "hello world", "mode": "default"}
        )
        assert resp.status_code == 429
        assert "quota exceeded" in resp.json()["detail"]

    @patch("src.main.generate", side_effect=ProviderError("unauthorized", 401))
    def test_provider_auth_error(self, mock_gen, client):
        resp = client.post(
            "/rewrite", json={"text": "hello world", "mode": "default"}
        )
        assert resp.status_code == 401


class TestSecurityToggle:
    """ENABLE_SECURITY env var behavior."""

    @patch("src.main.generate", return_value="ok")
    @patch("src.main.validate_input", side_effect=Exception("blocked"))
    def test_security_enabled_blocks(self, mock_val, mock_gen, secure_client):
        resp = secure_client.post(
            "/rewrite", json={"text": "bad input", "mode": "default"}
        )
        assert resp.status_code == 400
        assert "Security validation failed" in resp.json()["detail"]

    @patch("src.main.generate", return_value="ok")
    @patch("src.main.validate_input", side_effect=Exception("should not be called"))
    def test_security_disabled_skips(self, mock_val, mock_gen, client):
        resp = client.post(
            "/rewrite", json={"text": "hello", "mode": "default"}
        )
        assert resp.status_code == 200
        mock_val.assert_not_called()


class TestHealthEndpoint:

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
