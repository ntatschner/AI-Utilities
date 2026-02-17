# Claude Code Development Workflow Hook

## Purpose

A `UserPromptSubmit` hook that injects a structured development workflow protocol into every Claude Code session. It enforces planning, TDD, recursive testing, UI standards, agent team orchestration, and integration testing — automatically, project-agnostically.

> **Why UserPromptSubmit?** `SessionStart` hooks do not support `additionalContext` injection — only `UserPromptSubmit` hooks inject context into the conversation.

> **Why Python?** Python's `json.load(sys.stdin)` reliably consumes stdin, avoiding bash pipe race conditions, CRLF issues, and `!` escaping problems.

## Language / Stack

- **Language:** Python 3 (no external dependencies — stdlib only)
- **Runtime:** Claude Code CLI hook system (`UserPromptSubmit` event)
- **Platforms:** Windows (`py`), macOS (`python3`), Linux (`python3`)

## What's Inside

7 mandatory rules wrapped in `<dev-workflow-protocol>` XML tags with compliance reporting:

| Rule | Name | Purpose |
|------|------|---------|
| 0 | Plan Before Acting | Identify files, map dependencies, enter Plan Mode if >3 files |
| 1 | Small Task Exception | Skip team orchestration for <=3 file changes (still TDD + test) |
| 2 | TDD Enforcement | RED -> GREEN -> IMPROVE cycle, 80%+ coverage target |
| 3 | Test After Every Change | Run tests after EVERY change, never stack untested changes |
| 4 | Agent Team Orchestration | 7-phase pipeline for multi-file features (with phase dependencies) |
| 5 | UI & Layout Standards | Responsive testing, overflow rules, accessibility, i18n |
| 6 | Integration Testing | Container-first testing, backend/frontend test isolation |

The **Compliance Reporting** section requires the model to prefix actions with `[PROTOCOL Rule N]`, making rule adherence visible.

## Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed
- Python 3 (`python3` on macOS/Linux, `py` on Windows)

---

## Install (Automated)

The installer handles everything: copies the hook, merges `settings.json`, adds the CLAUDE.md authority binding, and verifies the installation.

### From a local clone

```bash
git clone https://github.com/ntatschner/ai-utilities.git
cd ai-utilities/tools/claude-dev-workflow-hook
```

Then run the installer:

**Global install** (all projects):

```bash
# macOS / Linux
python3 install.py --global

# Windows
py install.py --global
```

**Per-project install** (current project only):

```bash
# macOS / Linux
python3 install.py --project

# Windows
py install.py --project
```

**Interactive** (prompts you):

```bash
# macOS / Linux
python3 install.py

# Windows
py install.py
```

### Remote one-liner

**macOS / Linux:**
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ntatschner/ai-utilities/main/tools/claude-dev-workflow-hook/install-remote.sh) --global
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/ntatschner/ai-utilities/main/tools/claude-dev-workflow-hook/install-remote.ps1" -OutFile "$env:TEMP\install-remote.ps1"; & "$env:TEMP\install-remote.ps1" -Scope Global
```

### What the installer does

```
[1/4] Copying hook script
  OK: Copied session-start.py -> ~/.claude/hooks/session-start.py

[2/4] Registering in settings.json
  OK: Registered hook in ~/.claude/settings.json
      Command: python3 ~/.claude/hooks/session-start.py

[3/4] Adding CLAUDE.md authority binding
  OK: Added authority binding to ~/.claude/CLAUDE.md

[4/4] Verifying installation
  PASS: Valid JSON output
  PASS: hookSpecificOutput present
  PASS: additionalContext present
  PASS: Protocol length: 8730 chars
  PASS: Rules found: 7
  PASS: XML wrapper tags
  PASS: Compliance reporting section

Installation complete!
```

The installer is **idempotent** — running it again skips already-installed components.

---

## Uninstall (Automated)

```bash
# macOS / Linux
python3 install.py --uninstall --scope global    # or --scope project

