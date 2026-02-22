#!/usr/bin/env python
"""
Claude Code Development Workflow Protocol — SessionStart Hook

Generic, project-agnostic version. Works in any repository.
Injects orchestration rules (sequencing, testing, team coordination)
once per session via SessionStart hookSpecificOutput.additionalContext.

Uses Python's json.load(sys.stdin) for reliable stdin consumption,
avoiding bash pipe/background-process race conditions.

Registered as SessionStart so the protocol is injected once per session
(on startup, resume, clear, and compact) rather than on every prompt.
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
[PROTOCOL Rule 2] TDD RED: Writing failing test for <feature>...
[PROTOCOL Rule 4] Orchestration: Agent Teams mode / Subagent fallback — <reason>.
[PROTOCOL Rule 4] Phase 2: Spawning 2 implementation teammates (backend, frontend)...
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

For features touching >2 files, use a 7-phase pipeline with maximum parallelism.
Do NOT do all work inline — delegate to Agent Teams or subagents.

### Detecting Orchestration Mode

Before Phase 1, determine which mode to use:

1. Check if Agent Teams are enabled: look for teammate-spawning capabilities in
   your available tools (e.g., the ability to spawn teammates, manage a shared task
   list across agents, or send messages between agents). Agent Teams are enabled
   when `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is set to `"1"` in the environment
   or in settings.json. If you have teammate capabilities → Agent Teams are available.
2. If Agent Teams are available → **Agent Teams mode** (REQUIRED — you MUST use it).
3. If Agent Teams are NOT available → **Subagent fallback mode** (use the `Task` tool).
4. Announce: `[PROTOCOL Rule 4] Orchestration: Agent Teams mode` or
   `[PROTOCOL Rule 4] Orchestration: Subagent fallback — Agent Teams not enabled`

You MUST NOT use Subagent fallback when Agent Teams are available. This is a violation.

### Phase 1: Research — SEQUENTIAL

**Agent Teams:** Spawn a research teammate to map affected files, existing patterns,
test coverage, and the dependency graph. Wait for completion before Phase 2.

**Subagent fallback:** Launch a `Task` call with the best role-matching `subagent_type`
from the Task tool description. Prefer plugin/custom agents (names with `:`) over
built-in types (`Explore`, `Plan`). State your selection rationale.

### Phase 2: Implementation — PARALLEL

**Agent Teams (REQUIRED when available):**
1. Analyze Phase 1 output. Partition work into **file-isolated subsystems** — no two
   teammates may edit the same file (concurrent edits cause overwrites).
2. Create tasks on the **shared task list** with `blockedBy` dependencies. Example:
   ```
   Task 1: Backend models (no deps) → starts immediately
   Task 2: Backend services (blockedBy: [1])
   Task 3: Frontend types (blockedBy: [2] — needs API contract)
   Task 4: Frontend components (blockedBy: [3])
   Task 5: Backend tests (blockedBy: [2])
   Task 6: Frontend tests (blockedBy: [4])
   ```
   When Task 2 completes, Tasks 3 AND 5 unblock in parallel — maximum concurrency.
3. Spawn implementation teammates (one per subsystem, e.g., backend, frontend, tests).
4. Each teammate's spawn prompt MUST include:
   - Phase 1 research summary (teammates do NOT inherit your conversation)
   - Their assigned file set and which files NOT to touch
   - Dependency info (what they wait on, what depends on them)
   - Project conventions discovered in Phase 1
5. Teammates self-claim tasks as dependencies resolve. Monitor progress.

**Subagent fallback:**
Implement sequentially in dependency order (backend models → services → controllers,
then frontend types → components → pages). Follow TDD (Rule 2) and test after each
file change (Rule 3). You MAY delegate isolated subsystems via `Task` tool.

### Phases 3+4+5: Review Team — PARALLEL

**Agent Teams:** Spawn 3 review teammates simultaneously. Tell them to **communicate
directly and challenge each other's findings** — this cross-pollination is the key
advantage over independent subagents.

**Subagent fallback:** Launch exactly 3 `Task` calls in a SINGLE response message
(parallel execution). Select the best role-matching `subagent_type` for each.

**Phase 3 — Fact Check:** Verify all planned changes were implemented. Check API
contracts match between backend and frontend. Check i18n completeness.

**Phase 4 — Security & Quality:** Audit for hardcoded secrets, unvalidated inputs,
injection vectors, N+1 queries. Verify naming and file-structure conventions.

**Phase 5 — Readability:** Review naming consistency, function size, nesting depth.
Flag redundant or missing comments where logic is non-obvious.

### Phase 6: Synthesis — SEQUENTIAL

Read all review outputs (teammate findings or subagent results). Fix bugs,
inconsistencies, or issues raised. Run the full test suite one final time.

### Phase 7: Finalize — SEQUENTIAL
- If the project uses containers: rebuild and verify all services are healthy.
- Smoke-test the new feature (manual or automated).
- Update project memory/docs if the project tracks build status or feature summaries.

### Phase Dependencies
```
Phase 1 (research)
  -> Phase 2 (parallel implementation via teammates OR sequential)
    -> Phases 3+4+5 (parallel review team)
      -> Phase 6 (synthesis + fix + final tests)
        -> Phase 7 (finalize)
```

### Enforcement
- Agent Teams mode is REQUIRED when `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`.
- In subagent fallback mode: prefer plugin/custom subagent_types over built-in types.
- Never skip phases. If a phase finds no issues, report it ran clean.
- Report each phase: `[PROTOCOL Rule 4] Phase N: <description>...`

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
            "hookEventName": "SessionStart",
            "additionalContext": PROTOCOL,
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
