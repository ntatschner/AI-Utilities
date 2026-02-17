#!/usr/bin/env python
"""
Claude Code Development Workflow Protocol — UserPromptSubmit Hook

Generic, project-agnostic version. Works in any repository.
Injects orchestration rules (sequencing, testing, team coordination)
into every Claude Code session via hookSpecificOutput.

Uses Python's json.load(sys.stdin) for reliable stdin consumption,
avoiding bash pipe/background-process race conditions.

Registered as UserPromptSubmit (not SessionStart) because SessionStart
hooks do not inject additionalContext into the conversation.
"""
import json
import sys

PROTOCOL = r"""<dev-workflow-protocol>
MANDATORY WORKFLOW RULES — You MUST follow these rules for ALL work in this project.
Violations (skipping tests, skipping planning, ignoring TDD) are NOT acceptable.

## COMPLIANCE REPORTING (NON-NEGOTIABLE)

You MUST announce rule adherence explicitly as you work. Before starting any task:
1. State which rules apply (use the Quick Reference table to determine the rule set).
2. As you execute each rule, prefix your action with `[PROTOCOL Rule N]`.
3. If you skip a rule, you MUST state why (e.g., Rule 1 small task exception).

Format:
```
[PROTOCOL Rule 0] Planning: This task modifies X files — <list files>.
[PROTOCOL Rule 1] Small task — skipping team orchestration (<=2 files, no new entity).
[PROTOCOL Rule 2] TDD RED: Writing failing test for <feature>...
[PROTOCOL Rule 3] Test loop: Running tests after <file> change...
[PROTOCOL Rule 4] Launching agent team — Phase 1: Research via Task(Explore)...
[PROTOCOL Rule 4] Phase 3+4+5: Launching 3 parallel Task agents (fact-check, security, readability)...
[PROTOCOL Rule 5] UI check: Verifying responsive layout at 375px/768px/1024px...
```

If you do NOT output these prefixes, you are violating this protocol.

## RULE 0 — Plan Before Acting

Before writing ANY code:
1. Identify every file that will be created or modified.
2. Map dependencies between changes (e.g., backend model change breaks frontend types, API contract change breaks consumers).
3. If >2 files are affected, enter Plan Mode and get approval.
4. If the plan changes mid-implementation, STOP and revise the plan.

## RULE 1 — Small Task Exception

If a task changes 2 or fewer files AND does not add a new entity/endpoint:
- Skip team orchestration (Rule 4).
- Still follow Rules 0, 2, 3 (plan, TDD, test loop).
- Still follow Rule 5 if modifying frontend components.
- Still follow Rule 6 if modifying API endpoints/services.
- Still run the full test suite before marking done.

## RULE 2 — TDD Enforcement

For new features and bug fixes:
1. RED — Write a failing test that describes the expected behavior.
2. GREEN — Write the minimum code to make the test pass.
3. IMPROVE — Refactor without changing behavior; re-run tests.
4. Target 80%+ coverage. Use the `tdd-guide` agent when available.

## RULE 3 — Test After Every Change

After EVERY code change (not just at the end):
1. Run the relevant test suite for the area you changed.
2. If ANY test fails, fix it BEFORE moving to the next change.
3. Never stack multiple untested changes — each change must pass before proceeding.
4. After all changes, run the project's full test suite.

### Auto-Detect Test Runner
Use the first match found in the project root:
- `package.json` with `test` script -> `npm test` (or `yarn test` / `pnpm test` / `bun test` based on lockfile)
- `Makefile` with `test` target -> `make test`
- `Cargo.toml` -> `cargo test`
- `go.mod` -> `go test ./...`
- `*.sln` or `*.slnx` -> `dotnet test <solution-file>`
- `pyproject.toml` or `setup.py` -> `pytest` (or `python -m pytest`)
- `build.gradle` or `pom.xml` -> `./gradlew test` or `mvn test`
- `mix.exs` -> `mix test`
- `Gemfile` -> `bundle exec rspec` or `bundle exec rake test`
- If multiple ecosystems exist (e.g., .NET backend + React frontend), run BOTH test suites.

## RULE 4 — Agent Team Orchestration (Multi-File Features)

For features touching >2 files, you MUST delegate work to specialized agents.
Do NOT do all the work yourself inline — use agent teams or subagents for each phase.
This is a 7-phase pipeline.

### Detecting Available Agents

Before starting, determine which orchestration mode to use:

**Agent Teams (preferred):** If the user has configured agent teams (e.g., agents defined in
`~/.claude/agents/` such as `planner`, `architect`, `code-reviewer`, `security-reviewer`,
`tdd-guide`, `build-error-resolver`, `e2e-runner`, `refactor-cleaner`, `doc-updater`),
use those named agents via the `Task` tool with matching `subagent_type` values.

**Subagent Fallback:** If no agent team configuration is detected, use the built-in `Task` tool
`subagent_type` values listed below for each phase.

In BOTH modes, you MUST use the `Task` tool — never do agent-designated work inline.

### Phase 1: Research (Read-Only) — SEQUENTIAL
Launch a single `Task` call:
- **Agent Team**: `subagent_type`: `everything-claude-code:planner` or `everything-claude-code:architect`
- **Subagent Fallback**: `subagent_type`: `Explore` (codebase mapping) or `Plan` (architecture)
- Prompt the agent to: map affected files, existing patterns, test coverage, and dependency graph.
- Wait for the result before proceeding. Use the output to inform Phase 2.

### Phase 2: Implementation — SEQUENTIAL
You (the parent agent) implement changes directly, following TDD (Rule 2):
- Implement in dependency order:
  - Backend: models -> services -> controllers/handlers -> middleware
  - Frontend: types -> API client -> stores/hooks -> components -> pages
  - Fullstack: backend first, then frontend consuming the new API
- Run tests after each file change (Rule 3).
- For large implementations, you MAY delegate isolated subsystems to `Task` with
  `subagent_type: general-purpose` or the appropriate language-specific agent
  (e.g., `everything-claude-code:tdd-guide`).

### Phases 3+4+5: Review Team — PARALLEL (MANDATORY)
After Phase 2 completes, you MUST launch exactly 3 `Task` calls in a SINGLE response message.
All three MUST appear in the same tool-use block so they execute in parallel.
This is NON-NEGOTIABLE — sequential launch of these phases violates the protocol.

**Phase 3 — Fact Check:**
- **Agent Team**: `subagent_type`: `feature-dev:code-reviewer`
- **Subagent Fallback**: `subagent_type`: `general-purpose`
- Prompt: "Verify all planned changes were implemented. Check API contracts: request/response
  types match between backend and frontend. Check i18n completeness. Check that API consumers
  handle the response format correctly. List files: <list from Phase 1>."

**Phase 4 — Security & Quality Audit:**
- **Agent Team**: `subagent_type`: `everything-claude-code:security-reviewer`
- **Subagent Fallback**: `subagent_type`: `feature-dev:code-reviewer`
- Prompt: "Audit for security issues: hardcoded secrets, unvalidated inputs, SQL injection,
  XSS vectors. Check performance: efficient queries, no N+1 patterns. Verify conventions:
  project patterns for naming, file structure, error handling. Files changed: <list>."

**Phase 5 — Readability & Consistency:**
- **Agent Team**: `subagent_type`: `everything-claude-code:code-reviewer`
- **Subagent Fallback**: `subagent_type`: `pr-review-toolkit:code-simplifier`
- Prompt: "Review naming consistency against existing patterns. Check code readability: small
  functions, clear names, minimal nesting. Flag comments that are redundant or missing where
  logic is non-obvious. Files changed: <list>."

### Phase 6: Parent Review — SEQUENTIAL
After phases 3-5 complete:
- Read all three agent outputs.
- Cross-check findings — fix any bugs, inconsistencies, or issues they raised.
- Run the full test suite one final time.

### Phase 7: Finalize — SEQUENTIAL
- If the project uses containers: rebuild and verify all services are healthy.
- Smoke-test the new feature (manual or automated).
- Update project memory/docs if the project tracks build status or feature summaries.

### Phase Dependencies (STRICT)
```
Phase 1 (Task: planner/architect OR Explore/Plan)
  -> Phase 2 (implement + TDD)
    -> Phases 3+4+5 (THREE parallel Task calls in ONE message — MANDATORY)
      -> Phase 6 (parent review + fix + final tests)
        -> Phase 7 (finalize)
```

### ENFORCEMENT
- You MUST use the `Task` tool for phases 1, 3, 4, and 5. Doing this work inline violates the protocol.
- Phases 3, 4, 5 MUST be launched as parallel `Task` calls in a single response. Sequential launch is a violation.
- Prefer Agent Team subagent_types when available; fall back to built-in subagent_types otherwise.
- Never skip phases. If a phase finds no issues, still report that it ran clean.
- Report each phase launch with `[PROTOCOL Rule 4] Phase N: Launching Task(subagent_type)...`

## RULE 5 — UI & Layout Standards

When modifying frontend components:
- **Responsive testing**: Verify at 375px (mobile), 768px (tablet), and 1024px (desktop) breakpoints.
- **Layout stability**: Ensure no content overflow, clipped dropdowns, or scroll containers trapping positioned elements.
- **Overflow rules**: Prefer `overflow-x-clip` over `overflow-hidden` when you need clipping without creating a scroll container. Never use `overflow-x-auto` on wrappers containing absolutely-positioned menus (CSS spec forces `overflow-y: auto` too).
- **Flexbox constraint chain**: `h-screen` (root) -> `min-h-0` (flex items) -> `overflow-y-auto` (scrollable area).
- **Accessibility basics**: Semantic HTML, keyboard navigation for interactive elements, visible focus indicators, sufficient color contrast.
- **Consistency**: Follow the project's existing design system, color tokens, and component patterns.
- **i18n**: If the project uses internationalization, ensure all user-facing strings go through the translation system. Update ALL locale files when adding new keys.

## RULE 6 — Integration Testing

When adding or modifying API endpoints, services, or middleware:

### Container-First Testing (if applicable)
1. Start the project's container stack BEFORE running tests.
2. Verify all services are healthy.
3. Test new endpoints against live containers first — catches issues that in-memory/mock providers hide (constraint violations, nullable columns, auth middleware, etc.).
4. Kill stale dev processes that may occupy the same ports.

### Backend Integration Tests
1. Use the project's test factory/fixture (e.g., WebApplicationFactory, TestServer, Supertest setup).
2. Mock or stub external dependencies: databases (in-memory/SQLite), caches (no-op), job queues (no-op), third-party APIs (mock HTTP).
3. When adding new DI services, add corresponding test doubles in the test factory.
4. When adding constructor dependencies to existing services, fix ALL test files that mock that service.
5. Be aware of global query filters, soft-delete scopes, or tenant isolation that may behave differently in test vs production databases.

### Frontend Test Isolation
1. Initialize i18n in test setup so translation keys resolve to readable strings.
2. Mock API calls (MSW, manual mocks, or test interceptors) — never hit real endpoints from unit/integration tests.
3. Test paginated API consumers: verify they handle the pagination wrapper (e.g., `.items`, `.data`, `.results`), not raw arrays.
4. For components using data-fetching libraries (React Query, SWR, Apollo), wrap in the appropriate provider with a fresh client per test.

### Common Pitfalls
- In-memory database providers don't support migrations, constraints, or triggers — guard migration calls with provider checks.
- Background job frameworks often need a no-op storage set BEFORE the app starts in test mode.
- WebApplicationFactory patterns may require a `public partial class Program { }` sentinel.
- HTTP status codes matter for client-side interceptors (e.g., 401 may trigger auto-logout — don't return 401 for validation errors).

## Quick Reference

| Situation | Required Rules |
|-----------|---------------|
| New entity + API + frontend | Rules 0, 2, 3, 4 (agent team), 5, 6 (full pipeline) |
| Multi-file feature (>2 files) | Rules 0, 2, 3, 4 (agent team), + 5/6 if applicable |
| Bug fix (1-2 files) | Rules 0, 1, 2, 3 |
| UI-only change (1-2 files) | Rules 0, 1, 2, 3, 5 |
| UI change (>2 files) | Rules 0, 2, 3, 4, 5 |
| Backend-only change (1-2 files) | Rules 0, 1, 2, 3, 6 |
| Backend change (>2 files) | Rules 0, 2, 3, 4, 6 |
| New API endpoint | Rules 0, 1, 2, 3, 6 |
| Refactor (>2 files) | Rules 0, 3, 4 + full test suite before AND after |
| Refactor (1-2 files) | Rules 0, 1, 3 + full test suite before AND after |
</dev-workflow-protocol>
""".strip()


def main():
    # Read stdin synchronously — matches CARL's json.load(sys.stdin) pattern.
    # Hook runner pipes JSON input; we must consume it before outputting.
    try:
        json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        pass  # Input doesn't matter; we just need to drain stdin

    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": PROTOCOL,
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
