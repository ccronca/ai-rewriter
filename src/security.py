"""
Security module for AI Rewriter service.

Defends against:
- OWASP LLM04: Model Denial of Service (input length limit)
- OWASP LLM01: Prompt Injection (when Guardrails Hub validators are available)
- Toxic content (when Guardrails Hub validators are available)

Guardrails validators are optional. They are enabled only when the
guardrails-hub validators are installed and a valid token is configured.

Reference: https://owasp.org/www-project-top-10-for-large-language-model-applications/
"""

import logging
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


class RewriteRequest(BaseModel):
    """Validated request model with security checks."""

    text: str
    mode: str = "default"

    @field_validator("text")
    @classmethod
    def validate_text_length(cls, v: str) -> str:
        """Mitigates LLM04 (DoS) by enforcing max length."""
        if len(v) > 5000:
            raise ValueError(f"Text too long ({len(v)} chars). Max: 5000")
        if len(v) < 1:
            raise ValueError("Text cannot be empty")
        return v

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Validate mode is allowed."""
        allowed_modes = ["default", "formal", "short", "friendly", "claude-prompt"]
        if v not in allowed_modes:
            raise ValueError(f"Invalid mode: {v}")
        return v


def _create_input_guard():
    """
    Try to create a Guardrails input guard with Hub validators.

    Returns None if validators are not installed or token is not configured.
    """
    try:
        from guardrails import Guard
        from guardrails.hub import UnusualPrompt, ToxicLanguage

        guard = Guard().use_many(
            UnusualPrompt(llm_callable="gemini/gemini-2.5-flash", on_fail="exception"),
            ToxicLanguage(
                threshold=0.5, validation_method="sentence", on_fail="exception"
            ),
        )
        logger.info("Guardrails Hub validators enabled (LLM01 + toxic content)")
        return guard
    except (ImportError, Exception) as e:
        logger.warning(f"Guardrails Hub validators not available, skipping: {e}")
        return None


# Try to initialize at startup; may be None if Hub is not configured
_input_guard = _create_input_guard()


def validate_input(text: str) -> str:
    """
    Validate input against security threats.

    Uses Guardrails Hub validators if available, otherwise only length
    validation (enforced by RewriteRequest) applies.

    Raises:
        Exception: If a validator blocks the input
    """
    if _input_guard is None:
        return text

    validated_output = _input_guard.validate(text)
    return validated_output.validated_output
