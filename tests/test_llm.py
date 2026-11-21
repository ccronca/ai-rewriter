"""Tests for the provider-aware LLM completion helper."""

import types

import pytest

import src.llm as llm


def _fake_openai(monkeypatch, built, content):
    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.init_kwargs = kwargs
            built.append(self)
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(create=self._create)
            )

        def _create(self, **kwargs):
            self.create_kwargs = kwargs
            return types.SimpleNamespace(
                choices=[
                    types.SimpleNamespace(
                        message=types.SimpleNamespace(content=content)
                    )
                ]
            )

    monkeypatch.setattr(llm, "OpenAI", FakeOpenAI)


def test_enmaas_used_when_no_gemini_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("ENMAAS_KEY", "k")
    monkeypatch.setenv("ENMAAS_BASE_URL", "https://gw.example/v1")
    built = []
    _fake_openai(monkeypatch, built, content=" out ")

    assert llm.complete("hi") == "out"

    client = built[0]
    assert client.init_kwargs == {"base_url": "https://gw.example/v1", "api_key": "k"}
    assert client.create_kwargs["model"] == "rits/zai-org/glm-5-3"
    assert client.create_kwargs["messages"] == [{"role": "user", "content": "hi"}]


def test_gemini_used_when_both_keys_set(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("ENMAAS_KEY", "k")
    gen_calls = []

    class FakeModels:
        def generate_content(self, **kwargs):
            gen_calls.append(kwargs)
            return types.SimpleNamespace(text=" out ")

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setattr(llm.genai, "Client", FakeClient)

    class NeverOpenAI:
        def __init__(self, *args, **kwargs):
            raise AssertionError(
                "OpenAI must not be constructed when GEMINI_API_KEY is set"
            )

    monkeypatch.setattr(llm, "OpenAI", NeverOpenAI)

    assert llm.complete("hi") == "out"
    assert gen_calls == [{"model": "models/gemini-2.5-flash", "contents": "hi"}]


def test_missing_all_keys_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ENMAAS_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ENMAAS_KEY"):
        llm.complete("hi")


def test_enmaas_key_without_base_url_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("ENMAAS_KEY", "k")
    monkeypatch.delenv("ENMAAS_BASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="ENMAAS_BASE_URL"):
        llm.complete("hi")


def test_none_content_returns_empty(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("ENMAAS_KEY", "k")
    monkeypatch.setenv("ENMAAS_BASE_URL", "https://gw.example/v1")
    built = []
    _fake_openai(monkeypatch, built, content=None)

    assert llm.complete("hi") == ""
