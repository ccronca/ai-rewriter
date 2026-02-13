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

**Note:** This setup has been tested on Fedora 43. Other Linux distributions may require adjustments.

- Python 3.14+ (or your installed Python version)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- `wl-paste` and `wl-copy` (for Wayland clipboard) or `xclip` (for X11)
- `jq` - JSON processor
- `notify-send` - Desktop notifications (usually pre-installed on GNOME/KDE)
- Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

## Setup

1. Install uv if not already installed:

**Option A: Package Manager (Recommended for Fedora/RHEL)**
```bash
sudo dnf install uv
```

**Option B: Standalone Installer**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, verify the path:
```bash
which uv
# Common locations:
# /usr/bin/uv (package manager)
# ~/.cargo/bin/uv (standalone installer)
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
ENABLE_RELOAD=false  # Set to true for development mode (auto-reload on code changes)
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
ExecStart=/path/to/ai-rewriter/scripts/run.sh
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

**Important:** Replace the following paths:
- `WorkingDirectory` - Full path to your ai-rewriter directory
- `EnvironmentFile` - Full path to your `.env` file
- `ExecStart` - Full path to the run.sh script in your ai-rewriter directory

**Development Mode:**
- Set `ENABLE_RELOAD=true` in your `.env` file to enable auto-reload on code changes
- The service will automatically restart when you modify Python files
- Set `ENABLE_RELOAD=false` or remove it for production use (no auto-reload)

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

### Troubleshooting Systemd Service

**Service fails to start**
- Check the logs: `journalctl --user -u ai-rewriter.service -n 50`
- Verify paths in the service file are correct (use absolute paths)
- Ensure `run.sh` is executable: `chmod +x /path/to/ai-rewriter/scripts/run.sh`
- Check that `.env` file exists and contains valid configuration

**Auto-reload not working**
- Verify `ENABLE_RELOAD=true` is set in your `.env` file
- Restart the service: `systemctl --user restart ai-rewriter.service`
- Check logs to confirm "Will watch for changes" message appears

**Service fails to start at boot**
- Ensure the service is enabled: `systemctl --user enable ai-rewriter.service`
- Check that `uv` is installed and accessible
- If using standalone `uv` installer, consider using package manager: `sudo dnf install uv`

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