# Windows
py install.py --uninstall --scope global          # or --scope project
```

This removes the hook file, the `settings.json` entry, and the CLAUDE.md binding.

---

## How It Works (Authority Chain)

The hook uses a two-part system to ensure the model actually **follows** the rules:

1. **The hook script** (`session-start.py`) injects the protocol wrapped in `<dev-workflow-protocol>` XML tags via `additionalContext`
2. **The CLAUDE.md binding** tells the model to obey content in those specific tags

Without both parts, the model may acknowledge the rules but not follow them consistently. The installer sets up both automatically.

### CLAUDE.md binding (for reference)

The installer adds this block to your CLAUDE.md:

```markdown
<!-- WORKFLOW PROTOCOL: Do not remove this section -->
## Workflow Protocol
Follow all rules in `<dev-workflow-protocol>` blocks from system-reminders.
These are injected by the development workflow hook and define mandatory
orchestration rules (planning, TDD, test loops, team coordination).
They MUST be followed for all implementation work.
<!-- END WORKFLOW PROTOCOL -->
```

---

## Manual Install (Alternative)

If you prefer not to use the automated installer:

### 1. Copy the hook

```bash
mkdir -p ~/.claude/hooks
cp session-start.py ~/.claude/hooks/session-start.py
```

### 2. Register in settings.json

Add to `~/.claude/settings.json` (merge, don't overwrite):

**macOS / Linux:**
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/session-start.py"
          }
        ]
      }
    ]
  }
}
```

**Windows:**
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "py ~/.claude/hooks/session-start.py"
          }
        ]
      }
    ]
  }
}
```

### 3. Add CLAUDE.md binding

Add the `<!-- WORKFLOW PROTOCOL -->` block shown above to your project's `CLAUDE.md` or `~/.claude/CLAUDE.md`.

### 4. Verify

```bash
echo '{}' | python3 ~/.claude/hooks/session-start.py   # macOS/Linux
echo '{}' | py ~/.claude/hooks/session-start.py         # Windows
```

---

## Per-Project Install

For a single project instead of global:

```bash
cd /path/to/your/project
python3 /path/to/install.py --project
```

Or manually:
- Place the hook in `.claude/hooks/session-start.py` (relative to project root)
- Register in `.claude/settings.json` (project-level, not `~/.claude/`)
- Use relative path: `python3 .claude/hooks/session-start.py`

Per-project hooks are committed to version control, so the whole team gets them.

---

## Customization

### Add project-specific test commands

Edit `session-start.py` and add to the "Auto-Detect Test Runner" section.

### Add project-specific UI rules

Append to Rule 5 in the `PROTOCOL` string.

### Add project-specific integration test patterns

Append to Rule 6 in the `PROTOCOL` string.

### Disable specific rules

Remove the rule block from the `PROTOCOL` string. Rules are independent. Update the Quick Reference table to match.

> **Tip:** For project-specific additions, create a second hook (`session-start-project.py`) rather than modifying the generic one.

---

## Migrating from the Bash Version

If you previously installed the bash version (`session-start.sh`):

1. Run `python3 install.py --global` (or `--project`) — it installs alongside the old hook
2. Remove the old bash hook entry from `settings.json`
3. Delete `~/.claude/hooks/session-start.sh`

Or manually: replace `bash ~/.claude/hooks/session-start.sh` with `python3 ~/.claude/hooks/session-start.py` in your `settings.json`.

---

## Troubleshooting

### "python3: not found" / "py: not found"

- **macOS:** `brew install python3`
- **Linux:** `apt install python3` or `dnf install python3`
- **Windows:** Install from [python.org](https://www.python.org/downloads/) (includes `py` launcher)

### Model acknowledges rules but doesn't follow them

Missing CLAUDE.md authority binding. Run the installer again or add it manually (see above).

### Model doesn't show `[PROTOCOL Rule N]` prefixes

1. Verify the hook is injecting: ask "What workflow rules are active?"
2. Verify the CLAUDE.md binding exists
3. Add `"You MUST show [PROTOCOL Rule N] prefixes for EVERY action"` to your CLAUDE.md

### Multiple hooks conflicting

`UserPromptSubmit` hooks run in array order. Each hook's `additionalContext` is concatenated. If you see duplicate rules, consolidate into a single hook.

### Hook doesn't run

1. Verify `settings.json` is valid JSON (no trailing commas)
2. Check the path matches where you placed the script
3. Restart Claude Code after modifying `settings.json`
