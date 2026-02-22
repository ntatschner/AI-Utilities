# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-Utilities is a collection of prompt engineering tools. Each tool is self-contained under `tools/` with its own language, dependencies, and build setup. Tools can be CLI utilities, importable libraries, or both.

## Architecture

```
tools/
  <tool-name>/       # Each tool is an independent unit
    README.md        # Purpose, setup, usage (follow .template/README.md)
    tests/           # Tests for that tool
    ...              # Language-specific files (pyproject.toml, package.json, etc.)
shared/
  prompts/           # Reusable prompt templates shared across tools
  schemas/           # Shared data schemas (JSON Schema, etc.)
docs/                # Cross-cutting documentation
scripts/             # Repo-level automation (CI helpers, release scripts)
```

**Key principle:** tools are isolated. Each tool owns its own dependencies and can use any language (Python, TypeScript, PowerShell, etc.). Shared assets live under `shared/`.

## Adding a New Tool

1. Copy `tools/.template/` to `tools/<tool-name>/`
2. Fill in the README following the template structure
3. Add language-specific config (e.g., `pyproject.toml`, `package.json`)
4. Add a `tests/` directory with the appropriate test framework
5. Build and test instructions go in the tool's own README

## CI / CD

- GitHub Actions workflows live at repo-root `.github/workflows/` (not inside tool subdirectories — GitHub ignores nested `.github/`)
- Each tool's workflow uses `paths:` filter for monorepo isolation and `defaults.run.working-directory` to scope commands
- Workflow naming convention: `<tool-name>.yml` (e.g., `claude-dev-workflow-hook.yml`)
- npm packages under `@thecodesaiyan` scope; release gated by git tag existence check

## Cross-Platform Testing Notes

- `node --test` glob patterns (`tests/*.test.js`) don't expand on Windows PowerShell — use explicit file paths in `package.json` test scripts
- `process.exit(0)` can truncate stdout on macOS if buffer hasn't flushed — use `process.stdout.write(data, callback)` + `process.exitCode` instead
- YAML shell quoting: avoid `node -p 'require(\"...\")` in CI — use `jq -r .field file.json` for reading package.json values

## Conventions

- Each tool must have a README with setup, usage, and configuration sections
- Tests live inside each tool's directory, not at the repo root
- Shared prompts/schemas go in `shared/`, not duplicated per tool
- Environment variables and secrets use `.env` files (gitignored) with `.env.example` as reference
- Zero-dependency tools preferred (stdlib/built-ins only) to minimize supply chain risk
- When a tool has both Node.js and Python implementations, keep them as parallel alternatives (not replacements)
