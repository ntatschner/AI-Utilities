#!/usr/bin/env bash
# Claude Code Workflow Hook — Remote Installer (macOS / Linux)
#
# Usage:
#   bash <(curl -fsSL https://raw.githubusercontent.com/ntatschner/ai-utilities/main/tools/claude-dev-workflow-hook/install-remote.sh) --global
#   bash <(curl -fsSL https://raw.githubusercontent.com/ntatschner/ai-utilities/main/tools/claude-dev-workflow-hook/install-remote.sh) --project
#
# Downloads session-start.py and install.py to a temp directory, then runs the installer.

set -euo pipefail

REPO_BASE="https://raw.githubusercontent.com/ntatschner/ai-utilities/main/tools/claude-dev-workflow-hook"
TMPDIR_PATH=$(mktemp -d)

cleanup() {
    rm -rf "$TMPDIR_PATH"
}
trap cleanup EXIT

echo "Downloading workflow hook files..."
curl -fsSL "$REPO_BASE/session-start.py" -o "$TMPDIR_PATH/session-start.py"
curl -fsSL "$REPO_BASE/install.py" -o "$TMPDIR_PATH/install.py"

echo "Running installer..."

# Detect python command
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "ERROR: Python 3 not found. Install it first:"
    echo "  macOS:  brew install python3"
    echo "  Linux:  apt install python3"
    exit 1
fi

# Pass all arguments through to install.py
$PYTHON "$TMPDIR_PATH/install.py" "$@"
