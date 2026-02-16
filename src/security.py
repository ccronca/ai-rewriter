"""
Security module for AI Rewriter service using Guardrails AI.

Defends against:
- OWASP LLM01: Prompt Injection
- OWASP LLM04: Model Denial of Service
- Toxic content

Reference: https://owasp.org/www-project-top-10-for-large-language-model-applications/
"""

from guardrails import Guard
from guardrails.hub import UnusualPrompt, ToxicLanguage
from pydantic import BaseModel, field_validator


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


def create_input_guard() -> Guard:
    """
    Create input validation guard.

    Validators:
    - UnusualPrompt: Detects jailbreaking and prompt injection (OWASP LLM01)
    - ToxicLanguage: Filters harmful content
    """
    return Guard().use_many(
        UnusualPrompt(llm_callable="gemini/gemini-2.5-flash", on_fail="exception"),
        ToxicLanguage(threshold=0.5, validation_method="sentence", on_fail="exception"),
    )


# Global guard instance
input_guard = create_input_guard()


def validate_input(text: str) -> str:
    """
    Validate input against security threats.

    Args:
        text: Input text to validate

    Returns:
        Validated text

    Raises:
        Exception: If validation fails
    """
    validated_output = input_guard.validate(text)
    return validated_output.validated_output
