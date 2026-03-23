## Problem Statement

The desktop app uses JSON files for persistence. A proper database abstraction layer
is needed for the web service to support concurrent access and future scalability.

## Scope

**In scope:**
- SQLAlchemy 2.0 ORM models for projects, sessions, jobs, and users
- Alembic migration scripts (initial schema)
- SQLite for development, PostgreSQL for production
- Repository pattern abstracting DB operations from business logic

**Out of scope:**
- Data migration from existing JSON files (separate task)
- Caching layer (deferred)

## Acceptance Criteria

- [ ] All models defined with Alembic migrations
- [ ] Repository layer unit-tested with SQLite in-memory DB
- [ ] Switching from SQLite to PostgreSQL requires only config change
- [ ] `alembic upgrade head` runs without errors on a fresh DB

## Dependencies

- **Milestone:** M1 — Backend API Extraction (Phase 1)
- **Parent epic:** [Epic] Phase 1 — Backend API Extraction

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Migration scripts tested on both SQLite and PostgreSQL
- [ ] Merged to `main`
