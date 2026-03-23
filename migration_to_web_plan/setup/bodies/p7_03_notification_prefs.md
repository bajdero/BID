## Problem Statement

Different users care about different events. Notification preferences allow each user
to choose which event types trigger in-app notifications or emails.

## Scope

**In scope:**
- Preferences page: event type → notification channel (none / in-app / email)
- In-app notification badge in header
- Preferences stored via API per user

**Out of scope:**
- Push notifications / mobile (deferred)

## Acceptance Criteria

- [ ] Preferences page accessible from user settings
- [ ] In-app notifications fire only for subscribed event types
- [ ] Preferences persist across sessions

## Dependencies

- **Milestone:** M9 — Event System UI (Phase 7)
- **Depends on:** P7-01, P1-04 (auth/user API)
- **Parent epic:** [Epic] Phase 7 — Event System UI

## Definition of Done

- [ ] Code reviewed, tests pass, merged to `main`
