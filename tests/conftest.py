"""Shared test fixtures."""

import os

import pytest


@pytest.fixture(autouse=True)
def _restore_environ():
    # security._validator_llm_callable force-writes OPENAI_* into os.environ,
    # writes monkeypatch cannot restore because it never saw them.
    snapshot = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(snapshot)
