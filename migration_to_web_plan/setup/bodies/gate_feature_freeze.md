## Problem Statement

As of 2027-01-20 the BID 2.0.0 feature set must be locked. This gate issue formally
enforces that no pull requests adding new functionality (`type:feature` label) may be
merged to `main` after this date.

## Scope

**In scope:**
- Enforcing the feature freeze policy from 2027-01-20 onwards
- Documenting any exception requests with justification and project-lead approval
- Communicating the freeze status to all contributors

**Out of scope:**
- Bug fixes (allowed until Code Freeze on 2027-02-24)
- Infrastructure and test improvements (allowed until Code Freeze)

## Acceptance Criteria

- [ ] All `type:feature` PRs opened before 2027-01-20 are either merged, closed, or explicitly deferred to 2.1.0
- [ ] Branch protection rule or PR label check configured to block `type:feature` merges after freeze
- [ ] Team notified of Feature Freeze via GitHub Discussion or email
- [ ] This gate issue is closed on or after 2027-01-20 by the project lead

## Dependencies

- **Milestone:** M10 — Feature Freeze
- **Depends on:** Epic E9 (M9) — Event System UI complete

## Definition of Done

- [ ] No new `type:feature` PRs merged after 2027-01-20
- [ ] Exception log reviewed (zero unreviewed exceptions)
- [ ] Gate issue closed by project lead
