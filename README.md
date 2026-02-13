# AI Rewriter

A local AI assistant to improve your English messages for Slack and workplace communication.
Runs as a background service with clipboard-based hotkey integration.

## Features

- Improves grammar and clarity of your messages
- Clipboard-based workflow with desktop notifications
- Multiple modes for different communication contexts
- Runs as background service (auto-start on login)
- Privacy-focused: runs locally, only API calls go to Gemini

## Prerequisites

- Python 3.14+ (or your installed Python version)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- `wl-paste` and `wl-copy` (for Wayland clipboard) or `xclip` (for X11)
- `jq` - JSON processor
- `notify-send` - Desktop notifications (usually pre-installed on GNOME/KDE)
- Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

## Setup

1. Install uv if not already installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone repo:

```bash
git clone <repo_url>
cd ai-rewriter
```

3. Copy environment template and configure:

```bash
cp .env.example .env
nano .env  # Edit with your Gemini API key and preferred port
```

Edit `.env`:
```bash
GEMINI_API_KEY=your_actual_api_key_here
PORT=8787  # Optional, defaults to 8787
```

4. Install dependencies with uv:

```bash
uv sync
```

5. Start server:

```bash
./scripts/run.sh
```

The service will be available at `http://127.0.0.1:8787` (or your configured PORT)

---

## Systemd User Service (Auto-start on Login)

To run the AI Rewriter automatically in the background whenever you log in:

1. Ensure your `.env` file is configured with your API key and port

2. Create the systemd user service directory if it doesn't exist:

```bash
mkdir -p ~/.config/systemd/user
```

3. Create the service file:

```bash
nano ~/.config/systemd/user/ai-rewriter.service
```

Paste the following (adjust paths to match your installation):

```ini
[Unit]
Description=Local AI Rewriter Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/ai-rewriter
EnvironmentFile=/path/to/ai-rewriter/.env
ExecStart=/usr/local/bin/uv run uvicorn src.main:app --host 127.0.0.1 --port ${PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

**Note:** Replace the following paths:
- `WorkingDirectory` - Full path to your ai-rewriter directory
- `EnvironmentFile` - Full path to your `.env` file
- `ExecStart` - Path to `uv` binary (find with `which uv`)

4. Reload systemd, enable, and start the service:

```bash
systemctl --user daemon-reload
systemctl --user enable ai-rewriter.service
systemctl --user start ai-rewriter.service
```

5. Check service status:

```bash
systemctl --user status ai-rewriter.service
```

6. View logs if needed:

```bash
journalctl --user -u ai-rewriter.service -f
```

Once enabled, the service will **automatically start on login** and run in the background.

---

## Usage

### Quick Start

1. Copy text you want to improve (Ctrl+C)
2. Press your configured hotkey
3. See notification with improved text
4. Paste the improved text (Ctrl+V)

---

## Keyboard Shortcut Setup

### GNOME/KDE Setup

1. Open Settings → Keyboard → Custom Shortcuts
2. Add a new shortcut:
   - Name: `AI Rewrite`
   - Command: `/path/to/ai-rewriter/scripts/rewrite_hotkey.sh`
   - Shortcut: `Ctrl + Alt + R` (or your preference)

Replace `/path/to/ai-rewriter` with your actual installation path.

### Desktop Notifications

When you press the hotkey, you'll see:
- **"Processing: [text preview]"** - AI is improving your text
- **"✓ Ready to paste: [improved text]"** - Success! Paste with Ctrl+V

### Error Messages

- **"No text in clipboard"** - Copy text first (Ctrl+C)
- **"Failed to connect to server"** - Service not running (run `./scripts/run.sh`)

### Customization

To use different rewriting modes, edit `scripts/rewrite_hotkey.sh` and change the `mode` parameter.
See `claude.md` for available modes and customization options.

---

## Development

For development guidelines, API documentation, and customization options, see `claude.md`.

### Pre-commit Hooks

Install pre-commit hooks for automatic code quality checks:

```bash
uv pip install pre-commit
pre-commit install
```

This will run syntax validation, linting, and security checks before each commit.
