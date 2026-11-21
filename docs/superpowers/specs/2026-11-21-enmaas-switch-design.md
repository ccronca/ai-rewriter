# Switch ai-rewriter to EnMaaS (keep Gemini optional)

## Intent

Make Red Hat's EnMaaS gateway the default LLM provider. Keep the Gemini path
working when its API key is provided. The app must import cleanly without
`GEMINI_API_KEY` — today `src/main.py` crashes at import time without it.

## Why

The user has EnMaaS access (`ENMAAS_KEY` already in the environment). The
hosted GLM 5.3 model (`rits/zai-org/glm-5-3`) costs nothing and is text-only,
which fits this text-rewriting app. Removes the personal Google API key as a
hard dependency.

## Goals

- Default provider: EnMaaS — base URL from the `ENMAAS_BASE_URL` env var
  (OpenAI Chat Completions dialect), model `rits/zai-org/glm-5-3`, key from
  `ENMAAS_KEY`.
- Gemini is used when `GEMINI_API_KEY` is set (model unchanged:
  `gemini-2.5-flash`).
- No client or key required at import time; a missing key fails at request
  time with a clear error.
- The Guardrails `UnusualPrompt` validator follows the same provider path
  (it currently hardcodes a litellm `gemini/...` string and would break
  without `GEMINI_API_KEY`).

## Non-goals

- No provider/model selection config, no multi-provider abstraction.
- No change to prompts, modes, endpoints, or hotkey scripts.

## Constraints

- EnMaaS speaks OpenAI/Anthropic dialects, not the Gemini dialect, so the
  google-genai SDK cannot point at it — EnMaaS calls go through the openai SDK.
- Exact model ID `rits/zai-org/glm-5-3`; GLM 5.3 is text-only (fine here).
- The Guardrails `UnusualPrompt` validator's `llm_callable` parameter is a
  litellm model **string only** (verified from validator source — it passes it
  straight to `litellm.completion`). Hub install needs an unexpired
  guardrailsai.com token, unavailable here, so validator wiring is verified at
  unit level, not through a live guard.
- Both call paths verified live against the gateway from this machine:
  openai SDK with explicit `base_url`/`api_key`, and litellm with
  `openai/rits/zai-org/glm-5-3` + `OPENAI_API_KEY`/`OPENAI_API_BASE` env vars.

## Approaches

1. **Chosen:** one `complete(prompt)` helper in a new `src/llm.py` — Gemini
   when `GEMINI_API_KEY` is set, else EnMaaS via the openai SDK with explicit
   `base_url`/`api_key`. `main.py` calls it (avoids the circular import
   security.py ← main.py). The validator gets a provider-aware litellm string
   instead — `gemini/gemini-2.5-flash` when the Gemini key is set, else
   `openai/rits/zai-org/glm-5-3` with `OPENAI_API_KEY`/`OPENAI_API_BASE`
   pointing at EnMaaS (litellm reads its route from env).
2. litellm for both providers — rejected: extra translation layer for two
   fixed paths.
3. Drop Gemini entirely — rejected: user wants it kept.

## Local config (not committed)

- `.env`: add `ENMAAS_KEY` (copy from shell), comment out `GEMINI_API_KEY`
  (rollback = uncomment one line).
