# AGENTS.md -- Development Workflow Protocol

Follow these mandatory workflow rules for ALL implementation work.
Violations (skipping tests, skipping planning, ignoring TDD) are NOT acceptable.

## Compliance Reporting

Announce rule adherence as you work. Before starting any task:

1. State which rules apply (see the Quick Reference table at the bottom).
2. Prefix each action with `[PROTOCOL Rule N]` as you execute it.
3. If you skip a rule, state why (e.g. Rule 1 small-task exception).

Example output:

```
[PROTOCOL Rule 0] Planning: This task modifies 4 files -- api.ts, schema.ts, UserForm.tsx, user.test.ts.
[PROTOCOL Rule 1] Small task -- skipping team orchestration (2 files, no new entity).
[PROTOCOL Rule 2] TDD RED: Writing failing test for createUser validation...
[PROTOCOL Rule 3] Test loop: Running tests after schema.ts change...
[PROTOCOL Rule 4] Phase 1: Researching affected files and dependency graph...
[PROTOCOL Rule 5] UI check: Verifying responsive layout at 375px / 768px / 1024px...
[PROTOCOL Rule 6] Integration test: Starting container stack...
```

If you do NOT output these prefixes, you are violating this protocol.

## Rule 0 -- Plan Before Acting

Before writing ANY code:

1. Identify every file that will be created or modified.
2. Map dependencies between changes (e.g. backend model change breaks frontend types).
3. If more than 2 files are affected, create a detailed plan and get approval before proceeding.
4. If the plan changes mid-implementation, STOP and revise the plan.

## Rule 1 -- Small Task Exception

If a task changes 2 or fewer files AND does not add a new entity or endpoint:

- Skip team orchestration (Rule 4).
- Still follow Rules 0, 2, 3 (plan, TDD, test loop).
- Still follow Rule 5 if modifying frontend components.
- Still follow Rule 6 if modifying API endpoints or services.
- Still run the full test suite before marking done.

## Rule 2 -- TDD Enforcement

For new features and bug fixes:

1. **RED** -- Write a failing test that describes the expected behavior.
2. **GREEN** -- Write the minimum code to make the test pass.
3. **IMPROVE** -- Refactor without changing behavior; re-run tests.
4. Target 80%+ coverage.

## Rule 3 -- Test After Every Change

After EVERY code change (not just at the end):

1. Run the relevant test suite for the area you changed.
2. If ANY test fails, fix it BEFORE moving to the next change.
3. Never stack multiple untested changes -- each change must pass before proceeding.
4. After all changes, run the full test suite.

### Auto-Detect Test Runner

Use the first match found in the project root:

| Indicator | Command |
|-----------|---------|
| `package.json` with `test` script | `npm test` / `yarn test` / `pnpm test` / `bun test` (match lockfile) |
| `Makefile` with `test` target | `make test` |
| `Cargo.toml` | `cargo test` |
| `go.mod` | `go test ./...` |
| `*.sln` or `*.slnx` | `dotnet test <solution-file>` |
| `pyproject.toml` or `setup.py` | `pytest` or `python -m pytest` |
| `build.gradle` or `pom.xml` | `./gradlew test` or `mvn test` |
| `mix.exs` | `mix test` |
| `Gemfile` | `bundle exec rspec` or `bundle exec rake test` |

If multiple ecosystems exist (e.g. .NET backend + React frontend), run BOTH test suites.

## Rule 4 -- Agent Team Orchestration (Multi-File Features)

For features touching more than 2 files, use a structured 7-phase pipeline.
Do NOT do all the work inline -- delegate review work to specialized passes.

### Phase 1: Research (Read-Only) -- SEQUENTIAL

Map the affected area before implementing:

- Identify all affected files, existing patterns, test coverage, and the dependency graph.
- Wait for the research to complete before proceeding.

### Phase 2: Implementation -- SEQUENTIAL

Implement changes following TDD (Rule 2):

- Implement in dependency order:
  - Backend: models -> services -> controllers/handlers -> middleware
  - Frontend: types -> API client -> stores/hooks -> components -> pages
  - Fullstack: backend first, then frontend consuming the new API
- Run tests after each file change (Rule 3).

### Phases 3 + 4 + 5: Review Team -- PARALLEL

After Phase 2, perform three independent review passes in parallel:

**Phase 3 -- Fact Check:**
Verify all planned changes were implemented. Check API contracts -- request/response
types must match between backend and frontend. Check i18n completeness.

**Phase 4 -- Security and Quality Audit:**
Audit for hardcoded secrets, unvalidated inputs, SQL injection, XSS vectors.
Check for efficient queries and no N+1 patterns. Verify naming and file-structure conventions.

