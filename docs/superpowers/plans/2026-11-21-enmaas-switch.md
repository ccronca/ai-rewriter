# EnMaaS Switch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make EnMaaS the default LLM provider, keep Gemini as an optional path gated on `GEMINI_API_KEY`, and stop requiring any key at import time.

**Architecture:** One `complete(prompt)` helper in new `src/llm.py` picks the provider per call: Gemini via google-genai when `GEMINI_API_KEY` is set, else EnMaaS via the openai SDK (base URL from the `ENMAAS_BASE_URL` env var, model `rits/zai-org/glm-5-3`). The Guardrails `UnusualPrompt` validator takes a litellm model string only (verified from its source), so it gets a provider-aware string with `OPENAI_API_KEY`/`OPENAI_API_BASE` set for the EnMaaS case. Both paths verified live against the gateway.

**Tech Stack:** Python 3.14, FastAPI, google-genai (existing, kept), openai SDK (already in uv.lock via litellm; becomes a direct dependency), pytest, guardrails-ai 0.8.1 + litellm 1.81.

**Spec:** `docs/superpowers/specs/2026-11-21-enmaas-switch-design.md`

## Global Constraints

- EnMaaS base URL: configured via the `ENMAAS_BASE_URL` env var (moved out of the code)
- EnMaaS model: `rits/zai-org/glm-5-3` (openai SDK) / `openai/rits/zai-org/glm-5-3` (litellm string)
- EnMaaS key env var: `ENMAAS_KEY` (user's name — NOT `ENMAAS_API_KEY`)
- Gemini unchanged: `models/gemini-2.5-flash` (google-genai) / `gemini/gemini-2.5-flash` (litellm)
- Precedence: `GEMINI_API_KEY` set → Gemini; else `ENMAAS_KEY` → EnMaaS; neither → `RuntimeError` at request time, never at import
- `pyproject.toml` gains `openai>=2.21.0`; google-genai stays
- All work in worktree `/home/ccota/repositories/github/ai-rewriter-enmaas-switch` (branch `enmaas-switch`), Conventional Commits subjects

## Review Focus

- GLM can return empty/None content → `complete()` returns `""`, not `AttributeError` — Task 1
- Both keys set → Gemini wins (documented precedence) — Task 1
- Import with no keys at all → must not raise (the regression this change fixes) — Task 2
- No keys at request time → clear `RuntimeError` naming the env vars — Task 1
- Validator wiring with no keys → guard disabled (`None`), app still imports/serves — Task 2

---

### Task 1: `src/llm.py` provider helper

**Files:**
- Create: `src/llm.py`
- Test: `tests/test_llm.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `complete(prompt: str) -> str`; constant `ENMAAS_MODEL = "rits/zai-org/glm-5-3"` (base URL via `ENMAAS_BASE_URL` env var); module-level `OpenAI` and `genai` names (tests monkeypatch `src.llm.OpenAI` / `src.llm.genai.Client`).

- [ ] **Step 1: Write failing tests** in `tests/test_llm.py` (monkeypatch fakes; no network):
  - `test_enmaas_used_when_no_gemini_key` — delenv `GEMINI_API_KEY`, setenv `ENMAAS_KEY=k`; fake `OpenAI` records init + create kwargs; assert `complete("hi") == "out"`, init `base_url == ENMAAS_BASE_URL`, init `api_key == "k"`, create `model == "rits/zai-org/glm-5-3"`, message content `" out "` → returned stripped `"out"`
  - `test_gemini_used_when_both_keys_set` — setenv both keys; fake `genai.Client` returns `.text = " out "`; assert result `"out"`, `generate_content` called with `model="models/gemini-2.5-flash"`, fake `OpenAI` never constructed
  - `test_missing_all_keys_raises` — delenv both; `pytest.raises(RuntimeError, match="ENMAAS_KEY")`
  - `test_none_content_returns_empty` — enmaas fake returns `content=None`; assert `complete(...) == ""`
- [ ] **Step 2:** `uv run pytest tests/test_llm.py -v` → FAIL (`No module named 'src.llm'`)
- [ ] **Step 3: Implement `src/llm.py`** — `complete(prompt)` with the two branches and the `RuntimeError("No LLM provider configured: set ENMAAS_KEY (EnMaaS) or GEMINI_API_KEY (Gemini)")`; both branches strip and guard `or ""` on the text/content. One `shortcut:` comment: clients are created per call — fine at clipboard-rewrite volume; cache if this ever serves concurrent traffic.
- [ ] **Step 4:** Add `"openai>=2.21.0"` to pyproject dependencies; `uv lock` (no new packages — already locked via litellm)
- [ ] **Step 5:** `uv run pytest tests/test_llm.py -v` → PASS
- [ ] **Step 6:** Commit `feat: add LLM completion helper with EnMaaS default and optional Gemini`

### Task 2: wire `main.py` + `security.py`

**Files:**
- Modify: `src/main.py`, `src/security.py`, `tests/test_security.py`
- Create: `tests/test_main.py`

**Interfaces:**
- Consumes: `complete()` from Task 1
- Produces: `src.main` endpoint `/rewrite` returns `{"result": complete(prompt)}`; `src.security._validator_llm_callable() -> str`

- [ ] **Step 1: Write failing tests**:
  - `tests/test_main.py::test_imports_without_any_key` — delenv both keys, `importlib.reload(src.main)` must not raise (regression test for the import crash)
  - `tests/test_main.py::test_rewrite_returns_result` — monkeypatch `src.main.complete` → `"cleaned"`; `fastapi.testclient.TestClient` POST `/rewrite` `{"text": "hi", "mode": "default"}` → 200 `{"result": "cleaned"}`; invalid mode still 422
  - `tests/test_security.py::test_validator_llm_callable_enmaas` — delenv `GEMINI_API_KEY`, setenv `ENMAAS_KEY=k`, delenv `OPENAI_API_KEY`/`OPENAI_API_BASE`; `_validator_llm_callable()` returns `"openai/rits/zai-org/glm-5-3"` and sets `OPENAI_API_KEY=k`, `OPENAI_API_BASE=$ENMAAS_BASE_URL`
  - `tests/test_security.py::test_validator_llm_callable_gemini` — setenv `GEMINI_API_KEY=g`; returns `"gemini/gemini-2.5-flash"`, leaves `OPENAI_*` unset
  - Update the three `skipif` conditions in `tests/test_security.py` to run when `GEMINI_API_KEY` **or** `ENMAAS_KEY` is set
- [ ] **Step 2:** `uv run pytest -v` → new tests FAIL
- [ ] **Step 3: Modify `src/main.py`** — drop `from google import genai` and the module-level `client`; `from .llm import complete`; `rewrite()` ends `return {"result": complete(prompt)}`
- [ ] **Step 4: Modify `src/security.py`** — add `import os`; new `_validator_llm_callable()`: gemini string when `GEMINI_API_KEY` set, else set `OPENAI_API_KEY`/`OPENAI_API_BASE` (force-set, not setdefault — a stale user `OPENAI_*` would misroute litellm) and return the enmaas string; `_create_input_guard` uses `UnusualPrompt(llm_callable=_validator_llm_callable(), on_fail="exception")`. Missing `ENMAAS_KEY` raises inside `_create_input_guard`, whose existing `except` disables the guard — unchanged optional behavior.
- [ ] **Step 5:** `uv run pytest -v` → PASS (validator classes still skip locally — hub validators not installed; existing optional behavior)
- [ ] **Step 6:** Commit `feat: route rewrite endpoint and validator through provider-aware LLM path`

### Task 3: docs + local env + live smoke test

**Files:**
- Modify: `.env.example`, `README.md`, `claude.md`
- Local, not committed: `.env` in the MAIN tree

- [ ] **Step 1:** `.env.example` — `ENMAAS_KEY` as the default provider key; `GEMINI_API_KEY` shown commented as the optional Gemini path
- [ ] **Step 2:** `README.md` — prerequisites (EnMaaS key via Atlas onboarding flow, corporate VPN), `.env` sample, privacy line updated ("only API calls go to the LLM provider — EnMaaS by default, Gemini optional")
- [ ] **Step 3:** `claude.md` — replace "`GEMINI_API_KEY` - Required" with the provider env docs (`ENMAAS_KEY` default, `GEMINI_API_KEY` optional)
- [ ] **Step 4:** Main-tree `.env`: append `ENMAAS_KEY` from the shell env (never print it), comment out `GEMINI_API_KEY` (rollback = uncomment one line)
- [ ] **Step 5:** Live smoke test from the worktree: start the server with `GEMINI_API_KEY= PORT=8790 ./scripts/run.sh` (background), wait for `/health`, POST `/rewrite` with a short text, assert 200 and a sane result, stop the server
- [ ] **Step 6:** Commit `docs: document EnMaaS as the default LLM provider`
