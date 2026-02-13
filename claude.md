# AI Rewriter Development Guidelines

This file contains implementation details and guidelines for developing the AI Rewriter project.

## Language Level Guidelines

### B2-Level English Standard

All prompts should target **B2-level English** (upper-intermediate) as defined by the Common European Framework of Reference for Languages (CEFR).

**Why B2-level:**
- Professional workplace standard
- Clear and natural, not overly formal or academic
- Suitable for international team communication
- Easier for non-native speakers to understand
- Maintains professionalism without being stiff

**Key characteristics of B2-level English:**
- Clear, direct sentence structure
- Active voice preferred over passive
- Common professional vocabulary (avoiding unnecessary jargon)
- Natural conversational flow
- Grammatically correct but not overly complex

### Rewrite Modes

The application supports multiple modes optimized for different communication contexts:

- **default** - Conversational workplace tone, professional but not formal
- **formal** - Formal professional English for management/official communication
- **short** - Concise messages with minimum words, maximum clarity
- **friendly** - Casual, team-oriented tone for daily Slack communication

All modes maintain B2-level English standards while adjusting tone appropriately.

## Prompt Engineering Guidelines

When modifying prompts in `src/prompts.py`:

1. **Always specify B2-level** in the prompt to ensure consistent quality
2. **Be explicit about output format** - "Return only the rewritten message, no explanations"
3. **Specify tone clearly** - conversational, formal, casual, etc.
4. **Focus on workplace communication** - prompts should optimize for Slack/team messaging
5. **Grammar correction** - always include instruction to fix grammar errors
6. **Preserve meaning** - instruct the AI to keep original intent

## Code Style Guidelines

### Python
- Use type hints where appropriate
- Follow PEP 8 conventions
- Keep functions focused and single-purpose
- Use Pythonic patterns (context managers, comprehensions, etc.)

### Bash
- Always use `set -euo pipefail` for error handling
- Quote all variables: `"${VAR}"` not `$VAR`
- Use `#!/usr/bin/env bash` shebang
- Document complex logic with comments

## Testing

Before committing:
```bash
# Install pre-commit hooks
uv pip install pre-commit
pre-commit install

# Run checks manually
pre-commit run --all-files

# Test bash scripts
shellcheck scripts/*.sh

# Test Python syntax
python -m py_compile src/*.py
```

## Project Structure

```
ai-rewriter/
├── src/               # Application source code
│   ├── main.py       # FastAPI application
│   └── prompts.py    # AI prompt templates
├── scripts/          # Utility scripts
│   ├── run.sh       # Development server launcher
│   ├── rewrite_hotkey.sh  # Hotkey integration script
│   ├── rewrite.py   # Legacy standalone script
│   └── list_models.py     # Gemini model listing utility
├── .env.example     # Environment configuration template
└── pyproject.toml   # Python project metadata
```

## Environment Variables

- `GEMINI_API_KEY` - Required. Google Gemini API key
- `PORT` - Optional. Server port (default: 8787)

## API Design

### Endpoints

- `POST /rewrite` - Main rewrite endpoint
- `GET /health` - Health check endpoint

### Request Format

```json
{
  "text": "message to rewrite",
  "mode": "default|formal|short|friendly"
}
```

### Response Format

```json
{
  "result": "rewritten message"
}
```

## Deployment Considerations

### Systemd Service
- Use `EnvironmentFile` to load `.env` configuration
- Set `Restart=always` with `RestartSec=5` for reliability
- Run as user service (not system-wide)

### Security
- Never commit `.env` file
- API key should be stored in `.env` only
- Server binds to localhost only (not exposed to network)

## Future Enhancements

Ideas for future development:

- Response caching to reduce API calls
- Support for other AI models (Claude, local LLMs)
- Batch processing for multiple messages
- Custom user-defined modes
- Keyboard shortcuts for mode selection
- Integration with other clipboard tools
- Browser extension for direct Slack integration
