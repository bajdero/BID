## Problem Statement

There is no frontend codebase. A React TypeScript project must be scaffolded with
the right tooling so subsequent UI work has a consistent, well-configured foundation.

## Scope

**In scope:**
- React 18 + TypeScript 5 project via Vite
- ESLint + Prettier configuration
- Vitest for unit tests
- Path aliases and tsconfig settings
- `npm run dev/build/lint/test` scripts

**Out of scope:**
- Feature components (Phase 4+)

## Acceptance Criteria

- [ ] `npm run build` produces a production bundle with no TypeScript errors
- [ ] `npm run lint` passes with zero warnings
- [ ] `npm test` runs Vitest and exits 0 (with a placeholder test)

## Dependencies

- **Milestone:** M3 — Frontend Shell (Phase 3)
- **Parent epic:** [Epic] Phase 3 — Frontend Shell

## Definition of Done

- [ ] Scaffold committed to `frontend/`
- [ ] README updated with setup instructions
- [ ] Merged to `main`
