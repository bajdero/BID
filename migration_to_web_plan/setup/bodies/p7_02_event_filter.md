## Problem Statement

A raw event log is overwhelming. Users need to filter events by type, severity,
and date range to quickly find relevant entries.

## Scope

**In scope:**
- Filter controls: event type multi-select, severity multi-select, date range picker
- Filters applied client-side for live events; server-side for historical query
- Filter state persisted in URL query params

**Out of scope:**
- Full-text search (deferred)

## Acceptance Criteria

- [ ] Filters apply without page reload
- [ ] URL query params reflect active filters (shareable links)
- [ ] Clearing filters restores full live stream

## Dependencies

- **Milestone:** M9 — Event System UI (Phase 7)
- **Depends on:** P7-01
- **Parent epic:** [Epic] Phase 7 — Event System UI

## Definition of Done

- [ ] Code reviewed, tests pass, merged to `main`
