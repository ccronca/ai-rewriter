"""
Multi-model provider support for AI Rewriter.

Supports: Gemini (default), Claude, Grok, Ollama.
Provider is selected via AI_PROVIDER environment variable.
"""

import logging
import os

_log = logging.getLogger(__name__)

VALID_PROVIDERS = {"gemini", "claude", "grok", "ollama"}

_LITELLM_MAP = {
    "gemini": "gemini/gemini-2.5-flash",
    "claude": "anthropic/claude-sonnet-4-6",
    "grok": "openai/grok-3",
}


class ProviderError(Exception):
    """Error from an AI provider API (auth, billing, rate limits, etc.)."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _get_provider() -> str:
    provider = os.environ.get("AI_PROVIDER", "gemini").lower()
    if provider not in VALID_PROVIDERS:
        raise ValueError(
            f"Unknown AI_PROVIDER: '{provider}'. "
            f"Valid options: {', '.join(sorted(VALID_PROVIDERS))}"
        )
    return provider


def get_litellm_model() -> str:
    """Return the LiteLLM model identifier for the configured provider."""
    provider = _get_provider()
    if provider == "ollama":
        model = os.environ.get("OLLAMA_MODEL", "llama3")
        return f"ollama_chat/{model}"
    return _LITELLM_MAP[provider]


def _generate_gemini(prompt: str) -> str:
    from google import genai
    from google.genai.errors import APIError

    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except APIError as e:
        raise ProviderError(str(e), status_code=e.code) from e


def _generate_claude(prompt: str) -> str:
    import anthropic

    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except anthropic.APIStatusError as e:
        raise ProviderError(e.message, status_code=e.status_code) from e


def _generate_grok(prompt: str) -> str:
    import openai

    try:
        client = openai.OpenAI(
            api_key=os.environ["XAI_API_KEY"],
            base_url="https://api.x.ai/v1",
        )
        response = client.chat.completions.create(
            model="grok-3",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except openai.APIStatusError as e:
        raise ProviderError(e.message, status_code=e.status_code) from e


def _generate_ollama(prompt: str) -> str:
    import openai

    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    if not base_url.startswith(("http://", "https://")):
        raise ProviderError(f"Invalid OLLAMA_BASE_URL: '{base_url}'", status_code=500)

    model = os.environ.get("OLLAMA_MODEL", "llama3")
    try:
        client = openai.OpenAI(
            api_key="ollama",
            base_url=f"{base_url}/v1",
        )
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except openai.APIStatusError as e:
        raise ProviderError(e.message, status_code=e.status_code) from e


_PROVIDERS = {
    "gemini": _generate_gemini,
    "claude": _generate_claude,
    "grok": _generate_grok,
    "ollama": _generate_ollama,
}


def generate(prompt: str) -> str:
    """Generate text using the configured AI provider."""
    provider = _get_provider()
    _log.info("Using AI provider: %s", provider)
    return _PROVIDERS[provider](prompt)
