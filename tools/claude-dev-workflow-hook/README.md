# Claude Code Development Workflow Hook

## Purpose

A `SessionStart` hook that injects a structured development workflow protocol once per Claude Code session. It enforces planning, TDD, recursive testing, UI standards, agent team orchestration, and integration testing — automatically, project-agnostically.

> **Why SessionStart?** The protocol injects once per session (on startup, resume, clear, and compact) rather than on every prompt. This saves significant context window budget over long conversations. `SessionStart` supports `additionalContext` injection via `hookSpecificOutput`.

## Language / Stack

- **Languages:** Node.js (primary), Python 3 (alternative)
- **Runtime:** Claude Code CLI hook system (`SessionStart` event)
- **Platforms:** Windows, macOS, Linux
- **Dependencies:** None (Node.js built-ins only / Python stdlib only)

## AGENTS.md (Platform-Agnostic Version)

This tool also ships an `AGENTS.md` file — a portable, plain-Markdown version of the same workflow protocol that works with **any AI coding agent** (GitHub Copilot, Cursor, Codex, Google Jules, and [20+ other platforms](https://agents.md)).

### How to use it

Copy `AGENTS.md` into the root of any repository where you want agents to follow the protocol:

```bash
cp AGENTS.md /path/to/your/project/AGENTS.md
```

That's it. No hooks, no installer, no authority binding — agents that support the [AGENTS.md standard](https://agents.md) will read it automatically.

### When to use which

| Approach | Best for | How it works |
|----------|----------|--------------|
| **Hook** (Node.js or Python) | Claude Code users | Injected once per session via `SessionStart` + CLAUDE.md authority binding |
| **AGENTS.md** | Any AI agent | Placed at repo root; agents read it as project context automatically |

You can use both — they contain the same rules. The hook enforces via injection; the AGENTS.md file relies on the agent reading it from the repo.

### Nested AGENTS.md

For monorepos, place an AGENTS.md in subdirectories to override or extend the root rules. The closest file to the edited code takes precedence.

## What's Inside

7 mandatory rules wrapped in `<dev-workflow-protocol>` XML tags with compliance reporting:

| Rule | Name | Purpose |
|------|------|---------|
| 0 | Plan Before Acting | Identify files, map dependencies, enter Plan Mode if >2 files |
| 1 | Small Task Exception | Skip team orchestration for <=2 file changes (still TDD + test) |
| 2 | TDD Enforcement | RED -> GREEN -> IMPROVE cycle, 80%+ coverage target |
| 3 | Test After Every Change | Run tests after EVERY change, never stack untested changes |
| 4 | Agent Team Orchestration | 7-phase pipeline with parallel implementation via Agent Teams (subagent fallback) |
| 5 | UI & Layout Standards | Responsive testing, overflow rules, accessibility, i18n |
| 6 | Integration Testing | Container-first testing, backend/frontend test isolation |

The **Compliance Reporting** section requires the model to prefix actions with `[PROTOCOL Rule N]`, making rule adherence visible.

## Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed
- **Node.js 18+** (for npm install) OR **Python 3** (for Python install)

---

## Install via npm (Recommended)

Single command — no clone needed:

**Global install** (all projects):

```bash
npx @thecodesaiyan/claude-dev-workflow-hook --global
```

**Per-project install** (current project only):

```bash
npx @thecodesaiyan/claude-dev-workflow-hook --project
```

### Uninstall via npm

```bash
npx @thecodesaiyan/claude-dev-workflow-hook --uninstall --scope global
npx @thecodesaiyan/claude-dev-workflow-hook --uninstall --scope project
```

---

## Install via Python (Alternative)

If you prefer Python or don't have Node.js:

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

### Uninstall via Python

```bash
# macOS / Linux
python3 install.py --uninstall --scope global    # or --scope project

# Windows
py install.py --uninstall --scope global          # or --scope project
```

---

## What the installer does

Both the npm and Python installers perform the same 4 steps:

```
[1/4] Copying hook script
  OK: Copied session-start.js -> ~/.claude/hooks/session-start.js

[2/4] Registering in settings.json
  OK: Registered hook in ~/.claude/settings.json
      Command: node ~/.claude/hooks/session-start.js

[3/4] Adding CLAUDE.md authority binding
  OK: Added authority binding to ~/.claude/CLAUDE.md

[4/4] Verifying installation
  PASS: Valid JSON output
  PASS: hookSpecificOutput present
  PASS: additionalContext present
  PASS: Protocol length: 11318 chars
  PASS: Rules found: 7
  PASS: XML wrapper tags
  PASS: Compliance reporting section

Installation complete!
```

The installer is **idempotent** — running it again skips already-installed components. It also **auto-migrates** from the Python hook to Node.js, and from `UserPromptSubmit` to `SessionStart`.

---

## How It Works (Authority Chain)

The hook uses a two-part system to ensure the model actually **follows** the rules:

1. **The hook script** injects the protocol wrapped in `<dev-workflow-protocol>` XML tags via `additionalContext`
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
cp src/hook.js ~/.claude/hooks/session-start.js
cp src/protocol.js ~/.claude/hooks/protocol.js
```

### 2. Register in settings.json

Add to `~/.claude/settings.json` (merge, don't overwrite):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node ~/.claude/hooks/session-start.js"
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
echo '{}' | node ~/.claude/hooks/session-start.js
```

---

## Per-Project Install

For a single project instead of global:

```bash
npx @thecodesaiyan/claude-dev-workflow-hook --project
```

Or manually:
- Place the hook in `.claude/hooks/session-start.js` (relative to project root)
- Copy `protocol.js` alongside it
- Register in `.claude/settings.json` (project-level, not `~/.claude/`)
- Use relative path: `node .claude/hooks/session-start.js`

Per-project hooks are committed to version control, so the whole team gets them.

---

## Customization

### Add project-specific test commands

Edit `src/protocol.js` (or `session-start.py`) and add to the "Auto-Detect Test Runner" section.

### Add project-specific UI rules

Append to Rule 5 in the `PROTOCOL` string.

### Add project-specific integration test patterns

Append to Rule 6 in the `PROTOCOL` string.

### Disable specific rules

Remove the rule block from the `PROTOCOL` string. Rules are independent. Update the Quick Reference table to match.

> **Tip:** For project-specific additions, create a second hook rather than modifying the generic one.

---

## Migration

### From the Python hook

The npm installer automatically migrates:
- Detects `session-start.py` under `SessionStart` and replaces with `session-start.js`
- No manual steps needed — just run `npx @thecodesaiyan/claude-dev-workflow-hook --global`

### From the UserPromptSubmit version

Both installers automatically migrate:
- Remove the old `UserPromptSubmit` entry
- Register under `SessionStart` instead
- The new registration injects once per session instead of on every prompt

### From the Bash version

1. Run `npx @thecodesaiyan/claude-dev-workflow-hook --global`
2. Remove the old bash hook entry from `settings.json`
3. Delete `~/.claude/hooks/session-start.sh`

---

## Troubleshooting

### "node: not found"

Install Node.js 18+ from [nodejs.org](https://nodejs.org/).

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

`SessionStart` hooks run in array order. Each hook's `additionalContext` is concatenated. If you see duplicate rules, consolidate into a single hook.

### Hook doesn't run

1. Verify `settings.json` is valid JSON (no trailing commas)
2. Check the path matches where you placed the script
3. Restart Claude Code after modifying `settings.json`
