#!/usr/bin/env python3
"""
Claude Code Development Workflow Hook — Installer

Automates:
  1. Copies session-start.py to the hooks directory
  2. Merges hook registration into settings.json (without clobbering)
  3. Adds CLAUDE.md authority binding (without clobbering)
  4. Verifies the installation works

Usage:
  python install.py              # Interactive (prompts for global vs per-project)
  python install.py --global     # Install globally (~/.claude/)
  python install.py --project    # Install in current project (.claude/)
  python install.py --uninstall  # Remove the hook
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
#  Constants
# --------------------------------------------------------------------------- #

HOOK_FILENAME = "session-start.py"
SETTINGS_FILENAME = "settings.json"

CLAUDE_MD_BINDING = """\

<!-- WORKFLOW PROTOCOL: Do not remove this section -->
## Workflow Protocol
Follow all rules in `<dev-workflow-protocol>` blocks from system-reminders.
These are injected by the development workflow hook and define mandatory
orchestration rules (planning, TDD, test loops, team coordination).
They MUST be followed for all implementation work.
<!-- END WORKFLOW PROTOCOL -->
"""

CLAUDE_MD_MARKER = "<!-- WORKFLOW PROTOCOL:"


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #

def get_python_cmd():
    """Return the python command that works on this system."""
    if platform.system() == "Windows":
        # Windows: try 'py' first (Python Launcher), then 'python3', then 'python'
        for cmd in ("py", "python3", "python"):
            if shutil.which(cmd):
                return cmd
    else:
        for cmd in ("python3", "python"):
            if shutil.which(cmd):
                return cmd
    return "python3"  # fallback


def get_claude_home():
    """Return ~/.claude as a Path."""
    return Path.home() / ".claude"


def get_project_claude():
    """Return .claude in the current working directory."""
    return Path.cwd() / ".claude"


def prompt_choice(question, options):
    """Simple interactive prompt. Returns the chosen option string."""
    print(f"\n{question}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}) {opt}")
    while True:
        try:
            choice = input(f"Enter choice [1-{len(options)}]: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except (ValueError, EOFError):
            pass
        print(f"  Please enter a number between 1 and {len(options)}.")


def green(text):
    return f"\033[32m{text}\033[0m"


def yellow(text):
    return f"\033[33m{text}\033[0m"


def red(text):
    return f"\033[31m{text}\033[0m"


def bold(text):
    return f"\033[1m{text}\033[0m"


# --------------------------------------------------------------------------- #
#  Core operations
# --------------------------------------------------------------------------- #

def copy_hook(target_dir: Path, source_dir: Path):
    """Copy session-start.py to target hooks directory."""
    hooks_dir = target_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    src = source_dir / HOOK_FILENAME
    dst = hooks_dir / HOOK_FILENAME

    if not src.exists():
        print(red(f"  ERROR: {src} not found. Run this script from the hook directory."))
        return False

    if dst.exists():
        # Check if it's the same file
        if src.read_text(encoding="utf-8") == dst.read_text(encoding="utf-8"):
            print(yellow(f"  SKIP: {dst} already up-to-date"))
            return True
        print(yellow(f"  UPDATE: {dst} exists — overwriting with new version"))

    shutil.copy2(src, dst)
    print(green(f"  OK: Copied {HOOK_FILENAME} -> {dst}"))
    return True


def merge_settings(target_dir: Path, is_global: bool):
    """Merge hook registration into settings.json without clobbering."""
    settings_path = target_dir / SETTINGS_FILENAME
    python_cmd = get_python_cmd()

    # Build the command path
    if is_global:
        hook_path = f"~/.claude/hooks/{HOOK_FILENAME}"
    else:
        hook_path = f".claude/hooks/{HOOK_FILENAME}"

    command = f"{python_cmd} {hook_path}"

    new_hook_entry = {
        "hooks": [
            {
                "type": "command",
                "command": command
            }
        ]
    }

    # Load or create settings
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(red(f"  ERROR: {settings_path} contains invalid JSON. Fix it manually."))
            return False
    else:
        settings = {}

    # Check if hook is already registered under SessionStart
    existing_hooks = settings.get("hooks", {}).get("SessionStart", [])
    for entry in existing_hooks:
        for hook in entry.get("hooks", []):
            if HOOK_FILENAME in hook.get("command", ""):
                print(yellow(f"  SKIP: Hook already registered in {settings_path}"))
                return True

    # Migrate: remove old UserPromptSubmit registration if present
    old_hooks = settings.get("hooks", {}).get("UserPromptSubmit", [])
    migrated = False
    if old_hooks:
        filtered = [
            entry for entry in old_hooks
            if not any(HOOK_FILENAME in h.get("command", "") for h in entry.get("hooks", []))
        ]
        if len(filtered) < len(old_hooks):
            if filtered:
                settings["hooks"]["UserPromptSubmit"] = filtered
            else:
                del settings["hooks"]["UserPromptSubmit"]
            migrated = True
            print(green(f"  OK: Removed old UserPromptSubmit registration"))

    # Add the hook under SessionStart
    if "hooks" not in settings:
        settings["hooks"] = {}
    if "SessionStart" not in settings["hooks"]:
        settings["hooks"]["SessionStart"] = []

    settings["hooks"]["SessionStart"].append(new_hook_entry)

    # Write back
    settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    print(green(f"  OK: Registered hook in {settings_path}"))
    print(f"      Command: {command}")
    return True


def add_claude_md_binding(target_dir: Path):
    """Add the authority binding to CLAUDE.md if not already present."""
    # For global install, use ~/.claude/CLAUDE.md
    # For project install, use ./CLAUDE.md (project root)
    if target_dir == get_claude_home():
        claude_md_path = get_claude_home() / "CLAUDE.md"
    else:
        # Project install — CLAUDE.md lives in the project root, one level up from .claude/
        claude_md_path = target_dir.parent / "CLAUDE.md"

    if claude_md_path.exists():
        content = claude_md_path.read_text(encoding="utf-8")
        if CLAUDE_MD_MARKER in content:
            print(yellow(f"  SKIP: Authority binding already in {claude_md_path}"))
            return True

        # Prepend the binding after the first heading (or at the top)
        lines = content.split("\n")
        insert_idx = 0

        # Find the first line after the top-level heading (# Title)
        for i, line in enumerate(lines):
            if line.startswith("# "):
                insert_idx = i + 1
                # Skip any blank lines immediately after the heading
                while insert_idx < len(lines) and lines[insert_idx].strip() == "":
                    insert_idx += 1
                break

        # Insert the binding
        binding_lines = CLAUDE_MD_BINDING.strip().split("\n")
        lines = lines[:insert_idx] + [""] + binding_lines + [""] + lines[insert_idx:]
        claude_md_path.write_text("\n".join(lines), encoding="utf-8")
        print(green(f"  OK: Added authority binding to {claude_md_path}"))
    else:
        # Create a minimal CLAUDE.md with the binding
        claude_md_path.write_text(
            f"# Project\n{CLAUDE_MD_BINDING}",
            encoding="utf-8"
        )
        print(green(f"  OK: Created {claude_md_path} with authority binding"))

    return True


def verify_installation(target_dir: Path):
    """Run the hook and verify JSON output."""
    hook_path = target_dir / "hooks" / HOOK_FILENAME
    python_cmd = get_python_cmd()

    if not hook_path.exists():
        print(red(f"  FAIL: {hook_path} not found"))
        return False

    try:
        result = subprocess.run(
            [python_cmd, str(hook_path)],
            input="{}",
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            print(red(f"  FAIL: Hook exited with code {result.returncode}"))
            if result.stderr:
                print(f"        stderr: {result.stderr.strip()}")
            return False

        output = json.loads(result.stdout.strip())
        ctx = output["hookSpecificOutput"]["additionalContext"]
        rule_count = ctx.count("## RULE")
        has_xml = "<dev-workflow-protocol>" in ctx and "</dev-workflow-protocol>" in ctx
        has_compliance = "COMPLIANCE REPORTING" in ctx

        checks = [
            ("Valid JSON output", True),
            ("hookSpecificOutput present", "hookSpecificOutput" in output),
            ("additionalContext present", len(ctx) > 0),
            (f"Protocol length: {len(ctx)} chars", len(ctx) > 1000),
            (f"Rules found: {rule_count}", rule_count == 7),
            ("XML wrapper tags", has_xml),
            ("Compliance reporting section", has_compliance),
        ]

        all_ok = True
        for label, passed in checks:
            icon = green("PASS") if passed else red("FAIL")
            print(f"  {icon}: {label}")
            if not passed:
                all_ok = False

        return all_ok

    except subprocess.TimeoutExpired:
        print(red("  FAIL: Hook timed out (10s)"))
        return False
    except json.JSONDecodeError as e:
        print(red(f"  FAIL: Invalid JSON output — {e}"))
        return False
    except FileNotFoundError:
        print(red(f"  FAIL: '{python_cmd}' not found. Install Python 3."))
        return False


# --------------------------------------------------------------------------- #
#  Uninstall
# --------------------------------------------------------------------------- #

def uninstall(target_dir: Path):
    """Remove the hook, settings entry, and CLAUDE.md binding."""
    print(bold("\nUninstalling workflow hook..."))

    # Remove hook file
    hook_path = target_dir / "hooks" / HOOK_FILENAME
    if hook_path.exists():
        hook_path.unlink()
        print(green(f"  OK: Removed {hook_path}"))
    else:
        print(yellow(f"  SKIP: {hook_path} not found"))

    # Remove from settings.json (check both SessionStart and legacy UserPromptSubmit)
    settings_path = target_dir / SETTINGS_FILENAME
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            removed_any = False

            for event_name in ("SessionStart", "UserPromptSubmit"):
                hooks_list = settings.get("hooks", {}).get(event_name, [])
                original_len = len(hooks_list)

                filtered = [
                    entry for entry in hooks_list
                    if not any(HOOK_FILENAME in h.get("command", "") for h in entry.get("hooks", []))
                ]

                if len(filtered) < original_len:
                    if filtered:
                        settings["hooks"][event_name] = filtered
                    else:
                        del settings["hooks"][event_name]
                    removed_any = True

            if removed_any:
                if "hooks" in settings and not settings["hooks"]:
                    del settings["hooks"]
                settings_path.write_text(
                    json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8"
                )
                print(green(f"  OK: Removed hook entry from {settings_path}"))
            else:
                print(yellow(f"  SKIP: No hook entry found in {settings_path}"))
        except json.JSONDecodeError:
            print(yellow(f"  SKIP: {settings_path} has invalid JSON — edit manually"))

    # Remove CLAUDE.md binding
    if target_dir == get_claude_home():
        claude_md_path = get_claude_home() / "CLAUDE.md"
    else:
        claude_md_path = target_dir.parent / "CLAUDE.md"

    if claude_md_path.exists():
        content = claude_md_path.read_text(encoding="utf-8")
        if CLAUDE_MD_MARKER in content:
            # Remove the binding block
            lines = content.split("\n")
            new_lines = []
            skip = False
            for line in lines:
                if CLAUDE_MD_MARKER in line:
                    skip = True
                    # Also remove the blank line before the marker if present
                    if new_lines and new_lines[-1].strip() == "":
                        new_lines.pop()
                    continue
                if skip and "<!-- END WORKFLOW PROTOCOL -->" in line:
                    skip = False
                    continue
                if not skip:
                    new_lines.append(line)

            # Clean up double blank lines left behind
            cleaned = "\n".join(new_lines)
            while "\n\n\n" in cleaned:
                cleaned = cleaned.replace("\n\n\n", "\n\n")

            claude_md_path.write_text(cleaned, encoding="utf-8")
            print(green(f"  OK: Removed authority binding from {claude_md_path}"))
        else:
            print(yellow(f"  SKIP: No authority binding found in {claude_md_path}"))

    # Clean up empty hooks directory
    hooks_dir = target_dir / "hooks"
    if hooks_dir.exists() and not any(hooks_dir.iterdir()):
        hooks_dir.rmdir()
        print(green(f"  OK: Removed empty {hooks_dir}"))

    print(green("\nUninstall complete."))


# --------------------------------------------------------------------------- #
#  Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Install the Claude Code Development Workflow Hook"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--global", dest="install_global", action="store_true",
                       help="Install globally to ~/.claude/")
    group.add_argument("--project", dest="install_project", action="store_true",
                       help="Install to current project's .claude/")
    group.add_argument("--uninstall", action="store_true",
                       help="Remove the hook")
    parser.add_argument("--scope", choices=["global", "project"],
                        help="Scope for --uninstall (default: prompts)")

    args = parser.parse_args()

    # Determine source directory (where this script lives)
    source_dir = Path(__file__).resolve().parent

    if not (source_dir / HOOK_FILENAME).exists():
        print(red(f"ERROR: {HOOK_FILENAME} not found in {source_dir}"))
        print("Run this script from the hook distribution directory.")
        sys.exit(1)

    print(bold("Claude Code Development Workflow Hook"))
    print(f"Python: {get_python_cmd()} | Platform: {platform.system()}")
    print(f"Source: {source_dir}")

    # Determine install scope
    if args.uninstall:
        if args.scope == "global":
            target_dir = get_claude_home()
        elif args.scope == "project":
            target_dir = get_project_claude()
        else:
            choice = prompt_choice("Uninstall from:", ["Global (~/.claude/)", "Project (.claude/)"])
            target_dir = get_claude_home() if "Global" in choice else get_project_claude()
        uninstall(target_dir)
        return

    if args.install_global:
        target_dir = get_claude_home()
        scope_label = "Global"
    elif args.install_project:
        target_dir = get_project_claude()
        scope_label = "Project"
    else:
        choice = prompt_choice("Install scope:", [
            "Global — applies to all projects (~/.claude/)",
            "Project — this project only (.claude/)"
        ])
        if "Global" in choice:
            target_dir = get_claude_home()
            scope_label = "Global"
        else:
            target_dir = get_project_claude()
            scope_label = "Project"

    print(bold(f"\nInstalling ({scope_label})..."))
    print(f"Target: {target_dir}")

    # Step 1: Copy hook
    print(bold("\n[1/4] Copying hook script"))
    if not copy_hook(target_dir, source_dir):
        sys.exit(1)

    # Step 2: Merge settings
    print(bold("\n[2/4] Registering in settings.json"))
    is_global = (target_dir == get_claude_home())
    if not merge_settings(target_dir, is_global):
        sys.exit(1)

    # Step 3: Add CLAUDE.md binding
    print(bold("\n[3/4] Adding CLAUDE.md authority binding"))
    add_claude_md_binding(target_dir)

    # Step 4: Verify
    print(bold("\n[4/4] Verifying installation"))
    if verify_installation(target_dir):
        print(green(bold("\nInstallation complete!")))
        print(f"\nRestart Claude Code to activate the workflow protocol.")
        print(f"Verify by asking: \"What development workflow rules are active?\"")
    else:
        print(yellow(bold("\nInstallation finished with warnings.")))
        print("The hook was copied and registered but verification found issues.")
        print("Check the output above and fix any problems.")


if __name__ == "__main__":
    main()
