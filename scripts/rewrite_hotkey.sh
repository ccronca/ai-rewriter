#!/usr/bin/env bash
set -euo pipefail

# Get project root directory (parent of scripts dir)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

# Load environment variables from .env if it exists
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
fi

# Default port if not set
PORT="${PORT:-8787}"

# Small delay to ensure clipboard is updated after Ctrl+C
sleep 0.2

# Get selected text from clipboard
TEXT=$(wl-paste)

# Check if clipboard is empty
if [ -z "${TEXT}" ]; then
    notify-send "AI Rewriter" "No text in clipboard. Copy text first (Ctrl+C)" -i dialog-error -u critical
    exit 1
fi

# Truncate text for notification display (max 100 chars)
TRUNCATED_TEXT="${TEXT:0:100}"
if [ ${#TEXT} -gt 100 ]; then
    TRUNCATED_TEXT="${TRUNCATED_TEXT}..."
fi

# Show processing notification with original text
notify-send "AI Rewriter" "Processing: ${TRUNCATED_TEXT}" -i dialog-information -t 3000

# Call local AI rewriter with timeout
if ! RESULT=$(curl -s --max-time 30 "http://127.0.0.1:${PORT}/rewrite" \
    -H "Content-Type: application/json" \
    -d "{\"text\":\"${TEXT}\",\"mode\":\"friendly\"}" 2>&1); then
    notify-send "AI Rewriter" "Failed to connect to server. Is it running?" -i dialog-error -u critical
    exit 1
fi

# Extract rewritten text and check for errors
if ! IMPROVED=$(echo "${RESULT}" | jq -r .result 2>&1); then
    notify-send "AI Rewriter" "Invalid response from server" -i dialog-error -u critical
    exit 1
fi

# Check if result is empty or null
if [ -z "${IMPROVED}" ] || [ "${IMPROVED}" = "null" ]; then
    notify-send "AI Rewriter" "Empty response from AI" -i dialog-error -u critical
    exit 1
fi

# Put improved text back into clipboard
echo "${IMPROVED}" | wl-copy

# Truncate improved text for notification display
TRUNCATED_IMPROVED="${IMPROVED:0:100}"
if [ ${#IMPROVED} -gt 100 ]; then
    TRUNCATED_IMPROVED="${TRUNCATED_IMPROVED}..."
fi

# Show success notification with improved text
notify-send "AI Rewriter" "✓ Ready to paste: ${TRUNCATED_IMPROVED}" -i dialog-information -t 5000