**Phase 5 -- Readability and Consistency:**
Review naming against existing patterns. Check for small functions, clear names,
minimal nesting. Flag redundant comments or missing comments where logic is non-obvious.

### Phase 6: Cross-Check -- SEQUENTIAL

After phases 3-5 complete:

- Read all review outputs and fix any bugs, inconsistencies, or issues raised.
- Run the full test suite one final time.

### Phase 7: Finalize -- SEQUENTIAL

- If the project uses containers: rebuild and verify all services are healthy.
- Smoke-test the new feature (manual or automated).
- Update project docs if the project tracks build status or feature summaries.

### Phase Dependencies

```
Phase 1 (research)
  -> Phase 2 (implement + TDD)
    -> Phases 3 + 4 + 5 (parallel reviews)
      -> Phase 6 (cross-check + fix + final tests)
        -> Phase 7 (finalize)
```

### Enforcement

- Never skip phases. If a phase finds no issues, report that it ran clean.
- Report each phase with `[PROTOCOL Rule 4] Phase N: <description>...`

## Rule 5 -- UI and Layout Standards

When modifying frontend components:

- **Responsive testing**: Verify at 375px (mobile), 768px (tablet), and 1024px (desktop).
- **Layout stability**: No content overflow, clipped dropdowns, or scroll containers trapping positioned elements.
- **Overflow rules**: Prefer `overflow-x-clip` over `overflow-hidden` when clipping without a scroll container. Never use `overflow-x-auto` on wrappers containing absolutely-positioned menus.
- **Flexbox chain**: `h-screen` (root) -> `min-h-0` (flex items) -> `overflow-y-auto` (scrollable area).
- **Accessibility**: Semantic HTML, keyboard navigation, visible focus indicators, sufficient color contrast.
- **Consistency**: Follow the project's design system, color tokens, and component patterns.
- **i18n**: If the project uses internationalization, all user-facing strings must go through the translation system. Update ALL locale files when adding keys.

## Rule 6 -- Integration Testing

When adding or modifying API endpoints, services, or middleware:

### Container-First Testing (if applicable)

1. Start the project's container stack BEFORE running tests.
2. Verify all services are healthy.
3. Test new endpoints against live containers first -- catches issues that mocks hide (constraint violations, nullable columns, auth middleware).
4. Kill stale dev processes that may occupy the same ports.

### Backend Integration Tests

1. Use the project's test factory or fixture (e.g. WebApplicationFactory, TestServer, Supertest).
2. Mock external dependencies: databases (in-memory/SQLite), caches (no-op), job queues (no-op), third-party APIs (mock HTTP).
3. When adding new DI services, add corresponding test doubles in the test factory.
4. When adding constructor dependencies, fix ALL test files that mock that service.
5. Watch for global query filters, soft-delete scopes, or tenant isolation that behaves differently in test vs production.

### Frontend Test Isolation

1. Initialize i18n in test setup so translation keys resolve to readable strings.
2. Mock API calls (MSW, manual mocks, test interceptors) -- never hit real endpoints from unit/integration tests.
3. Test paginated API consumers: verify they handle the pagination wrapper (`.items`, `.data`, `.results`), not raw arrays.
4. For data-fetching libraries (React Query, SWR, Apollo), wrap in the appropriate provider with a fresh client per test.

### Common Pitfalls

- In-memory database providers skip migrations, constraints, and triggers -- guard migration calls with provider checks.
- Background job frameworks often need no-op storage set BEFORE the app starts in test mode.
- WebApplicationFactory patterns may require a `public partial class Program { }` sentinel.
- HTTP status codes matter for client interceptors (e.g. 401 may trigger auto-logout -- do not return 401 for validation errors).

## Quick Reference

| Situation | Required Rules |
|-----------|---------------|
| New entity + API + frontend | 0, 2, 3, 4 (full pipeline), 5, 6 |
| Multi-file feature (>2 files) | 0, 2, 3, 4 + 5/6 if applicable |
| Bug fix (1-2 files) | 0, 1, 2, 3 |
| UI-only change (1-2 files) | 0, 1, 2, 3, 5 |
| UI change (>2 files) | 0, 2, 3, 4, 5 |
| Backend-only change (1-2 files) | 0, 1, 2, 3, 6 |
| Backend change (>2 files) | 0, 2, 3, 4, 6 |
| New API endpoint | 0, 1, 2, 3, 6 |
| Refactor (>2 files) | 0, 3, 4 + full test suite before AND after |
| Refactor (1-2 files) | 0, 1, 3 + full test suite before AND after |
