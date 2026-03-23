## Problem Statement

A progress bar and file-level status are not enough for large batches. A visual
throughput chart and per-file timeline help operators understand processing speed.

## Scope

**In scope:**
- Real-time throughput chart (files/min) via WebSocket
- Per-file progress bar for the active file
- ETA calculation based on recent throughput

**Out of scope:**
- Historical charts (P5-04)

## Acceptance Criteria

- [ ] Chart updates without page refresh
- [ ] ETA shown when batch has processed ≥ 3 files
- [ ] Chart renders correctly at 1280×800

## Dependencies

- **Milestone:** M7 — Processing Dashboard (Phase 5)
- **Depends on:** P5-01, P2-03
- **Parent epic:** [Epic] Phase 5 — Processing Dashboard

## Definition of Done

- [ ] Code reviewed, tests pass, merged to `main`
