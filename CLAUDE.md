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

## Conventions

- Each tool must have a README with setup, usage, and configuration sections
- Tests live inside each tool's directory, not at the repo root
- Shared prompts/schemas go in `shared/`, not duplicated per tool
- Environment variables and secrets use `.env` files (gitignored) with `.env.example` as reference
