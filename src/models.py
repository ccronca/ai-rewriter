"""Request models for AI Rewriter."""

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
