"""Tests for the multi-model provider module."""

import pytest

from src.providers import (
    ProviderError,
    VALID_PROVIDERS,
    _get_provider,
    get_litellm_model,
    generate,
)


class TestGetProvider:
    """Provider selection and validation."""

    def test_defaults_to_gemini(self, monkeypatch):
        monkeypatch.delenv("AI_PROVIDER", raising=False)
        assert _get_provider() == "gemini"

    def test_accepts_valid_providers(self, monkeypatch):
        for provider in VALID_PROVIDERS:
            monkeypatch.setenv("AI_PROVIDER", provider)
            assert _get_provider() == provider

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "GEMINI")
        assert _get_provider() == "gemini"

    def test_rejects_invalid_provider(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "invalid")
        with pytest.raises(ValueError, match="Unknown AI_PROVIDER"):
            _get_provider()


class TestGetLitellmModel:
    """LiteLLM model identifier mapping."""

    def test_gemini_mapping(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "gemini")
        assert get_litellm_model() == "gemini/gemini-2.5-flash"

    def test_claude_mapping(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "claude")
        assert get_litellm_model() == "anthropic/claude-sonnet-4-6"

    def test_grok_mapping(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "grok")
        assert get_litellm_model() == "openai/grok-3"

    def test_ollama_mapping(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "ollama")
        monkeypatch.setenv("OLLAMA_MODEL", "mistral")
        assert get_litellm_model() == "ollama_chat/mistral"

    def test_ollama_default_model(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "ollama")
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        assert get_litellm_model() == "ollama_chat/llama3"


class TestProviderError:
    """ProviderError exception."""

    def test_default_status_code(self):
        err = ProviderError("something failed")
        assert err.status_code == 502
        assert str(err) == "something failed"

    def test_custom_status_code(self):
        err = ProviderError("rate limited", status_code=429)
        assert err.status_code == 429


class TestGenerate:
    """Provider dispatch."""

    def test_invalid_provider_raises(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "nonexistent")
        with pytest.raises(ValueError, match="Unknown AI_PROVIDER"):
            generate("test prompt")

    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "gemini")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        with pytest.raises(KeyError):
            generate("test prompt")


class TestOllamaBaseUrlValidation:
    """OLLAMA_BASE_URL validation."""

    def test_rejects_invalid_scheme(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "ollama")
        monkeypatch.setenv("OLLAMA_BASE_URL", "ftp://localhost:11434")
        with pytest.raises(ProviderError, match="Invalid OLLAMA_BASE_URL"):
            generate("test prompt")
