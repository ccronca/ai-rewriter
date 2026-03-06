"""
Security module for AI Rewriter service using Guardrails AI.

Defends against:
- OWASP LLM01: Prompt Injection
- OWASP LLM04: Model Denial of Service
- Toxic content

Reference: https://owasp.org/www-project-top-10-for-large-language-model-applications/
"""

import logging

_log = logging.getLogger(__name__)
_input_guard = None
_guard_init_attempted = False


def _get_guard():
    global _input_guard, _guard_init_attempted
    if not _guard_init_attempted:
        _guard_init_attempted = True
        try:
            from guardrails import Guard
            from guardrails.hub import UnusualPrompt, ToxicLanguage
            from .providers import get_litellm_model

            _input_guard = Guard().use(
                UnusualPrompt(
                    llm_callable=get_litellm_model(), on_fail="exception"
                ),
                ToxicLanguage(
                    threshold=0.5, validation_method="sentence", on_fail="exception"
                ),
            )
        except ImportError:
            _log.warning(
                "Guardrails hub validators not installed. "
                "Security validation is disabled. "
                "Run 'guardrails hub install hub://guardrails/unusual_prompt "
                "hub://guardrails/toxic_language' to enable."
            )
    return _input_guard


def validate_input(text: str) -> str:
    """
    Validate input against security threats.

    Returns validated text. Falls back to passthrough if guardrails
    hub validators are not installed.
    """
    guard = _get_guard()
    if guard is None:
        return text
    validated_output = guard.validate(text)
    return validated_output.validated_output
