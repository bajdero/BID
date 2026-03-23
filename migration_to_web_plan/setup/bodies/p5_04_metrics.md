## Problem Statement

Management needs aggregate metrics (total images processed, error rate, average
processing time) to track system health and capacity over time.

## Scope

**In scope:**
- KPI cards: total jobs, total files, error rate, avg processing time
- Daily throughput chart (last 30 days)
- Data fetched from dedicated metrics API endpoint

**Out of scope:**
- Infrastructure-level metrics (Prometheus, Phase 8)

## Acceptance Criteria

- [ ] KPI cards display correct values from API
- [ ] Chart renders 30-day trend
- [ ] Metrics refresh on page load

## Dependencies

- **Milestone:** M7 — Processing Dashboard (Phase 5)
- **Parent epic:** [Epic] Phase 5 — Processing Dashboard

## Definition of Done

- [ ] Code reviewed, tests pass, merged to `main`
