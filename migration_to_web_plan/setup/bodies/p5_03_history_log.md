## Problem Statement

Operators need to review past processing jobs to diagnose recurring problems
and audit completed work.

## Scope

**In scope:**
- Paginated history table: job ID, start time, duration, file count, status
- Search by filename and filter by date range and status
- Expandable row showing per-file results

**Out of scope:**
- Real-time active jobs (P5-01)

## Acceptance Criteria

- [ ] History loads from API with pagination (50 rows/page)
- [ ] Search and filter apply without page reload
- [ ] Expanded row shows all files with individual status

## Dependencies

- **Milestone:** M7 — Processing Dashboard (Phase 5)
- **Parent epic:** [Epic] Phase 5 — Processing Dashboard

## Definition of Done

- [ ] Code reviewed, tests pass, merged to `main`
